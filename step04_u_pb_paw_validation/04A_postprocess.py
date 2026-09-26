#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from config_step04 import (
    RESULTS_DIR,
    PB_ENERGY_GATE_MEV_ATOM,
    PB_STRESS_GATE_GPA,
)


def load_json(name):
    return json.loads((RESULTS_DIR / name).read_text(encoding="utf-8"))


official = load_json("Pb_PBE_official.json")
generated = load_json("Pb_PBE_generated.json")
pbesol = load_json("Pb_PBEsol_generated.json")
load = load_json("paw_load_test.json")
audit = load_json("auditoria_geradores.json")
u_selection = load_json("u_pseudization_selection_R5.json")

with (RESULTS_DIR / "inventario_setups_instalados.csv").open(
    encoding="utf-8"
) as f:
    inventory = list(csv.DictReader(f))

de_mev_atom = abs(
    generated["energy_eV_atom"] - official["energy_eV_atom"]
) * 1000.0

ds_gpa = float(np.max(np.abs(
    np.array(generated["stress_GPa"]) -
    np.array(official["stress_GPa"])
)))

pb_gate = (
    de_mev_atom <= PB_ENERGY_GATE_MEV_ATOM
    and ds_gpa <= PB_STRESS_GATE_GPA
    and official["mpi_world_size"] == 4
    and generated["mpi_world_size"] == 4
)

u_records = [r for r in load if r["symbol"] == "U"]

u_load_gate = (
    len(u_records) == 2
    and all(abs(float(r["Nv"]) - 14.0) < 1e-12 for r in u_records)
)

u_internal_gate = (
    u_selection.get("PBE_passes") is True
    and u_selection.get("PBEsol_passes") is True
    and u_selection.get("no_check_flag_used") is False
    and u_selection.get("selected_candidate_id") is not None
)

decision = {
    "step": "04A-R5",
    "purpose": "Final internal generator2 gate before external/all-electron fallback",
    "matrix_reference_from_step03": {
        "xc": "PBEsol",
        "ecut_eV": 1400,
        "kgrid_primitive": [5, 5, 5],
    },
    "Pb": {
        "official_PBE_available": any(
            x["element"] == "Pb"
            and x["xc"] == "PBE"
            and x["installed_setup_found"].lower() == "true"
            for x in inventory
        ),
        "generated_PBE_old_generator_gate": {
            "delta_energy_meV_atom": de_mev_atom,
            "max_stress_component_difference_GPa": ds_gpa,
            "criterion_energy_meV_atom": PB_ENERGY_GATE_MEV_ATOM,
            "criterion_stress_GPa": PB_STRESS_GATE_GPA,
            "passes": bool(pb_gate),
        },
        "generated_PBEsol_loads": any(
            r["symbol"] == "Pb" and r["xc"] == "PBEsol"
            for r in load
        ),
        "PBEsol_fixed_fcc_singlepoint_completed":
            pbesol["mpi_world_size"] == 4,
    },
    "U": {
        "official_PBE_available": any(
            x["element"] == "U"
            and x["xc"] == "PBE"
            and x["installed_setup_found"].lower() == "true"
            for x in inventory
        ),
        "generator2_default_valence_electrons":
            audit["generator2"]["U_default_valence_electrons"],
        "prior_diagnostics": {
            "R2": "cutoff-radius scan failed and smaller radius worsened bound-5f error",
            "R3": "extra-f projector energy/count scan failed",
            "R4": "U24/U32 semicore promotion failed to improve bound-5f gate",
        },
        "R5_strategy": "scan poly/norm-conserving pseudization at fixed U14 defaults",
        "selected_candidate_id":
            u_selection.get("selected_candidate_id"),
        "pseudization":
            u_selection.get("pseudization"),
        "generator2_internal_check_passes": bool(u_internal_gate),
        "PBE_and_PBEsol_setup_load_with_14e": bool(u_load_gate),
        "no_check_flag_used":
            bool(u_selection.get("no_check_flag_used", False)),
        "status": (
            "CANDIDATE_ONLY_REQUIRES_COMPOUND_VALIDATION"
            if u_internal_gate and u_load_gate
            else "FAILED"
        ),
    },
    "step04A_passes": bool(pb_gate and u_internal_gate and u_load_gate),
    "production_authorization": False,
    "next_gate": (
        "If R5 passes: Step04B compound validation. "
        "If R5 fails: stop tuning GPAW generator2 for U and switch to a "
        "validated external/all-electron reference strategy."
    ),
    "warning": (
        "Passing Step04A does not validate oxidation-state energetics, "
        "DFT+U, SOC, or transferability of U/Pb PAWs to carbonate defects."
    ),
}

(RESULTS_DIR / "decisao_step04A.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04A-R5 — DECISÃO")
print("=" * 80)
print(
    "Pb PBE generated vs official:",
    "APROVADO" if pb_gate else "REPROVADO",
)
print(f"  ΔE = {de_mev_atom:.6f} meV/atom")
print(f"  Δstress(max) = {ds_gpa:.8f} GPa")
print(
    "U generator2 internal gate:",
    "APROVADO" if u_internal_gate else "REPROVADO",
)
print("U selected candidate:", u_selection.get("selected_candidate_id"))
print("U pseudization:", u_selection.get("pseudization"))
print(
    "U PBE/PBEsol load:",
    "APROVADO" if u_load_gate else "REPROVADO",
)
print(
    "STEP04A-R5:",
    "APROVADO" if decision["step04A_passes"] else "REPROVADO",
)
print("Produção com defeitos U/Pb: NÃO AUTORIZADA ainda.")
print("=" * 80)
