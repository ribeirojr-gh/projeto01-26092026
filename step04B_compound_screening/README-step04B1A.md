# Step 04B1A — triagem química de PAWs e Ueff

## Estado de entrada

O Step04A-R8 foi aprovado.

- U: `U14_poly6` passou o gate atômico em PBE e PBEsol.
- `U14_nc6` também passou e é mantido como candidato independente.
- Pb: o PAW-PBE gerado reproduziu a curva E(V), stress, `a0` e `B0` do
  PAW-PBE oficial dentro dos critérios definidos.
- A autorização para defeitos U/Pb permanece bloqueada até validação química.

## Objetivo desta subetapa

Fazer uma triagem de baixo custo antes das relaxações mais caras.

### Pb(II)

Cerussita, PbCO3:

- COD 9008411;
- refinamento por difração de nêutrons;
- referência diretamente relevante para ambiente carbonático.

Nesta subetapa é feito single point PBEsol na geometria experimental.

### U(IV)

UO2 fluorita:

- Fm-3m;
- a = 5.4706 Å;
- célula convencional de 12 átomos;
- configuração AFM 1-k colinear usada somente como benchmark computacional.

O estado magnético experimental de baixa temperatura é 3-k AFM não colinear.
Portanto esta subetapa NÃO afirma reproduzir o estado fundamental magnético
completo.

São comparados:

```text
U14_poly6
U14_nc6
```

com:

```text
Ueff = 0, 2, 3, 4, 5 eV
```

GPAW usa o formalismo de Dudarev:

```text
Ueff = U - J
```

e a correção é aplicada ao canal f.

### U(VI)

delta-UO3 ideal ReO3-type, Pm-3m, a = 4.1658 Å:

- pequeno sistema de 4 átomos;
- usado somente como triagem inicial do estado U(VI);
- não substitui a validação final em gamma-UO3.

Nesta fase comparamos `poly6` e `nc6` com Ueff=0.

## Por que não ajustar Ueff diretamente ao gap?

O Ueff não será escolhido por ajuste a um único observável.

A triagem usa:

- gap;
- momento local do U;
- forças/stress na estrutura experimental;
- sensibilidade ao PAW `poly6` vs `nc6`.

Depois serão feitos:

1. relaxação/volume dos melhores candidatos;
2. validação U(VI) em gamma-UO3;
3. sensibilidade controlada a SOC;
4. só então fixação do setup/Ueff para produção.

## Referências de trabalho

- GPAW DFT+U: documentação oficial, formalismo Dudarev e sintaxe
  `setups={'U': ':f,Ueff'}`.
- UO2 experimental: fluorita com a ~5.47 Å; momento ordenado ~1.74 μB/U;
  estado fundamental AFM 3-k.
- Cerussita: COD 9008411, Chevrier et al., Z. Kristallogr. 199 (1992).
- delta-UO3: estrutura ReO3-type usada como referência compacta U(VI);
  gamma-UO3 será o gate final.

## Execução

Após baixar o ZIP:

```bash
bash executar_pacote_upb.sh
```

## Saídas para compartilhar

```text
step04B_compound_screening/saida-step04B1A.txt
step04B_compound_screening/resultados_step04B1A/decisao_step04B1A.json
step04B_compound_screening/resultados_step04B1A/UO2_screening_summary.csv
step04B_compound_screening/resultados_step04B1A/U_dataset_comparison.json
```

Também são úteis os JSON individuais caso algum cálculo apresente
comportamento anômalo.
