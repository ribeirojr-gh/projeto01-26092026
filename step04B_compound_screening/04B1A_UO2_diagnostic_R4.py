#!/usr/bin/env python3
from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
from ase.dft.bandgap import bandgap
from ase.io import read
from ase.units import GPa, Ha
from gpaw import (
    GPAW,
    PW,
    MixerDif,
    KohnShamConvergenceError,
    setup_paths,
)
from gpaw.hubbard import HubbardU
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

DATASET = os.environ["UPB_R4_DATASET"]
OUT = Path(os.environ["UPB_R4_OUT"])
TXT_DIR = Path(os.environ["UPB_R4_TXT_DIR"])
GPW_DIR = Path(os.environ["UPB_R4_GPW_DIR"])

STRUCTURE = SCRIPT_DIR / "estruturas" / "UO2_fluorite_exp.traj"
MATRIX_SETUP_DIR = (
    PROJECT_ROOT
    / "step03_paw_pbesol_benchmark"
    / "paw_generated"
    / "PBEsol"
)
STEP04A = PROJECT_ROOT / "step04_u_pb_paw_validation"

if DATASET == "poly6":
    U_SETUP_DIR = STEP04A / "paw_generated" / "U" / "PBEsol"
elif DATASET == "nc6":
    U_SETUP_DIR = (
        STEP04A
        / "paw_candidates"
        / "U_R5_pseudization"
        / "U14_nc6"
        / "PBEsol"
    )
else:
    raise ValueError(f"Dataset desconhecido: {DATASET}")

for path in (STRUCTURE, MATRIX_SETUP_DIR / "O.PBEsol",
             U_SETUP_DIR / "U.PBEsol"):
    if not path.exists():
        raise FileNotFoundError(path)

setup_paths.insert(0, str(MATRIX_SETUP_DIR.resolve()))
setup_paths.insert(0, str(U_SETUP_DIR.resolve()))

TXT_DIR.mkdir(parents=True, exist_ok=True)
GPW_DIR.mkdir(parents=True, exist_ok=True)

ECUT = 1400.0
KPTS = (3, 3, 3)
NBANDS = 80


def fresh_atoms():
    atoms = read(STRUCTURE)
    uidx = [
        i for i, symbol in enumerate(atoms.get_chemical_symbols())
        if symbol == "U"
    ]
    if len(uidx) != 4:
        raise RuntimeError(f"Esperados 4 U; encontrados {len(uidx)}")

    # 1-k collinear AFM screening pattern.
    signs = (1.0, -1.0, -1.0, 1.0)
    moments = np.zeros(len(atoms))
    for i, sign in zip(uidx, signs):
        moments[i] = 2.0 * sign
    atoms.set_initial_magnetic_moments(moments)
    return atoms


def common_kwargs(*, setup_string: str, symmetry: Any,
                  width: float, maxiter: int,
                  txt: str, random: bool = True):
    # fixmagmom is deliberately omitted in R4.  The magnetic subgroup,
    # constructed from the signed initial moments, is allowed to preserve AFM.
    return dict(
        mode=PW(ECUT, dedecut="estimate"),
        xc="PBEsol",
        kpts={"size": KPTS, "gamma": True},
        nbands=NBANDS,
        random=random,
        spinpol=True,
        symmetry=symmetry,
        setups={"U": setup_string, "default": "paw"},
        occupations={
            "name": "fermi-dirac",
            "width": width,
        },
        mixer=MixerDif(
            beta=0.03,
            nmaxold=8,
            weight=100.0,
            beta_m=0.05,
            nmaxold_m=5,
            weight_m=50.0,
        ),
        eigensolver={"name": "dav", "niter": 5},
        convergence={
            "energy": 1.0e-3,
            "density": 1.0e-5,
            "eigenstates": 1.0e-7,
            "bands": "occupied",
        },
        maxiter=maxiter,
        verbose=1,
        txt=txt,
    )


