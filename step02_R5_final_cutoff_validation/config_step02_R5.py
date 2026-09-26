"""Configuração do Step 02-R5."""

from pathlib import Path

STEP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STEP_DIR.parent

R4_DIR = (
    PROJECT_ROOT
    / "step02_R4_structural_convergence"
    / "resultados_R4"
)

R1_REF_DIR = (
    PROJECT_ROOT
    / "step01_R2_final_references"
    / "referencias_finais"
)

SYSTEMS = {
    "calcita": {
        "r4_1400": R4_DIR / "calcita_PBE_1400eV_final.cif",
        "experimental": R1_REF_DIR / "calcita_ref_experimental_primitiva.cif",
    },
    "dolomita": {
        "r4_1400": R4_DIR / "dolomita_PBE_1400eV_final.cif",
        "experimental": R1_REF_DIR / "dolomita_ref_experimental_primitiva.cif",
    },
}

OUT_DIR = STEP_DIR / "resultados_R5"

XC = "PBE"
KGRID = 5
ECUT_REFERENCE_EV = 1400
ECUT_TEST_EV = 1600

FERMI_WIDTH_EV = 0.05

# Refinamento mais rigoroso que no R4.
FMAX_CELL_EV_A = 0.005
MAX_STEPS_CELL = 180

FMAX_ATOMS_EV_A = 0.003
MAX_STEPS_ATOMS = 100

# Mesmos critérios estruturais usados no R4.
MAX_LATTICE_REL_DIFF_PCT = 0.10
MAX_VOLUME_REL_DIFF_PCT = 0.20
MAX_BOND_DIFF_A = 0.005
