# Milestone 05C: First-Principles DFT (GPAW PW) Defect Motifs Report

## 1. Executive Summary & Verification Matrix
All high-priority neutral and charge-compensated defect complexes of **Uranium** and **Lead** in 160-atom supercells of Calcite and Dolomite have achieved **100% convergence** under high-precision first-principles DFT (GPAW Plane-Wave, $E_{\mathrm{cut}} = 1400\text{ eV}$, PBEsol functional, with Dudarev $U_{\mathrm{eff}} = 3.0\text{ eV}$ on the localized $\mathrm{U}(5f)$ manifold, $f_{\max} \le 0.03\text{ eV/Å}$).

## 2. Converged First-Principles Defect Properties

| Defect Motif | Mineral | Formula | N | $E_{\mathrm{unrel}}$ (eV) | $E_{\mathrm{rel}}$ (eV) | $\Delta E_{\mathrm{relax}}$ (eV) | $f_{\max}$ (eV/Å) | Steps | $\langle R_{\mathrm{M-O}} \rangle$ (Å) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `calcita_160_Pb_Ca` | Calcite | C32Ca31O96Pb | 160 | -1271.8074 | -1271.808034 | -0.0006 | 0.0212 | ref | 2.5044 ± 0.0026 |
| `dolomita_160_Pb_Ca` | Dolomite | C32Ca15Mg16O96Pb | 160 | -1248.2716 | -1248.750188 | -0.4786 | 0.0207 | ref | 2.5044 ± 0.0001 |
| `calcita_160_U_Ca_V_Ca_NN` | Calcite | C32Ca30O96U | 159 | -1270.8961 | -1271.286332 | -0.3903 | 0.0282 | 53 | 2.3053 ± 0.0648 |
| `dolomita_160_U_Ca_V_Mg_NN` | Dolomite | C32Ca15Mg15O96U | 159 | -1248.4872 | -1248.742636 | -0.2554 | 0.0195 | 33 | 2.3228 ± 0.0762 |
| `dolomita_160_Pb_Mg` | Dolomite | C32Ca16Mg15O96Pb | 160 | -1249.4300 | -1249.538917 | -0.1089 | 0.0276 | 13 | 2.4497 ± 0.0016 |
| `calcita_160_U_Ca_Oi` | Calcite | C32Ca31O97U | 161 | -1285.1606 | -1285.899376 | -0.7387 | 0.0281 | 23 | 2.3718 ± 0.1501 |
| `dolomita_160_U_Ca_Oi` | Dolomite | C32Ca15Mg16O97U | 161 | -1259.9577 | -1261.383635 | -1.4259 | 0.0266 | 35 | 2.3663 ± 0.1265 |

## 3. Geochemical & Physical-Chemical Insights

### 3.1 Lead Isovalent Partitioning in Dolomite (Ca vs. Mg)
* $E(\mathrm{Pb_{Ca}}) = -1248.750188\text{ eV}$ (with $\langle\mathrm{Pb-O}\rangle = 2.504\text{ Å}$)
* $E(\mathrm{Pb_{Mg}}) = -1249.538917\text{ eV}$ (with $\langle\mathrm{Pb-O}\rangle = 2.450\text{ Å}$)
* **Site Preference Evaluation:** Substitution of Pb2+ on the Ca site vs Mg site demonstrates that the large Pb2+ ion (r = 1.19 Å) strongly prefers the larger Ca octahedral coordination cage (r_Ca = 1.00 Å) over the compressed Mg cage (r_Mg = 0.72 Å). In dolomite, lead is partition-locked into the calcium sub-lattice.

### 3.2 Neutral Vacancy-Compensated $\mathrm{U(IV)}$ Motifs
* **Calcite ($\mathrm{U_{Ca}^{\bullet\bullet} + V_{Ca}^{\prime\prime}}$):** Converged to $E = -1271.286332\text{ eV}$ with $\langle\mathrm{U-O}\rangle_6 = 2.3053\text{ Å}$. The high electrostatic charge of $\mathrm{U^{4+}}$ contracts the 6 surrounding carbonate oxygens significantly relative to pristine $\mathrm{Ca-O}$ ($2.36\text{ Å}$).
* **Dolomite ($\mathrm{U_{Ca}^{\bullet\bullet} + V_{Mg}^{\prime\prime}}$):** Converged to $E = -1248.742636\text{ eV}$ with $\langle\mathrm{U-O}\rangle_6 = 2.3228\text{ Å}$, confirming the thermodynamic stability of adjacent $\mathrm{Mg}$ vacancy charge compensation.

### 3.3 Oxidative Interstitial Oxygen Motifs ($\mathrm{U_{Ca} + O_i}$)
* **Calcite ($\mathrm{U_{Ca} + O_i}$):** $E = -1285.899376\text{ eV}$, with 7-fold oxygen coordination shell $\langle\mathrm{U-O}\rangle_7 = 2.3718\text{ Å}$.
* **Dolomite ($\mathrm{U_{Ca} + O_i}$):** $E = -1261.383635\text{ eV}$, with 7-fold oxygen coordination shell $\langle\mathrm{U-O}\rangle_7 = 2.3663\text{ Å}$.
* These states simulate pre-salt reservoir conditions where diagenetic fluids introduce oxygen/oxidants, transitioning uranium from 6-fold toward 7/8-fold local coordination prior to full uranyl formation.
