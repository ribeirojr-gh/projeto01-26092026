#!/usr/bin/env python3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Matriz já validada no Step03.
MATRIX_PBESOL_DIR = (
    PROJECT_ROOT
    / "step03_paw_pbesol_benchmark"
    / "paw_generated"
    / "PBEsol"
)

STEP04A_DIR = PROJECT_ROOT / "step04_u_pb_paw_validation"

U_POLY6_PBESOL_DIR = (
    STEP04A_DIR / "paw_generated" / "U" / "PBEsol"
)

U_NC6_PBESOL_DIR = (
    STEP04A_DIR
    / "paw_candidates"
    / "U_R5_pseudization"
    / "U14_nc6"
    / "PBEsol"
)

PB_PBESOL_DIR = (
    STEP04A_DIR / "paw_generated" / "Pb" / "PBEsol"
)

STRUCTURES_DIR = SCRIPT_DIR / "estruturas"
RESULTS_DIR = SCRIPT_DIR / "resultados_step04B1A"
LOGS_DIR = SCRIPT_DIR / "logs"

# Numerical screening parameters.
ECUT_EV = 1400.0
SMEARING_EV = 0.05

# Fixed experimental/reference structures.
UO2_A_EXP_A = 5.4706
DELTA_UO3_A_REF_A = 4.1658

# UO2 conventional fluorite AFM screening.
KPTS_UO2 = (3, 3, 3)

# delta-UO3 is a small cubic U(VI) screening reference.
KPTS_UO3 = (5, 5, 5)

# Cerussite PbCO3: 20-atom orthorhombic conventional cell.
KPTS_PBCO3 = (3, 2, 3)

# GPAW implements Dudarev Ueff = U - J.
UEFF_GRID_EV = (0.0, 2.0, 3.0, 4.0, 5.0)

# Experimental targets used only as screening guides.
# UO2 low-temperature ordered moment:
UO2_MOMENT_TARGET_MUB = 1.74

# Experimental optical/fundamental gap is literature-dependent; use a
# deliberately broad target interval rather than fitting to a single number.
UO2_GAP_TARGET_MIN_EV = 2.0
UO2_GAP_TARGET_MAX_EV = 2.5

CERUSSITE_COD_ID = 9008411
CERUSSITE_URL = (
    "https://www.crystallography.net/cod/9008411.cif"
)
