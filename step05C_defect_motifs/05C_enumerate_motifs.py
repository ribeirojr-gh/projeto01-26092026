#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic Defect Motif Enumerator for Step 05C.
Constructs neutral, charge-compensated U and Pb defect complexes
in 160-atom Calcite and Dolomite supercells.
"""

import json
from pathlib import Path
import numpy as np
from ase.io import read, write
from ase import Atom, Atoms

from config_step05C import SUPERCELLS

OUT_DIR = Path(__file__).resolve().parent / "structures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_center_site(atoms: Atoms, element: str) -> int:
    """Find index of specified element closest to fractional coordinates (0.5, 0.5, 0.5)."""
    scaled = atoms.get_scaled_positions(wrap=True)
    cell = np.asarray(atoms.cell)
    indices = [i for i, s in enumerate(atoms.get_chemical_symbols()) if s == element]
    scores = []
    for i in indices:
        ds = scaled[i] - 0.5
        ds -= np.round(ds)
        dist = float(np.linalg.norm(ds @ cell))
        scores.append((dist, i))
    scores.sort()
    return scores[0][1]


def build_calcite_motifs(host: Atoms) -> dict:
    motifs = {}
    ca_center = get_center_site(host, "Ca")
    ca_indices = [i for i, s in enumerate(host.get_chemical_symbols()) if s == "Ca" and i != ca_center]
    ca_dists = [(float(host.get_distance(ca_center, i, mic=True)), i) for i in ca_indices]
    ca_dists.sort()

    # 1. Pb_Ca isovalent (Step 05B reference)
    pb_ca = host.copy()
    pb_ca[ca_center].symbol = "Pb"
    motifs["calcita_160_Pb_Ca"] = {
        "atoms": pb_ca,
        "type": "isovalent_Pb",
        "description": "Isovalent Pb2+ substitution on Ca2+ site (q=0)",
        "defect_indices": {"Pb": ca_center},
    }

    # 2. U_Ca + V_Ca (Nearest Neighbor: d ~ 4.04 A)
    nn_dist, v_ca_nn = ca_dists[0]
    u_vca_nn = host.copy()
    u_vca_nn[ca_center].symbol = "U"
    del u_vca_nn[v_ca_nn]
    # Update index if needed after deletion
    u_idx = ca_center if ca_center < v_ca_nn else ca_center - 1
    motifs["calcita_160_U_Ca_V_Ca_NN"] = {
        "atoms": u_vca_nn,
        "type": "charge_compensated_U_IV",
        "description": f"U4+ on Ca site compensated by nearest-neighbor Ca vacancy (d_init = {nn_dist:.3f} A)",
        "pair_distance_init_A": nn_dist,
        "defect_indices": {"U": u_idx},
    }

    # 3. U_Ca + V_Ca (Next-Nearest Neighbor: d ~ 5.00 A)
    # Find first Ca with dist > 4.5 A
    nnn_candidate = [x for x in ca_dists if x[0] > 4.5][0]
    nnn_dist, v_ca_nnn = nnn_candidate
    u_vca_nnn = host.copy()
    u_vca_nnn[ca_center].symbol = "U"
    del u_vca_nnn[v_ca_nnn]
    u_idx_nnn = ca_center if ca_center < v_ca_nnn else ca_center - 1
    motifs["calcita_160_U_Ca_V_Ca_NNN"] = {
        "atoms": u_vca_nnn,
        "type": "charge_compensated_U_IV",
        "description": f"U4+ on Ca site compensated by next-nearest-neighbor Ca vacancy (d_init = {nnn_dist:.3f} A)",
        "pair_distance_init_A": nnn_dist,
        "defect_indices": {"U": u_idx_nnn},
    }

    # 4. U_Ca + O_interstitial (U(IV) with extra oxygen in open interstitial site)
    # Find interstitial channel along c-axis void near U
    u_oi = host.copy()
    u_oi[ca_center].symbol = "U"
    u_pos = u_oi[ca_center].position
    # Candidate interstitial position ~2.1 A from U along open void direction
    # Average position of 3 neighboring carbonate triangles
    o_indices = [i for i, s in enumerate(u_oi.get_chemical_symbols()) if s == "O"]
    o_dists = [(float(u_oi.get_distance(ca_center, i, mic=True)), i) for i in o_indices]
    o_dists.sort()
    # Coordination shell centroid
    nn_o_vecs = [u_oi.get_distance(ca_center, i, vector=True, mic=True) for _, i in o_dists[:6]]
    # Open void normal to octahedral face
    void_vec = np.sum(nn_o_vecs[:3], axis=0)
    void_vec = void_vec / np.linalg.norm(void_vec) * 2.15
    oi_pos = u_pos + void_vec
    u_oi.append(Atom("O", position=oi_pos))
    motifs["calcita_160_U_Ca_Oi"] = {
        "atoms": u_oi,
        "type": "charge_compensated_U_IV",
        "description": "U4+ on Ca site compensated by interstitial O2- (7-fold coordination)",
        "defect_indices": {"U": ca_center, "Oi": len(u_oi) - 1},
    }

    # 5. Uranyl UO2(2+) complex on Ca site
    # Uranyl is linear [O=U=O]2+ with U-O ~ 1.79 A aligned with the 3-fold c-axis
    uo2_ca = host.copy()
    uo2_ca[ca_center].symbol = "U"
    c_axis = host.cell[2]
    c_unit = c_axis / np.linalg.norm(c_axis)
    # Add two axial uranyl oxygens along c-axis
    uo2_ca.append(Atom("O", position=u_pos + c_unit * 1.79))
    uo2_ca.append(Atom("O", position=u_pos - c_unit * 1.79))
    motifs["calcita_160_UO2_Ca"] = {
        "atoms": uo2_ca,
        "type": "uranyl_U_VI",
        "description": "Uranyl [O=U=O]2+ moiety on Ca site with axial oxygens along 3-fold axis",
        "defect_indices": {"U": ca_center, "O_ax1": len(uo2_ca) - 2, "O_ax2": len(uo2_ca) - 1},
    }

    return motifs


def build_dolomite_motifs(host: Atoms) -> dict:
    motifs = {}
    ca_center = get_center_site(host, "Ca")
    mg_center = get_center_site(host, "Mg")

    # 1. Pb_Ca reference
    pb_ca = host.copy()
    pb_ca[ca_center].symbol = "Pb"
    motifs["dolomita_160_Pb_Ca"] = {
        "atoms": pb_ca,
        "type": "isovalent_Pb",
        "description": "Isovalent Pb2+ substitution on Ca2+ site (q=0)",
        "defect_indices": {"Pb": ca_center},
    }

    # 2. Pb_Mg (testing Ca vs Mg site preference)
    pb_mg = host.copy()
    pb_mg[mg_center].symbol = "Pb"
    motifs["dolomita_160_Pb_Mg"] = {
        "atoms": pb_mg,
        "type": "isovalent_Pb",
        "description": "Isovalent Pb2+ substitution on Mg2+ site (q=0) for site-preference evaluation",
        "defect_indices": {"Pb": mg_center},
    }

    # 3. U_Ca + V_Ca (NN Ca vacancy in dolomite: d ~ 4.94 A)
    ca_indices = [i for i, s in enumerate(host.get_chemical_symbols()) if s == "Ca" and i != ca_center]
    ca_dists = sorted([(float(host.get_distance(ca_center, i, mic=True)), i) for i in ca_indices])
    v_ca_dist, v_ca_idx = ca_dists[0]
    u_vca = host.copy()
    u_vca[ca_center].symbol = "U"
    del u_vca[v_ca_idx]
    u_idx = ca_center if ca_center < v_ca_idx else ca_center - 1
    motifs["dolomita_160_U_Ca_V_Ca_NN"] = {
        "atoms": u_vca,
        "type": "charge_compensated_U_IV",
        "description": f"U4+ on Ca site compensated by nearest Ca vacancy (d_init = {v_ca_dist:.3f} A)",
        "pair_distance_init_A": v_ca_dist,
        "defect_indices": {"U": u_idx},
    }

    # 4. U_Ca + V_Mg (NN Mg vacancy in dolomite: d ~ 3.85 A in adjacent layer)
    mg_indices = [i for i, s in enumerate(host.get_chemical_symbols()) if s == "Mg"]
    mg_dists = sorted([(float(host.get_distance(ca_center, i, mic=True)), i) for i in mg_indices])
    v_mg_dist, v_mg_idx = mg_dists[0]
    u_vmg = host.copy()
    u_vmg[ca_center].symbol = "U"
    del u_vmg[v_mg_idx]
    u_idx_mg = ca_center if ca_center < v_mg_idx else ca_center - 1
    motifs["dolomita_160_U_Ca_V_Mg_NN"] = {
        "atoms": u_vmg,
        "type": "charge_compensated_U_IV",
        "description": f"U4+ on Ca site compensated by nearest Mg vacancy in adjacent layer (d_init = {v_mg_dist:.3f} A)",
        "pair_distance_init_A": v_mg_dist,
        "defect_indices": {"U": u_idx_mg},
    }

    # 5. U_Ca + O_interstitial
    u_oi = host.copy()
    u_oi[ca_center].symbol = "U"
    u_pos = u_oi[ca_center].position
    o_indices = [i for i, s in enumerate(u_oi.get_chemical_symbols()) if s == "O"]
    o_dists = sorted([(float(u_oi.get_distance(ca_center, i, mic=True)), i) for i in o_indices])
    nn_o_vecs = [u_oi.get_distance(ca_center, i, vector=True, mic=True) for _, i in o_dists[:6]]
    void_vec = np.sum(nn_o_vecs[:3], axis=0)
    void_vec = void_vec / np.linalg.norm(void_vec) * 2.15
    oi_pos = u_pos + void_vec
    u_oi.append(Atom("O", position=oi_pos))
    motifs["dolomita_160_U_Ca_Oi"] = {
        "atoms": u_oi,
        "type": "charge_compensated_U_IV",
        "description": "U4+ on Ca site compensated by interstitial O2- in dolomite void",
        "defect_indices": {"U": ca_center, "Oi": len(u_oi) - 1},
    }

    # 6. Uranyl on Ca site
    uo2_ca = host.copy()
    uo2_ca[ca_center].symbol = "U"
    c_axis = host.cell[2]
    c_unit = c_axis / np.linalg.norm(c_axis)
    uo2_ca.append(Atom("O", position=u_pos + c_unit * 1.79))
    uo2_ca.append(Atom("O", position=u_pos - c_unit * 1.79))
    motifs["dolomita_160_UO2_Ca"] = {
        "atoms": uo2_ca,
        "type": "uranyl_U_VI",
        "description": "Uranyl [O=U=O]2+ complex on Ca site in dolomite",
        "defect_indices": {"U": ca_center, "O_ax1": len(uo2_ca) - 2, "O_ax2": len(uo2_ca) - 1},
    }

    return motifs


def main():
    print("=" * 78)
    print("STEP 05C: DEFECT MOTIF ENUMERATION & STRUCTURE GENERATION")
    print("=" * 78)

    c_host = read(str(SUPERCELLS["calcita"]))
    d_host = read(str(SUPERCELLS["dolomita"]))

    all_motifs = {}
    c_motifs = build_calcite_motifs(c_host)
    d_motifs = build_dolomite_motifs(d_host)
    all_motifs.update(c_motifs)
    all_motifs.update(d_motifs)

    manifest = []
    for tag, data in all_motifs.items():
        atoms = data["atoms"]
        cif_path = OUT_DIR / f"{tag}.cif"
        traj_path = OUT_DIR / f"{tag}.traj"
        write(str(cif_path), atoms)
        write(str(traj_path), atoms)
        
        info = {
            "tag": tag,
            "formula": atoms.get_chemical_formula(),
            "natoms": len(atoms),
            "type": data["type"],
            "description": data["description"],
            "cif": str(cif_path),
            "traj": str(traj_path),
        }
        if "pair_distance_init_A" in data:
            info["pair_distance_init_A"] = data["pair_distance_init_A"]
        manifest.append(info)
        print(f"[MOTIF] {tag:<32} | {atoms.get_chemical_formula():<16} | N = {len(atoms)} | {data['description']}")

    manifest_file = OUT_DIR / "motifs_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2))
    print(f"\n[OK] Successfully saved {len(manifest)} defect motifs to {OUT_DIR}")
    print(f"[OK] Manifest written to {manifest_file}")


if __name__ == "__main__":
    main()
