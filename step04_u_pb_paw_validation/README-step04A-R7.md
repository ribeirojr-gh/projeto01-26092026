# Step04A-R7 — correção de importação sob `gpaw python`

## Erro observado no R6

O R6 corrigiu a passagem de argumentos, mas o GPAW executa o script com
`runpy.run_path()`. Nessa situação, o diretório de
`04A_pb_singlepoint.py` não foi inserido automaticamente em `sys.path`.

O erro foi:

```text
ModuleNotFoundError: No module named 'config_step04'
```

## Correção

A R7 insere explicitamente:

```python
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
```

antes de:

```python
from config_step04 import ECUT, KGRID_PB, PB_A_REFERENCE
```

Nenhum PAW é regenerado. O `run-step04A.sh` da R6 detectará os artefatos
do R5 e retomará diretamente os gates computacionais.

## Execução

Depois de baixar o ZIP, na raiz do projeto:

```bash
bash executar_pacote_upb.sh
```

## Saída a compartilhar

```text
step04_u_pb_paw_validation/saida-step04A.txt
```

Se concluir:

```text
step04_u_pb_paw_validation/resultados_step04A/decisao_step04A.json
step04_u_pb_paw_validation/resultados_step04A/Pb_PBE_official.json
step04_u_pb_paw_validation/resultados_step04A/Pb_PBE_generated.json
step04_u_pb_paw_validation/resultados_step04A/Pb_PBEsol_generated.json
```
