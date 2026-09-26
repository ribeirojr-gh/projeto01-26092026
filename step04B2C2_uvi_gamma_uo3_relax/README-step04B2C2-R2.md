# Step04B2C2-R2 — correção do gate estrutural

## Diagnóstico

O B2C2 calculou corretamente a relaxação, os single points e o SOC.

A única reprovação veio do gate estrutural. O código original fez:

1. `SpacegroupAnalyzer(..., symprec=0.03)`;
2. a estrutura relaxada foi reconhecida como `I41/amd`, No. 141;
3. o `conventional_standard_structure` desse grupo tem 16 UO3;
4. ele foi comparado diretamente à célula Fddd experimental de 293 K,
   que tem 32 UO3.

Por isso apareceu artificialmente:

```text
erro de volume ~49 %
```

Isso não é uma contração física de 49%; é comparação entre células
convencionais com multiplicidades diferentes.

## Evidência do próprio cálculo

Com `symprec=0.01 Å`, a estrutura ainda é:

```text
Fddd, No. 70
```

Com 0.03–0.05 Å, a pequena distorção ortorrômbica desaparece
numericamente e a estrutura é reconhecida como `I41/amd`.

Isso é coerente com o fato experimental de que o gamma-UO3 a 293 K é
pseudotetragonal e está estruturalmente muito próximo da fase tetragonal
de maior temperatura.

## Reanálise correta

Comparamos grandezas independentes do setting convencional:

### volume por fórmula

```text
Vexp(Fddd)/32
Vrelax(primitiva)/8
```

### métrica pseudotetragonal a 293 K

```text
a_t1 = a_orth / sqrt(2)
a_t2 = c_orth / sqrt(2)
c_t  = b_orth
```

e comparamos o basal relaxado ao valor médio de `a_t1` e `a_t2`.

Mantemos também:

- U–O mínimo;
- perfil dos seis primeiros U–O;
- Fddd em `symprec=0.01 Å`;
- gates numéricos;
- gates SOC.

Nenhum DFT novo é executado.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B2C2_uvi_gamma_uo3_relax/saida-step04B2C2-R2.txt

step04B2C2_uvi_gamma_uo3_relax/resultados_step04B2C2/
  decisao_step04B2C2_R2.json
  structural_reanalysis_step04B2C2_R2.csv
```

Se `production_authorization=true`, a validação de compostos do Step04
é encerrada e o Step05 pode começar.
