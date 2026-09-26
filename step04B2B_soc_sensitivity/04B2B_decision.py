#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path

SCRIPT_DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPT_DIR))
from config_step04B2B import (
    RESULTS,MAX_SCALE0_GAP_DIFF,SIGNIFICANT_GAP_SHIFT,
    SIGNIFICANT_U_ANISO_MEV_FU
)

def load(name):
    return json.loads((RESULTS/name).read_text(encoding="utf-8"))

pbgs=load("PbCO3_scalar_groundstate.json")
ugs=load("UO2_scalar_groundstate.json")
pbsoc=load("PbCO3_SOC_sensitivity.json")
usoc=load("UO2_SOC_sensitivity.json")

pb0=pbsoc["results"]["scale0"]; pb1=pbsoc["results"]["scale1"]
u0=usoc["results"]["scale0_z"]; uz=usoc["results"]["scale1_z"]
ux=usoc["results"]["scale1_x"]; uy=usoc["results"]["scale1_y"]

pbsg=pbgs.get("scalar_gap_eV"); usg=ugs.get("scalar_gap_eV")
pbg0=pb0.get("indirect_gap_eV"); ug0=u0.get("indirect_gap_eV")

pb_diff=None if pbsg is None or pbg0 is None else abs(pbg0-pbsg)
u_diff=None if usg is None or ug0 is None else abs(ug0-usg)
pb_cons=pb_diff is not None and pb_diff<=MAX_SCALE0_GAP_DIFF
u_cons=u_diff is not None and u_diff<=MAX_SCALE0_GAP_DIFF

pb_shift=None if pb1["indirect_gap_eV"] is None else pb1["indirect_gap_eV"]-pbg0
u_shift=None if uz["indirect_gap_eV"] is None else uz["indirect_gap_eV"]-ug0

u_be=[uz["band_energy_eV_fu"],ux["band_energy_eV_fu"],uy["band_energy_eV_fu"]]
u_aniso=(max(u_be)-min(u_be))*1000.0

pb_sig=pb_shift is not None and abs(pb_shift)>=SIGNIFICANT_GAP_SHIFT
u_sig=((u_shift is not None and abs(u_shift)>=SIGNIFICANT_GAP_SHIFT)
       or u_aniso>=SIGNIFICANT_U_ANISO_MEV_FU)

technical=bool(pb_cons and u_cons)

decision={
    "step":"04B2B",
    "scope":"Controlled non-self-consistent SOC sensitivity for approved PbCO3 and UO2 references.",
    "technical_consistency":{
        "PbCO3_scale0_vs_scalar_gap_diff_eV":pb_diff,
        "PbCO3_pass":bool(pb_cons),
        "UO2_scale0_vs_scalar_gap_diff_eV":u_diff,
        "UO2_pass":bool(u_cons),
        "overall_pass":technical},
    "PbCO3_SOC":{
        "scalar_gap_eV":pbg0,
        "SOC_gap_eV":pb1["indirect_gap_eV"],
        "delta_gap_eV":pb_shift,
        "band_energy_shift_eV_fu":
            pb1["band_energy_eV_fu"]-pb0["band_energy_eV_fu"],
        "SOC_significant_for_electronic_structure":bool(pb_sig)},
    "UO2_SOC":{
        "scalar_gap_eV":ug0,
        "SOC_gap_z_eV":uz["indirect_gap_eV"],
        "SOC_gap_x_eV":ux["indirect_gap_eV"],
        "SOC_gap_y_eV":uy["indirect_gap_eV"],
        "delta_gap_z_eV":u_shift,
        "band_energy_anisotropy_meV_fu":float(u_aniso),
        "SOC_significant":bool(u_sig)},
    "policy":{
        "structural_relaxations":"Remain scalar-relativistic at this stage.",
        "electronic_structure":"Include SOC when classified significant.",
        "defect_thermodynamics":"For U/Pb defects, carry a SOC single-point energy sensitivity correction if SOC is significant."},
    "step04B2B_passes":technical,
    "production_authorization":False,
    "next_gate":"Step04B2C: realistic U(VI) compound validation before Step05 defect production.",
    "warning":"soc_eigenstates is non-self-consistent; UO2 remains a collinear 1-k sensitivity test, not a self-consistent 3-k SOC calculation."
}
(RESULTS/"decisao_step04B2B.json").write_text(
    json.dumps(decision,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(decision,indent=2,ensure_ascii=False))
