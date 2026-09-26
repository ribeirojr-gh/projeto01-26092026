#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS = SCRIPT_DIR / "resultados_step04B2C2"

# Referência experimental Fddd, 293 K.
A_ORTH = 9.787
B_ORTH = 19.932
C_ORTH = 9.705
V_ORTH = A_ORTH * B_ORTH * C_ORTH
Z_ORTH = 32  # fórmulas UO3 na célula convencional Fddd de 128 átomos

# Referência tetragonal de alta T apenas como comparação secundária.
A_TET_373 = 6.9013
C_TET_373 = 19.9754

# Gates revisados. Os limites NÃO foram afrouxados; corrigimos somente
# a comparação entre células convencionais de multiplicidades diferentes.
MAX_PSEUDOTET_BASAL_ERROR_PERCENT = 2.0
MAX_PSEUDOTET_LONG_ERROR_PERCENT = 2.0
MAX_VOLUME_PER_FU_ERROR_PERCENT = 4.0
MAX_SHORTEST_UO_ERROR_PERCENT = 5.0
MAX_UO6_RMS_REL_ERROR_PERCENT = 3.0

MAX_DENERGY_MEV_ATOM = 2.0
MAX_DGAP_EV = 0.08
MAX_DSTRESS_GPA = 0.20
MAX_FINAL_FORCE_EV_A = 0.05
MAX_FINAL_STRESS_GPA = 0.40

MAX_SOC_SCALE0_DIFF_EV = 0.05
MAX_SOC_SUBSPACE_DIFF_EV = 0.05
MAX_SOC_KPOINT_DIFF_EV = 0.10
MAX_SOC_CUTOFF_DIFF_EV = 0.08
MIN_FINAL_SOC_GAP_EV = 1.2
MAX_FINAL_SOC_GAP_EV = 3.2


def load(name: str):
    path = RESULTS / name
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


relax = load("relaxation_step04B2C2.json")
struct = load("structural_metrics_step04B2C2.json")
sp2 = load("gammaUO3_relaxed_1600_k222.json")
sp3 = load("gammaUO3_relaxed_1600_k333.json")
spc = load("gammaUO3_relaxed_1800_k222.json")
soc = load("gammaUO3_relaxed_SOC_convergence.json")

# -------------------------------------------------------------------------
# 1. Diagnóstico da falha do gate estrutural original
# -------------------------------------------------------------------------
# O relatório original chamou SpacegroupAnalyzer com symprec=0.03.
# Nesse tolerance, a estrutura relaxada foi promovida para I41/amd (#141),
# cuja célula convencional contém 16 f.u., enquanto a Fddd experimental
# contém 32 f.u. Comparar diretamente esses volumes produz ~50% de erro
# por construção.

symmetry_records = struct["symmetry"]

fine_fddd = any(
    x["number"] == 70 and abs(float(x["symprec_A"]) - 0.01) < 1e-12
    for x in symmetry_records
)

loose_tetragonal = any(
    x["number"] == 141 and float(x["symprec_A"]) >= 0.03
    for x in symmetry_records
)

relaxed_conv = struct["relaxed_conventional_cell_A"]
a_tet_rel = 0.5 * (float(relaxed_conv[0]) + float(relaxed_conv[1]))
c_tet_rel = float(relaxed_conv[2])

# Pseudotetragonalização da célula ortorrômbica Fddd a 293 K:
# a_t1 = a_orth/sqrt(2), a_t2 = c_orth/sqrt(2), c_t = b_orth.
a_t1 = A_ORTH / math.sqrt(2.0)
a_t2 = C_ORTH / math.sqrt(2.0)
a_t_mean = 0.5 * (a_t1 + a_t2)
c_t_ref = B_ORTH

basal_error = abs(a_tet_rel - a_t_mean) / a_t_mean * 100.0
long_error = abs(c_tet_rel - c_t_ref) / c_t_ref * 100.0

orthorhombic_distortion_percent = (
    abs(A_ORTH - C_ORTH) / (0.5 * (A_ORTH + C_ORTH)) * 100.0
)

# Volume por fórmula: comparação independente do setting convencional.
v_fu_exp = V_ORTH / Z_ORTH
v_fu_rel = float(relax["volume_A3"]) / 8.0  # primitiva: 8 UO3
v_fu_error = abs(v_fu_rel - v_fu_exp) / v_fu_exp * 100.0

# Comparação secundária com a fase tetragonal de 373 K.
a_373_error = abs(a_tet_rel - A_TET_373) / A_TET_373 * 100.0
c_373_error = abs(c_tet_rel - C_TET_373) / C_TET_373 * 100.0

local_geometry_pass = (
    float(struct["shortest_UO_error_percent"])
    <= MAX_SHORTEST_UO_ERROR_PERCENT
    and float(struct["UO6_mean_profile_RMS_relative_error_percent"])
    <= MAX_UO6_RMS_REL_ERROR_PERCENT
)

