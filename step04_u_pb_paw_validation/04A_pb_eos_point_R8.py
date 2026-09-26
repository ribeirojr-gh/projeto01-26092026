#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from ase.build import bulk
from ase.units import GPa
from gpaw import GPAW, PW, setup_paths
from gpaw.mpi import world

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04_R8 import ECUT_EV, KGRID, SMEARING_EV


def req(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Variável obrigatória ausente: {name}")
    return value


label = req("UPB_EOS_LABEL")
setup_kind = req("UPB_EOS_SETUP_KIND")
out = req("UPB_EOS_OUT")
txt = req("UPB_EOS_TXT")
a = float(req("UPB_EOS_A"))
setup_dir = os.environ.get("UPB_EOS_SETUP_DIR", "").strip()

if setup_kind not in {"official", "generated"}:
    raise ValueError(f"UPB_EOS_SETUP_KIND inválido: {setup_kind}")

if setup_kind == "generated":
    if not setup_dir:
        raise RuntimeError("Setup gerado requer UPB_EOS_SETUP_DIR.")
    setup_paths.insert(0, str(Path(setup_dir).resolve()))

atoms = bulk("Pb", "fcc", a=a)

atoms.calc = GPAW(
    mode=PW(ECUT_EV, dedecut="estimate"),
    xc="PBE",
    kpts={"size": KGRID, "gamma": True},
    occupations={"name": "fermi-dirac", "width": SMEARING_EV},
    convergence={"density": 1.0e-6},
    setups={"Pb": "paw"},
    txt=txt,
)

energy = atoms.get_potential_energy()
stress = atoms.get_stress(voigt=True) / GPa
forces = atoms.get_forces()
volume = atoms.get_volume()

record = {
    "label": label,
    "setup_kind": setup_kind,
    "setup_dir": setup_dir or "OFFICIAL_GPAW_SETUP_PATH",
    "xc": "PBE",
    "mpi_world_size": int(world.size),
    "ecut_eV": float(ECUT_EV),
    "kgrid": list(KGRID),
    "smearing_eV": float(SMEARING_EV),
    "a_A": float(a),
    "volume_A3_atom": float(volume / len(atoms)),
    "natoms": len(atoms),
    "energy_eV": float(energy),
    "energy_eV_atom": float(energy / len(atoms)),
    "stress_GPa": [float(x) for x in stress],
    "mean_normal_stress_GPa": float(np.mean(stress[:3])),
    "max_abs_stress_GPa": float(np.max(np.abs(stress))),
    "max_force_eV_A": float(np.max(np.abs(forces))),
}

world.barrier()
if world.rank == 0:
    Path(out).write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"{setup_kind:9s} a={a:.2f} Å "
        f"E={record['energy_eV_atom']:.9f} eV/atom "
        f"<σ>={record['mean_normal_stress_GPa']:.6f} GPa",
        flush=True,
    )
world.barrier()
