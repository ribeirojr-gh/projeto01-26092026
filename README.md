# First-Principles Quantum Simulations of U and Pb Incorporation, Point Defects, and Oxidation Pathways in Carbonate Minerals (Calcite and Dolomite)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DFT Engine: GPAW](https://img.shields.io/badge/DFT-GPAW%2025.7.0-blue.svg)](https://wiki.fysik.dtu.dk/gpaw/)
[![Framework: ASE](https://img.shields.io/badge/Framework-ASE%203.29-green.svg)](https://wiki.fysik.dtu.dk/ase/)
[![Functional: PBEsol](https://img.shields.io/badge/XC-PBEsol-orange.svg)](https://doi.org/10.1103/PhysRevLett.100.136406)
[![Environment: Micromamba](https://img.shields.io/badge/Environment-Micromamba-purple.svg)](https://mamba.readthedocs.io/)

---

## 1. Executive Summary & Scientific Scope

This repository hosts the official computational codebase, simulation protocols, and audit trail for the **U–Pb Carbonate Geochronology Project**, developed in collaboration with **Petrobras** and the **Computational Materials Science Laboratory (LCCMat)**.

### 1.1 Geological and Physical Background
Carbonate minerals—primarily **calcite** ($\mathrm{CaCO_3}$) and **dolomite** ($\mathrm{CaMg(CO_3)_2}$)—are fundamental archives for dating diagenetic, hydrothermal, and depositional events in hydrocarbon reservoirs, particularly within pre-salt carbonate systems. However, reliable interpretation of isotopic $\mathrm{U}$--$\mathrm{Pb}$ dates requires an atomistic understanding of:
1. **Lattice Incorporation & Thermodynamics:** How $\mathrm{U^{4+}}$, $\mathrm{U^{6+}}$, and radiogenic $\mathrm{Pb^{2+}}$ substitute into host cation sites ($\mathrm{Ca^{2+}}$ / $\mathrm{Mg^{2+}}$) and the associated lattice strain.
2. **Coupled Defect Compensation:** Charge balance mechanisms via calcium/magnesium vacancies ($V_{\mathrm{Ca}}''$, $V_{\mathrm{Mg}}''$), interstitial oxide ions ($\mathrm{O}_i''$), and carbonate defect complexes.
3. **Oxidation Cascade:** The ingress and migration of chemical oxidants driving $\mathrm{U^{4+}} \rightarrow \mathrm{U^{6+}}$, leading to uranyl-like ($\mathrm{UO_2^{2+}}$) complexes and potential remobilization or open-system loss of uranium.
4. **Diffusion Kinetics & Closure Temperatures:** High-accuracy migration barriers evaluated via Nudged Elastic Band (NEB) to feed continuum reaction-diffusion models and construct isotopic retention/preservation maps.

---

## 2. Computational Protocol & Theoretical Architecture

All simulations adhere to strict, validated density functional theory (DFT) standards designed for heavy actinide and lead chemistry:

* **Official DFT Engine:** [GPAW](https://wiki.fysik.dtu.dk/gpaw/) (v25.7.0) orchestrated via the [Atomic Simulation Environment (ASE)](https://wiki.fysik.dtu.dk/ase/) (v3.29).
* **Representation:** Plane-Wave (PW) mode with uniform kinetic energy cutoffs:
  * **Production:** $E_{\mathrm{cut}} = 1400\text{ eV}$
  * **Validation Benchmark:** $E_{\mathrm{cut}} = 1600\text{ eV}$
* **Exchange-Correlation:** PBEsol (Perdew et al., 2008), validated for high-accuracy equilibrium lattice constants and bulk moduli in alkaline-earth carbonates.
* **PAW Datasets & Pseudopotential Generation:**
  * **Lead ($\mathrm{Pb}$):** Custom generated semicore PBEsol PAW (`generated_Pb_PBEsol`) benchmarked against reference FCC Pb and cerussite ($\mathrm{PbCO_3}$).
  * **Uranium ($\mathrm{U}$):** Scalar-relativistic PAW `U14_nc6` (14 valence electrons, 6 projectors) maintaining rigorous 5f orbital character.
* **Strong Correlation ($DFT+U$):** Dudarev formulation ($U_{\mathrm{eff}} = 3.0\text{ eV}$) applied to actinide $5f$ manifolds, validated against antiferromagnetic AFM1-k $\mathrm{UO_2}$ and hexavalent $\gamma\text{-}\mathrm{UO_3}$.
* **Supercell Geometry:** Derived from relaxed primitive unit cells using Hermite Normal Form (HNF) decomposition combined with **Minkowski lattice reduction** (`minkowski_reduce`), ensuring maximal inter-defect distances and minimum cell shearing ($d_{\mathrm{min}} \ge 10.0\text{ \AA}$).
* **High-Performance Execution:** 8 MPI ranks with spatial domain decomposition (`parallel={'domain': 8, 'band': 1, 'kpt': 1}`), ScaLAPACK auto-tuning, and strict single-thread OpenMP (`OMP_NUM_THREADS=1`).

---

## 3. Project Workflow & Audit Status

The project is structured into sequential, rigorously gated milestones:

| Step | Milestone | Status | Key Results / Deliverables |
| :---: | :--- | :---: | :--- |
| **00** | Environment Setup & MPI Engine Validation | **Passed** | GPAW 25.7.0, MPI4/8 execution verified; automated environment manager (`scripts/env_manager.sh`). |
| **01** | Reference Structures Curation | **Passed** | Calcite COD 1010928 ($R\bar{3}c$, #167); Dolomite COD 1517796 ($R\bar{3}$, #148). |
| **02** | Plane-Wave & $k$-Point Convergence | **Passed** | PBE/PBEsol baseline; $k=5$ convergence; $E_{\mathrm{cut}} = 1400\text{ eV}$ established. |
| **03** | Host Matrix PAW Benchmarking | **Passed** | High-precision lattice parameters for $\mathrm{Ca}$--$\mathrm{Mg}$--$\mathrm{C}$--$\mathrm{O}$ phases under PBEsol. |
| **04A** | $\mathrm{U}$ and $\mathrm{Pb}$ PAW Dataset Validation | **Passed** | Validation of semicore `generated_Pb_PBEsol` and `U14_nc6` PAWs against elemental reference states. |
| **04B** | Reference Compounds & SOC Benchmark | **Passed** | $\mathrm{UO_2}$ AFM1-k ($a_0 \approx 5.466\text{ \AA}$, $B_0 \approx 207\text{ GPa}$); $\mathrm{PbCO_3}$ cerussite; $\gamma\text{-}\mathrm{UO_3}$ relaxation ($E_{\mathrm{error}} < 1\%$); SOC force-theorem band splittings. |
| **05A** | Pristine Supercell Generation | **Passed** | Minkowski-reduced supercells of 80, 160, and 240 atoms for both calcite ($d_{\mathrm{min}} = 10.0\text{--}15.3\text{ \AA}$) and dolomite ($d_{\mathrm{min}} = 9.6\text{--}14.6\text{ \AA}$). |
| **05B** | $\mathrm{Pb_{Ca}}$ Finite-Size Convergence Gate | **In Progress (R3)** | Gamma-calibrated against dense $16\text{ \AA}$ mesh; 80-atom baseline validated; cluster protocol established for $\ge 160$ atoms under memory ceiling. |
| **05C** | $\mathrm{U}$ Defect Motifs & Charge Compensation | **Upcoming** | Cation vacancy complexes ($V_{\mathrm{Ca}}''$, $V_{\mathrm{Mg}}''$), interstitial oxygens ($\mathrm{O}_i''$), and uranyl moiety stability. |
| **06** | Advanced Electronic Structure & PDOS | **Roadmap** | Bader charge analysis, projected density of states, and $5f$ hybridization. |
| **07** | Defect Migration & NEB Activation Energies | **Roadmap** | Minimum Energy Pathways (MEP) and activation barriers for $\mathrm{U}$ and $\mathrm{Pb}$ diffusion. |
| **08** | Reaction-Diffusion & Retention Mapping | **Roadmap** | Finite-element kinetic models and geochronological closure temperature maps. |

---

## 4. Repository Layout

```text
.
├── scripts/
│   └── env_manager.sh                 <- Environment isolation & activation orchestrator
├── step00_environment/                <- Initial build scripts, GPAW tests, and dependencies
├── step01_structures/                 <- Curation and standardized POSCAR/CIF structures
├── step02_pristine_benchmark/         <- Cutoff and k-point convergence benchmarks
├── step03_paw_pbesol_benchmark/       <- Matrix constituent validation (Ca-Mg-C-O)
├── step04_u_pb_paw_validation/        <- Semicore PAW generation for heavy elements
├── step04B_compound_screening/        <- Reference compounds: UO2, PbCO3, and UO3
├── step04B1B2_uo2_eos/                <- Equation of state and stress-tensor validation for UO2
├── step04B2A_pb_cerussite_validation/ <- Cerussite structural and electronic validation
├── step04B2B_soc_sensitivity/         <- Spin-orbit coupling force-theorem diagnostics
├── step04B2C1_uvi_gamma_uo3_screen/   <- Hexavalent U(VI) gamma-UO3 initial screen
├── step04B2C2_uvi_gamma_uo3_relax/    <- Structural reanalysis and production relaxations of UO3
├── step05A_host_supercells/           <- Minkowski-reduced 80, 160, 240 atom host cells
├── step05B_pbca_size_gate/            <- Finite-size scaling and substitution gate for Pb_Ca
├── packages/                          <- Documented archival patches and revision bundles
├── chat_completo_projeto_datacao_UPb_Petrobras.md <- Full project trajectory & audit baseline
└── README.md                          <- This primary scientific overview
```

---

## 5. Scientific Validation Data Summary

### 5.1 Host Minerals (Relaxed Primitive Cells, PBEsol, 1400 eV, $k=5\times 5\times 5$)
* **Calcite ($\mathrm{CaCO_3}$):** $V_0 = 122.18\text{ \AA}^3$, $f_{\mathrm{max}} = 0.0052\text{ eV/\AA}$, $\sigma_{\mathrm{res}} = 0.029\text{ GPa}$.
* **Dolomite ($\mathrm{CaMg(CO_3)_2}$):** $V_0 = 106.98\text{ \AA}^3$, $f_{\mathrm{max}} = 0.0065\text{ eV/\AA}$, $\sigma_{\mathrm{res}} = 0.208\text{ GPa}$.

### 5.2 Actinide Reference Validation ($\mathrm{UO_2}$ and $\gamma\text{-}\mathrm{UO_3}$)
* **$\mathrm{UO_2}$ (AFM1-k, $U_{\mathrm{eff}} = 3.0\text{ eV}$):** $a_0 = 5.466\text{ \AA}$, bulk modulus $B_0 \approx 207\text{--}211\text{ GPa}$.
* **$\gamma\text{-}\mathrm{UO_3}$ ($U(\mathrm{VI})$, $Fddd$):** Minimal $\mathrm{U}$--$\mathrm{O}$ distance $1.793\text{ \AA}$; magnetic moment collapses to $< 2\times 10^{-5}\ \mu_{\mathrm{B}}$ confirming clean $5f^0$ hexavalent state; scalar band gap $2.69\text{ eV}$ ($\Delta_{\mathrm{SOC}} \approx -0.85\text{ eV}$).

### 5.3 $\mathrm{Pb}_{\mathrm{Ca}}$ Substitution Baseline (Calcite 80-atom, 1400 eV)
* Average first-coordination bond distance: $\langle \mathrm{Pb}\text{--}\mathrm{O} \rangle_6 = 2.5050\text{ \AA}$.
* Residual force maximum: $f_{\mathrm{max}} = 0.0224\text{ eV/\AA}$.
* Raw substitution energy proxy: $\Delta E_{\mathrm{raw}} = E(\mathrm{Pb}_{\mathrm{Ca}}) - E(\mathrm{host}) = 2.7266\text{ eV}$.
* Lattice relaxation energy: $\Delta E_{\mathrm{relax}} = -0.5582\text{ eV}$.

---

## 6. Reproducibility & Execution Guide

### 6.1 Environment Bootstrap
The project strictly employs **micromamba** to maintain reproducible C-library bindings (`libxc 7.0`, `ELPA`, `FFTW`, `ScaLAPACK`):

```bash
# Verify environment isolation via project manager
bash scripts/env_manager.sh gpaw python -c "import gpaw; print(gpaw.__version__)"
```

### 6.2 Running Milestones
Each milestone directory includes a dedicated driver script following the convention `run-stepXX.sh`. Output streams are piped and recorded via `|& tee`:

```bash
# Example: Executing Step 05B Finite-Size Gate
cd step05B_pbca_size_gate
bash run-step05B.sh
```

---

## 7. Citation & Attribution

If using methods, structures, or results from this repository, please cite:
1. **GPAW:** J. Enkovaara et al., *Electronic structure calculations with GPAW: a Python-based open-source grid-based code*, J. Phys.: Condens. Matter **22**, 253202 (2010).
2. **ASE:** A. H. Larsen et al., *The Atomic Simulation Environment—a Python library for working with atoms*, J. Phys.: Condens. Matter **29**, 273002 (2017).
3. **PBEsol:** J. P. Perdew et al., *Restoring the Density-Gradient Expansion for Exchange in Solids and Surfaces*, Phys. Rev. Lett. **100**, 136406 (2008).
4. **Petrobras / LCCMat Collaboration:** *U–Pb Carbonate Geochronology Project Technical Reports* (2026).
