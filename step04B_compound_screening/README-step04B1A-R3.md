# Step04B1A-R3 — correção da especificação do eigensolver

## Erro observado

O GPAW 25.7.0 interrompeu a inicialização com:

```text
KeyError: 'name'
```

A revisão R2 fornecia:

```python
eigensolver={"niter": 5}
```

No GPAW 25.7.0, quando o eigensolver é fornecido como dicionário, o campo
`name` é obrigatório.

## Correção

As tentativas UO2 agora usam explicitamente:

```python
eigensolver={"name": "dav", "niter": 5}
```

Os demais cálculos usam:

```python
eigensolver={"name": "dav", "niter": 3}
```

O Davidson (`dav`) é apropriado para a base de ondas planas e para a
obtenção dos estados ocupados e desocupados usados na estimativa do gap.

Nenhum resultado convergido é removido. O PbCO3 existente será reutilizado.

## Execução

Na raiz do projeto:

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B_compound_screening/saida-step04B1A.txt
step04B_compound_screening/resultados_step04B1A/decisao_step04B1A.json
step04B_compound_screening/resultados_step04B1A/UO2_screening_summary.csv
step04B_compound_screening/resultados_step04B1A/U_dataset_comparison.json
step04B_compound_screening/resultados_step04B1A/SCF_failures_R2.json
```
