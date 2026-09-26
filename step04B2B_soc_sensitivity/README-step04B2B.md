# Step04B2B — sensibilidade controlada a SOC

Entrada validada:
- UO2: U14_nc6 + PBEsol + Ueff=3 eV, 1600 eV, 3x3x3, AFM 1-k;
- PbCO3: Pb PBEsol gerado, estrutura relaxada, validação 1600 eV / 4x3x4.

O GPAW 25.7 usa `gpaw.spinorbit.soc_eigenstates()` para adicionar SOC
não autoconsistentemente aos estados Kohn-Sham escalares.

PbCO3:
- scale=0, 0.5, 1.

UO2:
- scale=0 e 0.5 em z;
- scale=1 em z, x e y.

Antes de interpretar SOC, `scale=0` deve reproduzir o gap escalar em
até 0.05 eV. SOC é classificado como relevante para estrutura eletrônica
quando |Δgap| >= 0.10 eV. Em UO2, anisotropia >= 1 meV/f.u. também é
classificada como relevante.

Este gate não rejeita PAWs por SOC forte: ele define a política dos passos
seguintes. Relaxações permanecem escalares por enquanto; análises
eletrônicas e energias de defeito com U/Pb recebem correção SOC de
sensibilidade se o efeito for significativo.

Execução:
```bash
bash executar_pacote_upb.sh
```

Saídas:
```text
step04B2B_soc_sensitivity/saida-step04B2B.txt
step04B2B_soc_sensitivity/resultados_step04B2B/
  PbCO3_scalar_groundstate.json
  UO2_scalar_groundstate.json
  PbCO3_SOC_sensitivity.json
  UO2_SOC_sensitivity.json
  decisao_step04B2B.json
```

Próximo gate: referência U(VI) estruturalmente realista.
