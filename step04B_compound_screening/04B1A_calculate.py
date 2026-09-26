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
    MixerSum,
    KohnShamConvergenceError,
    setup_paths,
)
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1A import (
    ECUT_EV,
    MATRIX_PBESOL_DIR,
    U_POLY6_PBESOL_DIR,
    U_NC6_PBESOL_DIR,
    PB_PBESOL_DIR,
)


def req(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


def configure_setup_paths(system: str, dataset: str) -> None:
    setup_paths.insert(0, str(MATRIX_PBESOL_DIR.resolve()))

    if system in {"UO2", "delta_UO3"}:
        if dataset == "poly6":
            udir = U_POLY6_PBESOL_DIR
        elif dataset == "nc6":
            udir = U_NC6_PBESOL_DIR
        else:
            raise ValueError(f"Dataset U inválido: {dataset}")
        setup_paths.insert(0, str(udir.resolve()))
    elif system == "PbCO3":
        setup_paths.insert(0, str(PB_PBESOL_DIR.resolve()))
    else:
        raise ValueError(f"Sistema desconhecido: {system}")


def setups_for(system: str, ueff: float):
    if system not in {"UO2", "delta_UO3"}:
        return "paw"
    if abs(ueff) < 1.0e-12:
        return {"U": "paw"}
    return {"U": f":f,{ueff:.8f}"}


def attempts_for(system: str):
    if system == "UO2":
        return [
            {
                "name": "mixersum_screening",
                "width_eV": 0.15,
                "mixer": MixerSum(
                    beta=0.02,
                    nmaxold=5,
                    weight=100.0,
                ),
                "maxiter": 500,
                "eigensolver": {"name": "dav", "niter": 5},
                "convergence": {
                    "energy": 1.0e-3,
                    "density": 1.0e-5,
                    "eigenstates": 1.0e-7,
                    "bands": "occupied",
                },
            },
            {
                "name": "mixerdif_damped",
                "width_eV": 0.20,
                "mixer": MixerDif(
                    beta=0.01,
                    nmaxold=5,
                    weight=100.0,
                    beta_m=0.05,
                    nmaxold_m=5,
                    weight_m=100.0,
                ),
                "maxiter": 700,
                "eigensolver": {"name": "dav", "niter": 5},
                "convergence": {
                    "energy": 2.0e-3,
                    "density": 2.0e-5,
                    "eigenstates": 2.0e-7,
                    "bands": "occupied",
                },
            },
        ]

    return [
        {
            "name": "standard_screening",
            "width_eV": 0.05,
            "mixer": None,
            "maxiter": 400,
            "eigensolver": {"name": "dav", "niter": 3},
            "convergence": {
                "energy": 1.0e-3,
                "density": 1.0e-5,
                "eigenstates": 1.0e-7,
                "bands": "occupied",
            },
        }
    ]


def make_calculator(*, system, ueff, kpts, attempt, txt_file):
    kwargs = dict(
        mode=PW(ECUT_EV, dedecut="estimate"),
        xc="PBEsol",
        kpts={"size": kpts, "gamma": True},
        occupations={
            "name": "fermi-dirac",
            "width": attempt["width_eV"],
            "fixmagmom": system == "UO2",
        },
        setups=setups_for(system, ueff),
        spinpol=(system == "UO2"),
        symmetry="off" if system == "UO2" else {},
        convergence=attempt["convergence"],
        eigensolver=attempt["eigensolver"],
        maxiter=attempt["maxiter"],
        txt=txt_file,
        verbose=1,
    )
    if attempt["mixer"] is not None:
        kwargs["mixer"] = attempt["mixer"]
    return GPAW(**kwargs)


def calculate_record(*, atoms, calc, system, structure_file, dataset, ueff, kpts, attempt):
    atoms.calc = calc
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    stress = atoms.get_stress(voigt=True) / GPa

    try:
        magmoms = atoms.get_magnetic_moments()
    except Exception:
        magmoms = np.zeros(len(atoms))

    symbols = atoms.get_chemical_symbols()
    u_indices = [i for i, s in enumerate(symbols) if s == "U"]
    u_moments = [float(magmoms[i]) for i in u_indices]

    gap_value = None
    gap_error = None
    try:
        gap_value = float(bandgap(calc, output=None)[0])
    except Exception as exc:
        gap_error = repr(exc)

    return {
        "status": "converged",
        "system": system,
        "structure_file": str(structure_file),
        "xc": "PBEsol",
        "ecut_eV": ECUT_EV,
        "kpts": list(kpts),
        "mpi_world_size": int(world.size),
        "U_dataset": dataset or None,
        "Ueff_eV": ueff if system in {"UO2", "delta_UO3"} else None,
        "scf_strategy": attempt["name"],
        "smearing_eV": attempt["width_eV"],
        "maxiter_allowed": attempt["maxiter"],
        "scf_iterations": int(calc.scf.niter),
        "energy_eV": float(energy),
        "energy_eV_atom": float(energy / len(atoms)),
        "volume_A3": float(atoms.get_volume()),
        "max_force_eV_A": float(np.max(np.linalg.norm(forces, axis=1))),
        "stress_GPa": [float(x) for x in stress],
        "max_abs_stress_GPa": float(np.max(np.abs(stress))),
        "total_magnetic_moment_muB": float(np.sum(magmoms)),
        "U_local_moments_muB": u_moments,
        "U_abs_mean_moment_muB": (
            float(np.mean(np.abs(u_moments))) if u_moments else None
        ),
        "band_gap_eV": gap_value,
        "band_gap_error": gap_error,
    }


def main() -> None:
    system = req("UPB_B1A_SYSTEM")
    structure_file = Path(req("UPB_B1A_STRUCTURE"))
    out_file = Path(req("UPB_B1A_OUT"))
    txt_base = Path(req("UPB_B1A_TXT"))
    dataset = os.environ.get("UPB_B1A_U_DATASET", "").strip()
    ueff = float(os.environ.get("UPB_B1A_UEFF", "0.0"))
    kpts = tuple(int(x) for x in req("UPB_B1A_KPTS").split(","))

    configure_setup_paths(system, dataset)

    failures = []
    final_record = None

    for attempt_index, attempt in enumerate(attempts_for(system), start=1):
        atoms = read(structure_file)

        if system == "UO2":
            uidx = [
                i for i, s in enumerate(atoms.get_chemical_symbols())
                if s == "U"
            ]
            signs = [1.0, -1.0, -1.0, 1.0]
            magmoms = np.zeros(len(atoms))
            for i, sign in zip(uidx, signs):
                magmoms[i] = 2.0 * sign
            atoms.set_initial_magnetic_moments(magmoms)

        txt_attempt = txt_base.with_name(
            f"{txt_base.stem}_attempt{attempt_index}_"
            f"{attempt['name']}{txt_base.suffix}"
        )

        calc = make_calculator(
            system=system,
            ueff=ueff,
            kpts=kpts,
            attempt=attempt,
            txt_file=str(txt_attempt),
        )

        try:
            final_record = calculate_record(
                atoms=atoms,
                calc=calc,
                system=system,
                structure_file=structure_file,
                dataset=dataset,
                ueff=ueff,
                kpts=kpts,
                attempt=attempt,
            )
            break
        except KohnShamConvergenceError as exc:
            failures.append({
                "attempt": attempt_index,
                "strategy": attempt["name"],
                "smearing_eV": attempt["width_eV"],
                "maxiter": attempt["maxiter"],
                "scf_iterations_reached": int(calc.scf.niter),
                "txt": str(txt_attempt),
                "error": repr(exc),
            })
        finally:
            atoms.calc = None
            del calc
            gc.collect()

    world.barrier()

    if final_record is None:
        final_record = {
            "status": "failed_scf",
            "system": system,
            "structure_file": str(structure_file),
            "xc": "PBEsol",
            "ecut_eV": ECUT_EV,
            "kpts": list(kpts),
            "mpi_world_size": int(world.size),
            "U_dataset": dataset or None,
            "Ueff_eV": ueff if system in {"UO2", "delta_UO3"} else None,
            "attempts": failures,
        }
    else:
        final_record["failed_attempts_before_success"] = failures

    if world.rank == 0:
        out_file.write_text(
            json.dumps(final_record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(final_record, indent=2, ensure_ascii=False), flush=True)

    world.barrier()


if __name__ == "__main__":
    main()
