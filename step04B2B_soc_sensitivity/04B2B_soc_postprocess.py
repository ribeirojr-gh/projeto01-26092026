#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from gpaw import GPAW, setup_paths
from gpaw.spinorbit import soc_eigenstates

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config_step04B2B import (
    RESULTS,
    GPW,
    MATRIX_DIR,
    PB_DIR,
    U_DIR,
    PB_FU,
    U_FU,
)

U_APPROVED_GPW = (
    PROJECT_ROOT
    / "step04B1B2_uo2_eos_R2"
    / "resultados_step04B1B2_R2"
    / "restart"
    / "UO2_nc6_U3p0_center_1600_tight.gpw"
)


def gap_info(states):
    eig = np.asarray(states.eigenvalues(), dtype=float)
    ef = float(states.fermi_level)

    below = eig[eig <= ef]
    above = eig[eig > ef]

    if below.size == 0 or above.size == 0:
        return {
            "fermi_level_eV": ef,
            "indirect_gap_eV": None,
            "VBM_eV": None,
            "CBM_eV": None,
            "direct_gap_eV": None,
        }

    vbm = float(np.max(below))
    cbm = float(np.min(above))
    indirect = max(0.0, cbm - vbm)

    direct_values = []
    for eig_k in eig:
        occ_k = eig_k[eig_k <= ef]
        emp_k = eig_k[eig_k > ef]
        if occ_k.size and emp_k.size:
            direct_values.append(
                float(np.min(emp_k) - np.max(occ_k))
            )

    return {
        "fermi_level_eV": ef,
        "indirect_gap_eV": float(indirect),
        "VBM_eV": vbm,
        "CBM_eV": cbm,
        "direct_gap_eV": (
            float(min(direct_values))
            if direct_values else None
        ),
    }


def evaluate(calc, *, scale, theta, phi, fu):
    states = soc_eigenstates(
        calc,
        scale=scale,
        theta=theta,
        phi=phi,
    )
    result = gap_info(states)

    band_energy = float(
        states.calculate_band_energy()
    )

    result.update({
        "scale": float(scale),
        "theta_deg": float(theta),
        "phi_deg": float(phi),
        "band_energy_eV_cell": band_energy,
        "band_energy_eV_fu": band_energy / fu,
    })
    return result


def main():
    system = os.environ.get(
        "UPB_SOC_SYSTEM",
        "",
    ).strip()

    # A .gpw file stores setup identifiers, not the custom PAW XML files.
    # Therefore setup_paths must be restored before GPAW(gpw).
    setup_paths.insert(
        0,
        str(MATRIX_DIR.resolve()),
    )

    if system == "PbCO3":
        setup_paths.insert(
            0,
            str(PB_DIR.resolve()),
        )
        gpw = (
            GPW
            / "PbCO3_scalar_1600_k434_all.gpw"
        )
        fu = PB_FU
        cases = [
            ("scale0", 0.0, 0.0, 0.0),
            ("scale0p5", 0.5, 0.0, 0.0),
            ("scale1", 1.0, 0.0, 0.0),
        ]
        outfile = (
            RESULTS
            / "PbCO3_SOC_sensitivity.json"
        )

    elif system == "UO2":
        setup_paths.insert(
            0,
            str(U_DIR.resolve()),
        )

        # Crucial R3 change:
        # use the already-approved Step04B1B2-R2 .gpw directly.
        #
        # soc_eigenstates() needs eigenvalues, PAW projections, density
        # matrices and setups; it does NOT require PW coefficient arrays.
        # Therefore mode='all' is unnecessary for this SOC postprocessing.
        gpw = U_APPROVED_GPW
        fu = U_FU
        cases = [
            ("scale0_z", 0.0, 0.0, 0.0),
            ("scale0p5_z", 0.5, 0.0, 0.0),
            ("scale1_z", 1.0, 0.0, 0.0),
            ("scale1_x", 1.0, 90.0, 0.0),
            ("scale1_y", 1.0, 90.0, 90.0),
        ]
        outfile = (
            RESULTS
            / "UO2_SOC_sensitivity.json"
        )

    else:
        raise ValueError(
            "UPB_SOC_SYSTEM deve ser PbCO3 ou UO2"
        )

    if not gpw.exists():
        raise FileNotFoundError(gpw)

    calc = GPAW(str(gpw))

    results = {}
    for name, scale, theta, phi in cases:
        print(
            f"[SOC] {system}: {name} "
            f"scale={scale} theta={theta} phi={phi}",
            flush=True,
        )
        results[name] = evaluate(
            calc,
            scale=scale,
            theta=theta,
            phi=phi,
            fu=fu,
        )

    record = {
        "status": "completed",
        "step": "04B2B-R3",
        "system": system,
        "method": (
            "GPAW-25.7 non-self-consistent "
            "soc_eigenstates"
        ),
        "gpw_file": str(gpw),
        "requires_mode_all_wavefunctions": False,
        "results": results,
    }

    outfile.write_text(
        json.dumps(
            record,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            record,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
