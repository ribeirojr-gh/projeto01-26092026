#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS = SCRIPT_DIR / "resultados_step04B1A_R4"

records = {}
for dataset in ("poly6", "nc6"):
    path = RESULTS / f"UO2_{dataset}_diagnostic_R4.json"
    records[dataset] = json.loads(path.read_text(encoding="utf-8"))

successes = {
    key: value.get("selected_success")
    for key, value in records.items()
    if value.get("target_Ueff_4eV_converged")
}

if successes:
    action = (
        "Use the successful SCF strategy only to rebuild the Ueff grid. "
        "Then repeat shortlisted states with 0.05 eV smearing and tighter "
        "criteria."
    )
    status = "DIAGNOSTIC_SUCCESS"
else:
    action = (
        "Stop blind mixer scans. UO2 DFT+U requires explicit occupation-"
        "matrix control or a code/workflow that supports robust OMC. "
        "Keep GPAW for Pb/carbonate matrix and U(VI) screening until the "
        "UO2 reference route is formally revised."
    )
    status = "OCCUPATION_MATRIX_CONTROL_REQUIRED"

decision = {
    "step": "04B1A-R4",
    "poly6": records["poly6"],
    "nc6": records["nc6"],
    "successful_datasets": list(successes),
    "status": status,
    "scientific_action": action,
    "production_authorization": False,
    "notes": [
        "Ueff=0 converged previously for both PAWs.",
        "All independent Ueff=2-5 eV cold starts failed in R2.",
        "R4 removes fixmagmom, restores magnetic symmetry, tests normalized "
        "versus unnormalized Hubbard projections, and finally attempts a "
        "density-preserving in-place U ramp as a diagnostic.",
        "The in-place ramp uses GPAW-25.7 internal APIs and cannot by itself "
        "authorize production calculations.",
    ],
}

(RESULTS / "decisao_step04B1A_R4.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B1A-R4 — DECISÃO")
print("=" * 80)
print("poly6 Ueff=4 convergiu:",
      records["poly6"]["target_Ueff_4eV_converged"])
print("nc6   Ueff=4 convergiu:",
      records["nc6"]["target_Ueff_4eV_converged"])
print("Status:", status)
print("Produção com defeitos: NÃO AUTORIZADA.")
print("=" * 80)
