#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from ase.dft.kpoints import mindistance2monkhorstpack
from ase.io import read

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step05B import (
    SUPERCELLS,
    RESULTS,
    KPT_MIN_DISTANCE_DIAGNOSTIC_A,
    KPT_MIN_DISTANCE_FINAL_A,
)

RESULTS.mkdir(parents=True, exist_ok=True)

record = {
    "step": "05B-R1-preflight",
    "reason": (
        "Diagnose the k-point load before DFT after the original "
        "80-atom calcite job was killed with SIGKILL."
    ),
    "cases": {},
}

for mineral in ("calcita", "dolomita"):
    record["cases"][mineral] = {}
    for n in (80, 160, 240):
        atoms = read(SUPERCELLS[mineral][n])

        meshes = {}
        for label, distance in (
            ("original_24A", KPT_MIN_DISTANCE_DIAGNOSTIC_A),
            ("R1_final_16A", KPT_MIN_DISTANCE_FINAL_A),
        ):
            mesh = tuple(
                int(x)
                for x in mindistance2monkhorstpack(
                    atoms,
                    min_distance=distance,
                    maxperdim=8,
                    even=False,
                )
            )
            meshes[label] = {
                "min_distance_A": distance,
                "mesh": list(mesh),
                "reducible_kpoints": int(np.prod(mesh)),
            }

        record["cases"][mineral][str(n)] = meshes

out = RESULTS / "kpoint_preflight_step05B_R1.json"
out.write_text(
    json.dumps(record, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(record, indent=2, ensure_ascii=False))
