#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
from ase.eos import EquationOfState
from ase.units import GPa

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B1B2_R2 import (
    RESULTS, B1B1_CENTER, A_REF, A_EXP, SCALES, UEFFS,
    ECUT_LADDER, MAX_EOS_RMSE_MEV_ATOM,
    MAX_LATTICE_ERROR_PERCENT, B0_MIN_GPA, B0_MAX_GPA,
    MAX_CENTER_BRANCH_DE_MEV_ATOM, MAX_CENTER_BRANCH_DGAP_EV,
    MAX_CENTER_BRANCH_DMOMENT_MUB,
    MAX_CUTOFF_DE_MEV_ATOM, MAX_CUTOFF_DGAP_EV,
    MAX_CUTOFF_DMOMENT_MUB, MAX_CUTOFF_DPRESSURE_GPA
)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def tag_u(u):
    return str(u).replace(".", "p")


def tag_s(s):
    return f"{s:.2f}".replace(".", "p")


def eos_path(u, s):
    return RESULTS / f"UO2_nc6_U{tag_u(u)}_s{tag_s(s)}_1400.json"


def cutoff_path(u, ecut):
    return RESULTS / f"UO2_nc6_U{tag_u(u)}_center_{int(ecut)}.json"


eos_summary = {}
branch_summary = {}
cutoff_summary = {}
failed = []
rows = []

for ueff in UEFFS:
    records = []
    for scale in SCALES:
        r = load(eos_path(ueff, scale))
        if r.get("status") != "converged_tight":
            failed.append({
                "kind": "EOS",
                "Ueff_eV": ueff,
                "scale": scale,
                "record": r,
            })
        else:
            records.append(r)

    if len(records) == len(SCALES):
        records = sorted(records, key=lambda r: r["volume_A3"])
        volumes = np.array([r["volume_A3"] for r in records], float)
        energies = np.array([r["energy_eV"] for r in records], float)

        eos = EquationOfState(volumes, energies, eos="birchmurnaghan")
        v0, e0, B_eVA3 = eos.fit()
        a0 = float(v0 ** (1.0 / 3.0))
        B0 = float(B_eVA3 / GPa)

        # RMSE do ajuste em meV/átomo. EquationOfState.func recebe os
        # parâmetros ajustados armazenados internamente.
        fitted = eos.func(volumes, *eos.eos_parameters)
        rmse = float(
            np.sqrt(np.mean((energies - fitted) ** 2))
            / len(records[0].get("U_local_moments_muB", []))
            * 1000.0
        )
        # A célula contém 12 átomos; a divisão acima por 4 seria errada.
        # Recalcula explicitamente por 12.
        rmse = float(
            np.sqrt(np.mean((energies - fitted) ** 2))
            / 12.0 * 1000.0
        )

        aerr = abs(a0 - A_EXP) / A_EXP * 100.0
        structural = (
            rmse <= MAX_EOS_RMSE_MEV_ATOM
            and aerr <= MAX_LATTICE_ERROR_PERCENT
            and B0_MIN_GPA <= B0 <= B0_MAX_GPA
        )

        eos_summary[str(ueff)] = {
            "Ueff_eV": ueff,
            "npoints": 5,
            "a0_A": a0,
            "a_exp_A": A_EXP,
            "lattice_error_percent": float(aerr),
            "B0_GPa": B0,
            "eos_rmse_meV_atom": rmse,
            "structural_pass": bool(structural),
        }

        emin = min(r["energy_eV_atom"] for r in records)
        for r in records:
            rows.append({
                "Ueff_eV": ueff,
                "a_A": r["a_A"],
                "energy_eV_atom": r["energy_eV_atom"],
                "deltaE_from_min_meV_atom":
                    (r["energy_eV_atom"] - emin) * 1000.0,
                "band_gap_eV": r.get("band_gap_eV"),
                "U_abs_mean_moment_muB":
                    r.get("U_abs_mean_moment_muB"),
                "hydrostatic_stress_GPa":
                    r.get("hydrostatic_stress_GPa"),
                "max_abs_stress_GPa":
                    r.get("max_abs_stress_GPa"),
            })
    else:
        eos_summary[str(ueff)] = {
            "Ueff_eV": ueff,
            "npoints": len(records),
            "structural_pass": False,
            "status": "incomplete_eos",
        }

    # Ramo central determinístico versus B1B1.
    center_det = load(eos_path(ueff, 1.00))
    center_old = load(B1B1_CENTER[ueff])
    if (
        center_det.get("status") == "converged_tight"
        and center_old.get("status") == "converged_tight"
    ):
        dE = abs(
            center_det["energy_eV_atom"]
            - center_old["energy_eV_atom"]
        ) * 1000.0
        dgap = abs(
            center_det["band_gap_eV"]
            - center_old["band_gap_eV"]
        )
        dm = abs(
            center_det["U_abs_mean_moment_muB"]
            - center_old["U_abs_mean_moment_muB"]
        )
        same_branch = (
            dE <= MAX_CENTER_BRANCH_DE_MEV_ATOM
            and dgap <= MAX_CENTER_BRANCH_DGAP_EV
            and dm <= MAX_CENTER_BRANCH_DMOMENT_MUB
        )
        branch_summary[str(ueff)] = {
            "delta_energy_meV_atom": float(dE),
            "delta_gap_eV": float(dgap),
            "delta_moment_muB": float(dm),
            "same_branch_as_B1B1": bool(same_branch),
        }
    else:
        branch_summary[str(ueff)] = {
            "same_branch_as_B1B1": False,
            "status": "missing_center",
        }

    # Cutoff ladder.
    ladder = {}
    for ecut in ECUT_LADDER:
        r = load(cutoff_path(ueff, ecut))
        ladder[int(ecut)] = r

    steps = []
    selected = None
    for e1, e2 in zip(ECUT_LADDER[:-1], ECUT_LADDER[1:]):
        r1 = ladder[int(e1)]
        r2 = ladder[int(e2)]

        if (
            r1.get("status") != "converged_tight"
            or r2.get("status") != "converged_tight"
        ):
            steps.append({
                "from_eV": e1,
                "to_eV": e2,
                "passes": False,
                "status": "missing_converged_endpoint",
            })
            continue

        dE = abs(r2["energy_eV_atom"] - r1["energy_eV_atom"]) * 1000.0
        dgap = abs(r2["band_gap_eV"] - r1["band_gap_eV"])
        dm = abs(
            r2["U_abs_mean_moment_muB"]
            - r1["U_abs_mean_moment_muB"]
        )
        dp = abs(
            r2["hydrostatic_stress_GPa"]
            - r1["hydrostatic_stress_GPa"]
        )
        passes = (
            dE <= MAX_CUTOFF_DE_MEV_ATOM
            and dgap <= MAX_CUTOFF_DGAP_EV
            and dm <= MAX_CUTOFF_DMOMENT_MUB
            and dp <= MAX_CUTOFF_DPRESSURE_GPA
        )
        steps.append({
            "from_eV": e1,
            "to_eV": e2,
            "delta_energy_meV_atom": float(dE),
            "delta_gap_eV": float(dgap),
            "delta_moment_muB": float(dm),
            "delta_hydrostatic_stress_GPa": float(dp),
            "passes": bool(passes),
        })
        if passes and selected is None:
            selected = int(e1)

    cutoff_summary[str(ueff)] = {
        "steps": steps,
        "selected_production_cutoff_eV": selected,
        "validation_cutoff_eV": (
            selected + 200 if selected is not None else None
        ),
        "passes": selected is not None,
    }


