#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from ase.filters import StrainFilter
from ase.io import read, write
from ase.io.trajectory import Trajectory
from ase.optimize import BFGS
from ase.units import GPa
from gpaw import GPAW, PW, setup_paths

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2A import (
    CERUSSITE_TRAJ,
    MATRIX_PBESOL_DIR,
    PB_PBESOL_DIR,
    RESULTS_DIR,
    LOGS_DIR,
    RELAX_DIR,
    PROD_ECUT_EV,
    PROD_KPTS,
    SMEARING_EV,
    ATOM_FMAX_STAGE1,
    ATOM_FMAX_FINAL,
    CELL_FMAX_STAGE1,
    CELL_FMAX_FINAL,
)

RELAX_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

setup_paths.insert(0, str(MATRIX_PBESOL_DIR.resolve()))
setup_paths.insert(0, str(PB_PBESOL_DIR.resolve()))

atoms = read(CERUSSITE_TRAJ)

calc = GPAW(
    mode=PW(PROD_ECUT_EV, dedecut="estimate"),
    xc="PBEsol",
    kpts={"size": PROD_KPTS, "gamma": True},
    setups={"Pb": "paw", "default": "paw"},
    occupations={
        "name": "fermi-dirac",
        "width": SMEARING_EV,
    },
    convergence={
        "energy": 1.0e-3,
        "density": 1.0e-5,
        "eigenstates": 1.0e-7,
        "bands": "occupied",
    },
    eigensolver={"name": "dav", "niter": 4},
    random=False,
    txt=str(LOGS_DIR / "PbCO3_relax_gpaw.txt"),
)
atoms.calc = calc

stages = []


def atom_stage(name, fmax, steps):
    opt = BFGS(
        atoms,
        logfile=str(LOGS_DIR / f"{name}.log"),
        trajectory=str(RELAX_DIR / f"{name}.traj"),
    )
    converged = bool(opt.run(fmax=fmax, steps=steps))
    stages.append({
        "stage": name,
        "type": "atomic_positions_fixed_cell",
        "target_fmax_eV_A": fmax,
        "steps": int(opt.nsteps),
        "converged": converged,
        "cell_A": atoms.cell.lengths().tolist(),
    })
    write(RELAX_DIR / f"{name}_final.traj", atoms)
    return converged


def cell_stage(name, fmax, steps):
    sf = StrainFilter(
        atoms,
        mask=[1, 1, 1, 0, 0, 0],
    )
    traj = Trajectory(
        str(RELAX_DIR / f"{name}.traj"),
        "w",
        atoms,
    )
    opt = BFGS(
        sf,
        logfile=str(LOGS_DIR / f"{name}.log"),
    )
    opt.attach(traj.write, interval=1)
    converged = bool(opt.run(fmax=fmax, steps=steps))
    traj.close()

    stress = atoms.get_stress(voigt=True) / GPa
    stages.append({
        "stage": name,
        "type": "cell_only_fixed_scaled_positions",
        "target_generalized_fmax_eV": fmax,
        "steps": int(opt.nsteps),
        "converged": converged,
        "cell_A": atoms.cell.lengths().tolist(),
        "stress_GPa": [float(x) for x in stress],
    })
    write(RELAX_DIR / f"{name}_final.traj", atoms)
    return converged


# GPAW documentation recommends verifying cell and atomic relaxations
# separately.  We therefore alternate the two degrees of freedom.
atom_stage("01_atoms_exp_cell", ATOM_FMAX_STAGE1, 160)
cell_stage("02_cell_round1", CELL_FMAX_STAGE1, 120)
atom_stage("03_atoms_round1", ATOM_FMAX_STAGE1, 160)
cell_stage("04_cell_round2", CELL_FMAX_FINAL, 120)
atom_stage("05_atoms_final", ATOM_FMAX_FINAL, 220)

energy = atoms.get_potential_energy()
forces = atoms.get_forces()
stress = atoms.get_stress(voigt=True) / GPa

final_traj = RELAX_DIR / "PbCO3_relaxed_production.traj"
final_cif = RELAX_DIR / "PbCO3_relaxed_production.cif"
write(final_traj, atoms)
write(final_cif, atoms)

summary = {
    "status": "completed",
    "step": "04B2A-relaxation",
    "production_matrix": {
        "xc": "PBEsol",
        "ecut_eV": PROD_ECUT_EV,
        "kpts": list(PROD_KPTS),
    },
    "stages": stages,
    "all_stages_converged": all(
        stage["converged"] for stage in stages
    ),
    "energy_eV": float(energy),
    "energy_eV_atom": float(energy / len(atoms)),
    "cell_lengths_A": [float(x) for x in atoms.cell.lengths()],
    "cell_angles_deg": [float(x) for x in atoms.cell.angles()],
    "volume_A3": float(atoms.get_volume()),
    "max_force_eV_A": float(
        np.max(np.linalg.norm(forces, axis=1))
    ),
    "stress_GPa": [float(x) for x in stress],
    "max_abs_stress_GPa": float(np.max(np.abs(stress))),
    "final_traj": str(final_traj),
    "final_cif": str(final_cif),
}

(RESULTS_DIR / "relaxation_step04B2A.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(summary, indent=2, ensure_ascii=False))
