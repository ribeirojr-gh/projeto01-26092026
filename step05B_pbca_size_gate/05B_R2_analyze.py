#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent; sys.path.insert(0,str(SCRIPT_DIR))
from config_step05B_R2 import *
p=argparse.ArgumentParser(); p.add_argument("--phase",choices=["initial","final"],required=True); args=p.parse_args()

def load(m,n):
    f=RESULTS/f"{m}_{n}_PbCa.json"
    return None if not f.exists() else json.loads(f.read_text(encoding="utf-8"))

def sanity(r):
    pbo=r["PbO_first6_A"]
    return bool(r["status"]=="converged" and r["defect_max_force_gamma_eV_A"]<=MAX_FINAL_FORCE_EV_A
                and min(pbo)>=MIN_PBO_A and max(pbo)<=MAX_PBO_A)

def densepass(r):
    d=r["dense80_calibration"]
    return bool(d is not None and d["gamma_to_dense_raw_delta_eV"]<=MAX_GAMMA_TO_DENSE_RAW_DELTA_EV)

def compare(a,b):
    d={"delta_raw_substitution_energy_gamma_eV":abs(a["raw_substitution_energy_gamma_eV"]-b["raw_substitution_energy_gamma_eV"]),
       "delta_relaxation_energy_gamma_eV":abs(a["relaxation_energy_gamma_eV"]-b["relaxation_energy_gamma_eV"]),
       "delta_PbO6_mean_A":abs(a["PbO6_mean_A"]-b["PbO6_mean_A"])}
    d["passes"]=bool(d["delta_raw_substitution_energy_gamma_eV"]<=MAX_DELTA_RAW_SUBSTITUTION_ENERGY_EV
      and d["delta_relaxation_energy_gamma_eV"]<=MAX_DELTA_RELAXATION_ENERGY_EV
      and d["delta_PbO6_mean_A"]<=MAX_DELTA_MEAN_PBO6_A)
    return d

hosts={}; fallback=[]; overall=True
for m in ("calcita","dolomita"):
    r80=load(m,80); r160=load(m,160)
    if r80 is None or r160 is None: raise FileNotFoundError(f"80/160 ausente: {m}")
    s80,s160=sanity(r80),sanity(r160); k80=densepass(r80); c1=compare(r80,r160)
    selected=None; s240=None; finalpair=c1
    if k80 and s80 and s160 and c1["passes"]:
        selected=160
    else:
        fallback.append(m)
        if args.phase=="final":
            r240=load(m,240)
            if r240 is None: raise FileNotFoundError(f"240 ausente: {m}")
            s240=sanity(r240); c2=compare(r160,r240); finalpair=c2
            if k80 and s160 and s240 and c2["passes"]: selected=240
    hp=selected is not None
    if args.phase=="final": overall=overall and hp
    hosts[m]={"gamma_vs_dense_80_passes":k80,
      "gamma_vs_dense_80_delta_eV":r80["dense80_calibration"]["gamma_to_dense_raw_delta_eV"],
      "sanity_80":s80,"sanity_160":s160,"comparison_80_to_160":c1,
      "fallback_required":m in fallback,"sanity_240":s240,"final_pair_comparison":finalpair,
      "selected_supercell_natoms":selected,"finite_size_gate_passes":hp}

initial={"step":"05B-R2-initial","hosts":hosts,"fallback_hosts":fallback,
         "all_hosts_converged_at_80_to_160":len(fallback)==0}
(RESULTS/"fallback_request_step05B_R2.json").write_text(json.dumps(initial,indent=2,ensure_ascii=False),encoding="utf-8")
if args.phase=="initial":
    print(json.dumps(initial,indent=2,ensure_ascii=False)); raise SystemExit(0)

dec={"step":"05B-R2",
 "reason_for_revision":"R1 calcite/80 succeeded with 6 reducible k-points, but calcite/160 was killed with 4. R2 therefore treats system-size/PW memory as the dominant bottleneck and uses Gamma-only finite-size energies, calibrated against a denser mesh in each 80-atom host.",
 "hosts":hosts,"step05B_R2_passes":bool(overall),
 "selected_supercells":{m:hosts[m]["selected_supercell_natoms"] for m in hosts},
 "defect_formation_energies_authorized":False,"charged_U_defects_authorized":False,
 "next_gate":"If approved: Step05C motif enumeration and targeted k-point/cutoff validation on the selected supercells before formation-energy production."}
(RESULTS/"decisao_step05B_R2.json").write_text(json.dumps(dec,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps(dec,indent=2,ensure_ascii=False))
if not overall: raise SystemExit(73)
