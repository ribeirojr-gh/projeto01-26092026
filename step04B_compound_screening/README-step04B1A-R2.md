# Step04B1A-R2 — estabilização do SCF de UO2

A cerussita PbCO3 convergiu normalmente. A primeira tentativa
UO2/poly6/Ueff=0 falhou por `KohnShamConvergenceError`.

A R2 usa duas estratégias automáticas para UO2:

1. `MixerSum(beta=0.02, nmaxold=5, weight=100)`, smearing 0.15 eV,
   eigensolver com cinco iterações e até 500 ciclos SCF.
2. Se necessário, `MixerDif` fortemente amortecido, smearing 0.20 eV
   e até 700 ciclos SCF.

O momento total AFM é fixado em zero. Falhas SCF são capturadas e registradas
sem interromper toda a matriz. O PbCO3 já convergido é reutilizado.

O smearing aumentado é apenas para triagem. Os finalistas serão repetidos
com 0.05 eV e critérios estritos.

Execução:

```bash
bash executar_pacote_upb.sh
```

Saídas:

```text
step04B_compound_screening/saida-step04B1A.txt
step04B_compound_screening/resultados_step04B1A/decisao_step04B1A.json
step04B_compound_screening/resultados_step04B1A/UO2_screening_summary.csv
step04B_compound_screening/resultados_step04B1A/U_dataset_comparison.json
step04B_compound_screening/resultados_step04B1A/SCF_failures_R2.json
```
