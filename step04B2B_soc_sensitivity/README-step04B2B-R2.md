# Step04B2B-R2 — correção do SOC

## Por que os arquivos SOC não foram gerados?

Os dois ground states escalares convergiram. A interrupção ocorreu somente
ao reabrir o `.gpw` de PbCO3:

```text
FileNotFoundError:
Could not find required PAW dataset file "Pb.PBEsol".
```

O `.gpw` grava qual setup foi usado, mas não incorpora o arquivo
`Pb.PBEsol`. Portanto `setup_paths` precisa ser configurado antes de
`GPAW(gpw)`.

A R2 corrige isso para Pb e U.

## Segunda correção importante: ramo eletrônico do UO2

O cold start criado no B2B original caiu em outro mínimo DFT+U:

```text
B2B original:
gap = 2.14241 eV
|mU| = 1.89513 μB
```

O estado que havia sido aprovado no Step04B1B2-R2, em 1600 eV, era:

```text
gap ≈ 2.53150 eV
|mU| ≈ 1.92910 μB
```

Portanto o `.gpw` UO2 criado pelo B2B original NÃO deve ser usado para
medir SOC.

A R2 reabre diretamente:

```text
step04B1B2_uo2_eos_R2/resultados_step04B1B2_R2/
  restart/UO2_nc6_U3p0_center_1600_tight.gpw
```

reconverge com os critérios finais, verifica automaticamente que energia,
gap e momento continuam no mesmo ramo aprovado e só então grava um novo
`.gpw` com `mode="all"` para o cálculo SOC.

Gates de identidade de ramo:

```text
ΔE      <= 2 meV/átomo
Δgap    <= 0.05 eV
Δ|mU|   <= 0.02 μB
```

Se esse gate falhar, o SOC UO2 é interrompido de propósito.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas esperadas

```text
step04B2B_soc_sensitivity/saida-step04B2B-R2.txt

step04B2B_soc_sensitivity/resultados_step04B2B/
  PbCO3_scalar_groundstate.json
  UO2_scalar_groundstate.json
  PbCO3_SOC_sensitivity.json
  UO2_SOC_sensitivity.json
  decisao_step04B2B.json
```
