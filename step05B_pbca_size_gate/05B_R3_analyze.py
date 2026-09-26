#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from config_step05B_R3 import *

parser = argparse.ArgumentParser()
parser.add_argument("--phase", choices=["initial", "final"], required=True)
args = parser.parse_args()


def load(mineral, n):
    p = RESULTS / f"{mineral}_{n}_PbCa.json"
    return None if not p.exists() else json.loads(p.read_text(encoding="utf-8"))


def sanity(r):
    pbo = r["PbO_first6_A"]
    return bool(
        r["status"] == "converged"
        and r["defect_max_force_gamma_eV_A"] <= MAX_FINAL_FORCE_EV_A
        and min(pbo) >= MIN_PBO_A
        and max(pbo) <= MAX_PBO_A
    )


def densepass(r):
    d = r["dense80_calibration"]
    return bool(
        d is not None
        and d["gamma_to_dense_raw_delta_eV"]
        <= MAX_GAMMA_TO_DENSE_RAW_DELTA_EV
    )


def compare(a, b):
    d = {
        "delta_raw_substitution_energy_gamma_eV":
            abs(
                a["raw_substitution_energy_gamma_eV"]
                - b["raw_substitution_energy_gamma_eV"]
            ),
        "delta_relaxation_energy_gamma_eV":
            abs(
                a["relaxation_energy_gamma_eV"]
                - b["relaxation_energy_gamma_eV"]
            ),
        "delta_PbO6_mean_A":
            abs(a["PbO6_mean_A"] - b["PbO6_mean_A"]),
    }
    d["passes"] = bool(
        d["delta_raw_substitution_energy_gamma_eV"]
        <= MAX_DELTA_RAW_SUBSTITUTION_ENERGY_EV
        and d["delta_relaxation_energy_gamma_eV"]
        <= MAX_DELTA_RELAXATION_ENERGY_EV
        and d["delta_PbO6_mean_A"]
        <= MAX_DELTA_MEAN_PBO6_A
    )
    return d


hosts = {}
fallback = []
overall = True

for mineral in ("calcita", "dolomita"):
    r80 = load(mineral, 80)
    r160 = load(mineral, 160)
    if r80 is None or r160 is None:
        raise FileNotFoundError(f"80/160 ausente: {mineral}")

    s80 = sanity(r80)
    s160 = sanity(r160)
    k80 = densepass(r80)
    c1 = compare(r80, r160)

    selected = None
    s240 = None
    finalpair = c1

    if k80 and s80 and s160 and c1["passes"]:
        selected = 160
    else:
        fallback.append(mineral)
        if args.phase == "final":
            r240 = load(mineral, 240)
            if r240 is None:
                raise FileNotFoundError(f"240 ausente: {mineral}")

            s240 = sanity(r240)
            c2 = compare(r160, r240)
            finalpair = c2

            if k80 and s160 and s240 and c2["passes"]:
                selected = 240

    host_pass = selected is not None
    if args.phase == "final":
        overall = overall and host_pass

    hosts[mineral] = {
        "gamma_vs_dense_80_passes": k80,
        "gamma_vs_dense_80_delta_eV":
            r80["dense80_calibration"]["gamma_to_dense_raw_delta_eV"],
        "sanity_80": s80,
        "sanity_160": s160,
        "comparison_80_to_160": c1,
        "fallback_required": mineral in fallback,
        "sanity_240": s240,
        "final_pair_comparison": finalpair,
        "selected_supercell_natoms": selected,
        "finite_size_gate_passes": host_pass,
    }

initial = {
    "step": "05B-R3-initial",
    "hosts": hosts,
    "fallback_hosts": fallback,
    "all_hosts_converged_at_80_to_160": len(fallback) == 0,
}

(RESULTS / "fallback_request_step05B_R3.json").write_text(
    json.dumps(initial, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

if args.phase == "initial":
    print(json.dumps(initial, indent=2, ensure_ascii=False))
    raise SystemExit(0)

decision = {
    "step": "05B-R3",
    "mpi_processes": MPI_PROCESSES,
    "hosts": hosts,
    "step05B_R3_passes": bool(overall),
    "selected_supercells": {
        m: hosts[m]["selected_supercell_natoms"]
        for m in hosts
    },
    "defect_formation_energies_authorized": False,
    "charged_U_defects_authorized": False,
    "next_gate": (
        "If approved: Step05C motif enumeration and targeted "
        "k-point/cutoff validation on the selected supercells "
        "before formation-energy production."
    ),
}

(RESULTS / "decisao_step05B_R3.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print(json.dumps(decision, indent=2, ensure_ascii=False))

if not overall:
    raise SystemExit(74)
