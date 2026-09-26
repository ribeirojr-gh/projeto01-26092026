# Step04B2B-R3 — SOC direto do ramo UO2 aprovado

## Diagnóstico da R2

A R2 não falhou na convergência do UO2. Ela falhou ao tentar escrever:

```python
calc.write(..., mode="all")
```

a partir de um restart `.gpw` que não continha coeficientes PW.

O traceback foi:

```text
TypeError: 'NoneType' object is not subscriptable
kpt.psit_nG[n]
```

Isso ocorre porque o arquivo de origem do Step04B1B2-R2 foi gravado sem
`mode="all"` e, portanto, não contém os arrays `psit_nG`.

## Por que não precisamos recriar essas wavefunctions?

A implementação exata do GPAW 25.7 de:

```python
gpaw.spinorbit.soc_eigenstates()
```

usa:

- eigenvalues;
- PAW projections;
- density matrices;
- PAW setups;
- XC potential.

Ela não acessa os coeficientes PW `psit_nG` para calcular os eigenvalues SOC
ou a band energy.

Assim, para o nosso teste SOC não autoconsistente, um `.gpw` normal é
suficiente.

## Correção R3

Não fazemos novo cold start de UO2 e não tentamos converter o restart para
`mode="all"`.

Usamos diretamente:

```text
step04B1B2_uo2_eos_R2/resultados_step04B1B2_R2/
  restart/UO2_nc6_U3p0_center_1600_tight.gpw
```

Esse é exatamente o ramo eletrônico já aprovado.

O script ainda restaura `setup_paths` para `U.PBEsol` e `Pb.PBEsol` antes
de abrir qualquer `.gpw`.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas esperadas

```text
step04B2B_soc_sensitivity/saida-step04B2B-R3.txt

step04B2B_soc_sensitivity/resultados_step04B2B/
  PbCO3_scalar_groundstate.json
  UO2_scalar_groundstate.json
  PbCO3_SOC_sensitivity.json
  UO2_SOC_sensitivity.json
  decisao_step04B2B.json
```
