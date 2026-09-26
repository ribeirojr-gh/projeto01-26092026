# Step04B1B1-R2 — correção do restart/tightening no GPAW 25.7.0

## Diagnóstico

A execução anterior mostrou dois eventos distintos:

1. `Ueff=2.5 eV, domínio kz` falhou genuinamente na pré-convergência
   mesmo após 701 e 1001 ciclos.
2. `Ueff=2.5 eV, domínio kx` conseguiu chegar ao estágio de tightening,
   mas a execução parou por erro de API:

```text
ValueError: Please use new(...) instead of set(...)
```

O erro era causado por:

```python
calc.set(..., mixer=..., maxiter=...)
```

No GPAW 25.7.0, `calc.set()` aceita alterações in-place apenas para um
subconjunto de parâmetros. `mixer` e `maxiter` não fazem parte desse
subconjunto.

A alternativa `calc.new(...)` também não é adequada neste ponto porque a
API do GPAW documenta que `new()` cria um novo calculador sem reutilizar
densidade nem wavefunctions — justamente o estado eletrônico que queremos
preservar do restart.

## Correção R2

Após ler o `.gpw`, a etapa tight agora altera somente:

```python
occupations={"name": "fermi-dirac", "width": 0.05}
eigensolver={"name": "dav", "niter": 5}
convergence={
    "energy": 5.0e-4,
    "density": 5.0e-6,
    "eigenstates": 5.0e-8,
    "bands": "occupied",
}
```

O mixer e `maxiter` permanecem os mesmos da pré-convergência, preservando
densidade e wavefunctions do restart.

## Interpretação do caso kz em Ueff=2.5 eV

A falha do domínio `kz` é mantida como resultado científico válido por
enquanto. Ela não será mascarada aumentando indefinidamente o número de
iterações. O gate exige reprodutibilidade entre os três domínios; portanto,
uma falha persistente já é informação relevante sobre a estabilidade
eletrônica desse `Ueff`.

## Execução

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04B1B_uo2_reproducibility/saida-step04B1B1.txt
step04B1B_uo2_reproducibility/resultados_step04B1B1/decisao_step04B1B1.json
step04B1B_uo2_reproducibility/resultados_step04B1B1/UO2_domain_reproducibility_B1B1.csv
```
