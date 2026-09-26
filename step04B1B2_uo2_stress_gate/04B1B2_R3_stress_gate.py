#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

R2_DIR = (
    PROJECT_ROOT
    / "step04B1B2_uo2_eos_R2"
    / "resultados_step04B1B2_R2"
)
R2_CSV = R2_DIR / "UO2_EOS_deterministic_R2.csv"
R2_DECISION = R2_DIR / "decisao_step04B1B2_R2.json"

B1B1_DECISION = (
    PROJECT_ROOT
    / "step04B1B_uo2_reproducibility"
    / "resultados_step04B1B1"
    / "decisao_step04B1B1.json"
)

RESULTS = SCRIPT_DIR / "resultados_step04B1B2_R3"
RESULTS.mkdir(parents=True, exist_ok=True)

A_EXP = 5.47127
U_TARGET = 3.0

# Gates estruturais independentes do EOS de energia.
MIN_STRESS_FIT_R2 = 0.98
MAX_A0_ERROR_PERCENT = 0.50
B0_MIN_GPA = 175.0
B0_MAX_GPA = 240.0
MAX_FULL_VS_LOCAL_A0_DIFF_A = 0.020
MAX_FULL_VS_LOCAL_B0_REL_DIFF_PERCENT = 5.0


def load_csv(path: Path):
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append({
                key: (
                    float(value)
                    if key not in {"dataset", "status"} and value not in {"", None}
                    else value
                )
                for key, value in row.items()
            })
    return rows


def linear_stress_fit(rows, label: str):
    rows = sorted(rows, key=lambda r: r["a_A"])
    a = np.array([r["a_A"] for r in rows], float)
    sigma = np.array([r["hydrostatic_stress_GPa"] for r in rows], float)

    v = a**3
    v_exp = A_EXP**3
    eps_v = (v - v_exp) / v_exp

    # sigma_h = B * eps_v + intercept, for small isotropic strains.
    slope, intercept = np.polyfit(eps_v, sigma, 1)
    pred = slope * eps_v + intercept

    residual = sigma - pred
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((sigma - sigma.mean())**2))
    r2 = 1.0 - ss_res / ss_tot
    rmse = float(np.sqrt(np.mean(residual**2)))

    eps_zero = -intercept / slope
    v0 = v_exp * (1.0 + eps_zero)
    a0 = float(v0 ** (1.0 / 3.0))
    aerr = abs(a0 - A_EXP) / A_EXP * 100.0
    b0 = float(slope)

    return {
        "fit": label,
        "npoints": len(rows),
        "a_min_A": float(a.min()),
        "a_max_A": float(a.max()),
        "a0_from_zero_stress_A": a0,
        "a_exp_A": A_EXP,
        "lattice_error_percent": float(aerr),
        "B0_from_stress_slope_GPa": b0,
        "stress_fit_R2": float(r2),
        "stress_fit_RMSE_GPa": rmse,
        "slope_GPa_per_volumetric_strain": float(slope),
        "intercept_GPa": float(intercept),
    }


for required in (R2_CSV, R2_DECISION, B1B1_DECISION):
    if not required.exists():
        raise FileNotFoundError(required)

rows = load_csv(R2_CSV)
u3 = [
    r for r in rows
    if abs(float(r["Ueff_eV"]) - U_TARGET) < 1.0e-12
]

if len(u3) != 5:
    raise RuntimeError(
        f"Esperados 5 pontos Ueff=3 eV no CSV R2; encontrados {len(u3)}"
    )

u3 = sorted(u3, key=lambda r: r["a_A"])
full = linear_stress_fit(u3, "five_point_pm2pct")
local = linear_stress_fit(u3[1:4], "central_three_pm1pct")

a0_diff = abs(
    full["a0_from_zero_stress_A"]
    - local["a0_from_zero_stress_A"]
)
b0_rel_diff = abs(
    full["B0_from_stress_slope_GPa"]
    - local["B0_from_stress_slope_GPa"]
) / local["B0_from_stress_slope_GPa"] * 100.0

full_pass = (
    full["stress_fit_R2"] >= MIN_STRESS_FIT_R2
    and full["lattice_error_percent"] <= MAX_A0_ERROR_PERCENT
    and B0_MIN_GPA <= full["B0_from_stress_slope_GPa"] <= B0_MAX_GPA
)

local_pass = (
    local["stress_fit_R2"] >= MIN_STRESS_FIT_R2
    and local["lattice_error_percent"] <= MAX_A0_ERROR_PERCENT
    and B0_MIN_GPA <= local["B0_from_stress_slope_GPa"] <= B0_MAX_GPA
)

fit_consistency_pass = (
    a0_diff <= MAX_FULL_VS_LOCAL_A0_DIFF_A
    and b0_rel_diff <= MAX_FULL_VS_LOCAL_B0_REL_DIFF_PERCENT
)

r2_decision = json.loads(R2_DECISION.read_text(encoding="utf-8"))
b1b1 = json.loads(B1B1_DECISION.read_text(encoding="utf-8"))

u3_cutoff = r2_decision["cutoff_ladder"]["3.0"]
u3_center = r2_decision["center_branch_consistency"]["3.0"]
u4_cutoff = r2_decision["cutoff_ladder"]["4.0"]

