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
from gpaw import GPAW, PW, MixerDif, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2C1 import (
    PRIM_TRAJ, MATRIX_DIR, U_DIR, RESULTS, LOGS, GPW,
    XC, SMEARING_EV, NBANDS
)


def req(name):
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


case = req("UPB_UVI_CASE")
ueff = float(req("UPB_UVI_UEFF"))
ecut = float(req("UPB_UVI_ECUT"))
kpts = tuple(int(x) for x in req("UPB_UVI_KPTS").split(","))
spin_mode = req("UPB_UVI_SPIN")
out = Path(req("UPB_UVI_OUT"))
txt = Path(req("UPB_UVI_TXT"))
gpw = Path(req("UPB_UVI_GPW"))

RESULTS.mkdir(parents=True, exist_ok=True)
LOGS.mkdir(parents=True, exist_ok=True)
GPW.mkdir(parents=True, exist_ok=True)

setup_paths.insert(0, str(MATRIX_DIR.resolve()))
setup_paths.insert(0, str(U_DIR.resolve()))

atoms = read(PRIM_TRAJ)

spinpol = spin_mode == "seeded"
if spinpol:
    uidx = [
        i for i, s in enumerate(atoms.get_chemical_symbols())
        if s == "U"
    ]
    m = np.zeros(len(atoms))
    for n, idx in enumerate(uidx):
        m[idx] = 1.0 if n % 2 == 0 else -1.0
    atoms.set_initial_magnetic_moments(m)

setups = {
    "U": "paw" if abs(ueff) < 1e-12 else f":f,{ueff:.8f}",
    "default": "paw",
}

kwargs = {}
if spinpol:
    kwargs.update(
        spinpol=True,
        symmetry={"point_group": False, "time_reversal": True},
        mixer=MixerDif(
            beta=0.03, nmaxold=8, weight=100.0,
            beta_m=0.05, nmaxold_m=5, weight_m=50.0,
        ),
        maxiter=900,
    )

calc = GPAW(
    mode=PW(ecut, dedecut="estimate"),
    xc=XC,
    kpts={"size": kpts, "gamma": True},
    nbands=NBANDS,
    random=False,
    setups=setups,
    occupations={"name": "fermi-dirac", "width": SMEARING_EV},
    eigensolver={"name": "dav", "niter": 5},
    convergence={
        "energy": 5.0e-4,
        "density": 5.0e-6,
        "eigenstates": 5.0e-8,
        "bands": "occupied",
    },
    txt=str(txt),
    **kwargs,
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

record = {
    "status": "converged",
    "step": "04B2C1",
    "case": case,
    "system": "gamma-UO3-Fddd",
    "formal_U_oxidation_state": 6,
    "dataset": "U14_nc6",
    "xc": XC,
    "Ueff_eV": ueff,
    "spin_mode": spin_mode,
    "ecut_eV": ecut,
    "kpts": list(kpts),
    "natoms": len(atoms),
    "energy_eV": float(energy),
    "energy_eV_atom": float(energy / len(atoms)),
    "band_gap_eV": gap,
    "band_gap_error": gap_error,
    "max_force_eV_A": float(
        np.max(np.linalg.norm(forces, axis=1))
    ),
    "stress_GPa": [float(x) for x in stress],
    "hydrostatic_stress_GPa": float(np.mean(stress[:3])),
    "max_abs_stress_GPa": float(np.max(np.abs(stress))),
    "mpi_world_size": int(world.size),
}

if spinpol:
    magmoms = atoms.get_magnetic_moments()
    uidx = [
        i for i, s in enumerate(atoms.get_chemical_symbols())
        if s == "U"
    ]
    um = [float(magmoms[i]) for i in uidx]
    record["U_local_moments_muB"] = um
    record["U_abs_mean_moment_muB"] = float(
        np.mean(np.abs(um))
    )
    record["total_magnetic_moment_muB"] = float(
        np.sum(magmoms)
    )

calc.write(gpw)
record["gpw_file"] = str(gpw)

world.barrier()
if world.rank == 0:
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(record, indent=2, ensure_ascii=False))
world.barrier()