structural_reanalysis_pass = bool(
    fine_fddd
    and basal_error <= MAX_PSEUDOTET_BASAL_ERROR_PERCENT
    and long_error <= MAX_PSEUDOTET_LONG_ERROR_PERCENT
    and v_fu_error <= MAX_VOLUME_PER_FU_ERROR_PERCENT
    and local_geometry_pass
)

# -------------------------------------------------------------------------
# 2. Gates numéricos existentes
# -------------------------------------------------------------------------
def compare(a, b):
    return {
        "delta_energy_meV_atom":
            abs(a["energy_eV_atom"] - b["energy_eV_atom"]) * 1000.0,
        "delta_gap_eV":
            abs(a["band_gap_eV"] - b["band_gap_eV"]),
        "delta_hydrostatic_stress_GPa":
            abs(a["hydrostatic_stress_GPa"] - b["hydrostatic_stress_GPa"]),
    }


kconv = compare(sp2, sp3)
cutconv = compare(sp2, spc)

for item in (kconv, cutconv):
    item["passes"] = bool(
        item["delta_energy_meV_atom"] <= MAX_DENERGY_MEV_ATOM
        and item["delta_gap_eV"] <= MAX_DGAP_EV
        and item["delta_hydrostatic_stress_GPa"] <= MAX_DSTRESS_GPA
    )

force_stress_pass = bool(
    spc["max_force_eV_A"] <= MAX_FINAL_FORCE_EV_A
    and spc["max_abs_stress_GPa"] <= MAX_FINAL_STRESS_GPA
)

# -------------------------------------------------------------------------
# 3. Gates SOC existentes
# -------------------------------------------------------------------------
cases = soc["cases"]

scalar_gap = sp2["band_gap_eV"]
scale0 = cases["central_n192_scale0"]["indirect_gap_eV"]
soc160 = cases["central_n160_scale1"]["indirect_gap_eV"]
soc192 = cases["central_n192_scale1"]["indirect_gap_eV"]
sock = cases["1600_k333_n192_scale1"]["indirect_gap_eV"]
socc = cases["1800_k222_n192_scale1"]["indirect_gap_eV"]

soc_scale0_pass = (
    scale0 is not None
    and abs(scale0 - scalar_gap) <= MAX_SOC_SCALE0_DIFF_EV
)

soc_subspace_delta = abs(soc160 - soc192)
soc_k_delta = abs(sock - soc192)
soc_cut_delta = abs(socc - soc192)

soc_pass = bool(
    soc_scale0_pass
    and soc_subspace_delta <= MAX_SOC_SUBSPACE_DIFF_EV
    and soc_k_delta <= MAX_SOC_KPOINT_DIFF_EV
    and soc_cut_delta <= MAX_SOC_CUTOFF_DIFF_EV
    and MIN_FINAL_SOC_GAP_EV <= soc192 <= MAX_FINAL_SOC_GAP_EV
)

overall = bool(
    relax["all_stages_converged"]
    and structural_reanalysis_pass
    and kconv["passes"]
    and cutconv["passes"]
    and force_stress_pass
    and soc_pass
)

summary_rows = [
    {"metric": "Fddd at symprec=0.01", "value": fine_fddd, "passes": fine_fddd},
    {"metric": "I41/amd at loose symprec", "value": loose_tetragonal, "passes": True},
    {"metric": "pseudotetragonal basal error (%)", "value": basal_error,
     "passes": basal_error <= MAX_PSEUDOTET_BASAL_ERROR_PERCENT},
    {"metric": "pseudotetragonal long-axis error (%)", "value": long_error,
     "passes": long_error <= MAX_PSEUDOTET_LONG_ERROR_PERCENT},
    {"metric": "volume/f.u. error (%)", "value": v_fu_error,
     "passes": v_fu_error <= MAX_VOLUME_PER_FU_ERROR_PERCENT},
    {"metric": "shortest U-O error (%)", "value": struct["shortest_UO_error_percent"],
     "passes": struct["shortest_UO_error_percent"] <= MAX_SHORTEST_UO_ERROR_PERCENT},
    {"metric": "U-O6 RMS relative error (%)",
     "value": struct["UO6_mean_profile_RMS_relative_error_percent"],
     "passes": struct["UO6_mean_profile_RMS_relative_error_percent"] <= MAX_UO6_RMS_REL_ERROR_PERCENT},
]

with (RESULTS / "structural_reanalysis_step04B2C2_R2.csv").open(
    "w", newline="", encoding="utf-8"
) as handle:
    writer = csv.DictWriter(handle, fieldnames=["metric", "value", "passes"])
    writer.writeheader()
    writer.writerows(summary_rows)

