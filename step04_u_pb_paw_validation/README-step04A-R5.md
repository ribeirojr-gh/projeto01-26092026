# Step04A-R5 — pseudização do PAW de U

## Diagnóstico acumulado

As revisões anteriores mostraram:

- R2: reduzir `rcut` de 2.50 para 2.10 Bohr piorou o erro do 5f ligado;
- R3: variar a energia/número dos projetores f extras não resolveu;
- R4: incluir 5d (U24) ou 5s/5p/5d (U32) como semicore não resolveu.

No R4, o erro do 5f permaneceu ~0.087 eV em 2.50 Bohr e aumentou para
~0.099/0.108 eV em raios menores.

## Motivação do R5

O `generator2` do GPAW suporta duas famílias de pseudização de ondas:

```text
poly
nc
```

No código, `nc` usa `pseudize_normalized()`, enquanto `poly` é a opção
padrão. Como o canal 5f mostra grande diferença de norma no dataset padrão,
este é um teste controlado e diretamente ligado à causa provável.

## Scan

Mantemos o U14 original:

```text
projectors = 6s,7s,6p,7p,6d,d,5f,f,G
r_s = r_p = r_d = r_f = 2.5 Bohr
```

e testamos:

```text
poly,4
poly,6
poly,8
nc,4
nc,6
nc,8
```

Todos precisam passar o `check_all()` padrão em PBE e PBEsol.

`-n/--no-check` continua proibido.

## Critério de parada

Este é o último scan interno do `generator2` planejado para U.

Se todos os candidatos falharem, o workflow NÃO continuará com ajustes
arbitrários. A estratégia será alterada para referência externa/all-electron
validada para U, preservando o GPAW para a matriz Ca-Mg-C-O e Pb quando
metodologicamente adequado.

## Execução

Com o launcher genérico já instalado na raiz do projeto, após baixar o ZIP:

```bash
bash executar_pacote_upb.sh
```

## Saídas

```text
step04_u_pb_paw_validation/saida-step04A.txt
step04_u_pb_paw_validation/resultados_step04A/u_pseudization_scan_R5.csv
step04_u_pb_paw_validation/resultados_step04A/u_pseudization_selection_R5.json
step04_u_pb_paw_validation/resultados_step04A/decisao_step04A.json
```
