#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration module for Step 05C: Defect Motifs & Charge Compensation
in 160-Atom Minkowski Supercells for Calcite and Dolomite.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Validated Supercell Paths (from Step 05A / Step 05B)
SUPERCELLS = {
    "calcita": ROOT / "step05A_host_supercells" / "resultados_step05A" / "supercells_R1" / "calcita_det16_160atoms_R1.cif",
    "dolomita": ROOT / "step05A_host_supercells" / "resultados_step05A" / "supercells_R1" / "dolomita_det16_160atoms_R1.cif",
}

# Validated PAW Directories
PAW_DIRS = [
    ROOT / "step04_u_pb_paw_validation" / "paw_generated" / "U" / "PBEsol",
    ROOT / "step04_u_pb_paw_validation" / "paw_generated" / "Pb" / "PBEsol",
    ROOT / "step03_paw_pbesol_benchmark" / "paw_generated" / "PBEsol",
]

# DFT+U Hubbard parameter on localized U 5f manifold
HUBBARD_U_EV = 3.0

# GPAW setups dictionary
SETUPS = {
    "U": f":f,{HUBBARD_U_EV:.1f}",
    "default": "paw",
}

# DFT & Parallelization parameters
XC = "PBEsol"
ECUT_EV = 1400.0
SMEARING_EV = 0.05
MPI_PROCESSES = 8
NBANDS = -8

# DFT+U Hubbard parameter on localized U 5f manifold
HUBBARD_U_EV = 3.0

# Relaxation thresholds
FINAL_FMAX_EV_A = 0.03
MAX_STEPS = 120
LOCAL_RELAX_RADIUS_A = 4.8
