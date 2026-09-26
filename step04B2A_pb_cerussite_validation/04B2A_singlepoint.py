#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from ase.dft.bandgap import bandgap
from ase.io import read
from ase.units import GPa
from gpaw import GPAW, PW, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2A import (
    MATRIX_PBESOL_DIR,
    PB_PBESOL_DIR,
    SMEARING_EV,
)


def req(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


structure = Path(req("UPB_PB_STRUCTURE"))
out = Path(req("UPB_PB_OUT"))
txt = req("UPB_PB_TXT")
ecut = float(req("UPB_PB_ECUT"))
kpts = tuple(int(x) for x in req("UPB_PB_KPTS").split(","))

setup_paths.insert(0, str(MATRIX_PBESOL_DIR.resolve()))
setup_paths.insert(0, str(PB_PBESOL_DIR.resolve()))

atoms = read(structure)

calc = GPAW(
    mode=PW(ecut, dedecut="estimate"),
    xc="PBEsol",
    kpts={"size": kpts, "gamma": True},
    setups={"Pb": "paw", "default": "paw"},
    occupations={
        "name": "fermi-dirac",
        "width": SMEARING_EV,
    },
    convergence={
        "energy": 5.0e-4,
        "density": 5.0e-6,
        "eigenstates": 5.0e-8,
        "bands": "occupied",
    },
    eigensolver={"name": "dav", "niter": 4},
    random=False,
    txt=txt,
)

atoms.calc = calc

energy = atoms.get_potential_energy()
forces = atoms.get_forces()
stress = atoms.get_stress(voigt=True) / GPa

gap = None
gap_error = None
try:
    gap = float(bandgap(calc, output=None)[0])
except Exception as exc:
    gap_error = repr(exc)

hydrostatic = float(np.mean(stress[:3]))

record = {
    "status": "converged",
    "step": "04B2A",
    "system": "PbCO3_cerussite",
    "xc": "PBEsol",
    "ecut_eV": ecut,
    "kpts": list(kpts),
    "mpi_world_size": int(world.size),
    "energy_eV": float(energy),
    "energy_eV_atom": float(energy / len(atoms)),
    "band_gap_eV": gap,
    "band_gap_error": gap_error,
    "max_force_eV_A": float(
        np.max(np.linalg.norm(forces, axis=1))
    ),
    "stress_GPa": [float(x) for x in stress],
    "hydrostatic_stress_GPa": hydrostatic,
    "max_abs_stress_GPa": float(np.max(np.abs(stress))),
    "volume_A3": float(atoms.get_volume()),
}

world.barrier()
if world.rank == 0:
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(record, indent=2, ensure_ascii=False))
world.barrier()