def extract_record(atoms, calc, *, strategy: str,
                   ueff: float, normalized: bool,
                   gpw_path: Path | None):
    forces = atoms.get_forces()
    stress = atoms.get_stress(voigt=True) / GPa
    magmoms = atoms.get_magnetic_moments()
    symbols = atoms.get_chemical_symbols()
    uidx = [i for i, s in enumerate(symbols) if s == "U"]
    umom = [float(magmoms[i]) for i in uidx]

    gap = None
    gap_error = None
    try:
        gap = float(bandgap(calc, output=None)[0])
    except Exception as exc:
        gap_error = repr(exc)

    record = {
        "status": "converged",
        "dataset": DATASET,
        "strategy": strategy,
        "Ueff_eV": float(ueff),
        "hubbard_normalized": bool(normalized),
        "mpi_world_size": int(world.size),
        "ecut_eV": ECUT,
        "kpts": list(KPTS),
        "nbands": NBANDS,
        "scf_iterations": int(calc.scf.niter),
        "energy_eV": float(atoms.get_potential_energy()),
        "energy_eV_atom": float(
            atoms.get_potential_energy() / len(atoms)
        ),
        "band_gap_eV": gap,
        "band_gap_error": gap_error,
        "total_magnetic_moment_muB": float(np.sum(magmoms)),
        "U_local_moments_muB": umom,
        "U_abs_mean_moment_muB": float(
            np.mean(np.abs(umom))
        ),
        "max_force_eV_A": float(
            np.max(np.linalg.norm(forces, axis=1))
        ),
        "stress_GPa": [float(x) for x in stress],
        "max_abs_stress_GPa": float(
            np.max(np.abs(stress))
        ),
        "gpw_file": str(gpw_path) if gpw_path else None,
    }
    return record


def cold_attempt(config):
    atoms = fresh_atoms()
    txt = TXT_DIR / f"{DATASET}_{config['name']}.txt"
    calc = GPAW(**common_kwargs(
        setup_string=config["setup"],
        symmetry=config["symmetry"],
        width=config["width"],
        maxiter=config["maxiter"],
        txt=str(txt),
    ))
    atoms.calc = calc

    try:
        atoms.get_potential_energy()
        gpw = GPW_DIR / f"{DATASET}_{config['name']}.gpw"
        calc.write(gpw, mode="all")
        record = extract_record(
            atoms,
            calc,
            strategy=config["name"],
            ueff=4.0,
            normalized=config["normalized"],
            gpw_path=gpw,
        )
    except KohnShamConvergenceError as exc:
        record = {
            "status": "failed_scf",
            "dataset": DATASET,
            "strategy": config["name"],
            "Ueff_eV": 4.0,
            "hubbard_normalized": config["normalized"],
            "scf_iterations": int(calc.scf.niter),
            "txt": str(txt),
            "error": repr(exc),
        }
    finally:
        atoms.calc = None
        del calc
        gc.collect()
    return record


def attach_hubbard_in_place(calc, atoms, ueff: float):
    """Diagnostic continuation without discarding the converged U=0 density.

    GPAW stores the Hubbard object on each PAW setup.  We update the setup
    objects shared by wave functions, density and Hamiltonian and then reset
    only the SCF loop/mixer.  This is explicitly a diagnostic use of the
    GPAW-25.7 internal API, not a production workflow.
    """
    hu = HubbardU(
        U=[ueff / Ha],
        l=[3],
        scale=[True],
    )

    collections = [
        calc.wfs.setups,
        calc.density.setups,
        calc.hamiltonian.setups,
    ]

    symbols = atoms.get_chemical_symbols()
    seen = set()
    for collection in collections:
        for atom_index, symbol in enumerate(symbols):
            if symbol != "U":
                continue
            setup = collection[atom_index]
            key = id(setup)
            if key in seen:
                continue
            setup.hubbard_u = hu
            seen.add(key)

    calc.parameters.setups = {
        "U": f":f,{ueff:.8f}",
        "default": "paw",
    }
    calc.results.clear()
    calc.scf.reset()
    calc.scf.converged = False
    calc.density.mixer.reset()


