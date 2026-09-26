#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from ase.eos import EquationOfState
from ase.units import GPa

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04_R8 import (
    LATTICE_CONSTANTS_A,
    REFERENCE_A,
    MAX_RELATIVE_CURVE_DIFF_MEV_ATOM,
    MAX_OFFSET_SPAN_MEV_ATOM,
    MAX_STRESS_COMPONENT_DIFF_GPA,
    MAX_A0_REL_DIFF_PERCENT,
    MAX_B0_REL_DIFF_PERCENT,
)

RESULTS_ROOT = SCRIPT_DIR / "resultados_step04A"
EOS_DIR = RESULTS_ROOT / "eos_Pb_PBE_R8"


def load_series(kind: str):
    rows = []
    for a in LATTICE_CONSTANTS_A:
        tag = f"{a:.2f}".replace(".", "p")
        p = EOS_DIR / kind / f"a_{tag}.json"
        rows.append(json.loads(p.read_text(encoding="utf-8")))
    return rows


def fit_eos(rows):
    volumes = np.array([r["volume_A3_atom"] for r in rows], dtype=float)
    energies = np.array([r["energy_eV_atom"] for r in rows], dtype=float)
    eos = EquationOfState(volumes, energies, eos="birchmurnaghan")
    v0, e0, B_eVA3 = eos.fit()
    a0 = (4.0 * v0) ** (1.0 / 3.0)  # fcc conventional lattice constant
    B_GPa = B_eVA3 / GPa
    return {
        "v0_A3_atom": float(v0),
        "a0_A": float(a0),
        "e0_eV_atom": float(e0),
        "B0_GPa": float(B_GPa),
    }


official = load_series("official")
generated = load_series("generated")

off_map = {round(r["a_A"], 8): r for r in official}
gen_map = {round(r["a_A"], 8): r for r in generated}

ref_key = round(float(REFERENCE_A), 8)
Eoff_ref = off_map[ref_key]["energy_eV_atom"]
Egen_ref = gen_map[ref_key]["energy_eV_atom"]

table = []
offsets_mev = []
rel_curve_diffs_mev = []
stress_diffs = []

for a in LATTICE_CONSTANTS_A:
    key = round(float(a), 8)
    o = off_map[key]
    g = gen_map[key]

    off_rel = (o["energy_eV_atom"] - Eoff_ref) * 1000.0
    gen_rel = (g["energy_eV_atom"] - Egen_ref) * 1000.0
    rel_diff = gen_rel - off_rel
    offset = (g["energy_eV_atom"] - o["energy_eV_atom"]) * 1000.0

    so = np.array(o["stress_GPa"], dtype=float)
    sg = np.array(g["stress_GPa"], dtype=float)
    stress_diff = float(np.max(np.abs(sg - so)))

    offsets_mev.append(offset)
    rel_curve_diffs_mev.append(rel_diff)
    stress_diffs.append(stress_diff)

    table.append({
        "a_A": float(a),
        "E_official_eV_atom": o["energy_eV_atom"],
        "E_generated_eV_atom": g["energy_eV_atom"],
        "offset_generated_minus_official_meV_atom": offset,
        "Erel_official_meV_atom_ref_5A": off_rel,
        "Erel_generated_meV_atom_ref_5A": gen_rel,
        "relative_curve_difference_meV_atom": rel_diff,
        "max_stress_component_difference_GPa": stress_diff,
    })

fit_off = fit_eos(official)
fit_gen = fit_eos(generated)

max_rel_curve = float(np.max(np.abs(rel_curve_diffs_mev)))
offset_span = float(np.max(offsets_mev) - np.min(offsets_mev))
max_stress_diff = float(np.max(stress_diffs))
a0_rel_diff = abs(fit_gen["a0_A"] - fit_off["a0_A"]) / fit_off["a0_A"] * 100.0
B0_rel_diff = abs(fit_gen["B0_GPa"] - fit_off["B0_GPa"]) / abs(fit_off["B0_GPa"]) * 100.0

gate = {
    "max_relative_curve_difference_meV_atom": max_rel_curve,
    "criterion_max_relative_curve_difference_meV_atom":
        MAX_RELATIVE_CURVE_DIFF_MEV_ATOM,
    "energy_offset_span_meV_atom": offset_span,
    "criterion_energy_offset_span_meV_atom": MAX_OFFSET_SPAN_MEV_ATOM,
    "max_stress_component_difference_GPa": max_stress_diff,
    "criterion_max_stress_component_difference_GPa":
        MAX_STRESS_COMPONENT_DIFF_GPA,
    "a0_relative_difference_percent": float(a0_rel_diff),
    "criterion_a0_relative_difference_percent": MAX_A0_REL_DIFF_PERCENT,
    "B0_relative_difference_percent": float(B0_rel_diff),
    "criterion_B0_relative_difference_percent": MAX_B0_REL_DIFF_PERCENT,
}