if rows:
    with (RESULTS / "UO2_EOS_deterministic_R2.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

eligible = []
for ueff in UEFFS:
    if (
        eos_summary[str(ueff)].get("structural_pass")
        and branch_summary[str(ueff)].get("same_branch_as_B1B1")
        and cutoff_summary[str(ueff)].get("passes")
    ):
        eligible.append(ueff)

preferred = 3.0 if 3.0 in eligible else (eligible[0] if eligible else None)

decision = {
    "step": "04B1B2-R2",
    "purpose": (
        "Rebuild UO2 EOS with deterministic LCAO initialization and "
        "determine the minimum converged PW cutoff from a 1400/1600/1800 "
        "eV ladder."
    ),
    "eos_summary": eos_summary,
    "center_branch_consistency": branch_summary,
    "cutoff_ladder": cutoff_summary,
    "eligible_candidates": eligible,
    "preferred_Ueff_eV": preferred,
    "step04B1B2_R2_passes": preferred is not None,
    "failed_runs": failed,
    "production_authorization": False,
    "next_gate": (
        "If approved: Pb(II)/cerussite structural validation, then "
        "controlled SOC sensitivity for UO2 and realistic U(VI) validation."
    ),
    "warning": (
        "The scalar-collinear UO2 EOS remains a benchmark model and does "
        "not replace the non-collinear 3-k magnetic ground state."
    ),
}

(RESULTS / "decisao_step04B1B2_R2.json").write_text(
    json.dumps(decision, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("STEP 04B1B2-R2 — EOS DETERMINÍSTICO / CUTOFF LADDER")
print("=" * 80)
for ueff in UEFFS:
    print(f"Ueff={ueff:.1f} eV")
    print("  EOS:", eos_summary[str(ueff)])
    print("  ramo:", branch_summary[str(ueff)])
    print("  cutoff:", cutoff_summary[str(ueff)])
print("Elegíveis:", eligible)
print("Preferido:", preferred)
print(
    "STEP04B1B2-R2:",
    "APROVADO" if decision["step04B1B2_R2_passes"] else "REPROVADO",
)
print("Produção com defeitos: NÃO AUTORIZADA.")
print("=" * 80)
