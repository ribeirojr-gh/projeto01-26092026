#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# GPAW 25.7.0 executa este arquivo via runpy quando chamado com:
#
#     gpaw python /caminho/04A_pb_singlepoint.py
#
# Nesse modo, o diretório do script não é necessariamente incluído em
# sys.path. Inserimos explicitamente a pasta da etapa antes de importar a
# configuração local.
# -----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import numpy as np
from ase.build import bulk
from ase.units import GPa
from gpaw import GPAW, PW, setup_paths
from gpaw.mpi import world

from config_step04 import ECUT, KGRID_PB, PB_A_REFERENCE


def required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(
            f"Variável de ambiente obrigatória ausente: {name}"
        )
    return value


def main() -> None:
    label = required_env("UPB_PB_LABEL")
    xc = required_env("UPB_PB_XC")
    out = required_env("UPB_PB_OUT")
    txt = required_env("UPB_PB_TXT")
    setup_dir = os.environ.get("UPB_PB_SETUP_DIR", "").strip()

    if setup_dir:
        setup_paths.insert(0, str(Path(setup_dir).resolve()))

    atoms = bulk("Pb", "fcc", a=PB_A_REFERENCE)

    calc = GPAW(
        mode=PW(ECUT, dedecut="estimate"),
        xc=xc,
        kpts={"size": KGRID_PB, "gamma": True},
        occupations={"name": "fermi-dirac", "width": 0.05},
        convergence={"density": 1.0e-6},
        setups={"Pb": "paw"},
        txt=txt,
    )
    atoms.calc = calc

    energy = atoms.get_potential_energy()
    stress = atoms.get_stress(voigt=True) / GPa
    forces = atoms.get_forces()

    record = {
        "label": label,
        "xc": xc,
        "setup_dir": setup_dir or "OFFICIAL_GPAW_SETUP_PATH",
        "mpi_world_size": int(world.size),
        "ecut_eV": float(ECUT),
        "kgrid": list(KGRID_PB),
        "a_reference_A": float(PB_A_REFERENCE),
        "natoms": len(atoms),
        "energy_eV": float(energy),
        "energy_eV_atom": float(energy / len(atoms)),
        "stress_GPa": [float(x) for x in stress],
        "max_abs_stress_GPa": float(np.max(np.abs(stress))),
        "max_force_eV_A": float(np.max(np.abs(forces))),
    }

    world.barrier()

    if world.rank == 0:
        Path(out).write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(record, indent=2, ensure_ascii=False), flush=True)

    world.barrier()


if __name__ == "__main__":
    main()
