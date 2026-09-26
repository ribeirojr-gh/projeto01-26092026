# Comprehensive Audit Trail & Milestone Verification

## Milestone Verification Matrix

| Step | Milestone Identifier | Implementation Status | Scientific Evaluation | Key Output Artefacts |
| :--- | :--- | :---: | :--- | :--- |
| **00** | Environment & Engine Setup | **PASSED** | GPAW 25.7.0, Python 3.11, ASE 3.29, Libxc 7.0; automated environment wrapper operational. | `step00_environment/`, `scripts/env_manager.sh` |
| **01** | Reference Structures | **PASSED** | Calcite COD 1010928 ($R\bar{3}c$ #167); Dolomite COD 1517796 ($R\bar{3}$ #148); COD 1517797 rejected. | `step01_structures/` |
| **02** | Convergence & MLIP Testing | **PASSED** | MLIP pristino lacked sufficient accuracy for defect substitution; DFT baseline fixed at $E_{\mathrm{cut}} = 1400\text{ eV}$, $k=5$. | `step02_pristine_benchmark/` |
| **03** | Host Matrix PAW Benchmark | **PASSED** | PBEsol functional selected; verified $\mathrm{Ca}$--$\mathrm{Mg}$--$\mathrm{C}$--$\mathrm{O}$ bonding and elastic properties. | `step03_paw_pbesol_benchmark/` |
| **04A** | Semicore U and Pb PAWs | **PASSED** | Custom semicore Pb validated against FCC Pb; `U14_nc6` selected as primary scalar-relativistic actinide dataset. | `step04_u_pb_paw_validation/` |
| **04B1** | $\mathrm{UO_2}$ Electronic & EOS Validation | **PASSED** | AFM1-k, $U_{\mathrm{eff}} = 3.0\text{ eV}$; $a_0 \approx 5.466\text{ \AA}$; bulk modulus $B_0 \approx 207\text{--}211\text{ GPa}$; stress-strain gate passed. | `step04B1B2_uo2_eos/` |
| **04B2A** | $\mathrm{PbCO_3}$ Cerussite Validation | **PASSED** | Orthorhombic cerussite structural relaxation passed ($1400\text{ eV}$, $k=3\times 2\times 3$). | `step04B2A_pb_cerussite_validation/` |
| **04B2B** | Spin-Orbit Coupling (SOC) Benchmark | **PASSED** | Scalar vs SOC band gap shifts: $\Delta E_{\mathrm{gap}}^{\mathrm{SOC}} = -0.243\text{ eV}$ ($\mathrm{PbCO_3}$), $-0.235\text{ eV}$ ($\mathrm{UO_2}$); force-theorem recognized as non-self-consistent. | `step04B2B_soc_sensitivity/` |
| **04B2C** | $\gamma\text{-}\mathrm{UO_3}$ Hexavalent Relaxation | **PASSED** | $Fddd$ primitive cell; minimal $\mathrm{U}$--$\mathrm{O} \approx 1.793\text{ \AA}$; clean $5f^0$ hexavalent state; structural error $< 1\%$; production authorized. | `step04B2C2_uvi_gamma_uo3_relax/` |
| **05A** | Host Supercells & Minkowski Reduction | **PASSED** | Minkowski-reduced cells for Calcite and Dolomite (80, 160, 240 atoms) generated with minimal shear strain and $d_{\mathrm{min}} \ge 9.6\text{--}15.3\text{ \AA}$. | `step05A_host_supercells/resultados_step05A/supercells_R1/` |
| **05B-R1** | $\mathrm{Pb_{Ca}}$ Size Gate (R1) | **PARTIAL** | Calcite 80-atom cell converged ($\langle\mathrm{Pb-O}\rangle_6 = 2.505\text{ \AA}$, $\Delta E_{\mathrm{sub}} = 2.727\text{ eV}$, $\Delta E_{\mathrm{relax}} = -0.558\text{ eV}$); 160 atoms suffered OOM termination. | `step05B_pbca_size_gate/resultados_step05B_R1/` |
| **05B-R2** | $\Gamma$-Only Calibrated Strategy | **PARTIAL** | Memory diagnostics implemented; identified system memory ceiling under dense mesh; OOM kill verified by kernel dmesg. | `step05B_pbca_size_gate/diagnostico_memoria_R2/` |
| **05B-R3** | 8 MPI Domain Decomposition Gate | **IN PROGRESS** | Full ionic relaxation in $\Gamma$-point passed for Calcite 80 ($f_{\mathrm{max}} = 0.0212\text{ eV/\AA}$); dense calibration on local 8 MPI reached RAM limit. Cluster migration protocol established for large cells. | `step05B_pbca_size_gate/resultados_step05B_R3/` |

---

## Technical Gate Criteria in Effect (Step 05B)

1. **$\Gamma$-to-Dense Convergence Gate (80-atom baseline):**
   $$|\Delta E_{\mathrm{raw}}^{\Gamma} - \Delta E_{\mathrm{raw}}^{\mathrm{dense}}| \le 0.10\text{ eV}$$
2. **Finite-Size Substitution Gate:**
   $$|\Delta\Delta E_{\mathrm{raw}}| = |\Delta E_{\mathrm{raw}}(N) - \Delta E_{\mathrm{raw}}(N')| \le 0.10\text{ eV}$$
3. **Lattice Relaxation Stability Gate:**
   $$|\Delta E_{\mathrm{relax}}| \le 0.10\text{ eV}$$
4. **Local Coordination Shell Preservation:**
   $$|\Delta \langle \mathrm{Pb}\text{--}\mathrm{O} \rangle_6| \le 0.05\text{ \AA}$$

*Important Methodological Distinction:* The quantity $\Delta E_{\mathrm{raw}} = E(\mathrm{Pb}_{\mathrm{Ca}}) - E(\mathrm{host})$ is strictly utilized as a **finite-size convergence proxy** and is **not** a defect formation energy, which requires chemical potential boundary conditions.
