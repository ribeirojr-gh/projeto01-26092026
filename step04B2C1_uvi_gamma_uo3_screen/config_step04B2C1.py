#!/usr/bin/env python3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

STRUCT_DIR = SCRIPT_DIR / "estruturas"
CIF = STRUCT_DIR / "gamma_UO3_293K_COD1527742.cif"
CONV_TRAJ = STRUCT_DIR / "gamma_UO3_293K_conventional.traj"
PRIM_TRAJ = STRUCT_DIR / "gamma_UO3_293K_primitive.traj"
MANIFEST = STRUCT_DIR / "gamma_UO3_structure_manifest.json"

MATRIX_DIR = (
    PROJECT_ROOT
    / "step03_paw_pbesol_benchmark"
    / "paw_generated"
    / "PBEsol"
)

U_DIR = (
    PROJECT_ROOT
    / "step04_u_pb_paw_validation"
    / "paw_candidates"
    / "U_R5_pseudization"
    / "U14_nc6"
    / "PBEsol"
)

RESULTS = SCRIPT_DIR / "resultados_step04B2C1"
LOGS = SCRIPT_DIR / "logs"
GPW = RESULTS / "gpw"

# Referência primária: Loopstra, Taylor & Waugh, JSSC 20 (1977) 9–19.
COD_ID = "1527742"
EXP_A_A = 9.787
EXP_B_A = 19.932
EXP_C_A = 9.705
EXP_SPACEGROUP = 70  # Fddd
EXP_TEMPERATURE_K = 293.0
EXP_SHORTEST_UO_A = 1.796

# Guia eletrônico compilado para gamma-UO3/Fddd.
EXP_GAP_GUIDE_EV = 2.38

XC = "PBEsol"
UEFF_MAIN_EV = 3.0
ECUT_PROD_EV = 1600.0
ECUT_VAL_EV = 1800.0
KPTS_PROD = (2, 2, 2)
KPTS_VAL = (3, 3, 3)
NBANDS = 160
SMEARING_EV = 0.05

# Gates numéricos.
MAX_DENERGY_MEV_ATOM = 2.0
MAX_DGAP_EV = 0.08
MAX_DSTRESS_GPA = 0.20

# Gates físicos amplos para a triagem em geometria experimental.
MIN_INSULATING_GAP_EV = 1.5
MAX_INSULATING_GAP_EV = 3.5
MAX_SEEDED_U_MOMENT_MUB = 0.20
MAX_FIXED_GEOM_FORCE_EV_A = 2.0
MAX_FIXED_GEOM_STRESS_GPA = 10.0

# Consistência SOC scale=0.
MAX_SOC_SCALE0_GAP_DIFF_EV = 0.05
