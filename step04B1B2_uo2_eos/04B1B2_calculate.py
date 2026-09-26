#!/usr/bin/env python3
from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

import numpy as np
from ase.dft.bandgap import bandgap
from ase.io import read
from ase.units import GPa
from gpaw import (
    GPAW,
    PW,
    MixerDif,
    KohnShamConvergenceError,
    restart,
    setup_paths,
)
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1B2 import (
    UO2_STRUCTURE,
    MATRIX_PBESOL_DIR,
    U_NC6_PBESOL_DIR,
    KPTS,
    NBANDS,
    AFM_DOMAIN,
    AFM_SIGNS,
    INITIAL_U_MOMENT_MUB,
)


def req(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def prepare_atoms(a_A: float):
    atoms = read(UO2_STRUCTURE)

    # Preserva coordenadas fracionárias e muda apenas a célula cúbica.
    atoms.set_cell(
        [(a_A, 0.0, 0.0),
         (0.0, a_A, 0.0),
         (0.0, 0.0, a_A)],
        scale_atoms=True,
    )

    uidx = [
        i for i, symbol in enumerate(atoms.get_chemical_symbols())
        if symbol == "U"
    ]
    if len(uidx) != 4:
        raise RuntimeError(
            f"Esperados quatro átomos U; encontrados {len(uidx)}"
        )

    moments = np.zeros(len(atoms))
    for idx, sign in zip(uidx, AFM_SIGNS):
        moments[idx] = INITIAL_U_MOMENT_MUB * sign
    atoms.set_initial_magnetic_moments(moments)

    return atoms


def pre_attempts():
    return [
        {
            "name": "pre_0p10",
            "width": 0.10,
            "maxiter": 700,
            "mixer": MixerDif(
                beta=0.03,
                nmaxold=8,
                weight=100.0,
                beta_m=0.05,
                nmaxold_m=5,
                weight_m=50.0,
            ),
        },
        {
            "name": "pre_0p15_damped",
            "width": 0.15,
            "maxiter": 1000,
            "mixer": MixerDif(
                beta=0.015,
                nmaxold=8,
                weight=120.0,
                beta_m=0.03,
                nmaxold_m=6,
                weight_m=80.0,
            ),
        },
    ]


def make_calc(
    *,
    ueff: float,
    ecut: float,
    attempt: dict,
    txt: Path,
):
    return GPAW(
        mode=PW(ecut, dedecut="estimate"),
        xc="PBEsol",
        kpts={"size": KPTS, "gamma": True},
        nbands=NBANDS,
        random=True,
        spinpol=True,
        symmetry={
            "point_group": False,
            "time_reversal": True,
        },
        setups={
            "U": f":f,{ueff:.8f}",
            "default": "paw",
        },
        occupations={
            "name": "fermi-dirac",
            "width": attempt["width"],
        },
        mixer=attempt["mixer"],
        eigensolver={
            "name": "dav",
            "niter": 5,
        },
        convergence={
            "energy": 1.0e-3,
            "density": 1.0e-5,
            "eigenstates": 1.0e-7,
            "bands": "occupied",
        },
        maxiter=attempt["maxiter"],
        verbose=1,
        txt=str(txt),
    )


def extract(
    *,
    atoms,
    calc,
    ueff: float,
    ecut: float,
    a_A: float,
    pre_strategy: str,
    pre_iterations: int,
    final_iterations: int,
    restart_file: Path,
):
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    stress = atoms.get_stress(voigt=True) / GPa
    magmoms = atoms.get_magnetic_moments()

    uidx = [
        i for i, symbol in enumerate(atoms.get_chemical_symbols())
        if symbol == "U"
    ]
    umom = [float(magmoms[i]) for i in uidx]

    gap = None
    gap_error = None
    try:
        gap = float(bandgap(calc, output=None)[0])
    except Exception as exc:
        gap_error = repr(exc)

    return {
        "status": "converged_tight",
        "step": "04B1B2",
        "system": "UO2",
        "dataset": "nc6",
        "Ueff_eV": float(ueff),
        "AFM_domain": AFM_DOMAIN,
        "xc": "PBEsol",
        "ecut_eV": float(ecut),
        "kpts": list(KPTS),
        "nbands": NBANDS,
        "a_A": float(a_A),
        "volume_A3": float(atoms.get_volume()),
        "volume_A3_atom": float(atoms.get_volume() / len(atoms)),
        "mpi_world_size": int(world.size),
        "hubbard_normalized": True,
        "symmetry_protocol": {
            "point_group": False,
            "time_reversal": True,
        },
        "fixmagmom": False,
        "preconvergence_strategy": pre_strategy,
        "preconvergence_iterations": int(pre_iterations),
        "final_smearing_eV": 0.05,
        "final_iterations": int(final_iterations),
        "energy_eV": float(energy),
        "energy_eV_atom": float(energy / len(atoms)),
        "band_gap_eV": gap,
        "band_gap_error": gap_error,
        "total_magnetic_moment_muB": float(np.sum(magmoms)),
        "U_local_moments_muB": umom,
        "U_abs_mean_moment_muB": float(np.mean(np.abs(umom))),
        "max_force_eV_A": float(
            np.max(np.linalg.norm(forces, axis=1))
        ),
        "stress_GPa": [float(x) for x in stress],
        "max_abs_stress_GPa": float(np.max(np.abs(stress))),
        "restart_file": str(restart_file),
    }


def main():
    ueff = float(req("UPB_B1B2_UEFF"))
    ecut = float(req("UPB_B1B2_ECUT"))
    a_A = float(req("UPB_B1B2_A"))
    tag = req("UPB_B1B2_TAG")
    out = Path(req("UPB_B1B2_OUT"))
    logs = Path(req("UPB_B1B2_LOG_DIR"))
    restarts = Path(req("UPB_B1B2_RESTART_DIR"))

    for path in (
        UO2_STRUCTURE,
        MATRIX_PBESOL_DIR / "O.PBEsol",
        U_NC6_PBESOL_DIR / "U.PBEsol",
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    setup_paths.insert(0, str(MATRIX_PBESOL_DIR.resolve()))
    setup_paths.insert(0, str(U_NC6_PBESOL_DIR.resolve()))

    logs.mkdir(parents=True, exist_ok=True)
    restarts.mkdir(parents=True, exist_ok=True)

    failures = []
    pre_success = None
    pre_gpw = restarts / f"{tag}_pre.gpw"
    tight_gpw = restarts / f"{tag}_tight.gpw"

    for number, attempt in enumerate(pre_attempts(), start=1):
        atoms = prepare_atoms(a_A)
        txt = logs / (
            f"{tag}_attempt{number}_{attempt['name']}.txt"
        )
        calc = make_calc(
            ueff=ueff,
            ecut=ecut,
            attempt=attempt,
            txt=txt,
        )
        atoms.calc = calc

        try:
            atoms.get_potential_energy()
            calc.write(pre_gpw, mode="all")
            pre_success = {
                "strategy": attempt["name"],
                "iterations": int(calc.scf.niter),
                "txt": str(txt),
            }
            break
        except KohnShamConvergenceError as exc:
            failures.append({
                "stage": "preconvergence",
                "attempt": number,
                "strategy": attempt["name"],
                "smearing_eV": attempt["width"],
                "maxiter": attempt["maxiter"],
                "scf_iterations_reached": int(calc.scf.niter),
                "txt": str(txt),
                "error": repr(exc),
            })
        finally:
            atoms.calc = None
            del calc
            gc.collect()

    if pre_success is None:
        result = {
            "status": "failed_preconvergence",
            "step": "04B1B2",
            "system": "UO2",
            "dataset": "nc6",
            "Ueff_eV": ueff,
            "ecut_eV": ecut,
            "a_A": a_A,
            "attempts": failures,
            "mpi_world_size": int(world.size),
        }
    else:
        tight_txt = logs / f"{tag}_tight_0p05.txt"
        atoms, calc = restart(
            str(pre_gpw),
            txt=str(tight_txt),
        )

        # GPAW 25.7.0: apenas parâmetros aceitos por calc.set().
        # Mixer/maxiter são preservados do restart para manter densidade
        # e wavefunctions.
        calc.set(
            occupations={
                "name": "fermi-dirac",
                "width": 0.05,
            },
            eigensolver={
                "name": "dav",
                "niter": 5,
            },
            convergence={
                "energy": 5.0e-4,
                "density": 5.0e-6,
                "eigenstates": 5.0e-8,
                "bands": "occupied",
            },
        )

        try:
            atoms.get_potential_energy()
            calc.write(tight_gpw)
            result = extract(
                atoms=atoms,
                calc=calc,
                ueff=ueff,
                ecut=ecut,
                a_A=a_A,
                pre_strategy=pre_success["strategy"],
                pre_iterations=pre_success["iterations"],
                final_iterations=int(calc.scf.niter),
                restart_file=tight_gpw,
            )
            result["failed_attempts_before_success"] = failures

        except KohnShamConvergenceError as exc:
            failures.append({
                "stage": "tight_0p05",
                "smearing_eV": 0.05,
                "scf_iterations_reached": int(calc.scf.niter),
                "txt": str(tight_txt),
                "error": repr(exc),
            })
            result = {
                "status": "failed_tightening",
                "step": "04B1B2",
                "system": "UO2",
                "dataset": "nc6",
                "Ueff_eV": ueff,
                "ecut_eV": ecut,
                "a_A": a_A,
                "preconvergence": pre_success,
                "attempts": failures,
                "mpi_world_size": int(world.size),
            }
        finally:
            atoms.calc = None
            del calc
            gc.collect()

    world.barrier()
    if world.rank == 0:
        out.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    world.barrier()


if __name__ == "__main__":
    main()
