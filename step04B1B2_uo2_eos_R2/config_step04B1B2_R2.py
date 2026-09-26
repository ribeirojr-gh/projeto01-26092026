#!/usr/bin/env python3
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

STRUCTURE = (
    PROJECT_ROOT
    / "step04B_compound_screening"
    / "estruturas"
    / "UO2_fluorite_exp.traj"
)

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

B1B1_RESULTS = (
    PROJECT_ROOT
    / "step04B1B_uo2_reproducibility"
    / "resultados_step04B1B1"
)

B1B1_CENTER = {
    3.0: B1B1_RESULTS / "UO2_nc6_U3p0_ky.json",
    4.0: B1B1_RESULTS / "UO2_nc6_U4p0_ky.json",
}

RESULTS = SCRIPT_DIR / "resultados_step04B1B2_R2"
LOGS = SCRIPT_DIR / "logs"
RESTARTS = RESULTS / "restart"

A_REF = 5.4706
A_EXP = 5.47127

SCALES = (0.98, 0.99, 1.00, 1.01, 1.02)
UEFFS = (3.0, 4.0)

ECUT_EOS = 1400.0
ECUT_LADDER = (1400.0, 1600.0, 1800.0)

KPTS = (3, 3, 3)
NBANDS = 80

AFM_DOMAIN = "ky"
AFM_SIGNS = (1.0, -1.0, 1.0, -1.0)
INITIAL_U_MOMENT = 2.0

# Gates do EOS / consistência de ramo.
MAX_EOS_RMSE_MEV_ATOM = 2.0
MAX_LATTICE_ERROR_PERCENT = 1.0
B0_MIN_GPA = 175.0
B0_MAX_GPA = 240.0

# Comparação do centro determinístico com o estado B1B1 já aprovado.
MAX_CENTER_BRANCH_DE_MEV_ATOM = 2.0
MAX_CENTER_BRANCH_DGAP_EV = 0.10
MAX_CENTER_BRANCH_DMOMENT_MUB = 0.05

# Cutoff: não relaxamos o gate retrospectivamente.
# Em vez disso, procuramos o primeiro degrau N cuja diferença para N+200
# satisfaça todos os critérios. Se 1600->1800 passar, produção U passa a
# usar 1600 eV, com 1800 eV como validação.
MAX_CUTOFF_DE_MEV_ATOM = 5.0
MAX_CUTOFF_DGAP_EV = 0.05
MAX_CUTOFF_DMOMENT_MUB = 0.02
MAX_CUTOFF_DPRESSURE_GPA = 0.10
