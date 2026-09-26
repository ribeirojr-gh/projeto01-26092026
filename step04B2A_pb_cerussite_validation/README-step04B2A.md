# Step04B2A — validação Pb(II) em cerussita PbCO3

## Estado de entrada

O benchmark escalar-colinear de U(IV)/UO2 foi aprovado no Step04B1B2-R3:

```text
PAW U          = U14_nc6
XC             = PBEsol
Ueff           = 3.0 eV
Ecut produção  = 1600 eV
Ecut validação = 1800 eV
```

A produção de defeitos U/Pb continua bloqueada.

## Referência Pb(II)

Usamos cerussita PbCO3, estrutura tipo aragonita, grupo espacial 62.

Referência primária:
Chevrier et al., Zeitschrift für Kristallographie 199 (1992) 67–74,
refinamento por difração de nêutrons em monocristal:

```text
a = 5.179 Å
b = 8.492 Å
c = 6.141 Å
Z = 4
grupo espacial Pmcn (setting equivalente ao No. 62)
aplanaridade CO3 ~0.026 Å
```

O arquivo experimental já foi armazenado no Step04B1A; este pacote não
depende de download externo.

## 1. Gate numérico

São feitos quatro single points na estrutura experimental:

```text
1400 eV / 3x2x3
1400 eV / 4x3x4
1600 eV / 3x2x3
1600 eV / 4x3x4
```

Critérios:

```text
ΔE             <= 1 meV/átomo
Δgap           <= 0.03 eV
Δstress_h      <= 0.10 GPa
Δforça máxima  <= 0.02 eV/Å
```

Se esse gate falhar, a execução para antes da relaxação.

## 2. Relaxação

A documentação GPAW/ASE recomenda verificar separadamente célula e
posições. Por isso não usamos uma única otimização variável simultânea.

Sequência:

```text
1. átomos, célula experimental fixa
2. célula ortorrômbica, posições fracionárias fixas
3. átomos
4. nova otimização da célula
5. átomos finais
```

A célula é otimizada com `StrainFilter` e apenas xx, yy e zz são livres;
cisalhamentos permanecem zero, coerente com a simetria ortorrômbica.

## 3. Validação estrutural

São comparados:

- a, b e c;
- volume;
- ângulos;
- grupo espacial;
- comprimentos C–O;
- nove vizinhos O mais próximos de cada Pb;
- distância do C ao plano O3 (aplanaridade do carbonato).

Gates principais:

```text
erro de cada parâmetro de rede <= 2%
erro de volume                 <= 4%
erro angular                   <= 0.5°
erro médio C-O                 <= 3%
erro médio Pb-O(9)             <= 4%
grupo espacial recuperado      = No. 62
```

A aplanaridade é reportada, mas não é gate rígido porque o valor
experimental inclui efeitos térmicos e a DFT é estática.

## 4. Validação final

Na geometria relaxada:

```text
PBEsol
1600 eV
4x3x4
```

Exigimos:

```text
força máxima <= 0.03 eV/Å
stress máximo <= 0.30 GPa
```

O gap escalar-relativístico é registrado, mas não decide a aprovação antes
do teste SOC.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B2A_pb_cerussite_validation/saida-step04B2A.txt

step04B2A_pb_cerussite_validation/resultados_step04B2A/
    numeric_gate_step04B2A.json
    relaxation_step04B2A.json
    structural_metrics_step04B2A.json
    PbCO3_relaxed_1600_k434.json
    decisao_step04B2A.json

step04B2A_pb_cerussite_validation/resultados_step04B2A/relax/
    PbCO3_relaxed_production.traj
    PbCO3_relaxed_production.cif
```

## Próximo gate

Se aprovado:

1. sensibilidade SOC controlada em PbCO3 e UO2;
2. referência U(VI) estruturalmente realista;
3. somente então liberação dos defeitos U/Pb em calcita/dolomita.
