#!/usr/bin/env python3
import json,sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent; sys.path.insert(0,str(SCRIPT_DIR))
from config_step04B2C2 import *
def load(n): return json.loads((RESULTS/n).read_text(encoding="utf-8"))
relax=load("relaxation_step04B2C2.json"); struct=load("structural_metrics_step04B2C2.json")
sp2=load("gammaUO3_relaxed_1600_k222.json"); sp3=load("gammaUO3_relaxed_1600_k333.json"); spc=load("gammaUO3_relaxed_1800_k222.json")
soc=load("gammaUO3_relaxed_SOC_convergence.json")
def comp(a,b):
    return {"delta_energy_meV_atom":abs(a["energy_eV_atom"]-b["energy_eV_atom"])*1000,
            "delta_gap_eV":abs(a["band_gap_eV"]-b["band_gap_eV"]),
            "delta_hydrostatic_stress_GPa":abs(a["hydrostatic_stress_GPa"]-b["hydrostatic_stress_GPa"])}
k=comp(sp2,sp3); c=comp(sp2,spc)
for x in (k,c):
    x["passes"]=bool(x["delta_energy_meV_atom"]<=MAX_DENERGY_MEV_ATOM and x["delta_gap_eV"]<=MAX_DGAP_EV and x["delta_hydrostatic_stress_GPa"]<=MAX_DSTRESS_GPA)
fs=bool(spc["max_force_eV_A"]<=MAX_FINAL_FORCE_EV_A and spc["max_abs_stress_GPa"]<=MAX_FINAL_STRESS_GPA)
cs=soc["cases"]; scalar=sp2["band_gap_eV"]
s0=cs["central_n192_scale0"]["indirect_gap_eV"]; s160=cs["central_n160_scale1"]["indirect_gap_eV"]; s192=cs["central_n192_scale1"]["indirect_gap_eV"]
sk=cs["1600_k333_n192_scale1"]["indirect_gap_eV"]; sc=cs["1800_k222_n192_scale1"]["indirect_gap_eV"]
g0=s0 is not None and abs(s0-scalar)<=MAX_SOC_SCALE0_VS_SCALAR_GAP_EV
gs=s160 is not None and s192 is not None and abs(s160-s192)<=MAX_SOC_SUBSPACE_DGAP_EV
gk=sk is not None and s192 is not None and abs(sk-s192)<=MAX_SOC_KPOINT_DGAP_EV
gc=sc is not None and s192 is not None and abs(sc-s192)<=MAX_SOC_CUTOFF_DGAP_EV
gp=s192 is not None and MIN_FINAL_SOC_GAP_EV<=s192<=MAX_FINAL_SOC_GAP_EV
ok=bool(relax["all_stages_converged"] and struct["structural_gate_passes"] and k["passes"] and c["passes"] and fs and g0 and gs and gk and gc and gp)
rec={"step":"04B2C2","system":"gamma-UO3-Fddd-relaxed","role":"final compound-level U(VI) validation",
 "relaxation_passes":bool(relax["all_stages_converged"]),"structural_gate_passes":bool(struct["structural_gate_passes"]),
 "kpoint_convergence":k,"cutoff_convergence":c,"validation_force_stress_passes":fs,
 "SOC":{"scalar_gap_eV":scalar,"final_SOC_gap_eV":s192,"experimental_gap_guide_eV":EXP_GAP_GUIDE_EV,
        "SOC_gap_shift_eV":None if s192 is None else s192-scalar,"scale0_consistency_passes":bool(g0),
        "subspace_160_vs_192_delta_gap_eV":None if s160 is None or s192 is None else abs(s160-s192),
        "subspace_convergence_passes":bool(gs),"kpoint_SOC_delta_gap_eV":None if sk is None or s192 is None else abs(sk-s192),
        "kpoint_SOC_convergence_passes":bool(gk),"cutoff_SOC_delta_gap_eV":None if sc is None or s192 is None else abs(sc-s192),
        "cutoff_SOC_convergence_passes":bool(gc),"physical_gap_gate_passes":bool(gp)},
 "step04B2C2_passes":ok,
 "selected_UVI_matrix":{"dataset":"U14_nc6","xc":"PBEsol","Ueff_eV":3.0,"production_cutoff_eV":1600,"validation_cutoff_eV":1800,
                        "spin_state":"nonmagnetic_5f0","SOC_required_for_electronic_structure":True} if ok else None,
 "production_authorization":ok,
 "next_gate":"If approved: Step05 may begin with carbonate supercell-size, charge-compensation and defect-configuration convergence before production formation-energy calculations.",
 "warning":"SOC remains non-self-consistent; do not use raw SOC band-energy shifts as defect formation-energy corrections."}
(RESULTS/"decisao_step04B2C2.json").write_text(json.dumps(rec,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(rec,indent=2,ensure_ascii=False))
if not ok: raise SystemExit(51)
