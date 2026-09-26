#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2B import RESULTS

SOURCE_JSON = (
    PROJECT_ROOT
    / "step04B1B2_uo2_eos_R2"
    / "resultados_step04B1B2_R2"
    / "UO2_nc6_U3p0_center_1600.json"
)

SOURCE_GPW = (
    PROJECT_ROOT
    / "step04B1B2_uo2_eos_R2"
    / "resultados_step04B1B2_R2"
    / "restart"
    / "UO2_nc6_U3p0_center_1600_tight.gpw"
)

TARGET_JSON = RESULTS / "UO2_scalar_groundstate.json"

for path in (SOURCE_JSON, SOURCE_GPW):
    if not path.exists():
        raise FileNotFoundError(path)

src = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))

if src.get("status") != "converged_tight":
    raise RuntimeError(
        "O estado UO2 de referência do Step04B1B2-R2 não está convergido."
    )

record = {
    "status": "approved_reference_reused",
    "system": "UO2",
    "dataset": "U14_nc6",
    "Ueff_eV": 3.0,
    "ecut_eV": 1600.0,
    "kpts": [3, 3, 3],
    "energy_eV": src["energy_eV"],
    "energy_eV_atom": src["energy_eV_atom"],
    "scalar_gap_eV": src.get("band_gap_eV"),
    "scalar_gap_error": src.get("band_gap_error"),
    "U_local_moments_muB": src.get("U_local_moments_muB"),
    "U_abs_mean_moment_muB": src.get("U_abs_mean_moment_muB"),
    "source_reference_json": str(SOURCE_JSON),
    "soc_source_gpw": str(SOURCE_GPW),
    "branch_policy": (
        "Use exactly the Step04B1B2-R2 approved scalar branch. "
        "No new cold-start UO2 calculation is performed in Step04B2B-R3."
    ),
}

TARGET_JSON.write_text(
    json.dumps(record, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(record, indent=2, ensure_ascii=False))
