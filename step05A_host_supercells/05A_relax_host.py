#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import spglib
from ase.constraints import FixSymmetry
from ase.filters import FrechetCellFilter
from ase.io import read, write
from ase.optimize import BFGS
from ase.units import GPa
from gpaw import GPAW, PW, setup_paths

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step05A import (
    HOSTS, PAW_DIR, RESULTS, RELAX, LOGS,
    XC, ECUT_RELAX_EV, KPTS_PRIMITIVE, SMEARING_EV,
    FMAX_ATOMS_EV_A, FMAX_CELL_EV_A, SYMPREC_A,
)

mineral = os.environ.get("UPB_HOST", "").strip()
if mineral not in HOSTS:
    raise ValueError("UPB_HOST deve ser calcita ou dolomita")

RESULTS.mkdir(parents=True, exist_ok=True)
RELAX.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)

info = HOSTS[mineral]
if not info["input"].exists():
    raise FileNotFoundError(info["input"])

for symbol in ("Ca", "Mg", "C", "O"):
    p = PAW_DIR / f"{symbol}.PBEsol"
    if symbol == "Mg" and mineral == "calcita":
        continue
    if not p.exists():
        raise FileNotFoundError(p)

setup_paths.insert(0, str(PAW_DIR.resolve()))

atoms = read(info["input"])
atoms.set_constraint(
    FixSymmetry(
        atoms,
        symprec=SYMPREC_A,
        adjust_positions=True,
        adjust_cell=True,
        verbose=False,
    )
)

calc = GPAW(
    mode=PW(ECUT_RELAX_EV, dedecut="estimate"),
    xc=XC,
    kpts={"size": KPTS_PRIMITIVE, "gamma": True},
    occupations={"name": "fermi-dirac", "width": SMEARING_EV},
    random=False,
    convergence={
        "energy": 5.0e-4,
        "density": 5.0e-6,
        "eigenstates": 5.0e-8,
        "bands": "occupied",
    },
    eigensolver={"name": "dav", "niter": 4},
    txt=str(LOGS / f"{mineral}_host_relax_gpaw.txt"),
)
atoms.calc = calc

# Primeiro posições atômicas.
opt1 = BFGS(
    atoms,
    logfile=str(LOGS / f"{mineral}_01_atoms.log"),
    trajectory=str(RELAX / f"{mineral}_01_atoms.traj"),
    maxstep=0.15,
)
ok1 = bool(opt1.run(fmax=FMAX_ATOMS_EV_A, steps=180))

# Depois célula + posições mantendo a simetria.
filt = FrechetCellFilter(atoms)
opt2 = BFGS(
    filt,
    logfile=str(LOGS / f"{mineral}_02_cell_atoms.log"),
    maxstep=0.10,
)
ok2 = bool(opt2.run(fmax=FMAX_CELL_EV_A, steps=220))

final = atoms.copy()
final.set_constraint()
final.calc = atoms.calc

energy = final.get_potential_energy()
forces = final.get_forces()
stress = final.get_stress(voigt=True) / GPa

cell = (
    np.asarray(final.cell),
    np.asarray(final.get_scaled_positions()),
    np.asarray(final.numbers),
)
ds = spglib.get_symmetry_dataset(cell, symprec=0.03)

out_traj = RELAX / f"{mineral}_PBEsol1400_relaxed.traj"
out_cif = RELAX / f"{mineral}_PBEsol1400_relaxed.cif"
write(out_traj, final)
write(out_cif, final)

record = {
    "step": "05A-host-relax",
    "mineral": mineral,
    "formula": info["formula"],
    "input": str(info["input"]),
    "xc": XC,
    "ecut_eV": ECUT_RELAX_EV,
    "kpts": list(KPTS_PRIMITIVE),
    "natoms": len(final),
    "atomic_stage_converged": ok1,
    "cell_stage_converged": ok2,
    "energy_eV": float(energy),
    "energy_eV_atom": float(energy / len(final)),
    "max_force_eV_A": float(
        np.max(np.linalg.norm(forces, axis=1))
    ),
    "stress_GPa": [float(x) for x in stress],
    "max_abs_stress_GPa": float(np.max(np.abs(stress))),
    "volume_A3": float(final.get_volume()),
    "cell_lengths_A": [float(x) for x in final.cell.lengths()],
    "cell_angles_deg": [float(x) for x in final.cell.angles()],
    "spacegroup": {
        "number": int(ds.number),
        "international": str(ds.international),
    },
    "expected_spacegroup": int(info["spacegroup"]),
    "traj": str(out_traj),
    "cif": str(out_cif),
}

(RESULTS / f"{mineral}_host_relax.json").write_text(
    json.dumps(record, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(record, indent=2, ensure_ascii=False))
