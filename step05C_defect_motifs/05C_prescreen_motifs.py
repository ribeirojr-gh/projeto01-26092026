#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast Machine-Learning Interatomic Potential (CHGNet) Pre-Screening
for U and Pb Defect Motifs in 160-Atom Carbonate Supercells.

Pre-relaxes defect complexes, analyzes local octahedral distortion,
evaluates vacancy binding and site-preference hierarchy prior to full DFT.
"""

import json
import time
from pathlib import Path
import numpy as np
from ase.io import read, write
from ase.optimize import BFGS
from chgnet.model.dynamics import CHGNetCalculator

SCRIPT_DIR = Path(__file__).resolve().parent
IN_DIR = SCRIPT_DIR / "structures"
OUT_DIR = SCRIPT_DIR / "structures_prescreened"
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = SCRIPT_DIR / "results"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def analyze_coordination(atoms, center_idx, neighbor_symbol="O", n_first=6):
    distances = []
    for i, s in enumerate(atoms.get_chemical_symbols()):
        if s == neighbor_symbol and i != center_idx:
            distances.append(float(atoms.get_distance(center_idx, i, mic=True)))
    distances.sort()
    first_shell = distances[:n_first]
    return {
        "distances": first_shell,
        "mean_A": float(np.mean(first_shell)),
        "std_A": float(np.std(first_shell)),
        "min_A": float(np.min(first_shell)),
        "max_A": float(np.max(first_shell)),
    }


def prescreen_case(tag, cif_path, calc):
    atoms = read(str(cif_path))
    atoms.calc = calc

    symbols = atoms.get_chemical_symbols()
    u_indices = [i for i, s in enumerate(symbols) if s == "U"]
    pb_indices = [i for i, s in enumerate(symbols) if s == "Pb"]
    active_idx = u_indices[0] if u_indices else (pb_indices[0] if pb_indices else 0)
    active_sym = symbols[active_idx]

    # Pre-relaxation coordination
    coord_init = analyze_coordination(atoms, active_idx, "O", 6 if "Oi" not in tag else 7)

    e_unrel = float(atoms.get_potential_energy())

    traj_path = OUT_DIR / f"{tag}_prescreened.traj"
    log_path = OUT_DIR / f"{tag}_prescreened.log"

    opt = BFGS(atoms, logfile=str(log_path), trajectory=str(traj_path), maxstep=0.15)
    t0 = time.time()
    converged = opt.run(fmax=0.05, steps=100)
    elapsed = time.time() - t0

    e_rel = float(atoms.get_potential_energy())
    f_rel = atoms.get_forces()
    fmax_final = float(np.max(np.linalg.norm(f_rel, axis=1)))

    coord_final = analyze_coordination(atoms, active_idx, "O", 6 if "Oi" not in tag else 7)

    # Save final pre-relaxed structure
    out_cif = OUT_DIR / f"{tag}_prescreened.cif"
    write(str(out_cif), atoms)

    return {
        "tag": tag,
        "active_element": active_sym,
        "active_index": active_idx,
        "energy_unrelaxed_eV": e_unrel,
        "energy_relaxed_eV": e_rel,
        "relaxation_energy_eV": e_rel - e_unrel,
        "fmax_eV_A": fmax_final,
        "converged": bool(converged),
        "steps": opt.get_number_of_steps(),
        "elapsed_sec": round(elapsed, 2),
        "coord_init": coord_init,
        "coord_relaxed": coord_final,
        "cif": str(out_cif),
        "traj": str(traj_path),
    }


def main():
    print("=" * 78)
    print("STEP 05C: FAST CHGNet PRE-SCREENING OF DEFECT MOTIFS")
    print("=" * 78)

    manifest_file = IN_DIR / "motifs_manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_file}. Run 05C_enumerate_motifs.py first.")

    manifest = json.loads(manifest_file.read_text())
    calc = CHGNetCalculator()

    results = {}
    for item in manifest:
        tag = item["tag"]
        cif_p = Path(item["cif"])
        print(f"\n>>> Pre-screening motif: {tag} ({item['description']})")
        res = prescreen_case(tag, cif_p, calc)
        res["description"] = item["description"]
        res["type"] = item["type"]
        results[tag] = res
        print(f"    E_rel = {res['energy_relaxed_eV']:.4f} eV | Delta_E_relax = {res['relaxation_energy_eV']:.4f} eV | "
              f"fmax = {res['fmax_eV_A']:.4f} eV/A ({res['steps']} steps, {res['elapsed_sec']}s)")
        print(f"    <{res['active_element']}-O> = {res['coord_relaxed']['mean_A']:.4f} +/- {res['coord_relaxed']['std_A']:.4f} A")

    summary_file = REPORTS_DIR / "prescreening_summary.json"
    summary_file.write_text(json.dumps(results, indent=2))
    print(f"\n[OK] Prescreening summary saved to {summary_file}")


if __name__ == "__main__":
    main()
