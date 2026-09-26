"""Configuração central do Step 03."""

from pathlib import Path

STEP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STEP_DIR.parent

REF_DIR = (
    PROJECT_ROOT
    / "step01_R2_final_references"
    / "referencias_finais"
)

R5_DIR = (
    PROJECT_ROOT
    / "step02_R5_final_cutoff_validation"
    / "resultados_R5"
)

SYSTEMS = {
    "calcita": {
        "experimental": REF_DIR / "calcita_ref_experimental_primitiva.cif",
        "pbe_official_1400": R5_DIR / "calcita_PBE_1400eV_R5_final.cif",
    },
    "dolomita": {
        "experimental": REF_DIR / "dolomita_ref_experimental_primitiva.cif",
        "pbe_official_1400": R5_DIR / "dolomita_PBE_1400eV_R5_final.cif",
    },
}

PAW_ROOT = STEP_DIR / "paw_generated"
PAW_PBE = PAW_ROOT / "PBE"
PAW_PBESOL = PAW_ROOT / "PBEsol"
OUT_DIR = STEP_DIR / "resultados_step03"

KGRID = 5
ECUT_MAIN_EV = 1400
ECUT_VALIDATION_EV = 1600

FERMI_WIDTH_EV = 0.05

FMAX_CELL_EV_A = 0.005
FMAX_ATOMS_EV_A = 0.003
MAX_STEPS_CELL = 180
MAX_STEPS_ATOMS = 100

# Critérios herdados do Step 02.
MAX_LATTICE_REL_DIFF_PCT = 0.10
MAX_VOLUME_REL_DIFF_PCT = 0.20
MAX_BOND_DIFF_A = 0.005
