# Step04B2C2 — validação final de U(VI) em gamma-UO3

O Step04B2C1 foi aprovado. Esta é a última validação de composto antes do
Step05.

Matriz escalar:
```text
U14_nc6
PBEsol
Ueff = 3 eV
1600 eV
2x2x2
U(VI) não magnético
```

A simetria Fddd é preservada explicitamente com
`ase.constraints.FixSymmetry`. A célula e as posições são relaxadas com
`FrechetCellFilter`, recomendado pelo ASE para otimização consistente de
célula.

Sequência:
1. átomos, célula experimental fixa;
2. posições + célula;
3. átomos tight;
4. posições + célula tight.

Gates estruturais:
```text
erro de cada parâmetro de rede <= 2%
erro de volume                 <= 4%
erro U-O mínimo                <= 5%
RMS do perfil dos 6 U-O        <= 3%
grupo espacial                 = No. 70
```

Na geometria relaxada:
```text
1600 eV / 2x2x2
1600 eV / 3x3x3
1800 eV / 2x2x2
```

Todos usam 192 bandas para permitir convergência SOC.

Como o B2C1 mostrou um deslocamento SOC grande (~ -0.96 eV), o SOC final
é testado quanto a:
```text
subespaço: n2=160 vs n2=192
k-points: 2x2x2 vs 3x3x3
cutoff:   1600 vs 1800 eV
```

`production_authorization=true` somente se relaxação, estrutura,
convergência numérica e convergência SOC passarem. Isso autoriza o início
do Step05, que ainda começa com testes de supercélula, compensação de
carga e configurações de defeito.

Execução:
```bash
bash executar_pacote_upb.sh
```

Saídas:
```text
step04B2C2_uvi_gamma_uo3_relax/saida-step04B2C2.txt

step04B2C2_uvi_gamma_uo3_relax/resultados_step04B2C2/
  relaxation_step04B2C2.json
  structural_metrics_step04B2C2.json
  gammaUO3_relaxed_1600_k222.json
  gammaUO3_relaxed_1600_k333.json
  gammaUO3_relaxed_1800_k222.json
  gammaUO3_relaxed_SOC_convergence.json
  decisao_step04B2C2.json
```
