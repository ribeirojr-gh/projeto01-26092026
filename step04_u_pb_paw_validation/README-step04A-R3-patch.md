# Patch R3 — Step 04A / otimização dos projetores 5f do U

## Diagnóstico do R2

O scan de raio comum produziu:

```text
r = 2.50 Bohr -> erro 5f ligado = 0.087 eV
r = 2.40 Bohr -> erro 5f ligado = 0.092 eV
r = 2.30 Bohr -> erro 5f ligado = 0.099 eV
r = 2.20 Bohr -> erro 5f ligado = 0.108 eV
r = 2.10 Bohr -> erro 5f ligado = 0.114 eV
```

O limite do `generator2.check_all()` é 0.05 eV para estados ligados.
Logo, reduzir o raio foi inequivocamente na direção errada para o canal 5f.

## Estratégia R3

Voltamos ao raio padrão U14:

```text
r_s = r_p = r_d = r_f = 2.5 Bohr
```

e ajustamos somente a representação do canal f.

No GPAW 25.7.0, `-P/--projectors` permite especificar explicitamente
energias em Hartree para projetores não ligados. Exemplo:

```text
5f,0.25f
```

inclui o estado ligado 5f e um projetor f extra a 0.25 Hartree.

O R3 testa primeiro um único projetor extra:

```text
0.00, 0.25, 0.50, 0.75, 1.00 Ha
```

e, se necessário, pares de projetores:

```text
0.00+0.50
0.00+0.25
0.25+0.75
0.00+1.00 Ha
```

Cada candidato precisa passar o `check_all()` padrão em PBE e PBEsol.
`-n/--no-check` permanece proibido.

## Por que isso é melhor do que continuar diminuindo o raio?

O R2 mostrou tendência monotônica de piora do 5f. A própria estrutura do
`generator2` mostra que um token flutuante como `0.5f` define diretamente
a energia do projetor extra. Assim podemos melhorar a flexibilidade do canal
5f sem alterar arbitrariamente todos os raios de aumento.

## Aplicação

Na raiz do projeto:

```bash
rm -rf /tmp/upb_step04A_R3
mkdir -p /tmp/upb_step04A_R3

unzip packages/petrobras_upb_step04A_R3_patch.zip \
    -d /tmp/upb_step04A_R3

cp -a /tmp/upb_step04A_R3/petrobras_upb_project/. .
rm -rf /tmp/upb_step04A_R3
```

Depois:

```bash
chmod +x step04_u_pb_paw_validation/*.sh
./step04_u_pb_paw_validation/run-step04A.sh
```

## Saídas importantes

```text
step04_u_pb_paw_validation/saida-step04A.txt
resultados_step04A/u_projector_scan_R3.csv
resultados_step04A/u_projector_selection_R3.json
resultados_step04A/decisao_step04A.json
```

Se nenhum candidato passar, não force o PAW. Compartilhe o log e o CSV;
o próximo passo será um ajuste mais fino por canal (raio f e energia dos
projetores) ou uma estratégia de referência externa/all-electron.
