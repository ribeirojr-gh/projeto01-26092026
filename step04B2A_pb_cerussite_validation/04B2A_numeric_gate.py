#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from config_step04B2A import (
    RESULTS_DIR,
    PROD_ECUT_EV,
    VAL_ECUT_EV,
    PROD_KPTS,
    VAL_KPTS,
    MAX_NUM_DELTA_ENERGY_MEV_ATOM,
    MAX_NUM_DELTA_GAP_EV,
    MAX_NUM_DELTA_HYDROSTATIC_STRESS_GPA,
    MAX_NUM_DELTA_FORCE_EV_A,
)


def load(name):
    return json.loads(
        (RESULTS_DIR / name).read_text(encoding="utf-8")
    )


r_prod = load("PbCO3_exp_1400_k323.json")
r_k = load("PbCO3_exp_1400_k434.json")
r_cut = load("PbCO3_exp_1600_k323.json")
r_val = load("PbCO3_exp_1600_k434.json")


def compare(a, b):
    gap_a = a.get("band_gap_eV")
    gap_b = b.get("band_gap_eV")

    return {
        "delta_energy_meV_atom":
            abs(b["energy_eV_atom"] - a["energy_eV_atom"]) * 1000.0,
        "delta_gap_eV": (
            None
            if gap_a is None or gap_b is None
            else abs(gap_b - gap_a)
        ),
        "delta_hydrostatic_stress_GPa":
            abs(
                b["hydrostatic_stress_GPa"]
                - a["hydrostatic_stress_GPa"]
            ),
        "delta_max_force_eV_A":
            abs(b["max_force_eV_A"] - a["max_force_eV_A"]),
    }


def passes(c):
    return (
        c["delta_energy_meV_atom"]
        <= MAX_NUM_DELTA_ENERGY_MEV_ATOM
        and c["delta_gap_eV"] is not None
        and c["delta_gap_eV"] <= MAX_NUM_DELTA_GAP_EV
        and c["delta_hydrostatic_stress_GPa"]
        <= MAX_NUM_DELTA_HYDROSTATIC_STRESS_GPA
        and c["delta_max_force_eV_A"]
        <= MAX_NUM_DELTA_FORCE_EV_A
    )


k1400 = compare(r_prod, r_k)
k1600 = compare(r_cut, r_val)
cut_k323 = compare(r_prod, r_cut)
cut_k434 = compare(r_k, r_val)

for item in (k1400, k1600, cut_k323, cut_k434):
    item["passes"] = passes(item)

overall = all(
    item["passes"]
    for item in (k1400, k1600, cut_k323, cut_k434)
)

decision = {
    "step": "04B2A-numerical-gate",
    "system": "PbCO3_cerussite",
    "production_candidate": {
        "ecut_eV": PROD_ECUT_EV,
        "kpts": list(PROD_KPTS),
    },
    "validation_matrix": {
        "ecut_eV": VAL_ECUT_EV,
        "kpts": list(VAL_KPTS),
    },
    "criteria": {
        "max_delta_energy_meV_atom":
            MAX_NUM_DELTA_ENERGY_MEV_ATOM,
        "max_delta_gap_eV":
            MAX_NUM_DELTA_GAP_EV,
        "max_delta_hydrostatic_stress_GPa":
            MAX_NUM_DELTA_HYDROSTATIC_STRESS_GPA,
        "max_delta_force_eV_A":
            MAX_NUM_DELTA_FORCE_EV_A,
    },
    "kpoint_1400": k1400,
    "kpoint_1600": k1600,
    "cutoff_k323": cut_k323,
    "cutoff_k434": cut_k434,
    "numerical_gate_passes": bool(overall),
}

(RESULTS_DIR / "numeric_gate_step04B2A.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP04B2A — GATE NUMÉRICO PbCO3")
print("=" * 80)
print("k 1400:", k1400)
print("k 1600:", k1600)
print("cutoff k323:", cut_k323)
print("cutoff k434:", cut_k434)
print("GATE:", "APROVADO" if overall else "REPROVADO")
print("=" * 80)

if not overall:
    raise SystemExit(31)
