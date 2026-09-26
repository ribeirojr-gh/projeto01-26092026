#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from config_step04B2A import (
    RESULTS_DIR,
    EXP_A_A,
    EXP_B_A,
    EXP_C_A,
    EXP_SPACEGROUP_NUMBER,
    MAX_VALIDATION_FORCE_EV_A,
    MAX_VALIDATION_STRESS_GPA,
)


def load(name):
    return json.loads(
        (RESULTS_DIR / name).read_text(encoding="utf-8")
    )


num = load("numeric_gate_step04B2A.json")
relax = load("relaxation_step04B2A.json")
metrics = load("structural_metrics_step04B2A.json")
val = load("PbCO3_relaxed_1600_k434.json")

validation_pass = (
    val["max_force_eV_A"] <= MAX_VALIDATION_FORCE_EV_A
    and val["max_abs_stress_GPa"] <= MAX_VALIDATION_STRESS_GPA
)

overall = (
    num["numerical_gate_passes"]
    and relax["all_stages_converged"]
    and metrics["structural_gate_passes"]
    and validation_pass
)

decision = {
    "step": "04B2A",
    "system": "cerussite_PbCO3",
    "oxidation_state_role": "Pb(II) carbonate reference",
    "experimental_reference": {
        "a_A": EXP_A_A,
        "b_A": EXP_B_A,
        "c_A": EXP_C_A,
        "spacegroup_number": EXP_SPACEGROUP_NUMBER,
    },
    "numerical_gate": num,
    "relaxation": {
        "all_stages_converged":
            relax["all_stages_converged"],
        "production_matrix":
            relax["production_matrix"],
    },
    "structural_metrics": metrics,
    "validation_singlepoint": val,
    "validation_force_stress_passes":
        bool(validation_pass),
    "step04B2A_passes": bool(overall),
    "selected_Pb_matrix": (
        {
            "dataset": "generated_Pb_PBEsol",
            "xc": "PBEsol",
            "production_cutoff_eV": 1400,
            "validation_cutoff_eV": 1600,
            "production_kpts_PbCO3": [3, 2, 3],
            "validation_kpts_PbCO3": [4, 3, 4],
            "SOC": False,
        }
        if overall else None
    ),
    "production_authorization": False,
    "next_gate": (
        "If approved: Step04B2B controlled non-self-consistent SOC "
        "sensitivity for PbCO3/Pb and UO2/U, followed by realistic U(VI) "
        "compound validation. Carbonate defect production remains blocked "
        "until those compound-level gates pass."
    ),
    "warning": (
        "The scalar-relativistic PbCO3 gap is reported but is not an "
        "electronic-structure acceptance criterion before the SOC gate."
    ),
}

(RESULTS_DIR / "decisao_step04B2A.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B2A — Pb(II) / CERUSSITA")
print("=" * 80)
print(
    "Gate numérico:",
    "PASS" if num["numerical_gate_passes"] else "FAIL",
)
print(
    "Relaxação:",
    "PASS" if relax["all_stages_converged"] else "FAIL",
)
print(
    "Estrutura:",
    "PASS" if metrics["structural_gate_passes"] else "FAIL",
)
print(
    "Validação força/stress:",
    "PASS" if validation_pass else "FAIL",
)
print(
    "STEP04B2A:",
    "APROVADO" if overall else "REPROVADO",
)
print("Produção com defeitos: NÃO AUTORIZADA.")
print("=" * 80)
