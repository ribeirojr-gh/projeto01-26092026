#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1A_R5 import (
    RESULTS, UEFF_GRID, GAP_MIN, GAP_MAX, MOMENT_TARGET
)

records = []
for path in sorted(RESULTS.glob("UO2_*_Ueff_*.json")):
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        continue
    rec["_file"] = path.name
    records.append(rec)

converged = [r for r in records if r.get("status") == "converged"]
failed = [r for r in records if r.get("status") == "failed_scf"]

rows = []
for r in converged:
    gap = r.get("band_gap_eV")
    moment = r.get("U_abs_mean_moment_muB")

    if gap is None:
        gap_penalty = 999.0
    elif gap < GAP_MIN:
        gap_penalty = GAP_MIN - gap
    elif gap > GAP_MAX:
        gap_penalty = gap - GAP_MAX
    else:
        gap_penalty = 0.0

    moment_error = (
        abs(moment - MOMENT_TARGET) if moment is not None else 999.0
    )

    rows.append({
        "dataset": r["dataset"],
        "Ueff_eV": r["Ueff_eV"],
        "band_gap_eV": gap,
        "U_abs_mean_moment_muB": moment,
        "gap_interval_penalty_eV": gap_penalty,
        "moment_abs_error_muB": moment_error,
        "screening_score": gap_penalty / 0.25 + moment_error / 0.25,
        "max_abs_stress_GPa": r.get("max_abs_stress_GPa"),
        "max_force_eV_A": r.get("max_force_eV_A"),
        "scf_strategy": r.get("scf_strategy"),
        "smearing_eV": r.get("smearing_eV"),
        "scf_iterations": r.get("scf_iterations"),
        "gpw_file": r.get("gpw_file"),
    })

rows.sort(key=lambda x: x["screening_score"])

if rows:
    with (RESULTS / "UO2_common_protocol_summary_R5.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

comparisons = []
for ueff in UEFF_GRID:
    poly = next(
        (r for r in converged
         if r["dataset"] == "poly6"
         and abs(r["Ueff_eV"] - ueff) < 1e-12),
        None,
    )
    nc = next(
        (r for r in converged
         if r["dataset"] == "nc6"
         and abs(r["Ueff_eV"] - ueff) < 1e-12),
        None,
    )
    if poly and nc:
        comparisons.append({
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
            "stress_poly6_GPa": poly.get("max_abs_stress_GPa"),
            "stress_nc6_GPa": nc.get("max_abs_stress_GPa"),
        })

(RESULTS / "U_dataset_common_protocol_comparison_R5.json").write_text(
    json.dumps(comparisons, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

failure_summary = [{
    "file": r.get("_file"),
    "dataset": r.get("dataset"),
    "Ueff_eV": r.get("Ueff_eV"),
    "attempts": r.get("attempts", []),
} for r in failed]

(RESULTS / "SCF_failures_R5.json").write_text(
    json.dumps(failure_summary, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

expected = 2 * len(UEFF_GRID)
complete = len(converged) == expected and not failed

best_by_dataset = {}
for dataset in ("poly6", "nc6"):
    candidates = [r for r in rows if r["dataset"] == dataset]
    best_by_dataset[dataset] = candidates[0] if candidates else None

decision = {
    "step": "04B1A-R5",
    "purpose": (
        "Rebuild the UO2 Ueff grid for poly6 and nc6 under one common "
        "symmetry and magnetization protocol."
    ),
    "protocol": {
        "xc": "PBEsol",
        "ecut_eV": 1400,
        "kpts": [3, 3, 3],
        "nbands": 80,
        "hubbard_normalized": True,
        "point_group": False,
        "time_reversal": True,
        "fixmagmom": False,
        "Ueff_grid_eV": list(UEFF_GRID),
    },
    "expected_calculations": expected,
    "converged_calculations": len(converged),
    "failed_calculations": len(failed),
    "complete": complete,
    "best_candidate_by_dataset": best_by_dataset,
    "overall_shortlist": rows[:4],
    "production_authorization": False,
    "next_gate": (
        "If complete: Step04B1B with EOS/structural relaxation for the "
        "shortlisted candidates, 1400-versus-1600 eV validation, tighter "
        "0.05 eV smearing and quantitative cerussite relaxation."
    ),
    "warning": (
        "R5 is fixed-geometry screening. Do not compare absolute total "
        "energies between poly6 and nc6. Multiple orbital solutions and "
        "SOC sensitivity remain mandatory."
    ),
}

(RESULTS / "decisao_step04B1A_R5.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B1A-R5 — PROTOCOLO COMUM")
print("=" * 80)
print(f"Convergidos: {len(converged)}/{expected}")
print(f"Falhas SCF: {len(failed)}")
for dataset in ("poly6", "nc6"):
    best = best_by_dataset[dataset]
    if best:
        print(
            f"Melhor {dataset}: Ueff={best['Ueff_eV']:.1f} eV | "
            f"gap={best['band_gap_eV']} eV | "
            f"|mU|={best['U_abs_mean_moment_muB']} muB | "
            f"score={best['screening_score']:.6f}"
        )
print("STEP04B1A-R5:", "COMPLETO" if complete else "INCOMPLETO")
print("Produção com defeitos: NÃO AUTORIZADA.")
print("=" * 80)
