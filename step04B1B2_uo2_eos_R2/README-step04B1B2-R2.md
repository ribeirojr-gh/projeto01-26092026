# Step04B1B2-R2 — EOS determinístico e cutoff ladder

## O que aprendemos no B1B2 original

O B1B2 não deve ser interpretado como uma reprovação física do nc6.

Dois pontos EOS falharam:
- Ueff=3 eV, s=0.99;
- Ueff=4 eV, s=0.98.

Além disso, a curva Ueff=3 eV mostrou sinais de mudança de ramo eletrônico:
o ponto s=1.01 apresentou salto de energia/gap incompatível com uma curva
EOS suave.

A causa metodológica mais importante é que o script usava:

```python
random=True
```

No GPAW, o padrão `random=False` usa uma inicialização LCAO determinística.
Para um sistema DFT+U com múltiplos mínimos orbitais, wavefunctions
aleatórias são inadequadas para construir uma curva EOS contínua.

## Correção R2

Todos os pontos são recalculados com:

```text
random=False
PBEsol
nc6
AFM 1-k ky
point_group=False
time_reversal=True
fixmagmom=False
smearing final=0.05 eV
```

São recalculados os 5 pontos para Ueff=3 e 4 eV. O centro também é
recalculado, de modo que nenhum EOS mistura estados obtidos por protocolos
de inicialização diferentes.

O pós-processamento compara o centro determinístico com o estado B1B1 para
verificar se ambos pertencem ao mesmo ramo eletrônico.

## Cutoff

O gate antigo 1400->1600 passou amplamente em energia, gap e momento, mas
o stress hidrostático mudou cerca de 0.11 GPa — ligeiramente acima do gate
de 0.10 GPa.

Não relaxamos o critério depois de ver o resultado. Em vez disso, fazemos:

```text
1400 -> 1600 -> 1800 eV
```

Se 1600->1800 satisfizer todos os critérios, a matriz U-containing passa a
usar:

```text
produção = 1600 eV
validação = 1800 eV
```

Isso permite que o novo PAW de U tenha um cutoff próprio, independente do
cutoff Ca-Mg-C-O validado no Step03.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B1B2_uo2_eos_R2/saida-step04B1B2-R2.txt
step04B1B2_uo2_eos_R2/resultados_step04B1B2_R2/decisao_step04B1B2_R2.json
step04B1B2_uo2_eos_R2/resultados_step04B1B2_R2/UO2_EOS_deterministic_R2.csv
```
