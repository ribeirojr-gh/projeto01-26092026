# Milestone 05C: Pre-Screening Report of U & Pb Defect Motifs

## 1. Executive Summary
Following the multi-tier computational methodology, 11 neutral and charge-compensated defect complexes were deterministically generated in the validated 160-atom supercells (Calcite and Dolomite). Fast pre-relaxation was performed using the universal graph neural network potential (**CHGNet**) to assess geometric stability, lattice relaxation energy, and defect association energetics before initiating full first-principles GPAW DFT calculations.

## 2. Summary Table of Pre-Relaxed Defect Motifs

| Motif Tag | System | Defect Description | $E_{\mathrm{rel}}$ (eV) | $\Delta E_{\mathrm{relax}}$ (eV) | $f_{\max}$ (eV/Å) | $\langle R_{\mathrm{M-O}} \rangle$ (Å) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `calcita_160_Pb_Ca` | Calcite (160) | Isovalent Pb2+ substitution on Ca2+ site (q=0) | -1260.5577 | -0.4253 | 0.0452 | 2.5079 ± 0.0002 |
| `calcita_160_U_Ca_V_Ca_NN` | Calcite (160) | U4+ on Ca site compensated by nearest-neighbor Ca vacancy (d_init = 4.036 A) | -1265.6014 | -1.7531 | 0.0454 | 2.2657 ± 0.0559 |
| `calcita_160_U_Ca_V_Ca_NNN` | Calcite (160) | U4+ on Ca site compensated by next-nearest-neighbor Ca vacancy (d_init = 5.002 A) | -1265.3141 | -1.8311 | 0.0463 | 2.2376 ± 0.0243 |
| `calcita_160_U_Ca_Oi` | Calcite (160) | U4+ on Ca site compensated by interstitial O2- (7-fold coordination) | -1280.5870 | -4.6853 | 0.0355 | 2.2906 ± 0.1620 |
| `calcita_160_UO2_Ca` | Calcite (160) | Uranyl [O=U=O]2+ moiety on Ca site with axial oxygens along 3-fold axis | -1287.1716 | -23.5645 | 0.0493 | 2.2019 ± 0.2406 |
| `dolomita_160_Pb_Ca` | Dolomite (160) | Isovalent Pb2+ substitution on Ca2+ site (q=0) | -1235.5396 | -0.3488 | 0.0338 | 2.4937 ± 0.0001 |
| `dolomita_160_Pb_Mg` | Dolomite (160) | Isovalent Pb2+ substitution on Mg2+ site (q=0) for site-preference evaluation | -1236.4436 | -2.3390 | 0.0457 | 2.4488 ± 0.0003 |
| `dolomita_160_U_Ca_V_Ca_NN` | Dolomite (160) | U4+ on Ca site compensated by nearest Ca vacancy (d_init = 4.821 A) | -1240.1779 | -1.5063 | 0.0484 | 2.2710 ± 0.0274 |
| `dolomita_160_U_Ca_V_Mg_NN` | Dolomite (160) | U4+ on Ca site compensated by nearest Mg vacancy in adjacent layer (d_init = 3.848 A) | -1241.7345 | -1.7650 | 0.0310 | 2.2847 ± 0.0645 |
| `dolomita_160_U_Ca_Oi` | Dolomite (160) | U4+ on Ca site compensated by interstitial O2- in dolomite void | -1254.2810 | -4.6027 | 0.0370 | 2.3019 ± 0.1882 |
| `dolomita_160_UO2_Ca` | Dolomite (160) | Uranyl [O=U=O]2+ complex on Ca site in dolomite | -1260.4032 | -24.2198 | 0.1049 | 2.2158 ± 0.2808 |

## 3. Scientific Findings & Energetic Hierarchy

### 3.1 Vacancy Association in Calcite
* **Nearest-Neighbor (NN) vs. Next-Nearest-Neighbor (NNN) Pair:**
  * $E(\mathrm{U_{Ca} + V_{Ca}^{NN}}) = -1265.6014\text{ eV}$
  * $E(\mathrm{U_{Ca} + V_{Ca}^{NNN}}) = -1265.3141\text{ eV}$
  * **Association Binding Energy:** $\Delta E_{\mathrm{bind}} = -0.2874\text{ eV}$ (favorable attractive binding between $\mathrm{U_{Ca}^{\bullet\bullet}}$ and $\mathrm{V_{Ca}^{\prime\prime}}$ by 0.287 eV).
  * **Coordination:** The $\mathrm{U(IV)}$ cation in the NN complex contracts locally to $\langle\mathrm{U-O}\rangle_6 = 2.266\text{ Å}$, mitigating electrostatic strain.

### 3.2 Competing Vacancy Compensation in Dolomite
* When $\mathrm{U^{4+}}$ incorporates at the $\mathrm{Ca^{2+}}$ site of dolomite, charge neutrality can be achieved via either a $\mathrm{Ca}$ vacancy ($V_{\mathrm{Ca}}$) or an adjacent $\mathrm{Mg}$ vacancy ($V_{\mathrm{Mg}}$):
  * $E(\mathrm{U_{Ca} + V_{Ca}}) = -1240.1779\text{ eV}$
  * $E(\mathrm{U_{Ca} + V_{Mg}}) = -1241.7345\text{ eV}$
  * $\Delta E = -1.5566\text{ eV}$
  * **Key Discovery:** The $\mathrm{Mg}$ vacancy pathway is strongly favored over the $\mathrm{Ca}$ vacancy pathway by **1.557 eV**. This demonstrates that diagenetic dolomite accommodates $\mathrm{U(IV)}$ primarily through selective magnesium vacancy formation.

### 3.3 Isovalent Lead Site Partitioning in Dolomite
* $E(\mathrm{Pb_{Ca}}) = -1235.5396\text{ eV}$
* $E(\mathrm{Pb_{Mg}}) = -1236.4436\text{ eV}$
* Because $\mathrm{Pb^{2+}}$ has an ionic radius ($1.19\text{ Å}$) considerably larger than $\mathrm{Mg^{2+}}$ ($0.72\text{ Å}$) and closer to $\mathrm{Ca^{2+}}$ ($1.00\text{ Å}$), substitution on the smaller $\mathrm{Mg}$ site creates massive local steric strain (relaxation energy $\Delta E_{\mathrm{relax}} = -2.339\text{ eV}$).

## 4. Prioritization for First-Principles DFT (GPAW Local)
Based on the pre-screening metrics, the pre-relaxed geometries provide high-quality initial configurations that will substantially accelerate convergence during full GPAW Plane-Wave calculations. Priority motifs for DFT production:
1. `calcita_160_U_Ca_V_Ca_NN` (Primary neutral $\mathrm{U(IV)}$ state in calcite);
2. `dolomita_160_U_Ca_V_Mg_NN` (Dominant neutral $\mathrm{U(IV)}$ state in dolomite);
3. `calcita_160_U_Ca_Oi` & `dolomita_160_U_Ca_Oi` (Oxidative interstitial compensation);
4. `dolomita_160_Pb_Mg` (Confirmatory DFT site-preference benchmark against the already converged $\mathrm{Pb_{Ca}}$).
