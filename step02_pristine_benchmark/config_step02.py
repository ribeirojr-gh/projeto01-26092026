"""Configuração central da Etapa 02."""

from pathlib import Path

STEP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STEP_DIR.parent

STEP01_R2 = PROJECT_ROOT / "step01_R2_final_references"
REF_DIR = STEP01_R2 / "referencias_finais"

SYSTEMS = {
    "calcita": REF_DIR / "calcita_ref_experimental_primitiva.cif",
    "dolomita": REF_DIR / "dolomita_ref_experimental_primitiva.cif",
}

MLIP_DIR = STEP_DIR / "resultados_mlip"
GPAW_DIR = STEP_DIR / "resultados_gpaw"
SUMMARY_DIR = STEP_DIR / "resumo_step02"
INPUT_SNAPSHOT = STEP_DIR / "inputs_step02"

# Relaxação MLIP
FMAX_MLIP = 0.02  # eV/Å
MAX_STEPS_MLIP = 500

# MACE: explicitamente fixado para reprodutibilidade.
MACE_MODEL = "medium-mpa-0"
MACE_DTYPE = "float64"
MACE_DEVICE = "cuda"

# GPAW: convergência numérica preliminar para sólidos.
XC_CONVERGENCE = "PBEsol"
ECUT_VALUES_EV = [400, 500, 600, 700]
ECUT_KGRID = 5
KGRID_VALUES = [3, 4, 5, 6, 7]
KGRID_ECUT_EV = 600

# Critérios usados apenas para RECOMENDAÇÃO automática.
# A decisão final deve ser revisada após a execução.
ENERGY_TOL_MEV_ATOM = 1.0
STRESS_TOL_GPA = 0.05

FERMI_WIDTH_EV = 0.05
