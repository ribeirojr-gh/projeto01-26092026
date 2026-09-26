#!/usr/bin/env bash
set -u
set -o pipefail

# ================================================================
# Step05B - diagnóstico de memória GPAW v2
# - não executa SCF real
# - força txt='-' para que o dry-run imprima RAM/paralelização
# - compara 4 vs 8 processos e 3 decomposições MPI
# ================================================================

PROJECT_ROOT="$(pwd)"
STEP_DIR="${PROJECT_ROOT}/step05B_pbca_size_gate"
OUTDIR="${STEP_DIR}/diagnostico_memoria_R3"
ENV_MANAGER="${PROJECT_ROOT}/scripts/env_manager.sh"
PROBE="${OUTDIR}/05B_memory_probe.py"
MASTER="${OUTDIR}/saida-step05B-memory-diagnostic-R3.txt"
SUMMARY="${OUTDIR}/resumo-step05B-memory-diagnostic-R3.txt"

mkdir -p "${OUTDIR}"

if [[ ! -f "${ENV_MANAGER}" ]]; then
    echo "ERRO: não encontrei ${ENV_MANAGER}"
    exit 10
fi

source "${ENV_MANAGER}"

cat > "${PROBE}" <<'PY'
from pathlib import Path
import os
import numpy as np
from ase.io import read
from gpaw import GPAW, PW, setup_paths
from gpaw.mpi import world

root = Path.cwd()
step05a = root / "step05A_host_supercells"
structure = (
    step05a / "resultados_step05A" / "supercells_R1"
    / "calcita_det8_80atoms_R1.traj"
)
host_paw = (
    root / "step03_paw_pbesol_benchmark"
    / "paw_generated" / "PBEsol"
)
pb_paw = (
    root / "step04_u_pb_paw_validation"
    / "paw_generated" / "Pb" / "PBEsol"
)

for p in [
    structure,
    host_paw / "Ca.PBEsol",
    host_paw / "C.PBEsol",
    host_paw / "O.PBEsol",
    pb_paw / "Pb.PBEsol",
]:
    if not p.exists():
        raise FileNotFoundError(p)

setup_paths.insert(0, str(host_paw.resolve()))
setup_paths.insert(0, str(pb_paw.resolve()))

atoms = read(structure)

# Worst-case probe: replace central Ca by Pb.
scaled = atoms.get_scaled_positions(wrap=True)
cell = np.asarray(atoms.cell)
ca = [i for i, s in enumerate(atoms.get_chemical_symbols()) if s == "Ca"]
scores = []
for i in ca:
    ds = scaled[i] - 0.5
    ds -= np.round(ds)
    scores.append((float(np.linalg.norm(ds @ cell)), i))
scores.sort()
atoms[scores[0][1]].symbol = "Pb"

mode = os.environ["UPB_PARALLEL_MODE"].strip()
if mode == "auto":
    parallel = {"sl_auto": True}
elif mode == "domain":
    parallel = {
        "domain": world.size,
        "band": 1,
        "kpt": 1,
        "sl_auto": True,
    }
elif mode == "hybrid":
    if world.size % 2:
        raise RuntimeError("hybrid requer número par de processos")
    parallel = {
        "domain": world.size // 2,
        "band": 2,
        "kpt": 1,
        "sl_auto": True,
    }
else:
    raise ValueError(mode)

print("=" * 72)
print(f"PROBE calcita 80 / Pb_Ca / Gamma / mode={mode}")
print(f"fake/world size = {world.size}")
print(f"parallel = {parallel}")
print("=" * 72)

calc = GPAW(
    mode=PW(1400.0, dedecut="estimate"),
    xc="PBEsol",
    kpts={"size": (1, 1, 1), "gamma": True},
    nbands=-8,
    occupations={"name": "fermi-dirac", "width": 0.05},
    random=False,
    parallel=parallel,
    convergence={
        "energy": 1.0e-3,
        "density": 1.0e-5,
        "eigenstates": 1.0e-7,
        "bands": "occupied",
    },
    eigensolver={"name": "dav", "niter": 4},
    txt="-",
)
atoms.calc = calc

# Em --dry-run=N o GPAW inicializa, imprime paralelização + memória e sai.
atoms.get_potential_energy()
PY

{
    echo "======================================================================"
    echo "STEP 05B - DIAGNÓSTICO DE MEMÓRIA GPAW R3"
    echo "======================================================================"
    echo "Data: $(date)"
    echo "Host: $(hostname)"
    echo "Projeto: ${PROJECT_ROOT}"
    echo

    echo ">>> MEMÓRIA DO SISTEMA"
    free -h || true
    echo

    echo ">>> CGROUP"
    for f in memory.max memory.current memory.events; do
        p="/sys/fs/cgroup/${f}"
        if [[ -r "${p}" ]]; then
            echo "--- ${p}"
            cat "${p}"
        fi
    done
    echo

    echo ">>> EVENTOS OOM DO KERNEL (se acessíveis)"
    journalctl -k -b --no-pager 2>/dev/null \
      | grep -Ei 'oom|out of memory|killed process|memory cgroup' \
      | tail -80 || true
    echo
} |& tee "${MASTER}"

run_probe() {
    local n="$1"
    local mode="$2"
    local out="${OUTDIR}/dryrun-${n}MPI-${mode}.txt"

    echo ">>> DRY-RUN: N=${n}, mode=${mode}" |& tee -a "${MASTER}"

    set +e
    UPB_PARALLEL_MODE="${mode}" \
      run_in_upb_env gpaw \
      gpaw python --dry-run="${n}" "${PROBE}" \
      |& tee "${out}"
    local status=${PIPESTATUS[0]}
    set -e

    echo "[STATUS] N=${n} mode=${mode}: ${status}" |& tee -a "${MASTER}"
    echo |& tee -a "${MASTER}"
}

for n in 4 8; do
    for mode in auto domain hybrid; do
        run_probe "${n}" "${mode}"
    done
done

{
    echo "======================================================================"
    echo "RESUMO EXTRAÍDO"
    echo "======================================================================"

    for n in 4 8; do
        for mode in auto domain hybrid; do
            f="${OUTDIR}/dryrun-${n}MPI-${mode}.txt"
            echo
            echo "### ${n} MPI / ${mode}"
            grep -iE -A15 -B4 \
              'RAM Memory estimate|Parallelization|domain|band|k-point|kpoint|ScaLAPACK' \
              "${f}" || true
        done
    done
} | tee "${SUMMARY}"

echo
echo "Arquivos principais:"
echo "  ${MASTER}"
echo "  ${SUMMARY}"
echo "  ${OUTDIR}/dryrun-4MPI-auto.txt"
echo "  ${OUTDIR}/dryrun-4MPI-domain.txt"
echo "  ${OUTDIR}/dryrun-4MPI-hybrid.txt"
echo "  ${OUTDIR}/dryrun-8MPI-auto.txt"
echo "  ${OUTDIR}/dryrun-8MPI-domain.txt"
echo "  ${OUTDIR}/dryrun-8MPI-hybrid.txt"
echo
echo "Nenhum SCF real foi executado."
