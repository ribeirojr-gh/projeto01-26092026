# Project Charter: U–Pb Carbonate Geochronology

## 1. Collaborative Framework & Strategic Scope
This project is conducted under the strategic collaboration between **Petrobras** and the **Computational Materials Science Laboratory (LCCMat)**. The central mission is to establish a rigorous, first-principles computational framework for understanding the mechanisms and environmental conditions governing uranium and lead retention, incorporation, and mobilization in carbonate reservoirs, with primary focus on Brazilian pre-salt depositional and diagenetic sequences.

## 2. Geological & Geochemical Problem Definition
U–Pb dating of carbonates represents a transformative geochronological tool for constraining the timing of sedimentation, diagenesis, fault reactivation, and hydrothermal fluid circulation in petroleum basins. Unlike zircon or monazite, carbonate minerals typically contain trace concentrations of uranium (sub-ppm to a few ppm) and variable initial common lead ($\mathrm{Pb_c}$).

A major challenge in carbonate geochronology is open-system behavior:
1. **Oxidation and Mobility:** In reduced diagenetic environments, $\mathrm{U(IV)}$ is relatively immobile and incorporates into calcium lattice sites. Exposure to oxidizing fluids converts $\mathrm{U(IV)}$ to the highly soluble and mobile uranyl moiety ($\mathrm{UO_2^{2+}}$), disrupting the isotopic parent-daughter clock.
2. **Radiogenic Lead ($\mathrm{Pb^*}$) Retention:** Decay of $^{238}\mathrm{U}$, $^{235}\mathrm{U}$, and $^{232}\mathrm{Th}$ produces radiogenic lead isotopes ($^{206}\mathrm{Pb}$, $^{207}\mathrm{Pb}$, $^{208}\mathrm{Pb}$) that experience recoil energy and lattice displacement. Understanding how lead sits within the host matrix is crucial to evaluate diffusion kinetics and closure temperatures.

## 3. Key Target Systems
* **Calcite ($\mathrm{CaCO_3}$):** Trigonal system, space group $R\bar{3}c$ (#167), $Z=6$ (hexagonal cell) / $Z=2$ (rhombohedral cell).
* **Dolomite ($\mathrm{CaMg(CO_3)_2}$):** Trigonal system, space group $R\bar{3}$ (#148), with alternating Ca and Mg cation layers along the $c$-axis.

## 4. Scientific Objectives & Causal Pathway
The overarching research tasks are structured to resolve the following causal chain:
```text
[Fluid Ingress / Oxidant Infiltration]
              │
              ▼
[Oxidation of U(IV) to U(VI) Complexes]
              │
              ▼
[Local Structural Distortion & Uranyl Complexation]
              │
              ▼
[Altered Incorporation Energies & Activation Barriers]
              │
              ▼
[Isotopic Remobilization / Leaching vs. Preservation Maps]
```
