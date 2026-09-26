#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent; sys.path.insert(0,str(SCRIPT_DIR))
from config_step05B import *
p=argparse.ArgumentParser(); p.add_argument("--phase",choices=["initial","final"],required=True); a=p.parse_args()
def load(m,n):
    f=RESULTS/f"{m}_{n}_PbCa.json"
    return None if not f.exists() else json.loads(f.read_text(encoding="utf-8"))
def sanity(r):
    pbo=r["PbO_first6_A"]
    return bool(r["full_stage_converged"] and r["max_force_eV_A"]<=MAX_FINAL_FORCE_EV_A and min(pbo)>=MIN_PBO_A and max(pbo)<=MAX_PBO_A)
def compare(x,y):
    d={"delta_raw_substitution_energy_eV":abs(x["raw_substitution_energy_eV"]-y["raw_substitution_energy_eV"]),
       "delta_relaxation_energy_eV":abs(x["relaxation_energy_eV"]-y["relaxation_energy_eV"]),
       "delta_PbO6_mean_A":abs(x["PbO6_mean_A"]-y["PbO6_mean_A"])}
    d["passes"]=bool(d["delta_raw_substitution_energy_eV"]<=MAX_DELTA_RAW_SUBSTITUTION_ENERGY_EV and d["delta_relaxation_energy_eV"]<=MAX_DELTA_RELAXATION_ENERGY_EV and d["delta_PbO6_mean_A"]<=MAX_DELTA_MEAN_PBO6_A)
    return d

hosts={}; fallback=[]; overall=True
for m in ("calcita","dolomita"):
    r80=load(m,80); r160=load(m,160)
    if r80 is None or r160 is None: raise FileNotFoundError(f"80/160 ausente: {m}")
    s80,s160=sanity(r80),sanity(r160); c1=compare(r80,r160)
    selected=None; s240=None; finalpair=c1
    if s80 and s160 and c1["passes"]:
        selected=160
    else:
        fallback.append(m)
        if a.phase=="final":
            r240=load(m,240)
            if r240 is None: raise FileNotFoundError(f"240 ausente: {m}")
            s240=sanity(r240); c2=compare(r160,r240); finalpair=c2
            if s160 and s240 and c2["passes"]: selected=240
    hp=selected is not None
    if a.phase=="final": overall=overall and hp
    hosts[m]={"sanity_80":s80,"sanity_160":s160,"comparison_80_to_160":c1,
      "fallback_required":m in fallback,"sanity_240":s240,"final_pair_comparison":finalpair,
      "selected_supercell_natoms":selected,"finite_size_gate_passes":hp}

initial={"step":"05B-initial-size-gate","hosts":hosts,"fallback_hosts":fallback,
         "all_hosts_converged_at_80_to_160":len(fallback)==0}
(RESULTS/"fallback_request_step05B.json").write_text(json.dumps(initial,indent=2,ensure_ascii=False),encoding="utf-8")
if a.phase=="initial":
    print(json.dumps(initial,indent=2,ensure_ascii=False)); raise SystemExit(0)

dec={"step":"05B","purpose":"Neutral isovalent Pb2+_Ca finite-size convergence gate before U defects.",
 "criteria":{"max_delta_raw_substitution_energy_eV":MAX_DELTA_RAW_SUBSTITUTION_ENERGY_EV,
             "max_delta_relaxation_energy_eV":MAX_DELTA_RELAXATION_ENERGY_EV,
             "max_delta_PbO6_mean_A":MAX_DELTA_MEAN_PBO6_A,"max_final_force_eV_A":MAX_FINAL_FORCE_EV_A},
 "hosts":hosts,"step05B_passes":bool(overall),"defect_formation_energies_authorized":False,
 "charged_U_defects_authorized":False,
 "next_gate":"If approved: Step05C enumerates physically distinct U4+, U6+ and Pb defect/charge-compensation motifs in the selected supercells, including Ca/Mg site specificity in dolomite.",
 "warning":"Raw Pb_Ca substitution energies are not formation energies; they are used only for the finite-size difference."}
(RESULTS/"decisao_step05B.json").write_text(json.dumps(dec,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(dec,indent=2,ensure_ascii=False))
if not overall: raise SystemExit(71)
