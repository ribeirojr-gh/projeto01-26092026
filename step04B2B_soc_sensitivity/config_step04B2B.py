from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

PBCO3_RELAXED = (PROJECT_ROOT / "step04B2A_pb_cerussite_validation"
                 / "resultados_step04B2A" / "relax"
                 / "PbCO3_relaxed_production.traj")
UO2_STRUCTURE = (PROJECT_ROOT / "step04B_compound_screening"
                 / "estruturas" / "UO2_fluorite_exp.traj")

MATRIX_DIR = (PROJECT_ROOT / "step03_paw_pbesol_benchmark"
              / "paw_generated" / "PBEsol")
PB_DIR = (PROJECT_ROOT / "step04_u_pb_paw_validation"
          / "paw_generated" / "Pb" / "PBEsol")
U_DIR = (PROJECT_ROOT / "step04_u_pb_paw_validation"
         / "paw_candidates" / "U_R5_pseudization"
         / "U14_nc6" / "PBEsol")

RESULTS = SCRIPT_DIR / "resultados_step04B2B"
LOGS = SCRIPT_DIR / "logs"
GPW = RESULTS / "gpw"

PB_ECUT = 1600.0
PB_KPTS = (4, 3, 4)

U_ECUT = 1600.0
U_KPTS = (3, 3, 3)
U_UEFF = 3.0
U_A = 5.4706
U_SIGNS = (1.0, -1.0, 1.0, -1.0)
U_M0 = 2.0
U_NBANDS = 80

SMEAR = 0.05

MAX_SCALE0_GAP_DIFF = 0.05
SIGNIFICANT_GAP_SHIFT = 0.10
SIGNIFICANT_U_ANISO_MEV_FU = 1.0

PB_FU = 4
U_FU = 4
