# Step04B1A-R5 — protocolo comum para UO2

A R4 convergiu em Ueff=4 eV para os dois PAWs, porém com tratamentos de
simetria diferentes:

- poly6: simetria magnética completa;
- nc6: point group desligado.

A R5 remove esse viés e aplica aos dois datasets:

```text
PBEsol; 1400 eV; 3x3x3; 80 bandas
AFM 1-k colinear
point_group=False
time_reversal=True
fixmagmom=False
Hubbard normalizado
Ueff=0,2,3,4,5 eV
```

O protocolo principal usa smearing de 0.10 eV. Uma tentativa amortecida com
0.15 eV é usada apenas quando necessário.

Não se comparam energias absolutas entre poly6 e nc6.

Execução:

```bash
bash executar_pacote_upb.sh
```

Saídas:

```text
step04B_compound_screening/saida-step04B1A-R5.txt
step04B_compound_screening/resultados_step04B1A_R5/decisao_step04B1A_R5.json
step04B_compound_screening/resultados_step04B1A_R5/UO2_common_protocol_summary_R5.csv
step04B_compound_screening/resultados_step04B1A_R5/U_dataset_common_protocol_comparison_R5.json
step04B_compound_screening/resultados_step04B1A_R5/SCF_failures_R5.json
```
