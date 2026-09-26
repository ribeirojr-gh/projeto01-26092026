#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1B1 import (
    RESULTS_DIR,
    UEFF_GRID_EV,
    AFM_DOMAINS,
    GAP_TARGET_MIN_EV,
    GAP_TARGET_MAX_EV,
    MOMENT_TARGET_MUB,
    MAX_DOMAIN_ENERGY_SPREAD_MEV_ATOM,
    MAX_DOMAIN_GAP_SPREAD_EV,
    MAX_DOMAIN_MOMENT_SPREAD_MUB,
)

records = []
for path in sorted(RESULTS_DIR.glob("UO2_nc6_U*_*.json")):
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    record["_file"] = path.name
    records.append(record)

tight = [
    r for r in records
    if r.get("status") == "converged_tight"
]
failed = [
    r for r in records
    if r.get("status") != "converged_tight"
]

rows = []
ueff_summaries = []

for ueff in UEFF_GRID_EV:
    subset = [
        r for r in tight
        if abs(r["Ueff_eV"] - ueff) < 1.0e-12
    ]

    if not subset:
        ueff_summaries.append({
            "Ueff_eV": ueff,
            "domains_converged": 0,
            "reproducible": False,
        })
        continue

    energies = np.array(
        [r["energy_eV_atom"] for r in subset],
        dtype=float,
    )
    gaps = np.array(
        [r["band_gap_eV"] for r in subset
         if r.get("band_gap_eV") is not None],
        dtype=float,
    )
    moments = np.array(
        [r["U_abs_mean_moment_muB"] for r in subset],
        dtype=float,
    )

    e_min = float(np.min(energies))
    energy_spread = float(
        (np.max(energies) - np.min(energies)) * 1000.0
    )
    gap_spread = (
        float(np.max(gaps) - np.min(gaps))
        if len(gaps) == len(subset)
        else None
    )
    moment_spread = float(np.max(moments) - np.min(moments))

    reproducible = (
        len(subset) == len(AFM_DOMAINS)
        and energy_spread <= MAX_DOMAIN_ENERGY_SPREAD_MEV_ATOM
        and gap_spread is not None
        and gap_spread <= MAX_DOMAIN_GAP_SPREAD_EV
        and moment_spread <= MAX_DOMAIN_MOMENT_SPREAD_MUB
    )

    minimum = min(
        subset,
        key=lambda r: r["energy_eV_atom"],
    )

    gap = minimum.get("band_gap_eV")
    moment = minimum.get("U_abs_mean_moment_muB")

    if gap is None:
        gap_penalty = 999.0
    elif gap < GAP_TARGET_MIN_EV:
        gap_penalty = GAP_TARGET_MIN_EV - gap
    elif gap > GAP_TARGET_MAX_EV:
        gap_penalty = gap - GAP_TARGET_MAX_EV
    else:
        gap_penalty = 0.0

    moment_error = abs(moment - MOMENT_TARGET_MUB)

    summary = {
        "Ueff_eV": ueff,
        "domains_converged": len(subset),
        "energy_spread_meV_atom": energy_spread,
        "gap_spread_eV": gap_spread,
        "moment_spread_muB": moment_spread,
        "reproducible": bool(reproducible),
        "minimum_energy_domain": minimum["AFM_domain"],
        "minimum_energy_eV_atom": minimum["energy_eV_atom"],
        "minimum_gap_eV": gap,
        "minimum_U_abs_mean_moment_muB": moment,
        "minimum_max_abs_stress_GPa":
            minimum["max_abs_stress_GPa"],
        "gap_interval_penalty_eV": gap_penalty,
        "moment_abs_error_muB": moment_error,
    }
    ueff_summaries.append(summary)

    for r in subset:
        rows.append({
            "Ueff_eV": ueff,
            "AFM_domain": r["AFM_domain"],
            "energy_eV_atom": r["energy_eV_atom"],
            "deltaE_from_domain_min_meV_atom":
                (r["energy_eV_atom"] - e_min) * 1000.0,
            "band_gap_eV": r.get("band_gap_eV"),
            "U_abs_mean_moment_muB":
                r["U_abs_mean_moment_muB"],
            "max_abs_stress_GPa":
                r["max_abs_stress_GPa"],
            "max_force_eV_A":
                r["max_force_eV_A"],
            "preconvergence_strategy":
                r["preconvergence_strategy"],
            "preconvergence_iterations":
                r["preconvergence_iterations"],
            "final_iterations":
                r["final_iterations"],
        })

