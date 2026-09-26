# Step04B2C2-R1 — correção da dependência `spglib`

## Diagnóstico

A execução anterior não chegou a iniciar a relaxação DFT.

O erro ocorreu imediatamente em:

```python
FixSymmetry(...)
```

porque `ase.constraints.FixSymmetry` usa as rotinas de simetrização do ASE,
que dependem de `spglib`.

O traceback foi:

```text
ModuleNotFoundError: No module named 'spglib'
```

O ambiente `structures` já possui `spglib`, mas o cálculo é executado no
ambiente `gpaw`. Como `FixSymmetry` é usado durante a otimização, `spglib`
precisa estar disponível diretamente no ambiente `gpaw`.

## Correção

Este patch:

1. verifica `import spglib` dentro de `.envs/gpaw`;
2. se necessário, instala `spglib` com o micromamba local do projeto;
3. valida a importação;
4. executa o Step04B2C2 original sem alterar o protocolo científico.

Nenhum pacote nativo do sistema é instalado.

## Execução

```bash
bash executar_pacote_upb.sh
```

ou diretamente:

```bash
bash step04B2C2_uvi_gamma_uo3_relax/run-step04B2C2.sh
```

## Log

```text
step04B2C2_uvi_gamma_uo3_relax/saida-step04B2C2-R1.txt
```
