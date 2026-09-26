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
