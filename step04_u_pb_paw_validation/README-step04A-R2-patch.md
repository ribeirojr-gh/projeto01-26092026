# Patch R2 — Step 04A / Uranium PAW

## Motivo

O dataset default `U14` do GPAW 25.7.0 usa raio de 2.5 Bohr, mas na execução
do projeto o `check_all()` reprovou o estado ligado 5f:

```text
5f AE = -3.333 eV
5f PS = -3.246 eV
erro = +0.087 eV
Error in bound f-states!
```

O `check_all()` do GPAW usa tolerância padrão de 0.05 eV para estados
ligados. Portanto a reprovação é real e não deve ser ignorada.

## O que a R2 faz

A R2 NÃO usa:

```text
-n
--no-check
```

Em vez disso, faz uma varredura controlada do raio PAW comum:

```text
2.50
2.40
2.30
2.20
2.10 Bohr
```

Para cada raio:

1. gera U/PBE, 14 elétrons de valência, scalar-relativistic;
2. exige que o `check_all()` padrão passe;
3. se PBE passar, testa U/PBEsol no mesmo raio;
4. escolhe o MAIOR raio comum que passe para ambos.

Escolher o maior raio aceitável evita tornar o PAW desnecessariamente duro.

Se nenhum raio passar, a etapa para. Não é permitido forçar um PAW inválido.

## Outro ajuste

`04A_load_test.py` foi corrigido: `SetupData()` já lê o XML por padrão e não
deve executar `read_xml()` novamente.

## Aplicação

Na raiz do projeto:

```bash
rm -rf /tmp/upb_step04A_R2
mkdir -p /tmp/upb_step04A_R2

unzip packages/petrobras_upb_step04A_R2_patch.zip \
    -d /tmp/upb_step04A_R2

cp -a /tmp/upb_step04A_R2/petrobras_upb_project/. .
rm -rf /tmp/upb_step04A_R2
```

Depois:

```bash
chmod +x step04_u_pb_paw_validation/*.sh
./step04_u_pb_paw_validation/run-step04A.sh
```

## Novas saídas relevantes

```text
resultados_step04A/u_radius_scan.csv
resultados_step04A/u_radius_selection.json
resultados_step04A/decisao_step04A.json
saida-step04A.txt
```

Se todos os raios falharem, compartilhar o `saida-step04A.txt` e
`u_radius_scan.csv`. Nesse caso faremos uma otimização explícita de projetores
e/ou raios por canal em vez de desativar o gate.
