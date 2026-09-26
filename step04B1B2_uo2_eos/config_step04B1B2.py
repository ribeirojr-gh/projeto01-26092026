#!/usr/bin/env python3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

B1B1_DIR = PROJECT_ROOT / "step04B1B_uo2_reproducibility"
UO2_STRUCTURE = (
    B1B1_DIR.parent
    / "step04B_compound_screening"
    / "estruturas"
    / "UO2_fluorite_exp.traj"
)

MATRIX_PBESOL_DIR = (
    PROJECT_ROOT
    / "step03_paw_pbesol_benchmark"
    / "paw_generated"
    / "PBEsol"
)

U_NC6_PBESOL_DIR = (
    PROJECT_ROOT
    / "step04_u_pb_paw_validation"
    / "paw_candidates"
    / "U_R5_pseudization"
    / "U14_nc6"
    / "PBEsol"
)

B1B1_RESULTS = (
    B1B1_DIR / "resultados_step04B1B1"
)

# Resultados centrais já validados no Step04B1B1-R2.
CENTER_JSON = {
    3.0: B1B1_RESULTS / "UO2_nc6_U3p0_ky.json",
    4.0: B1B1_RESULTS / "UO2_nc6_U4p0_ky.json",
}

RESULTS_DIR = SCRIPT_DIR / "resultados_step04B1B2"
LOGS_DIR = SCRIPT_DIR / "logs"
RESTART_DIR = RESULTS_DIR / "restart"

# Mantemos a mesma célula experimental usada nos Steps B1A/B1B1 para
# consistência numérica. A referência experimental de alta precisão usada
# apenas na comparação final é 5.47127 Å a 20 °C.
A_CENTER_A = 5.4706
A_EXP_HIGH_PRECISION_A = 5.47127

# Cinco pontos são suficientes para um primeiro Birch-Murnaghan em torno
# do mínimo e limitam o custo do gate.
LATTICE_SCALE = (0.98, 0.99, 1.00, 1.01, 1.02)

UEFF_GRID_EV = (3.0, 4.0)
AFM_DOMAIN = "ky"
AFM_SIGNS = (1.0, -1.0, 1.0, -1.0)
INITIAL_U_MOMENT_MUB = 2.0

KPTS = (3, 3, 3)
NBANDS = 80
ECUT_EOS_EV = 1400.0
ECUT_VALIDATION_EV = 1600.0

# Referência experimental aproximada de módulo volumétrico em torno de
# 200-210 GPa. Usamos 207 GPa apenas como guia, não como valor ajustado.
B0_EXP_GUIDE_GPA = 207.0

# Gates numéricos 1400 -> 1600 eV.
MAX_CUTOFF_DE_MEV_ATOM = 5.0
MAX_CUTOFF_DGAP_EV = 0.05
MAX_CUTOFF_DMOMENT_MUB = 0.02
MAX_CUTOFF_DSTRESS_GPA = 0.10

# Gate estrutural amplo para shortlist.
MAX_LATTICE_ERROR_PERCENT = 1.0
B0_GUIDE_MIN_GPA = 175.0
B0_GUIDE_MAX_GPA = 240.0
