#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from gpaw import GPAW, setup_paths
from gpaw.spinorbit import soc_eigenstates

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2C1 import (
    RESULTS, MATRIX_DIR, U_DIR
)

GPW = RESULTS / "gpw" / "gammaUO3_U3_1600_k222.gpw"

setup_paths.insert(0, str(MATRIX_DIR.resolve()))
setup_paths.insert(0, str(U_DIR.resolve()))

calc = GPAW(str(GPW))


def gap(states):
    eig = np.asarray(states.eigenvalues(), dtype=float)
    ef = float(states.fermi_level)
    occ = eig[eig <= ef]
    emp = eig[eig > ef]
    if occ.size == 0 or emp.size == 0:
        return None
    return float(max(0.0, np.min(emp) - np.max(occ)))


results = {}
for name, scale in (("scale0", 0.0), ("scale0p5", 0.5), ("scale1", 1.0)):
    states = soc_eigenstates(calc, scale=scale)
    results[name] = {
        "scale": scale,
        "indirect_gap_eV": gap(states),
        "fermi_level_eV": float(states.fermi_level),
        "band_energy_eV_cell": float(states.calculate_band_energy()),
    }

record = {
    "status": "completed",
    "step": "04B2C1-SOC",
    "system": "gamma-UO3-Fddd",
    "method": "GPAW-25.7 soc_eigenstates non-self-consistent",
    "results": results,
}

(RESULTS / "gammaUO3_SOC_sensitivity.json").write_text(
    json.dumps(record, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(json.dumps(record, indent=2, ensure_ascii=False))