if rows:
    with (
        RESULTS_DIR / "UO2_domain_reproducibility_B1B1.csv"
    ).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)

reproducible_candidates = [
    s for s in ueff_summaries
    if s.get("reproducible")
]

def candidate_key(s):
    return (
        s.get("gap_interval_penalty_eV", 999.0),
        s.get("moment_abs_error_muB", 999.0),
        abs(s.get("minimum_max_abs_stress_GPa", 999.0)),
    )

reproducible_candidates.sort(key=candidate_key)

decision = {
    "step": "04B1B1",
    "scope": (
        "Tight 0.05 eV fixed-geometry reproducibility test for nc6 "
        "using three symmetry-equivalent collinear 1-k AFM domains."
    ),
    "protocol": {
        "dataset": "nc6",
        "xc": "PBEsol",
        "ecut_eV": 1400,
        "kpts": [3, 3, 3],
        "nbands": 80,
        "Ueff_grid_eV": list(UEFF_GRID_EV),
        "AFM_domains": list(AFM_DOMAINS),
        "final_smearing_eV": 0.05,
        "point_group": False,
        "time_reversal": True,
        "fixmagmom": False,
    },
    "reproducibility_criteria": {
        "max_energy_spread_meV_atom":
            MAX_DOMAIN_ENERGY_SPREAD_MEV_ATOM,
        "max_gap_spread_eV":
            MAX_DOMAIN_GAP_SPREAD_EV,
        "max_moment_spread_muB":
            MAX_DOMAIN_MOMENT_SPREAD_MUB,
    },
    "ueff_summaries": ueff_summaries,
    "failed_runs": [{
        "file": r.get("_file"),
        "Ueff_eV": r.get("Ueff_eV"),
        "AFM_domain": r.get("AFM_domain"),
        "status": r.get("status"),
        "attempts": r.get("attempts", []),
    } for r in failed],
    "reproducible_candidates": reproducible_candidates,
    "preferred_candidate_for_next_gate": (
        reproducible_candidates[0]
        if reproducible_candidates else None
    ),
    "step04B1B1_passes": bool(reproducible_candidates),
    "production_authorization": False,
    "next_gate": (
        "Step04B1B2: EOS/structural validation of the best reproducible "
        "Ueff candidate(s), followed by 1400-versus-1600 eV convergence. "
        "SOC remains a later controlled sensitivity test."
    ),
    "warning": (
        "The three collinear 1-k domains are a reproducibility diagnostic, "
        "not a substitute for the experimental non-collinear 3-k magnetic "
        "ground state of UO2."
    ),
}

(RESULTS_DIR / "decisao_step04B1B1.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B1B1 — REPRODUTIBILIDADE UO2/nc6")
print("=" * 80)
for summary in ueff_summaries:
    print(
        f"Ueff={summary['Ueff_eV']:.1f} eV | "
        f"domínios={summary['domains_converged']}/3 | "
        f"reprodutível={summary['reproducible']} | "
        f"ΔEdom={summary.get('energy_spread_meV_atom')} meV/átomo | "
        f"Δgap={summary.get('gap_spread_eV')} eV"
    )
print()
print(
    "STEP04B1B1:",
    "APROVADO" if decision["step04B1B1_passes"] else "REPROVADO",
)
print(
    "Candidato preferencial:",
    decision["preferred_candidate_for_next_gate"],
)
print("Produção com defeitos: NÃO AUTORIZADA.")
print("=" * 80)