cutoff_pass = (
    u3_cutoff.get("passes") is True
    and u3_cutoff.get("selected_production_cutoff_eV") == 1600
    and u3_cutoff.get("validation_cutoff_eV") == 1800
)
center_pass = u3_center.get("same_branch_as_B1B1") is True
b1b1_pass = b1b1.get("step04B1B1_passes") is True

scalar_benchmark_pass = bool(
    full_pass
    and local_pass
    and fit_consistency_pass
    and cutoff_pass
    and center_pass
    and b1b1_pass
)

fit_rows = [full, local]
with (RESULTS / "UO2_stress_strain_fits_R3.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(handle, fieldnames=fit_rows[0].keys())
    writer.writeheader()
    writer.writerows(fit_rows)

decision = {
    "step": "04B1B2-R3",
    "purpose": (
        "Resolve the UO2 structural gate using the smooth hydrostatic "
        "stress-versus-volumetric-strain response after the energy EOS "
        "was shown to be contaminated by DFT+U orbital-branch offsets."
    ),
    "energy_eos_diagnostic": {
        "Ueff_3_eV_energy_EOS_valid_for_B0": False,
        "reason": (
            "The deterministic R2 energy fit has RMSE "
            f"{r2_decision['eos_summary']['3.0']['eos_rmse_meV_atom']:.4f} "
            "meV/atom and discontinuous gap/moment behavior across volumes. "
            "It is retained as a metastability diagnostic, not used for B0."
        ),
        "R2_energy_EOS_a0_A":
            r2_decision["eos_summary"]["3.0"]["a0_A"],
        "R2_energy_EOS_B0_GPa":
            r2_decision["eos_summary"]["3.0"]["B0_GPa"],
    },
    "stress_strain_fits": {
        "five_point": full,
        "central_three": local,
        "a0_difference_between_fits_A": float(a0_diff),
        "B0_relative_difference_between_fits_percent":
            float(b0_rel_diff),
        "fit_consistency_pass": bool(fit_consistency_pass),
    },
    "stress_gate_criteria": {
        "min_R2": MIN_STRESS_FIT_R2,
        "max_lattice_error_percent": MAX_A0_ERROR_PERCENT,
        "B0_range_GPa": [B0_MIN_GPA, B0_MAX_GPA],
        "max_full_vs_local_a0_difference_A":
            MAX_FULL_VS_LOCAL_A0_DIFF_A,
        "max_full_vs_local_B0_relative_difference_percent":
            MAX_FULL_VS_LOCAL_B0_REL_DIFF_PERCENT,
    },
    "B1B1_reproducibility_pass": bool(b1b1_pass),
    "center_branch_consistency_pass": bool(center_pass),
    "cutoff_gate": u3_cutoff,
    "cutoff_gate_pass": bool(cutoff_pass),
    "Ueff_4_eV_status": {
        "primary_candidate": False,
        "reason": (
            "Ueff=4 eV shows severe electronic branch switching in the "
            "cutoff ladder and an incomplete EOS."
        ),
        "cutoff_ladder": u4_cutoff,
    },
    "selected_scalar_collinear_reference": (
        {
            "dataset": "U14_nc6",
            "xc": "PBEsol",
            "Ueff_eV": 3.0,
            "production_cutoff_eV": 1600,
            "validation_cutoff_eV": 1800,
            "kpts_UO2": [3, 3, 3],
            "smearing_eV": 0.05,
            "magnetic_model": "collinear 1-k AFM benchmark",
            "SOC": False,
        }
        if scalar_benchmark_pass else None
    ),
    "step04B1B2_R3_passes": scalar_benchmark_pass,
    "production_authorization": False,
    "next_gate": (
        "Pb(II) compound-level validation in cerussite with the generated "
        "PBEsol Pb PAW, followed by controlled SOC sensitivity for UO2 and "
        "realistic U(VI) validation before carbonate-defect production."
    ),
    "warning": (
        "The stress-derived B0 is a local elastic estimate for the scalar-"
        "collinear benchmark. DFT+U orbital metastability invalidates the "
        "absolute energy EOS across independently initialized volumes."
    ),
}

(RESULTS / "decisao_step04B1B2_R3.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B1B2-R3 — STRESS–STRAIN GATE")
print("=" * 80)
print(
    f"5 pontos: a0={full['a0_from_zero_stress_A']:.8f} Å | "
    f"erro={full['lattice_error_percent']:.4f}% | "
    f"B0={full['B0_from_stress_slope_GPa']:.3f} GPa | "
    f"R²={full['stress_fit_R2']:.6f}"
)
print(
    f"3 centrais: a0={local['a0_from_zero_stress_A']:.8f} Å | "
    f"erro={local['lattice_error_percent']:.4f}% | "
    f"B0={local['B0_from_stress_slope_GPa']:.3f} GPa | "
    f"R²={local['stress_fit_R2']:.6f}"
)
print(f"Δa0 entre fits = {a0_diff:.6f} Å")
print(f"ΔB0 relativo   = {b0_rel_diff:.3f}%")
print(f"Cutoff U=3     = {'PASS' if cutoff_pass else 'FAIL'}")
print(f"B1B1 repro.    = {'PASS' if b1b1_pass else 'FAIL'}")
print(
    "SCALAR/COLLINEAR UO2:",
    "APROVADO" if scalar_benchmark_pass else "REPROVADO",
)
print("Produção com defeitos: NÃO AUTORIZADA.")
print("=" * 80)
