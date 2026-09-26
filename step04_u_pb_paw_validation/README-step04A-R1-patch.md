# Patch R1 — Step 04A

Corrige exclusivamente a auditoria inicial do Step 04A.

## Erro corrigido

O GPAW 25.7.0 retorna entradas de `gpaw.setup_paths` como objetos
`pathlib.Path`/`PosixPath`. A versão anterior tentou gravar diretamente:

```python
"setup_paths": list(setup_paths)
```

em JSON, causando:

```text
TypeError: Object of type PosixPath is not JSON serializable
```

A R1 converte explicitamente todos os caminhos para `str`.

## Aplicação

Na raiz do projeto:

```bash
rm -rf /tmp/upb_step04A_R1
mkdir -p /tmp/upb_step04A_R1

unzip packages/petrobras_upb_step04A_R1_patch.zip \
    -d /tmp/upb_step04A_R1

cp -a /tmp/upb_step04A_R1/petrobras_upb_project/. .
rm -rf /tmp/upb_step04A_R1
```

Depois execute novamente:

```bash
./step04_u_pb_paw_validation/run-step04A.sh
```

Não é necessário apagar resultados. A falha anterior ocorreu antes da geração
dos PAWs e dos cálculos.
