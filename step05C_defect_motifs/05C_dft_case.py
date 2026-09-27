#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Precision First-Principles DFT (GPAW Plane-Wave) Driver for Step 05C.
Calculates electronic structure and performs ionic relaxation of
U and Pb defect motifs in 160-atom Calcite and Dolomite supercells.
"""

import gc
import json
import os
import sys
import time
from pathlib import Path
import numpy as np

from ase.io import read, write
from ase.optimize import BFGS
from gpaw import GPAW, PW, setup_paths
from gpaw.mpi import world

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config_step05C import (
    XC,
    ECUT_EV,
    SMEARING_EV,
    MPI_PROCESSES,
    NBANDS,
    PAW_DIRS,
    SETUPS,
    FINAL_FMAX_EV_A,
    MAX_STEPS,
)

# Register validated PAW potential directories in GPAW search path
for p in PAW_DIRS:
    p_str = str(p.resolve())
    if p_str not in setup_paths:
        setup_paths.insert(0, p_str)

SCRIPT_DIR = Path(__file__).resolve().parent
STRUCTURES_DIR = SCRIPT_DIR / "structures_prescreened"
LOGS_DIR = SCRIPT_DIR / "logs"
RESULTS_DIR = SCRIPT_DIR / "results"
RELAX_DIR = RESULTS_DIR / "relax"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
RELAX_DIR.mkdir(parents=True, exist_ok=True)

tag = os.environ.get("UPB_MOTIF_TAG")
if not tag:
    raise ValueError("Environment variable UPB_MOTIF_TAG must be set.")

cif_file = STRUCTURES_DIR / f"{tag}_prescreened.cif"
if not cif_file.exists():
    # Fallback to unrelaxed structure if prescreened does not exist
    cif_file = SCRIPT_DIR / "structures" / f"{tag}.cif"
    if not cif_file.exists():
        raise FileNotFoundError(f"Structure not found for tag: {tag}")


def create_calculator(txt_log: Path) -> GPAW:
    return GPAW(
        mode=PW(ECUT_EV, dedecut="estimate"),
        xc=XC,
        kpts={"size": (1, 1, 1), "gamma": True},
        nbands=NBANDS,
        occupations={"name": "fermi-dirac", "width": SMEARING_EV},
        setups=SETUPS,
        random=False,
        parallel={
            "domain": world.size,
            "band": 1,
            "kpt": 1,
            "sl_auto": True,
        },
        convergence={
            "energy": 1.0e-3,
            "density": 1.0e-5,
            "eigenstates": 1.0e-7,
            "bands": "occupied",
        },
        eigensolver={"name": "dav", "niter": 4},
        txt=str(txt_log),
    )


def main():
    if world.rank == 0:
        print("=" * 78)
        print(f"STEP 05C DFT CASE: {tag} ({world.size} MPI ranks)")
        print(f"Structure: {cif_file.name}")
        print("=" * 78)

    atoms = read(str(cif_file))
    log_file = LOGS_DIR / f"{tag}_dft.log"
    calc = create_calculator(log_file)
    atoms.calc = calc

    t0 = time.time()
    e_unrel = float(atoms.get_potential_energy())
    f_unrel = atoms.get_forces()
    fmax_unrel = float(np.max(np.linalg.norm(f_unrel, axis=1)))

    if world.rank == 0:
        print(f">>> SCF Unrelaxed: E = {e_unrel:.6f} eV | fmax = {fmax_unrel:.6f} eV/A ({time.time() - t0:.1f}s)")

    traj_file = RELAX_DIR / f"{tag}_relaxed.traj"
    cif_out = RELAX_DIR / f"{tag}_relaxed.cif"

    opt = BFGS(
        atoms,
        logfile=str(LOGS_DIR / f"{tag}_bfgs.log"),
        trajectory=str(traj_file),
        maxstep=0.12,
    )

    t_rel0 = time.time()
    converged = bool(opt.run(fmax=FINAL_FMAX_EV_A, steps=MAX_STEPS))
    rel_time = time.time() - t_rel0

    e_rel = float(atoms.get_potential_energy())
    f_rel = atoms.get_forces()
    fmax_rel = float(np.max(np.linalg.norm(f_rel, axis=1)))

    # Coordination analysis for active metal center (U or Pb)
    symbols = atoms.get_chemical_symbols()
    u_idx = [i for i, s in enumerate(symbols) if s == "U"]
    pb_idx = [i for i, s in enumerate(symbols) if s == "Pb"]
    active_idx = u_idx[0] if u_idx else (pb_idx[0] if pb_idx else 0)
    active_sym = symbols[active_idx]

    o_dists = sorted([
        float(atoms.get_distance(active_idx, i, mic=True))
        for i, s in enumerate(symbols)
        if s == "O"
    ])
    first_shell = o_dists[:6] if "Oi" not in tag else o_dists[:7]

    summary = {
        "status": "converged" if converged else "unconverged",
        "step": "05C-DFT",
        "tag": tag,
        "formula": atoms.get_chemical_formula(),
        "natoms": len(atoms),
        "active_element": active_sym,
        "energy_unrelaxed_eV": e_unrel,
        "energy_relaxed_eV": e_rel,
        "relaxation_energy_eV": e_rel - e_unrel,
        "fmax_initial_eV_A": fmax_unrel,
        "fmax_final_eV_A": fmax_rel,
        "bfgs_steps": opt.get_number_of_steps(),
        "converged": converged,
        "relaxation_time_sec": round(rel_time, 2),
        "coordination_first_shell_A": first_shell,
        "coordination_mean_A": float(np.mean(first_shell)),
        "coordination_std_A": float(np.std(first_shell)),
        "relaxed_traj": str(traj_file),
        "relaxed_cif": str(cif_out),
    }

    if world.rank == 0:
        write(str(cif_out), atoms)
        out_json = RESULTS_DIR / f"{tag}.json"
        out_json.write_text(json.dumps(summary, indent=2))
        print(f">>> Concluido {tag}: E_rel = {e_rel:.6f} eV | fmax = {fmax_rel:.6f} eV/A ({opt.get_number_of_steps()} steps)")
        print(f">>> Geometria <{active_sym}-O> = {np.mean(first_shell):.4f} +/- {np.std(first_shell):.4f} A")
        print(f">>> Resultados salvos em {out_json}")

    # Memory release
    try:
        del atoms.calc
        del calc
    except Exception:
        pass
    gc.collect()


if __name__ == "__main__":
    main()
