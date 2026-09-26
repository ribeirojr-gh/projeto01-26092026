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

from config_step04B1B1 import (
    UO2_STRUCTURE,
    MATRIX_PBESOL_DIR,
    U_NC6_PBESOL_DIR,
    ECUT_EV,
    KPTS,
    NBANDS,
    AFM_DOMAINS,
    INITIAL_U_MOMENT_MUB,
)


def required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def prepare_atoms(domain: str):
    atoms = read(UO2_STRUCTURE)
    u_indices = [
        i for i, symbol in enumerate(atoms.get_chemical_symbols())
        if symbol == "U"
    ]
    if len(u_indices) != 4:
        raise RuntimeError(
            f"Esperados quatro átomos U; encontrados {len(u_indices)}"
        )

    signs = AFM_DOMAINS[domain]
    moments = np.zeros(len(atoms))
    for atom_index, sign in zip(u_indices, signs):
        moments[atom_index] = INITIAL_U_MOMENT_MUB * sign
    atoms.set_initial_magnetic_moments(moments)
    return atoms


def setup_string(ueff: float) -> str:
    return f":f,{ueff:.8f}"


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


def make_pre_calc(ueff: float, attempt: dict, txt: Path) -> GPAW:
    return GPAW(
        mode=PW(ECUT_EV, dedecut="estimate"),
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
            "U": setup_string(ueff),
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


def extract_record(
    *,
    atoms,
    calc,
    ueff: float,
    domain: str,
    pre_strategy: str,
    pre_iterations: int,
    final_iterations: int,
    restart_file: Path,
):
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    stress = atoms.get_stress(voigt=True) / GPa
    magmoms = atoms.get_magnetic_moments()

    u_indices = [
        i for i, symbol in enumerate(atoms.get_chemical_symbols())
        if symbol == "U"
    ]
    u_moments = [float(magmoms[i]) for i in u_indices]

    gap = None
    gap_error = None
    try:
        gap = float(bandgap(calc, output=None)[0])
    except Exception as exc:
        gap_error = repr(exc)

    return {
        "status": "converged_tight",
        "step": "04B1B1",
        "system": "UO2",
        "dataset": "nc6",
        "Ueff_eV": float(ueff),
        "AFM_domain": domain,
        "initial_U_moment_muB": INITIAL_U_MOMENT_MUB,
        "xc": "PBEsol",
        "ecut_eV": ECUT_EV,
        "kpts": list(KPTS),
        "nbands": NBANDS,
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
        "U_local_moments_muB": u_moments,
        "U_abs_mean_moment_muB": float(
            np.mean(np.abs(u_moments))
        ),
        "max_force_eV_A": float(
            np.max(np.linalg.norm(forces, axis=1))
        ),
        "stress_GPa": [float(x) for x in stress],
        "max_abs_stress_GPa": float(np.max(np.abs(stress))),
        "restart_file": str(restart_file),
    }


def main() -> None:
    ueff = float(required_env("UPB_B1B1_UEFF"))
    domain = required_env("UPB_B1B1_DOMAIN")
    out = Path(required_env("UPB_B1B1_OUT"))
    log_dir = Path(required_env("UPB_B1B1_LOG_DIR"))
    restart_dir = Path(required_env("UPB_B1B1_RESTART_DIR"))

    if domain not in AFM_DOMAINS:
        raise ValueError(f"Domínio AFM inválido: {domain}")

    for path in (
        UO2_STRUCTURE,
        MATRIX_PBESOL_DIR / "O.PBEsol",
        U_NC6_PBESOL_DIR / "U.PBEsol",
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    setup_paths.insert(0, str(MATRIX_PBESOL_DIR.resolve()))
    setup_paths.insert(0, str(U_NC6_PBESOL_DIR.resolve()))

    log_dir.mkdir(parents=True, exist_ok=True)
    restart_dir.mkdir(parents=True, exist_ok=True)

    tag = f"U{str(ueff).replace('.', 'p')}_{domain}"
    failures = []

    pre_gpw = restart_dir / f"{tag}_pre.gpw"
    final_gpw = restart_dir / f"{tag}_tight.gpw"

    pre_success = None

    for attempt_number, attempt in enumerate(pre_attempts(), start=1):
        atoms = prepare_atoms(domain)
        txt = log_dir / (
            f"{tag}_attempt{attempt_number}_{attempt['name']}.txt"
        )
        calc = make_pre_calc(ueff, attempt, txt)
        atoms.calc = calc

        try:
            atoms.get_potential_energy()
            calc.write(pre_gpw, mode="all")
            pre_success = {
                "strategy": attempt["name"],
                "iterations": int(calc.scf.niter),
                "txt": str(txt),
            }
            atoms.calc = None
            del calc
            gc.collect()
            break
        except KohnShamConvergenceError as exc:
            failures.append({
                "stage": "preconvergence",
                "attempt": attempt_number,
                "strategy": attempt["name"],
                "smearing_eV": attempt["width"],
                "maxiter": attempt["maxiter"],
                "scf_iterations_reached": int(calc.scf.niter),
                "txt": str(txt),
                "error": repr(exc),
            })
        finally:
            try:
                atoms.calc = None
            except Exception:
                pass
            try:
                del calc
            except Exception:
                pass
            gc.collect()

    if pre_success is None:
        result = {
            "status": "failed_preconvergence",
            "step": "04B1B1",
            "system": "UO2",
            "dataset": "nc6",
            "Ueff_eV": ueff,
            "AFM_domain": domain,
            "attempts": failures,
            "mpi_world_size": int(world.size),
        }
    else:
        tight_txt = log_dir / f"{tag}_tight_0p05.txt"

        atoms, calc = restart(
            str(pre_gpw),
            txt=str(tight_txt),
        )

        # GPAW 25.7.0 permite alterar in-place apenas um subconjunto
        # restrito de parâmetros via calc.set(). Em particular, mixer e
        # maxiter NÃO podem ser alterados por set(); isso gerava:
        #   ValueError: Please use new(...) instead of set(...)
        #
        # Usar calc.new(...) não é apropriado aqui, pois a própria API
        # documenta que new() NÃO reutiliza densidade nem wavefunctions.
        #
        # Portanto mantemos o mixer e maxiter herdados da pré-convergência
        # e apertamos somente ocupações, eigensolver e critérios de
        # convergência, que são parâmetros explicitamente aceitos por
        # calc.set() no GPAW 25.7.0. Assim preservamos o estado eletrônico
        # lido do arquivo .gpw.
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
            calc.write(final_gpw)
            result = extract_record(
                atoms=atoms,
                calc=calc,
                ueff=ueff,
                domain=domain,
                pre_strategy=pre_success["strategy"],
                pre_iterations=pre_success["iterations"],
                final_iterations=int(calc.scf.niter),
                restart_file=final_gpw,
            )
            result["failed_attempts_before_success"] = failures

        except KohnShamConvergenceError as exc:
            failures.append({
                "stage": "tight_0p05",
                "smearing_eV": 0.05,
                "maxiter": 700,
                "scf_iterations_reached": int(calc.scf.niter),
                "txt": str(tight_txt),
                "error": repr(exc),
            })
            result = {
                "status": "failed_tightening",
                "step": "04B1B1",
                "system": "UO2",
                "dataset": "nc6",
                "Ueff_eV": ueff,
                "AFM_domain": domain,
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
