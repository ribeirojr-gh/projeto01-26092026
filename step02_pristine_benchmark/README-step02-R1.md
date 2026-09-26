# Step 02-R1 — Correção e retomada

## Diagnóstico

O Step 02A terminou corretamente para calcita e dolomita.

O Step 02B falhou antes do primeiro cálculo GPAW com:

```text
ModuleNotFoundError: No module named 'config_step02'
```

A causa é o launcher:

```bash
gpaw python script.py
```

que executa o arquivo via `runpy` e não garante que o diretório do script
seja acrescentado ao `sys.path` da mesma forma que `python script.py`.

## Correções

1. `02A`, `02B` e `02C` acrescentam explicitamente seu próprio diretório
   ao `sys.path`.
2. Os wrappers exportam `PYTHONPATH` com o diretório do Step 02.
3. O GPAW recebe o caminho absoluto do script.
4. O Step 02B grava um checkpoint depois de cada ponto concluído e reutiliza
   esses pontos se a execução for interrompida.
5. `run-step02-R1-resume.sh` retoma diretamente no Step 02B e NÃO repete
   CHGNet/MACE já concluídos.

## Aplicação

Descompacte este pacote sobre a raiz do projeto, sobrescrevendo os arquivos
do diretório:

```text
step02_pristine_benchmark/
```

Não é necessário alterar ou recriar os ambientes Python.

## Retomada recomendada

Como o seu Step 02A já terminou, execute:

```bash
chmod +x step02_pristine_benchmark/*.sh
./step02_pristine_benchmark/run-step02-R1-resume.sh
```

O log será:

```text
step02_pristine_benchmark/saida-step02-R1.txt
```

## Reexecução completa

Somente se quiser repetir CHGNet/MACE:

```bash
./step02_pristine_benchmark/run-step02.sh
```

## Arquivos a enviar

```text
saida-step02-R1.txt
resultados_mlip/resumo_mlip.csv
resultados_gpaw/convergencia_gpaw.csv
resultados_gpaw/parametros_recomendados_gpaw.csv
resumo_step02/resumo_step02.txt
```
