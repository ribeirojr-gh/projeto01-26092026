# Step04A-R4 — semicore de U

## Diagnóstico que motivou esta revisão

O R3 variou a energia e o número de projetores f extras, mas o erro do estado
ligado 5f permaneceu praticamente inalterado (~0.087–0.088 eV), acima do
limite interno de 0.05 eV do `generator2.check_all()`.

Isso indica que o problema não está na energia do projetor f não ligado.

## Estratégia R4

A documentação do GPAW recomenda incluir estados semicore quando se busca um
dataset mais preciso.

O R4 testa:

### U24

Valência:

```text
5d10 6s2 6p6 5f3 6d1 7s2
```

Projetores:

```text
6s,7s,6p,7p,5d,6d,d,5f,f,G
```

### U32

Valência:

```text
5s2 5p6 5d10 6s2 6p6 5f3 6d1 7s2
```

Projetores:

```text
5s,6s,7s,5p,6p,7p,5d,6d,d,5f,f,G
```

Cada partição é testada com raios uniformes:

```text
2.50
2.30
2.20 Bohr
```

Todos os candidatos precisam passar pelo `check_all()` padrão em PBE e
PBEsol. O script não usa `-n/--no-check`.

Se mais de um candidato passar, a seleção automática prioriza:

1. menor raio;
2. para o mesmo raio, menor número de elétrons de valência.

Isso reduz a chance de sobreposição excessiva das regiões PAW em ligações
U-O curtas, sem escolher desnecessariamente um PAW de 32 elétrons quando um
de 24 elétrons for suficiente.

## Execução com o launcher genérico

Depois de baixar o ZIP, estando na raiz do projeto:

```bash
bash executar_pacote_upb.sh
```

O launcher localiza o pacote mais recente, copia para `packages/`,
descompacta, instala o patch, corrige permissões e executa `run-step04A.sh`.

## Saídas principais

```text
step04_u_pb_paw_validation/saida-step04A.txt
step04_u_pb_paw_validation/resultados_step04A/u_semicore_scan_R4.csv
step04_u_pb_paw_validation/resultados_step04A/u_semicore_selection_R4.json
step04_u_pb_paw_validation/resultados_step04A/decisao_step04A.json
```

Se nenhum candidato passar, o R4 para sem forçar PAWs. Nesse caso a próxima
decisão não será outro scan arbitrário: avaliaremos local potential/pseudization
ou migração para um PAW de U externo validado/all-electron reference.
