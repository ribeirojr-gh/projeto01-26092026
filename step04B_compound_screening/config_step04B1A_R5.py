from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
STRUCTURE = SCRIPT_DIR / "estruturas" / "UO2_fluorite_exp.traj"

MATRIX_DIR = (PROJECT_ROOT / "step03_paw_pbesol_benchmark"
              / "paw_generated" / "PBEsol")
STEP04A = PROJECT_ROOT / "step04_u_pb_paw_validation"
U_DIRS = {
    "poly6": STEP04A / "paw_generated" / "U" / "PBEsol",
    "nc6": (STEP04A / "paw_candidates" / "U_R5_pseudization"
            / "U14_nc6" / "PBEsol"),
}

RESULTS = SCRIPT_DIR / "resultados_step04B1A_R5"
LOGS = SCRIPT_DIR / "logs" / "R5"
GPW = RESULTS / "gpw"

ECUT = 1400.0
KPTS = (3, 3, 3)
NBANDS = 80
UEFF_GRID = (0.0, 2.0, 3.0, 4.0, 5.0)

GAP_MIN = 2.0
GAP_MAX = 2.5
MOMENT_TARGET = 1.74
