#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from ase.io import read
from ase.units import GPa
from gpaw import GPAW, PW, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step05A import (
    PAW_DIR, RESULTS, RELAX, LOGS,
    XC, ECUT_VALIDATE_EV, KPTS_PRIMITIVE, SMEARING_EV,
)

mineral = os.environ.get("UPB_HOST", "").strip()
traj = RELAX / f"{mineral}_PBEsol1400_relaxed.traj"
if not traj.exists():
    raise FileNotFoundError(traj)

setup_paths.insert(0, str(PAW_DIR.resolve()))
atoms = read(traj)

calc = GPAW(
    mode=PW(ECUT_VALIDATE_EV, dedecut="estimate"),
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
    txt=str(LOGS / f"{mineral}_host_validate1600.txt"),
)
atoms.calc = calc
energy = atoms.get_potential_energy()
forces = atoms.get_forces()
stress = atoms.get_stress(voigt=True) / GPa

record = {
    "step": "05A-host-validation",
    "mineral": mineral,
    "ecut_eV": ECUT_VALIDATE_EV,
    "kpts": list(KPTS_PRIMITIVE),
    "energy_eV": float(energy),
    "energy_eV_atom": float(energy / len(atoms)),
    "max_force_eV_A": float(
        np.max(np.linalg.norm(forces, axis=1))
    ),
    "stress_GPa": [float(x) for x in stress],
    "max_abs_stress_GPa": float(np.max(np.abs(stress))),
    "mpi_world_size": int(world.size),
}

world.barrier()
if world.rank == 0:
    (RESULTS / f"{mineral}_host_validate1600.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(record, indent=2, ensure_ascii=False))
world.barrier()