def ramp_attempt():
    atoms = fresh_atoms()
    txt = TXT_DIR / f"{DATASET}_ramp_inplace.txt"

    calc = GPAW(**common_kwargs(
        setup_string="paw",
        symmetry={},
        width=0.10,
        maxiter=500,
        txt=str(txt),
    ))
    atoms.calc = calc

    stages = []
    try:
        atoms.get_potential_energy()
        gpw0 = GPW_DIR / f"{DATASET}_ramp_U0p0.gpw"
        calc.write(gpw0, mode="all")
        stages.append(extract_record(
            atoms, calc,
            strategy="ramp_inplace_U0",
            ueff=0.0,
            normalized=True,
            gpw_path=gpw0,
        ))

        for ueff in (0.5, 1.0, 2.0, 3.0, 4.0):
            attach_hubbard_in_place(calc, atoms, ueff)
            atoms.get_potential_energy()
            gpw = GPW_DIR / (
                f"{DATASET}_ramp_U{str(ueff).replace('.', 'p')}.gpw"
            )
            calc.write(gpw, mode="all")
            stages.append(extract_record(
                atoms, calc,
                strategy="ramp_inplace",
                ueff=ueff,
                normalized=True,
                gpw_path=gpw,
            ))

        result = {
            "status": "converged",
            "dataset": DATASET,
            "strategy": "ramp_inplace",
            "target_Ueff_eV": 4.0,
            "stages": stages,
            "final": stages[-1],
            "internal_api_warning": True,
        }
    except KohnShamConvergenceError as exc:
        result = {
            "status": "failed_scf",
            "dataset": DATASET,
            "strategy": "ramp_inplace",
            "target_Ueff_eV": 4.0,
            "stages_completed": stages,
            "failed_at_next_stage_after_Ueff_eV": (
                stages[-1]["Ueff_eV"] if stages else None
            ),
            "scf_iterations": int(calc.scf.niter),
            "txt": str(txt),
            "error": repr(exc),
            "internal_api_warning": True,
        }
    finally:
        atoms.calc = None
        del calc
        gc.collect()
    return result


def main():
    # Magnetic symmetry is enabled. GPAW uses signed initial moments when
    # determining symmetry-compatible atomic identities.
    configs = [
        {
            "name": "sym_freeM_scaled",
            "setup": ":f,4.0",
            "normalized": True,
            "symmetry": {},
            "width": 0.10,
            "maxiter": 500,
        },
        {
            "name": "sym_freeM_unscaled",
            "setup": ":f,4.0,0",
            "normalized": False,
            "symmetry": {},
            "width": 0.10,
            "maxiter": 500,
        },
        {
            "name": "noPG_freeM_scaled",
            "setup": ":f,4.0",
            "normalized": True,
            "symmetry": {
                "point_group": False,
                "time_reversal": True,
            },
            "width": 0.15,
            "maxiter": 600,
        },
    ]

    attempts = []
    success = None

    for config in configs:
        record = cold_attempt(config)
        attempts.append(record)
        if record["status"] == "converged":
            success = record
            break

    ramp = None
    if success is None:
        ramp = ramp_attempt()
        if ramp["status"] == "converged":
            success = ramp["final"]

    result = {
        "step": "04B1A-R4",
        "purpose": (
            "Diagnose whether fixed total magnetization, disabled magnetic "
            "symmetry, Hubbard normalization, or cold-start orbital "
            "degeneracy caused the UO2 DFT+U failures."
        ),
        "dataset": DATASET,
        "cold_start_attempts": attempts,
        "ramp_attempt": ramp,
        "target_Ueff_4eV_converged": success is not None,
        "selected_success": success,
        "production_authorization": False,
    }

    world.barrier()
    if world.rank == 0:
        OUT.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    world.barrier()


if __name__ == "__main__":
    main()
