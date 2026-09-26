#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from ase.dft.bandgap import bandgap
from gpaw import restart, setup_paths

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2B import (
    MATRIX_DIR,
    U_DIR,
    RESULTS,
    LOGS,
    GPW,
    SMEAR,
)

SOURCE_DIR = (
    PROJECT_ROOT
    / "step04B1B2_uo2_eos_R2"
    / "resultados_step04B1B2_R2"
)

SOURCE_JSON = SOURCE_DIR / "UO2_nc6_U3p0_center_1600.json"
SOURCE_GPW = (
    SOURCE_DIR
    / "restart"
    / "UO2_nc6_U3p0_center_1600_tight.gpw"
)

TARGET_GPW = GPW / "UO2_scalar_1600_U3_all.gpw"
TARGET_JSON = RESULTS / "UO2_scalar_groundstate.json"

MAX_DELTA_E_MEV_ATOM = 2.0
MAX_DELTA_GAP_EV = 0.05
MAX_DELTA_MOMENT_MUB = 0.02


def get_gap(calc):
    try:
        return float(bandgap(calc, output=None)[0]), None
    except Exception as exc:
        return None, repr(exc)


for path in (
    SOURCE_JSON,
    SOURCE_GPW,
    MATRIX_DIR / "O.PBEsol",
    U_DIR / "U.PBEsol",
):
    if not path.exists():
        raise FileNotFoundError(path)

RESULTS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
GPW.mkdir(parents=True, exist_ok=True)

reference = json.loads(
    SOURCE_JSON.read_text(encoding="utf-8")
)

if reference.get("status") != "converged_tight":
    raise RuntimeError(
        "O estado UO2 de referência do Step04B1B2-R2 não está convergido."
    )

setup_paths.insert(0, str(MATRIX_DIR.resolve()))
setup_paths.insert(0, str(U_DIR.resolve()))

# Reabre o estado APROVADO do Step04B1B2-R2.  O objetivo é gerar um novo
# .gpw com wavefunctions (mode='all') sem partir de um cold start que possa
# cair em outro mínimo DFT+U.
atoms, calc = restart(
    str(SOURCE_GPW),
    txt=str(LOGS / "UO2_SOC_reference_from_approved_branch.txt"),
)

calc.set(
    occupations={
        "name": "fermi-dirac",
        "width": SMEAR,
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

energy = atoms.get_potential_energy()
gap, gap_error = get_gap(calc)
magmoms = atoms.get_magnetic_moments()

uidx = [
    i
    for i, symbol in enumerate(atoms.get_chemical_symbols())
    if symbol == "U"
]
umom = [float(magmoms[i]) for i in uidx]
mean_m = float(np.mean(np.abs(umom)))
e_atom = float(energy / len(atoms))

dE = abs(e_atom - reference["energy_eV_atom"]) * 1000.0
dGap = (
    None
    if gap is None or reference.get("band_gap_eV") is None
    else abs(gap - reference["band_gap_eV"])
)
dM = abs(
    mean_m - reference["U_abs_mean_moment_muB"]
)

same_branch = (
    dE <= MAX_DELTA_E_MEV_ATOM
    and dGap is not None
    and dGap <= MAX_DELTA_GAP_EV
    and dM <= MAX_DELTA_MOMENT_MUB
)

record = {
    "status": (
        "converged_approved_branch"
        if same_branch
        else "branch_mismatch"
    ),
    "system": "UO2",
    "dataset": "U14_nc6",
    "Ueff_eV": 3.0,
    "ecut_eV": 1600.0,
    "kpts": [3, 3, 3],
    "energy_eV": float(energy),
    "energy_eV_atom": e_atom,
    "scalar_gap_eV": gap,
    "scalar_gap_error": gap_error,
    "U_local_moments_muB": umom,
    "U_abs_mean_moment_muB": mean_m,
    "source_reference_json": str(SOURCE_JSON),
    "source_reference_gpw": str(SOURCE_GPW),
    "branch_validation": {
        "delta_energy_meV_atom": float(dE),
        "delta_gap_eV": dGap,
        "delta_moment_muB": float(dM),
        "criteria": {
            "max_delta_energy_meV_atom":
                MAX_DELTA_E_MEV_ATOM,
            "max_delta_gap_eV":
                MAX_DELTA_GAP_EV,
            "max_delta_moment_muB":
                MAX_DELTA_MOMENT_MUB,
        },
        "same_approved_branch": bool(same_branch),
    },
}

if not same_branch:
    TARGET_JSON.write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    raise SystemExit(
        "ERRO: o restart não reproduziu o ramo eletrônico aprovado "
        "do UO2. O SOC não será executado."
    )

calc.write(TARGET_GPW, mode="all")
record["gpw_file"] = str(TARGET_GPW)

TARGET_JSON.write_text(
    json.dumps(record, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(record, indent=2, ensure_ascii=False))
