# Step04B1B2-R3 — decisão estrutural via stress–strain

## Por que o EOS de energia do R2 não será usado para B0?

O R2 obteve para Ueff=3 eV:

```text
a0(EOS) = 5.46439 Å
B0(EOS) = 137.10 GPa
RMSE    = 8.53 meV/átomo
```

Apesar de todos os cinco pontos terem convergido, gap, momento e energia
mostram mudanças de solução orbital entre volumes. Em DFT+U, offsets entre
mínimos eletrônicos distintos destroem a interpretação de uma curva E(V)
como uma única superfície adiabática.

Portanto, esse B0=137 GPa não é aceito como módulo volumétrico físico.

## Informação estrutural que permaneceu suave

O stress hidrostático do mesmo conjunto Ueff=3 eV evoluiu de forma suave:

```text
a=5.361188 Å  sigma_h=-13.4681 GPa
a=5.415894 Å  sigma_h= -5.8766 GPa
a=5.470600 Å  sigma_h= +1.0283 GPa
a=5.525306 Å  sigma_h= +6.5691 GPa
a=5.580012 Å  sigma_h=+12.0032 GPa
```

Para pequenas deformações isotrópicas:

```text
sigma_h ≈ B0 * (V-V0)/V0
```

Assim, a inclinação stress × deformação volumétrica fornece um estimador
local de B0, enquanto o zero de stress fornece a0.

## Gates

São feitos dois ajustes independentes:

```text
5 pontos: ±2% em a
3 pontos centrais: ±1% em a
```

Para aprovar:

```text
R² do ajuste             >= 0.98
erro de a0               <= 0.50%
175 <= B0 <= 240 GPa
diferença a0 entre fits  <= 0.020 Å
diferença B0 entre fits  <= 5%
```

Também são exigidos:

```text
Step04B1B1 reprodutível
mesmo ramo no ponto central
cutoff Ueff=3 eV aprovado
```

O cutoff já identificado no R2 é:

```text
produção U-containing = 1600 eV
validação              = 1800 eV
```

## Ueff=4 eV

Ueff=4 eV deixa de ser candidato principal porque:

- o ponto comprimido 0.98 não convergiu;
- 1400 e 1800 eV convergem para gap ~3.345 eV;
- 1600 eV converge para outro ramo, gap ~2.883 eV;
- portanto o ladder de cutoff não é monotônico nem fisicamente utilizável.

## Execução

Nenhum DFT novo é executado.

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B1B2_uo2_stress_gate/saida-step04B1B2-R3.txt

step04B1B2_uo2_stress_gate/resultados_step04B1B2_R3/
    decisao_step04B1B2_R3.json
    UO2_stress_strain_fits_R3.csv
```
