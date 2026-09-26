# Step04B1B1 — reprodutibilidade UO2/nc6

## Decisão após o Step04B1A-R5

O protocolo comum mostrou:

- `nc6`: convergiu em Ueff = 2, 3, 4 e 5 eV;
- `poly6`: convergiu apenas em Ueff = 0 e 5 eV sob o mesmo protocolo;
- `nc6/Ueff=3 eV`: melhor compromisso eletrônico da triagem,
  gap = 2.5293 eV;
- `nc6/Ueff=4 eV`: stress muito pequeno na célula experimental,
  mas gap = 3.3440 eV.

O `poly6` permanece como teste de sensibilidade, mas deixa de ser o
candidato principal por apresentar forte dependência do tratamento de
simetria/SCF.

## Objetivo desta subetapa

Antes de executar EOS/relaxações caras, verificar se o resultado DFT+U do
`nc6` é reprodutível e se sobrevive ao smearing final de 0.05 eV.

São testados:

```text
Ueff = 2.5, 3.0 e 4.0 eV
```

em três domínios AFM 1-k colineares equivalentes no cristal cúbico sem SOC:

```text
kz
kx
ky
```

Cada cálculo:

1. pré-converge com smearing 0.10 eV;
2. se necessário usa uma tentativa amortecida a 0.15 eV;
3. grava restart com wavefunctions;
4. reinicia a partir do estado convergido;
5. aperta para smearing 0.05 eV e critérios SCF mais estritos.

## Gate de reprodutibilidade

Para um Ueff passar:

```text
3/3 domínios convergidos
spread de energia <= 2 meV/átomo
spread de gap     <= 0.10 eV
spread de momento <= 0.05 μB
```

Como os três domínios são equivalentes por simetria sem SOC, diferenças
maiores indicam sensibilidade a mínimo orbital/metaestabilidade ou
convergência insuficiente.

## Por que não fazemos EOS ainda?

UO2 + DFT+U possui múltiplos mínimos eletrônicos. Antes de comparar curvas
E(V), precisamos garantir que cada ponto não está caindo em um estado
eletrônico diferente. Esta subetapa evita gastar dezenas de cálculos EOS
sobre uma solução não reprodutível.

## Próximo gate

Se pelo menos um candidato for reprodutível:

```text
Step04B1B2
  -> EOS / a0 / B0
  -> comparação estrutural
  -> 1400 vs 1600 eV
  -> seleção final do Ueff escalar-colinear
```

SOC e o estado 3-k não colinear serão tratados separadamente como
sensibilidade física controlada.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B1B_uo2_reproducibility/saida-step04B1B1.txt

step04B1B_uo2_reproducibility/resultados_step04B1B1/
    decisao_step04B1B1.json
    UO2_domain_reproducibility_B1B1.csv
```

Os JSON individuais de cada domínio também são mantidos para auditoria.
