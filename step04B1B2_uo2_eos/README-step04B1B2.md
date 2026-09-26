# Step04B1B2 — EOS e validação 1400/1600 eV do UO2/nc6

## Entrada científica

O Step04B1B1-R2 aprovou o gate de reprodutibilidade:

### Ueff = 3 eV
- 3/3 domínios convergidos;
- spread de energia = 0.00103 meV/átomo;
- spread de gap = 0.01033 eV;
- spread de momento = 9.3e-6 μB;
- gap do domínio mínimo = 2.5212 eV.

### Ueff = 4 eV
- 3/3 domínios convergidos;
- spread de energia = 0.00117 meV/átomo;
- spread de gap = 0.00085 eV;
- stress muito pequeno na célula experimental;
- gap ~3.345 eV.

Ueff=2.5 eV não passa ao EOS porque apenas 1/3 domínios convergiu.

## Objetivo

Resolver o trade-off estrutura x eletrônica entre Ueff=3 e 4 eV.

Para ambos:

```text
PAW = nc6
PBEsol
AFM 1-k, domínio ky
k = 3x3x3
80 bandas
smearing final = 0.05 eV
Ecut EOS = 1400 eV
```

A curva EOS usa cinco constantes de rede:

```text
0.98 a_ref
0.99 a_ref
1.00 a_ref   <- reutilizado do Step04B1B1
1.01 a_ref
1.02 a_ref
```

com `a_ref = 5.4706 Å`.

São executados apenas quatro novos pontos EOS por Ueff; o centro já
convergido no B1B1 é reutilizado.

Ajuste:

```text
Birch-Murnaghan
```

Saídas principais:

```text
a0
B0
erro de a0 frente à referência experimental
```

## Referências experimentais de comparação

Para a constante de rede usamos como guia de alta precisão:

```text
a0 = 5.47127 Å a 20 °C
```

de Leinders et al., para UO2.000 ± 0.001.

Para o módulo volumétrico usamos apenas um guia amplo em torno de
200-210 GPa; o gate aceita 175-240 GPa porque a comparação mistura
temperatura experimental e DFT estática 0 K.

## Validação de cutoff

No centro, Ueff=3 e 4 eV são repetidos com:

```text
Ecut = 1600 eV
```

e comparados ao resultado 1400 eV já existente.

Critérios:

```text
|ΔE|      <= 5 meV/átomo
|Δgap|    <= 0.05 eV
|Δmoment| <= 0.02 μB
|Δstress| <= 0.10 GPa
```

## Critério estrutural de shortlist

```text
erro de a0 <= 1%
175 <= B0 <= 240 GPa
```

Esses critérios não são um ajuste de Ueff ao experimento; são apenas gates
de sanidade/transferibilidade.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B1B2_uo2_eos/saida-step04B1B2.txt

step04B1B2_uo2_eos/resultados_step04B1B2/
    decisao_step04B1B2.json
    UO2_EOS_points_B1B2.csv
```

## Próximo gate

Se aprovado:

1. relaxação/validação de cerussita PbCO3 com PBEsol/Pb;
2. sensibilidade SOC controlada no UO2;
3. validação U(VI) em uma estrutura realista;
4. somente depois, autorização da etapa de defeitos U/Pb em carbonatos.
