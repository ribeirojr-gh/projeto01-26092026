#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests
from ase import Atoms
from ase.io import read, write
from ase.spacegroup import crystal

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1A import (
    STRUCTURES_DIR,
    UO2_A_EXP_A,
    DELTA_UO3_A_REF_A,
    CERUSSITE_COD_ID,
    CERUSSITE_URL,
)

STRUCTURES_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# UO2: fluorite Fm-3m, conventional cell, experimental a ~ 5.4706 Å.
# U at 4a, O at 8c.
# -------------------------------------------------------------------------
uo2 = crystal(
    symbols=["U", "O"],
    basis=[(0.0, 0.0, 0.0), (0.25, 0.25, 0.25)],
    spacegroup=225,
    cellpar=[
        UO2_A_EXP_A,
        UO2_A_EXP_A,
        UO2_A_EXP_A,
        90.0,
        90.0,
        90.0,
    ],
    primitive_cell=False,
)

# 1-k collinear AFM screening pattern on the four U atoms.
# This is a benchmark state, not a claim to reproduce the experimental
# non-collinear 3-k ground state.
u_indices = [i for i, s in enumerate(uo2.get_chemical_symbols()) if s == "U"]
u_fracs = uo2.get_scaled_positions()[u_indices]

# Alternate sign according to z layer; tie-break using x+y to guarantee 2+/2-.
signs = []
for f in u_fracs:
    phase = int(round(2.0 * (f[0] + f[1] + f[2]))) % 2
    signs.append(1.0 if phase == 0 else -1.0)

if signs.count(1.0) != 2 or signs.count(-1.0) != 2:
    signs = [1.0, -1.0, -1.0, 1.0]

magmoms = [0.0] * len(uo2)
for idx, sign in zip(u_indices, signs):
    magmoms[idx] = 2.0 * sign
uo2.set_initial_magnetic_moments(magmoms)

write(STRUCTURES_DIR / "UO2_fluorite_exp.cif", uo2)
write(STRUCTURES_DIR / "UO2_fluorite_exp.traj", uo2)

# -------------------------------------------------------------------------
# delta-UO3: ideal ReO3-type screening reference, Pm-3m.
# U at (0,0,0); O at face centers.
# Nominal U(VI), 5f0.  This is deliberately a compact screening phase;
# gamma-UO3 will be used later in the final U(VI) validation.
# -------------------------------------------------------------------------
a = DELTA_UO3_A_REF_A
uo3 = Atoms(
    symbols=["U", "O", "O", "O"],
    scaled_positions=[
        (0.0, 0.0, 0.0),
        (0.5, 0.5, 0.0),
        (0.5, 0.0, 0.5),
        (0.0, 0.5, 0.5),
    ],
    cell=[(a, 0, 0), (0, a, 0), (0, 0, a)],
    pbc=True,
)
uo3.set_initial_magnetic_moments([0.0] * len(uo3))
write(STRUCTURES_DIR / "delta_UO3_ref.cif", uo3)
write(STRUCTURES_DIR / "delta_UO3_ref.traj", uo3)

# -------------------------------------------------------------------------
# PbCO3 cerussite: COD 9008411, neutron single-crystal refinement.
# Cache locally for reproducibility after first download.
# -------------------------------------------------------------------------
cif = STRUCTURES_DIR / f"cerussite_COD_{CERUSSITE_COD_ID}.cif"
if not cif.exists():
    print(f"Baixando cerussita COD {CERUSSITE_COD_ID}: {CERUSSITE_URL}")
    response = requests.get(CERUSSITE_URL, timeout=60)
    response.raise_for_status()
    cif.write_bytes(response.content)

cer = read(cif)
write(STRUCTURES_DIR / "cerussite_exp.traj", cer)

metadata = {
    "UO2": {
        "formula": "UO2",
        "role": "U(IV) screening reference",
        "space_group": "Fm-3m (225)",
        "a_A": UO2_A_EXP_A,
        "magnetism": (
            "1-k collinear AFM screening configuration; experimental "
            "ground state is non-collinear 3-k AFM."
        ),
    },
    "delta_UO3": {
        "formula": "UO3",
        "role": "compact U(VI) screening reference",
        "space_group": "Pm-3m (221), ideal ReO3 type",
        "a_A": DELTA_UO3_A_REF_A,
        "warning": (
            "Not the final ambient-condition U(VI) validation phase. "
            "gamma-UO3 will be required before production authorization."
        ),
    },
    "cerussite": {
        "formula": "PbCO3",
        "role": "Pb(II) carbonate transferability reference",
        "COD_ID": CERUSSITE_COD_ID,
        "source_url": CERUSSITE_URL,
        "expected_space_group": "Pmcn/Pnma setting, No. 62",
    },
}

(STRUCTURES_DIR / "referencias_estruturas.json").write_text(
    json.dumps(metadata, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("Estruturas preparadas:")
for p in sorted(STRUCTURES_DIR.iterdir()):
    print(" -", p.name)
