# Milestone 06: Electronic Structure, PDOS, Oxidation Mechanisms & Defect Thermodynamics

**Project:** U–Pb Carbonate Geochronology (Petrobras / LCCMat)  
**Execution Tier:** Local Workstation (Strictly Local First-Principles DFT with GPAW)  
**Status:** IN PROGRESS  

## 1. Objectives
1. **Electronic Structure & Projected Density of States (PDOS):**
   * Quantify the band alignment, gap states, and orbital projections ($\mathrm{U}(5f)$, $\mathrm{O}(2p)$, $\mathrm{Pb}(6p)$) for all converged defect complexes in Calcite and Dolomite 160-atom supercells.
   * Verify the formal oxidation state of Uranium: localized $5f^2$ ($\mathrm{U(IV)}$) vs. delocalized/empty $5f^0$ ($\mathrm{U(VI)}$) via integrated orbital occupation and magnetic moment.
   * Conduct charge transfer analysis (Löwdin & Bader charges) across the first coordination shell.
2. **Standard Reference Reservoirs & Chemical Potentials:**
   * Compute standard elemental and binary references: $\mathrm{O_2}$, $\mathrm{CO_2}$, $\mathrm{CaO}$, $\mathrm{MgO}$.
   * Integrate pre-computed standard references: $\mathrm{UO_2}$, $\gamma\text{-}\mathrm{UO_3}$, $\mathrm{PbCO_3}$, pristine calcite, and pristine dolomite.
   * Define the stability polygon in $(\Delta\mu_{\mathrm{Ca}}, \Delta\mu_{\mathrm{Mg}}, \Delta\mu_{\mathrm{O}})$ space avoiding secondary phase precipitation.
3. **Defect Formation Thermodynamics & Oxidation Boundaries:**
   * Calculate formation energy $\Delta E_f[D]$ as a function of oxygen chemical potential $\Delta\mu_{\mathrm{O}}$ for:
     * $\mathrm{Pb_{Ca}^{\times}}$ and $\mathrm{Pb_{Mg}^{\times}}$
     * Neutral $(\mathrm{U_{Ca}^{\bullet\bullet} + V_{cation}^{\prime\prime}})^{\times}$ vacancy pairs
     * Interstitial oxygen $(\mathrm{U_{Ca} + O_i})$ complexes
   * Determine the critical oxygen chemical potential $\mu_{\mathrm{O}}^*$ marking the transition from tetravalent preservation to oxidative remobilization.
