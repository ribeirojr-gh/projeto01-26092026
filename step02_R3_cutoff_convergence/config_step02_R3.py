"""Configuração do Step 02-R3."""

from pathlib import Path

STEP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STEP_DIR.parent

REF_DIR = (
    PROJECT_ROOT
    / "step01_R2_final_references"
    / "referencias_finais"
)

SYSTEMS = {
    "calcita": REF_DIR / "calcita_ref_experimental_primitiva.cif",
    "dolomita": REF_DIR / "dolomita_ref_experimental_primitiva.cif",
}

OUT_DIR = STEP_DIR / "resultados_R3"

XC = "PBE"
KGRID = 5

# Começamos novamente em 600 eV porque a correção de Pulay aplicada ao
# stress exige recalcular o tensor de stress. A energia pode ser comparada
# diretamente com a série anterior.
ECUT_VALUES_EV = [600, 700, 800, 900, 1000, 1200, 1400, 1600]

FERMI_WIDTH_EV = 0.05

# Critérios mantidos do Step 02 anterior.
ENERGY_TOL_MEV_ATOM = 1.0
STRESS_TOL_GPA = 0.05

# Exigimos dois intervalos consecutivos que satisfaçam simultaneamente
# energia e stress antes de declarar convergência.
REQUIRED_CONSECUTIVE_PASSES = 2
