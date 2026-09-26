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
from gpaw import GPAW, PW, MixerDif, KohnShamConvergenceError, restart, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1B2_R2 import (
    STRUCTURE, MATRIX_DIR, U_DIR, KPTS, NBANDS,
    AFM_SIGNS, INITIAL_U_MOMENT
)


def req(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def atoms_for(a_A: float):
    atoms = read(STRUCTURE)
    atoms.set_cell(
        [(a_A, 0, 0), (0, a_A, 0), (0, 0, a_A)],
        scale_atoms=True,
    )
    uidx = [i for i, s in enumerate(atoms.get_chemical_symbols()) if s == "U"]
    moments = np.zeros(len(atoms))
    for idx, sign in zip(uidx, AFM_SIGNS):
        moments[idx] = INITIAL_U_MOMENT * sign
    atoms.set_initial_magnetic_moments(moments)
    return atoms


def attempts():
    return [
        {
            "name": "lcao_0p10",
            "width": 0.10,
            "maxiter": 800,
            "mixer": MixerDif(
                beta=0.03, nmaxold=8, weight=100.0,
                beta_m=0.05, nmaxold_m=5, weight_m=50.0,
            ),
        },
        {
            "name": "lcao_0p15_damped",
            "width": 0.15,
            "maxiter": 1100,
            "mixer": MixerDif(
                beta=0.015, nmaxold=8, weight=120.0,
                beta_m=0.03, nmaxold_m=6, weight_m=80.0,
            ),
        },
    ]


def make_calc(ueff, ecut, attempt, txt):
    # R2 deliberately uses random=False (GPAW default).  This restores
    # the deterministic LCAO initial guess instead of random wavefunctions.
    return GPAW(
        mode=PW(ecut, dedecut="estimate"),
        xc="PBEsol",
        kpts={"size": KPTS, "gamma": True},
        nbands=NBANDS,
        random=False,
        spinpol=True,
        symmetry={"point_group": False, "time_reversal": True},
        setups={"U": f":f,{ueff:.8f}", "default": "paw"},
        occupations={"name": "fermi-dirac", "width": attempt["width"]},
        mixer=attempt["mixer"],
        eigensolver={"name": "dav", "niter": 5},
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


def extract(atoms, calc, ueff, ecut, a_A, pre, pre_niter, tight_niter, gpw):
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    stress = atoms.get_stress(voigt=True) / GPa
    magmoms = atoms.get_magnetic_moments()
    uidx = [i for i, s in enumerate(atoms.get_chemical_symbols()) if s == "U"]
    umom = [float(magmoms[i]) for i in uidx]

    gap = None
    gap_error = None
    try:
        gap = float(bandgap(calc, output=None)[0])
    except Exception as exc:
        gap_error = repr(exc)

    hydrostatic_stress = float(np.mean(stress[:3]))

    return {
        "status": "converged_tight",
        "step": "04B1B2-R2",
        "system": "UO2",
        "dataset": "nc6",
        "initialization": "deterministic_LCAO_random_false",
        "Ueff_eV": float(ueff),
        "ecut_eV": float(ecut),
        "a_A": float(a_A),
        "volume_A3": float(atoms.get_volume()),
        "volume_A3_atom": float(atoms.get_volume() / len(atoms)),
        "kpts": list(KPTS),
        "nbands": NBANDS,
        "mpi_world_size": int(world.size),
        "preconvergence_strategy": pre,
        "preconvergence_iterations": int(pre_niter),
        "final_smearing_eV": 0.05,
        "final_iterations": int(tight_niter),
        "energy_eV": float(energy),
        "energy_eV_atom": float(energy / len(atoms)),
        "band_gap_eV": gap,
        "band_gap_error": gap_error,
        "U_local_moments_muB": umom,
        "U_abs_mean_moment_muB": float(np.mean(np.abs(umom))),
        "total_magnetic_moment_muB": float(np.sum(magmoms)),
        "stress_GPa": [float(x) for x in stress],
        "hydrostatic_stress_GPa": hydrostatic_stress,
        "max_abs_stress_GPa": float(np.max(np.abs(stress))),
        "max_force_eV_A": float(np.max(np.linalg.norm(forces, axis=1))),
        "restart_file": str(gpw),
    }


def main():
    ueff = float(req("UPB_R2_UEFF"))
    ecut = float(req("UPB_R2_ECUT"))
    a_A = float(req("UPB_R2_A"))
    tag = req("UPB_R2_TAG")
    out = Path(req("UPB_R2_OUT"))
    logs = Path(req("UPB_R2_LOGS"))
    restarts = Path(req("UPB_R2_RESTARTS"))

    for p in (STRUCTURE, MATRIX_DIR / "O.PBEsol", U_DIR / "U.PBEsol"):
        if not p.exists():
            raise FileNotFoundError(p)

    setup_paths.insert(0, str(MATRIX_DIR.resolve()))
    setup_paths.insert(0, str(U_DIR.resolve()))
    logs.mkdir(parents=True, exist_ok=True)
    restarts.mkdir(parents=True, exist_ok=True)

    failures = []
    pre_gpw = restarts / f"{tag}_pre.gpw"
    final_gpw = restarts / f"{tag}_tight.gpw"
    pre_success = None

    for number, attempt in enumerate(attempts(), 1):
        atoms = atoms_for(a_A)
        txt = logs / f"{tag}_attempt{number}_{attempt['name']}.txt"
        calc = make_calc(ueff, ecut, attempt, txt)
        atoms.calc = calc
        try:
            atoms.get_potential_energy()
            calc.write(pre_gpw, mode="all")
            pre_success = {
                "strategy": attempt["name"],
                "iterations": int(calc.scf.niter),
            }
            break
        except KohnShamConvergenceError as exc:
            failures.append({
                "stage": "preconvergence",
                "attempt": number,
                "strategy": attempt["name"],
                "smearing_eV": attempt["width"],
                "maxiter": attempt["maxiter"],
                "iterations": int(calc.scf.niter),
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
            "step": "04B1B2-R2",
            "Ueff_eV": ueff,
            "ecut_eV": ecut,
            "a_A": a_A,
            "attempts": failures,
            "mpi_world_size": int(world.size),
        }
    else:
        tight_txt = logs / f"{tag}_tight_0p05.txt"
        atoms, calc = restart(str(pre_gpw), txt=str(tight_txt))
        calc.set(
            occupations={"name": "fermi-dirac", "width": 0.05},
            eigensolver={"name": "dav", "niter": 5},
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
            result = extract(
                atoms, calc, ueff, ecut, a_A,
                pre_success["strategy"],
                pre_success["iterations"],
                int(calc.scf.niter),
                final_gpw,
            )
            result["failed_attempts_before_success"] = failures
        except KohnShamConvergenceError as exc:
            failures.append({
                "stage": "tight_0p05",
                "iterations": int(calc.scf.niter),
                "txt": str(tight_txt),
                "error": repr(exc),
            })
            result = {
                "status": "failed_tightening",
                "step": "04B1B2-R2",
                "Ueff_eV": ueff,
                "ecut_eV": ecut,
                "a_A": a_A,
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