passes = (
    max_rel_curve <= MAX_RELATIVE_CURVE_DIFF_MEV_ATOM
    and offset_span <= MAX_OFFSET_SPAN_MEV_ATOM
    and max_stress_diff <= MAX_STRESS_COMPONENT_DIFF_GPA
    and a0_rel_diff <= MAX_A0_REL_DIFF_PERCENT
    and B0_rel_diff <= MAX_B0_REL_DIFF_PERCENT
    and all(r["mpi_world_size"] == 4 for r in official + generated)
)

gate["passes"] = bool(passes)

with (RESULTS_ROOT / "Pb_PBE_eos_comparison_R8.csv").open(
    "w", newline="", encoding="utf-8"
) as f:
    w = csv.DictWriter(f, fieldnames=table[0].keys())
    w.writeheader()
    w.writerows(table)

summary = {
    "step": "04A-R8",
    "rationale": (
        "Absolute total energies from different PAW datasets are not used as "
        "a transferability gate because GPAW energies are referenced to the "
        "atomic reference state stored/generated with each setup. The gate "
        "therefore compares relative E(V) curves, stress, a0 and B0."
    ),
    "official_PBE_fit": fit_off,
    "generated_PBE_fit": fit_gen,
    "gate": gate,
}

(RESULTS_ROOT / "Pb_PBE_eos_summary_R8.json").write_text(
    json.dumps(summary, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

# Atualiza a decisão global usando a seleção U do R5 já aprovada.
u_selection_path = RESULTS_ROOT / "u_pseudization_selection_R5.json"
u_selection = json.loads(u_selection_path.read_text(encoding="utf-8"))

decision = {
    "step": "04A-R8",
    "matrix_reference_from_step03": {
        "xc": "PBEsol",
        "ecut_eV": 1400,
        "kgrid_primitive": [5, 5, 5],
    },
    "U": {
        "selected_candidate_id": u_selection.get("selected_candidate_id"),
        "pseudization": u_selection.get("pseudization"),
        "internal_atomic_gate_PBE": bool(u_selection.get("PBE_passes")),
        "internal_atomic_gate_PBEsol": bool(u_selection.get("PBEsol_passes")),
        "status": "CANDIDATE_ONLY_REQUIRES_COMPOUND_VALIDATION",
    },
    "Pb": {
        "official_PBE_available": True,
        "generated_PBE_eos_gate": gate,
        "official_PBE_fit": fit_off,
        "generated_PBE_fit": fit_gen,
        "generated_PBEsol_setup_exists_and_executes":
            (SCRIPT_DIR / "paw_generated/Pb/PBEsol/Pb.PBEsol").exists(),
        "status": (
            "CANDIDATE_ONLY_REQUIRES_COMPOUND_VALIDATION"
            if passes else "FAILED_EOS_GATE"
        ),
    },
    "step04A_passes": bool(
        passes
        and u_selection.get("PBE_passes") is True
        and u_selection.get("PBEsol_passes") is True
    ),
    "production_authorization": False,
    "next_gate": (
        "Step04B: compound-level validation for Pb(II), U(IV) and U(VI). "
        "For U, compare at least U14_poly6 with U14_nc6 in reference compounds "
        "before fixing the production dataset."
    ),
    "warning": (
        "Step04A validates atomic/internal quality and Pb generator "
        "consistency only. It does not yet validate chemistry, oxidation-state "
        "energetics, DFT+U, SOC, or carbonate-defect transferability."
    ),
}

(RESULTS_ROOT / "decisao_step04A.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04A-R8 — Pb/PBE EOS GATE")
print("=" * 80)
print(f"a0 official  = {fit_off['a0_A']:.8f} Å")
print(f"a0 generated = {fit_gen['a0_A']:.8f} Å")
print(f"Δa0          = {a0_rel_diff:.6f} %")
print(f"B0 official  = {fit_off['B0_GPa']:.6f} GPa")
print(f"B0 generated = {fit_gen['B0_GPa']:.6f} GPa")
print(f"ΔB0          = {B0_rel_diff:.6f} %")
print(f"max ΔErel    = {max_rel_curve:.6f} meV/atom")
print(f"offset span  = {offset_span:.6f} meV/atom")
print(f"max Δstress  = {max_stress_diff:.8f} GPa")
print(f"Pb EOS gate  = {'APROVADO' if passes else 'REPROVADO'}")
print(f"STEP04A      = {'APROVADO' if decision['step04A_passes'] else 'REPROVADO'}")
print("=" * 80)
