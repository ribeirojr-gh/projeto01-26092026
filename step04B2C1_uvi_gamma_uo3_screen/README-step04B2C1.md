# Step04B2C1 — triagem realista de U(VI) em gamma-UO3

## Entrada

Step04B2B-R3 confirmou que SOC é relevante para PbCO3 e UO2:

- PbCO3: Δgap_SOC ≈ -0.243 eV;
- UO2: Δgap_SOC ≈ -0.235 eV;
- UO2: anisotropia de band energy ≈ 4.79 meV/f.u.

Assim, a referência U(VI) também deve ser avaliada com SOC.

## Estrutura escolhida

Usamos gamma-UO3 ortorrômbico a 293 K:

```text
COD 1527742
Fddd, No. 70
a = 9.787 Å
b = 19.932 Å
c = 9.705 Å
```

Referência: Loopstra, Taylor & Waugh, Journal of Solid State Chemistry
20 (1977) 9–19, refinamento por difração de nêutrons.

A célula convencional Fddd é convertida em uma célula primitiva de
32 átomos (8 U + 24 O), reduzindo o custo DFT.

O CIF é baixado automaticamente do COD na primeira execução e seu SHA256
é gravado no manifest.

## Motivação eletrônica

U(VI) possui configuração formal 5f0 e deve ser essencialmente
não magnético. O workflow compara:

```text
PBEsol / Ueff=0
PBEsol / Ueff=3 eV
```

e também inicia Ueff=3 eV com momentos alternados ±1 μB para verificar se
o funcional cria uma solução magnética espúria.

## Matriz numérica

Principal:

```text
U14_nc6
PBEsol
Ueff = 3 eV
1600 eV
2x2x2
```

Validações:

```text
1600 eV / 3x3x3
1800 eV / 2x2x2
```

## SOC

No estado Ueff=3 eV / não magnético:

```text
scale = 0
scale = 0.5
scale = 1
```

O gap experimental é usado apenas como guia, não como ajuste de U:

```text
gamma-UO3/Fddd ~2.38 eV
```

## Gates

Numéricos:

```text
ΔE      <= 2 meV/átomo
Δgap    <= 0.08 eV
Δstress <= 0.20 GPa
```

U(VI):

```text
momento médio no teste seeded <= 0.20 μB
1.5 <= gap_SOC <= 3.5 eV
força fixa <= 2 eV/Å
stress fixo <= 10 GPa
```

Esta é uma triagem em geometria experimental. A relaxação estrutural será
feita somente no Step04B2C2 se esta etapa passar.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B2C1_uvi_gamma_uo3_screen/saida-step04B2C1.txt

step04B2C1_uvi_gamma_uo3_screen/resultados_step04B2C1/
  gammaUO3_U0_1600_k222.json
  gammaUO3_U3_1600_k222.json
  gammaUO3_U3_1600_k333.json
  gammaUO3_U3_1800_k222.json
  gammaUO3_U3_seeded_1600_k222.json
  gammaUO3_SOC_sensitivity.json
  decisao_step04B2C1.json

step04B2C1_uvi_gamma_uo3_screen/estruturas/
  gamma_UO3_structure_manifest.json
```
