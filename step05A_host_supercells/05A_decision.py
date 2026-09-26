#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from config_step05A import (
    HOSTS, RESULTS, MAX_FINAL_FORCE_EV_A, MAX_FINAL_STRESS_GPA,
)

manifest = json.loads(
    (RESULTS / "supercell_manifest_step05A.json").read_text(
        encoding="utf-8"
    )
)

hosts = {}
overall = True

for mineral, info in HOSTS.items():
    relax = json.loads(
        (RESULTS / f"{mineral}_host_relax.json").read_text(
            encoding="utf-8"
        )
    )
    val = json.loads(
        (RESULTS / f"{mineral}_host_validate1600.json").read_text(
            encoding="utf-8"
        )
    )

    symmetry_pass = (
        relax["spacegroup"]["number"] == info["spacegroup"]
    )
    relaxation_pass = (
        relax["atomic_stage_converged"]
        and relax["cell_stage_converged"]
        and relax["max_force_eV_A"] <= MAX_FINAL_FORCE_EV_A
    )
    validation_pass = (
        val["max_force_eV_A"] <= MAX_FINAL_FORCE_EV_A
        and val["max_abs_stress_GPa"] <= MAX_FINAL_STRESS_GPA
    )

    candidates = manifest["hosts"][mineral]["candidates"]
    # Próximo gate usa os dois menores tamanhos. O terceiro fica como
    # escalonamento caso a energia de defeito 80/160 não convirja.
    selected_pair = candidates[:2]
    fallback = candidates[2]

    host_pass = bool(
        symmetry_pass and relaxation_pass and validation_pass
    )
    overall = overall and host_pass

    hosts[mineral] = {
        "host_relaxation_passes": host_pass,
        "symmetry_passes": symmetry_pass,
        "relaxation_passes": relaxation_pass,
        "validation1600_passes": validation_pass,
        "selected_supercells_for_PbCa_size_gate": selected_pair,
        "fallback_supercell": fallback,
    }

decision = {
    "step": "05A",
    "purpose": (
        "Freeze a fresh PBEsol pristine-host baseline and design "
        "near-isotropic supercells before introducing U/Pb defects."
    ),
    "hosts": hosts,
    "step05A_passes": bool(overall),
    "production_authorization_from_step04": True,
    "defect_production_started": False,
    "next_gate": (
        "Step05B: neutral Pb2+->Ca2+ substitution finite-size gate on the "
        "two selected supercells for calcite and dolomite. If the raw "
        "substitution-energy difference is not converged, use the fallback "
        "supercell. U substitutions and charged/compensated defects remain "
        "blocked until that finite-size gate is resolved."
    ),
}

(RESULTS / "decisao_step05A.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(decision, indent=2, ensure_ascii=False))

if not overall:
    raise SystemExit(61)
