# HPC Cluster Execution & SLURM Deployment Guide

## 1. Context & Scientific Justification
Calculations on 160-atom and 240-atom supercells with a strict plane-wave kinetic energy cutoff of $E_{\mathrm{cut}} = 1400\text{ eV}$ require substantial memory ($>30\text{ GiB}$) due to the large number of Fourier components and dense grid dimensions. To preserve the scientific integrity of the results, the cutoff must **not** be reduced arbitrarily. Instead, supercells $\ge 160$ atoms are scheduled for execution on high-performance computing (HPC) cluster nodes equipped with $\ge 64\text{--}128\text{ GiB}$ of RAM.

## 2. Standard SLURM Job Script Template

```bash
#!/usr/bin/env bash
#SBATCH --job-name=upb_step05B_160
#SBATCH --nodes=1
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --partition=standard
#SBATCH --output=slurm-%x-%j.out
#SBATCH --error=slurm-%x-%j.err

set -euo pipefail

# 1. Environment initialization
module purge
module load openmpi/4.1.5 libxc/7.0.0 fftw/3.3.10 scalapack/2.2.0

# Activate project environment
source "${HOME}/SIMULACOES/petrobras/datacao/petrobras_upb_project/scripts/env_manager.sh"

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# 2. Execution Directory
cd "${HOME}/SIMULACOES/petrobras/datacao/petrobras_upb_project/step05B_pbca_size_gate"

# 3. Launch with domain parallelization
srun --mpi=pmix -n 16 gpaw python 05B_R3_pbca_case.py |& tee saida-cluster-160.txt
```

## 3. Parallelization Matrix & Resource Allocation

| System Size | Recommended Hardware | MPI Tasks | Memory Allocation | Estimated Walltime |
| :---: | :---: | :---: | :---: | :---: |
| **80 atoms** | Workstation (Local) | 4 | $\approx 16\text{ GiB}$ | 2--4 hours |
| **160 atoms** | Cluster (1 Node) | 16 | $\ge 64\text{ GiB}$ | 6--12 hours |
| **240 atoms** | Cluster (1--2 Nodes) | 16--32 | $\ge 128\text{ GiB}$ | 12--24 hours |
