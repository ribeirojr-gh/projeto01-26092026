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
from gpaw import GPAW, PW, MixerDif, KohnShamConvergenceError, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1A_R5 import (
    STRUCTURE, MATRIX_DIR, U_DIRS, ECUT, KPTS, NBANDS
)


def env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def fresh_atoms():
    atoms = read(STRUCTURE)
    uidx = [i for i, s in enumerate(atoms.get_chemical_symbols()) if s == "U"]
    if len(uidx) != 4:
        raise RuntimeError(f"Esperados 4 átomos U; encontrados {len(uidx)}")

    moments = np.zeros(len(atoms))
    for idx, sign in zip(uidx, (1.0, -1.0, -1.0, 1.0)):
        moments[idx] = 2.0 * sign
    atoms.set_initial_magnetic_moments(moments)
    return atoms


def u_setup(ueff: float) -> str:
    return "paw" if abs(ueff) < 1.0e-12 else f":f,{ueff:.8f}"


def scf_attempts():
    return [
        {
            "name": "common_noPG_primary",
            "width": 0.10,
            "maxiter": 600,
            "mixer": MixerDif(
                beta=0.03, nmaxold=8, weight=100.0,
                beta_m=0.05, nmaxold_m=5, weight_m=50.0,
            ),
        },
        {
            "name": "common_noPG_damped",
            "width": 0.15,
            "maxiter": 900,
            "mixer": MixerDif(
                beta=0.015, nmaxold=8, weight=120.0,
                beta_m=0.03, nmaxold_m=6, weight_m=80.0,
            ),
        },
    ]


def make_calc(ueff: float, attempt: dict, txt: Path) -> GPAW:
    return GPAW(
        mode=PW(ECUT, dedecut="estimate"),
        xc="PBEsol",
        kpts={"size": KPTS, "gamma": True},
        nbands=NBANDS,
        random=True,
        spinpol=True,
        symmetry={"point_group": False, "time_reversal": True},
        setups={"U": u_setup(ueff), "default": "paw"},
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


def extract(atoms, calc, dataset: str, ueff: float, attempt: dict) -> dict:
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

    return {
        "status": "converged",
        "step": "04B1A-R5",
        "system": "UO2",
        "dataset": dataset,
        "Ueff_eV": float(ueff),
        "hubbard_normalized": True,
        "symmetry_protocol": {
            "point_group": False,
            "time_reversal": True,
        },
        "fixmagmom": False,
        "scf_strategy": attempt["name"],
        "smearing_eV": attempt["width"],
        "maxiter_allowed": attempt["maxiter"],
        "scf_iterations": int(calc.scf.niter),
        "mpi_world_size": int(world.size),
        "ecut_eV": ECUT,
        "kpts": list(KPTS),
        "nbands": NBANDS,
        "energy_eV": float(energy),
        "energy_eV_atom": float(energy / len(atoms)),
        "band_gap_eV": gap,
        "band_gap_error": gap_error,
        "total_magnetic_moment_muB": float(np.sum(magmoms)),
        "U_local_moments_muB": umom,
        "U_abs_mean_moment_muB": float(np.mean(np.abs(umom))),
        "max_force_eV_A": float(np.max(np.linalg.norm(forces, axis=1))),
        "stress_GPa": [float(x) for x in stress],
        "max_abs_stress_GPa": float(np.max(np.abs(stress))),
    }


def main():
    dataset = env("UPB_R5_DATASET")
    ueff = float(env("UPB_R5_UEFF"))
    out = Path(env("UPB_R5_OUT"))
    txt_dir = Path(env("UPB_R5_TXT_DIR"))
    gpw_dir = Path(env("UPB_R5_GPW_DIR"))

    if dataset not in U_DIRS:
        raise ValueError(f"Dataset inválido: {dataset}")

    udir = U_DIRS[dataset]
    for p in (STRUCTURE, MATRIX_DIR / "O.PBEsol", udir / "U.PBEsol"):
        if not p.exists():
            raise FileNotFoundError(p)

    setup_paths.insert(0, str(MATRIX_DIR.resolve()))
    setup_paths.insert(0, str(udir.resolve()))
    txt_dir.mkdir(parents=True, exist_ok=True)
    gpw_dir.mkdir(parents=True, exist_ok=True)

    failures = []
    result = None

    for number, attempt in enumerate(scf_attempts(), start=1):
        atoms = fresh_atoms()
        tag = str(ueff).replace(".", "p")
        txt = txt_dir / (
            f"UO2_{dataset}_Ueff_{tag}_attempt{number}_{attempt['name']}.txt"
        )
        calc = make_calc(ueff, attempt, txt)
        atoms.calc = calc

        try:
            result = extract(atoms, calc, dataset, ueff, attempt)
            gap = result.get("band_gap_eV")
            if abs(ueff - 4.0) < 1e-12 or (
                gap is not None and 1.5 <= gap <= 3.0
            ):
                gpw = gpw_dir / f"UO2_{dataset}_Ueff_{tag}.gpw"
                calc.write(gpw, mode="all")
                result["gpw_file"] = str(gpw)
            else:
                result["gpw_file"] = None
            break

        except KohnShamConvergenceError as exc:
            failures.append({
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

    world.barrier()

    if result is None:
        result = {
            "status": "failed_scf",
            "step": "04B1A-R5",
            "system": "UO2",
            "dataset": dataset,
            "Ueff_eV": ueff,
            "hubbard_normalized": True,
            "symmetry_protocol": {
                "point_group": False,
                "time_reversal": True,
            },
            "fixmagmom": False,
            "attempts": failures,
            "mpi_world_size": int(world.size),
        }
    else:
        result["failed_attempts_before_success"] = failures

    if world.rank == 0:
        out.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    world.barrier()


if __name__ == "__main__":
    main()