decision = {
    "step": "04B2C2-R2",
    "system": "gamma-UO3",
    "purpose": (
        "Correct the structural gate by comparing equivalent crystallographic "
        "normalizations after the relaxed structure becomes pseudotetragonal."
    ),
    "original_gate_diagnosis": {
        "original_structural_gate_passes": struct["structural_gate_passes"],
        "reason": (
            "The original code standardized the relaxed structure at "
            "symprec=0.03 as I41/amd (#141), whose conventional cell contains "
            "16 UO3 formula units, and compared that cell directly to the "
            "293 K Fddd conventional cell containing 32 formula units. "
            "The resulting ~49% volume error is therefore not a physical "
            "volume error."
        ),
        "fine_symmetry_Fddd_at_0p01_A": fine_fddd,
        "higher_symmetry_I41amd_at_looser_tolerance": loose_tetragonal,
    },
    "pseudotetragonal_comparison_293K": {
        "experimental_a_over_sqrt2_A": a_t1,
        "experimental_c_over_sqrt2_A": a_t2,
        "experimental_mean_basal_A": a_t_mean,
        "relaxed_tetragonal_basal_A": a_tet_rel,
        "basal_error_percent": basal_error,
        "experimental_long_axis_b_A": c_t_ref,
        "relaxed_tetragonal_long_axis_A": c_tet_rel,
        "long_axis_error_percent": long_error,
        "experimental_orthorhombic_distortion_percent":
            orthorhombic_distortion_percent,
    },
    "volume_per_formula_unit": {
        "experimental_A3_fu": v_fu_exp,
        "relaxed_A3_fu": v_fu_rel,
        "error_percent": v_fu_error,
    },
    "local_UO_geometry": {
        "shortest_UO_error_percent": struct["shortest_UO_error_percent"],
        "UO6_RMS_relative_error_percent":
            struct["UO6_mean_profile_RMS_relative_error_percent"],
        "passes": local_geometry_pass,
    },
    "secondary_373K_tetragonal_comparison": {
        "reference_a_A": A_TET_373,
        "reference_c_A": C_TET_373,
        "a_error_percent": a_373_error,
        "c_error_percent": c_373_error,
        "note": (
            "Supporting comparison only; not used as the primary 293 K gate."
        ),
    },
    "structural_reanalysis_passes": structural_reanalysis_pass,
    "kpoint_convergence": kconv,
    "cutoff_convergence": cutconv,
    "force_stress_validation_passes": force_stress_pass,
    "SOC": {
        "scalar_gap_eV": scalar_gap,
        "final_SOC_gap_eV": soc192,
        "SOC_gap_shift_eV": soc192 - scalar_gap,
        "scale0_consistency_passes": soc_scale0_pass,
        "subspace_delta_gap_eV": soc_subspace_delta,
        "kpoint_delta_gap_eV": soc_k_delta,
        "cutoff_delta_gap_eV": soc_cut_delta,
        "passes": soc_pass,
    },
    "step04B2C2_R2_passes": overall,
    "selected_UVI_matrix": (
        {
            "dataset": "U14_nc6",
            "xc": "PBEsol",
            "Ueff_eV": 3.0,
            "production_cutoff_eV": 1600,
            "validation_cutoff_eV": 1800,
            "spin_state": "nonmagnetic_5f0",
            "SOC_required_for_electronic_structure": True,
        }
        if overall else None
    ),
    "production_authorization": overall,
    "next_gate": (
        "If approved, Step05 may begin with carbonate supercell-size, "
        "charge-compensation and defect-configuration convergence."
    ),
    "scientific_caveat": (
        "Static PBEsol+U relaxation suppresses the small orthorhombic "
        "distortion and approaches the closely related pseudotetragonal/"
        "I41/amd geometry. This is documented explicitly and is not treated "
        "as evidence that the experimental 293 K phase is tetragonal."
    ),
}

(RESULTS / "decisao_step04B2C2_R2.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B2C2-R2 — REANÁLISE ESTRUTURAL")
print("=" * 80)
print(f"Fddd @ 0.01 Å                  : {fine_fddd}")
print(f"I41/amd em tolerância frouxa  : {loose_tetragonal}")
print(f"Erro basal pseudotetragonal   : {basal_error:.4f} %")
print(f"Erro eixo longo               : {long_error:.4f} %")
print(f"Erro volume/f.u.              : {v_fu_error:.4f} %")
print(f"Erro U-O mínimo               : {struct['shortest_UO_error_percent']:.4f} %")
print(f"RMS perfil U-O6               : {struct['UO6_mean_profile_RMS_relative_error_percent']:.4f} %")
print(f"Gate estrutural corrigido     : {'PASS' if structural_reanalysis_pass else 'FAIL'}")
print(f"Gate k-points                 : {'PASS' if kconv['passes'] else 'FAIL'}")
print(f"Gate cutoff                   : {'PASS' if cutconv['passes'] else 'FAIL'}")
print(f"Gate SOC                      : {'PASS' if soc_pass else 'FAIL'}")
print(f"STEP04B2C2-R2                 : {'APROVADO' if overall else 'REPROVADO'}")
print(f"PRODUCTION AUTHORIZATION      : {overall}")
print("=" * 80)

if not overall:
    raise SystemExit(52)
