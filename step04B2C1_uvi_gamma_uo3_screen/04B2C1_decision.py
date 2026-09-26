#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from config_step04B2C1 import (
    RESULTS, MANIFEST, EXP_GAP_GUIDE_EV,
    MAX_DENERGY_MEV_ATOM, MAX_DGAP_EV, MAX_DSTRESS_GPA,
    MIN_INSULATING_GAP_EV, MAX_INSULATING_GAP_EV,
    MAX_SEEDED_U_MOMENT_MUB, MAX_FIXED_GEOM_FORCE_EV_A,
    MAX_FIXED_GEOM_STRESS_GPA, MAX_SOC_SCALE0_GAP_DIFF_EV
)


def load(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

u0 = load("gammaUO3_U0_1600_k222.json")
u3 = load("gammaUO3_U3_1600_k222.json")
u3k = load("gammaUO3_U3_1600_k333.json")
u3c = load("gammaUO3_U3_1800_k222.json")
seed = load("gammaUO3_U3_seeded_1600_k222.json")
soc = load("gammaUO3_SOC_sensitivity.json")

def compare(a, b):
    return {
        "delta_energy_meV_atom":
            abs(a["energy_eV_atom"] - b["energy_eV_atom"]) * 1000.0,
        "delta_gap_eV":
            abs(a["band_gap_eV"] - b["band_gap_eV"]),
        "delta_hydrostatic_stress_GPa":
            abs(
                a["hydrostatic_stress_GPa"]
                - b["hydrostatic_stress_GPa"]
            ),
    }

kconv = compare(u3, u3k)
cutconv = compare(u3, u3c)

for c in (kconv, cutconv):
    c["passes"] = bool(
        c["delta_energy_meV_atom"] <= MAX_DENERGY_MEV_ATOM
        and c["delta_gap_eV"] <= MAX_DGAP_EV
        and c["delta_hydrostatic_stress_GPa"] <= MAX_DSTRESS_GPA
    )

seed_m = seed.get("U_abs_mean_moment_muB")
nonmagnetic_pass = (
    seed_m is not None
    and seed_m <= MAX_SEEDED_U_MOMENT_MUB
)

fixed_geom_pass = (
    u3["max_force_eV_A"] <= MAX_FIXED_GEOM_FORCE_EV_A
    and u3["max_abs_stress_GPa"] <= MAX_FIXED_GEOM_STRESS_GPA
)

scale0_gap = soc["results"]["scale0"]["indirect_gap_eV"]
scale1_gap = soc["results"]["scale1"]["indirect_gap_eV"]
soc_consistency = (
    scale0_gap is not None
    and abs(scale0_gap - u3["band_gap_eV"])
    <= MAX_SOC_SCALE0_GAP_DIFF_EV
)

insulating_pass = (
    scale1_gap is not None
    and MIN_INSULATING_GAP_EV
    <= scale1_gap
    <= MAX_INSULATING_GAP_EV
)

overall = bool(
    manifest["structure_gate_passes"]
    and kconv["passes"]
    and cutconv["passes"]
    and nonmagnetic_pass
    and fixed_geom_pass
    and soc_consistency
    and insulating_pass
)

decision = {
    "step": "04B2C1",
    "system": "gamma-UO3-Fddd-293K",
    "role": "realistic U(VI), formal 5f0 reference",
    "structure_gate_passes": manifest["structure_gate_passes"],
    "U0_screen": {
        "gap_eV": u0["band_gap_eV"],
        "max_force_eV_A": u0["max_force_eV_A"],
        "max_abs_stress_GPa": u0["max_abs_stress_GPa"],
    },
    "U3_screen": {
        "gap_scalar_eV": u3["band_gap_eV"],
        "gap_SOC_eV": scale1_gap,
        "experimental_gap_guide_eV": EXP_GAP_GUIDE_EV,
        "SOC_gap_shift_eV": (
            None if scale1_gap is None
            else scale1_gap - scale0_gap
        ),
        "max_force_eV_A": u3["max_force_eV_A"],
        "max_abs_stress_GPa": u3["max_abs_stress_GPa"],
    },
    "U3_vs_U0_delta_gap_eV":
        u3["band_gap_eV"] - u0["band_gap_eV"],
    "seeded_magnetism": {
        "U_abs_mean_moment_muB": seed_m,
        "UVI_nonmagnetic_gate_passes": bool(nonmagnetic_pass),
    },
    "kpoint_convergence": kconv,
    "cutoff_convergence": cutconv,
    "fixed_geometry_sanity_passes": bool(fixed_geom_pass),
    "SOC_scale0_consistency_passes": bool(soc_consistency),
    "SOC_insulating_gate_passes": bool(insulating_pass),
    "step04B2C1_passes": overall,
    "selected_UVI_scalar_matrix": (
        {
            "dataset": "U14_nc6",
            "xc": "PBEsol",
            "Ueff_eV": 3.0,
            "ecut_eV": 1600,
            "kpts_primitive_gammaUO3": [2, 2, 2],
            "spin_state": "nonmagnetic_5f0",
            "SOC_for_electronic_structure": True,
        }
        if overall else None
    ),
    "production_authorization": False,
    "next_gate": (
        "If approved: Step04B2C2 relax the 32-atom primitive gamma-UO3 "
        "structure with the selected scalar matrix, validate the relaxed "
        "structure against the 293 K neutron reference, and repeat the "
        "final SOC gap. Only then can Step05 defect production be authorized."
    ),
}

(RESULTS / "decisao_step04B2C1.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(decision, indent=2, ensure_ascii=False))

if not overall:
    raise SystemExit(41)
