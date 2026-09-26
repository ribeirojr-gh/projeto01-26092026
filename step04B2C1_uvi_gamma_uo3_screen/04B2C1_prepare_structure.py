#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import requests
import spglib
from ase.io import read, write
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2C1 import (
    STRUCT_DIR, CIF, CONV_TRAJ, PRIM_TRAJ, MANIFEST,
    COD_ID, EXP_A_A, EXP_B_A, EXP_C_A, EXP_SPACEGROUP,
    EXP_TEMPERATURE_K, EXP_SHORTEST_UO_A
)

URLS = [
    f"https://www.crystallography.net/cod/{COD_ID}.cif",
    f"https://qiserver.ugr.es/cod/{COD_ID}.cif",
]

STRUCT_DIR.mkdir(parents=True, exist_ok=True)

if not CIF.exists():
    errors = []
    for url in URLS:
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            text = r.text
            if "_cell_length_a" not in text or "U" not in text:
                raise RuntimeError("conteúdo não parece um CIF UO3 válido")
            CIF.write_text(text, encoding="utf-8")
            break
        except Exception as exc:
            errors.append(f"{url}: {exc!r}")
    else:
        raise RuntimeError(
            "Não foi possível baixar COD 1527742.\n" + "\n".join(errors)
        )

sha = hashlib.sha256(CIF.read_bytes()).hexdigest()

pmg = Structure.from_file(str(CIF))
sga = SpacegroupAnalyzer(pmg, symprec=1e-3, angle_tolerance=0.1)
primitive = sga.get_primitive_standard_structure()

pmg.to(filename=str(STRUCT_DIR / "gamma_UO3_293K_conventional.cif"))
primitive.to(filename=str(STRUCT_DIR / "gamma_UO3_293K_primitive.cif"))

conv_ase = read(str(STRUCT_DIR / "gamma_UO3_293K_conventional.cif"))
prim_ase = read(str(STRUCT_DIR / "gamma_UO3_293K_primitive.cif"))
write(CONV_TRAJ, conv_ase)
write(PRIM_TRAJ, prim_ase)

def spg(atoms, symprec):
    cell = (
        np.asarray(atoms.cell),
        np.asarray(atoms.get_scaled_positions()),
        np.asarray(atoms.numbers),
    )
    ds = spglib.get_symmetry_dataset(cell, symprec=symprec)
    return {
        "number": int(ds.number),
        "international": str(ds.international),
        "hall": str(ds.hall),
    }

symbols = prim_ase.get_chemical_symbols()
nU = symbols.count("U")
nO = symbols.count("O")

u_indices = [i for i, s in enumerate(symbols) if s == "U"]
o_indices = [i for i, s in enumerate(symbols) if s == "O"]
uo = [
    prim_ase.get_distance(i, j, mic=True)
    for i in u_indices for j in o_indices
]
shortest_uo = float(min(uo))

lengths = sorted(float(x) for x in conv_ase.cell.lengths())
exp_sorted = sorted([EXP_A_A, EXP_B_A, EXP_C_A])
cell_error = [
    abs(a - b) / b * 100.0
    for a, b in zip(lengths, exp_sorted)
]

manifest = {
    "step": "04B2C1-structure",
    "source": {
        "COD_ID": COD_ID,
        "reference": (
            "Loopstra, Taylor & Waugh, Journal of Solid State Chemistry "
            "20 (1977) 9-19; neutron powder refinement at 293 K."
        ),
        "temperature_K": EXP_TEMPERATURE_K,
        "spacegroup_expected": EXP_SPACEGROUP,
        "cell_A": [EXP_A_A, EXP_B_A, EXP_C_A],
        "shortest_UO_reference_A": EXP_SHORTEST_UO_A,
    },
    "sha256_cif": sha,
    "conventional": {
        "natoms": len(conv_ase),
        "formula": conv_ase.get_chemical_formula(),
        "cell_lengths_A": [float(x) for x in conv_ase.cell.lengths()],
        "cell_angles_deg": [float(x) for x in conv_ase.cell.angles()],
        "spacegroup": spg(conv_ase, 1e-2),
        "sorted_cell_relative_errors_percent": cell_error,
    },
    "primitive": {
        "natoms": len(prim_ase),
        "nU": nU,
        "nO": nO,
        "formula": prim_ase.get_chemical_formula(),
        "spacegroup": spg(prim_ase, 1e-2),
        "shortest_UO_A": shortest_uo,
    },
}

valid = (
    manifest["conventional"]["spacegroup"]["number"] == EXP_SPACEGROUP
    and max(cell_error) < 0.2
    and nU == 8
    and nO == 24
    and len(prim_ase) == 32
    and abs(shortest_uo - EXP_SHORTEST_UO_A) < 0.10
)

manifest["structure_gate_passes"] = bool(valid)

MANIFEST.write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(manifest, indent=2, ensure_ascii=False))

if not valid:
    raise SystemExit(21)
