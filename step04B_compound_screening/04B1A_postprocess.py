#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1A import (
    RESULTS_DIR,
    UEFF_GRID_EV,
    UO2_MOMENT_TARGET_MUB,
    UO2_GAP_TARGET_MIN_EV,
    UO2_GAP_TARGET_MAX_EV,
)

all_records = []
for p in sorted(RESULTS_DIR.glob("*.json")):
    if p.name == "decisao_step04B1A.json":
        continue
    try:
        record = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    if isinstance(record, dict) and "system" in record:
        record["_file"] = p.name
        all_records.append(record)

converged = [
    r for r in all_records
    if r.get("status", "converged") == "converged"
    and "energy_eV" in r
]
failed = [r for r in all_records if r.get("status") == "failed_scf"]

uo2 = [r for r in converged if r["system"] == "UO2"]
uo3 = [r for r in converged if r["system"] == "delta_UO3"]
pbco3 = [r for r in converged if r["system"] == "PbCO3"]

rows = []
for r in uo2:
    moment = r.get("U_abs_mean_moment_muB")
    gap = r.get("band_gap_eV")
    moment_err = abs(moment - UO2_MOMENT_TARGET_MUB) if moment is not None else 999.0

    if gap is None:
        gap_penalty = 999.0
    elif gap < UO2_GAP_TARGET_MIN_EV:
        gap_penalty = UO2_GAP_TARGET_MIN_EV - gap
    elif gap > UO2_GAP_TARGET_MAX_EV:
        gap_penalty = gap - UO2_GAP_TARGET_MAX_EV
    else:
        gap_penalty = 0.0

    score = moment_err / 0.25 + gap_penalty / 0.25
    rows.append({
        "dataset": r["U_dataset"],
        "Ueff_eV": r["Ueff_eV"],
        "band_gap_eV": gap,
        "U_abs_mean_moment_muB": moment,
        "moment_abs_error_muB": moment_err,
        "gap_interval_penalty_eV": gap_penalty,
        "screening_score": score,
        "scf_strategy": r.get("scf_strategy"),
        "smearing_eV": r.get("smearing_eV"),
        "scf_iterations": r.get("scf_iterations"),
        "max_force_eV_A": r["max_force_eV_A"],
        "max_abs_stress_GPa": r["max_abs_stress_GPa"],
    })

rows.sort(key=lambda x: x["screening_score"])

if rows:
    with (RESULTS_DIR / "UO2_screening_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

comparison = []
for ueff in UEFF_GRID_EV:
    poly = next(
        (r for r in uo2 if r["U_dataset"] == "poly6"
         and abs(r["Ueff_eV"] - ueff) < 1e-9),
        None,
    )
    nc = next(
        (r for r in uo2 if r["U_dataset"] == "nc6"
         and abs(r["Ueff_eV"] - ueff) < 1e-9),
        None,
    )
    if poly and nc:
        comparison.append({
            "Ueff_eV": ueff,
            "gap_poly6_eV": poly.get("band_gap_eV"),
            "gap_nc6_eV": nc.get("band_gap_eV"),
            "delta_gap_nc_minus_poly_eV": (
                None if poly.get("band_gap_eV") is None
                or nc.get("band_gap_eV") is None
                else nc["band_gap_eV"] - poly["band_gap_eV"]
            ),
            "moment_poly6_muB": poly.get("U_abs_mean_moment_muB"),
            "moment_nc6_muB": nc.get("U_abs_mean_moment_muB"),
            "delta_moment_nc_minus_poly_muB": (
                None if poly.get("U_abs_mean_moment_muB") is None
                or nc.get("U_abs_mean_moment_muB") is None
                else nc["U_abs_mean_moment_muB"]
                - poly["U_abs_mean_moment_muB"]
            ),
        })

(RESULTS_DIR / "U_dataset_comparison.json").write_text(
    json.dumps(comparison, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

failure_summary = [{
    "file": r.get("_file"),
    "system": r.get("system"),
    "dataset": r.get("U_dataset"),
    "Ueff_eV": r.get("Ueff_eV"),
    "attempts": r.get("attempts", []),
} for r in failed]

(RESULTS_DIR / "SCF_failures_R2.json").write_text(
    json.dumps(failure_summary, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

expected = {"UO2": 10, "delta_UO3": 2, "PbCO3": 1}
counts = {"UO2": len(uo2), "delta_UO3": len(uo3), "PbCO3": len(pbco3)}
complete = all(counts[k] == v for k, v in expected.items())

decision = {
    "step": "04B1A-R2",
    "scope": "Fixed-geometry chemical screening with robust SCF handling.",
    "calculations_expected": expected,
    "calculations_converged": counts,
    "failed_scf_count": len(failed),
    "failed_scf_records": failure_summary,
    "UO2_experimental_guides": {
        "a_A": 5.4706,
        "ordered_moment_muB_per_U": UO2_MOMENT_TARGET_MUB,
        "gap_target_interval_eV": [
            UO2_GAP_TARGET_MIN_EV,
            UO2_GAP_TARGET_MAX_EV,
        ],
        "magnetic_model_warning": (
            "Collinear 1-k AFM screening state; experimental "
            "low-temperature ground state is non-collinear 3-k AFM."
        ),
    },
    "best_screening_candidates": rows[:4],
    "step04B1A_complete": complete,
    "production_authorization": False,
    "next_gate": (
        "If complete: Step04B1B with structural relaxation/EOS for the "
        "shortlisted Ueff/dataset candidates and quantitative cerussite "
        "validation. If incomplete: inspect SCF_failures_R2.json and the "
        "corresponding attempt text logs."
    ),
    "warning": (
        "The robust screening uses 0.15-0.20 eV smearing for UO2. "
        "Final shortlisted calculations must be repeated at 0.05 eV "
        "and tighter convergence before production."
    ),
}

(RESULTS_DIR / "decisao_step04B1A.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B1A-R2 — RESUMO")
print("=" * 80)
print(f"UO2 convergidos:       {len(uo2)}/10")
print(f"delta-UO3 convergidos: {len(uo3)}/2")
print(f"PbCO3 convergidos:     {len(pbco3)}/1")
print(f"Falhas SCF:            {len(failed)}")
print()
if rows:
    print("Melhores candidatos UO2 (triagem apenas):")
    for row in rows[:4]:
        print(
            f"  {row['dataset']:5s} Ueff={row['Ueff_eV']:.1f} eV | "
            f"gap={row['band_gap_eV']} eV | "
            f"|mU|={row['U_abs_mean_moment_muB']} muB | "
            f"SCF={row['scf_strategy']} | "
            f"score={row['screening_score']:.4f}"
        )
print()
print("STEP04B1A-R2:", "COMPLETO" if complete else "INCOMPLETO")
print("Produção com defeitos: NÃO AUTORIZADA.")
print("=" * 80)
