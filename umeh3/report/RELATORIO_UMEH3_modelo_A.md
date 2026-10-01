# UMEH-3, modelo A final: relatório

1º de outubro de 2026. Modelo 3D: https://claude.ai/artifact/Sx1FKkQEhf4qXN1DecbGXC

## 1. O que é

Fone circumaural de fundo fechado, uma concha só para drivers de 40 a 60 mm, sem cola. Fica preso por um gancho atrás
da orelha (estilo KSC75, com mais apoio) e por uma faixa fina na nuca que liga os dois lados. Todas as peças próprias
são impressas em FDM; o resto é comprado pronto.

## 2. Peças

| Peça | Material | Como se obtém | Massa (g) |
|---|---|---|---|
| Concha (placa + copo 31 mm + bucha do gancho + parede da trava + caixa do conector + canal da faixa) | PETG grafite | impressa | 26,1 |
| Anel de travamento do driver (baioneta) | PETG bronze | impresso | 1,7 |
| Adaptador do driver, um por tamanho | TPU 95A | impresso | 1,2 |
| Bucha de fricção do gancho | TPU 95A | impressa | 0,1 |
| Palheta atrás da orelha, 14 × 36 mm | TPU 95A | impressa | 1,4 |
| Berço da sela (placa fina + clipe no tubo) | TPU 95A | impresso | 3,3 |
| Almofada redonda 110 mm (furo ~68 mm), veludo | comprada | 11 [A] |
| Fio do gancho, aço mola (corda de piano) 1,6 mm | comprado | 2,3 |
| Tubo de PTFE 2 × 4 mm no arco + tubo de silicone 4 × 7 mm na perna | comprados | 3,6 |
| Espuma da sela 6 mm (viscoelástica média, ~25 kPa) em capa de veludo | comprada | 0,6 |
| Faixa da nuca: aço mola 1,8 mm (sem espiras) em tubo de silicone 2 × 4 mm | comprada | 12,5 o par |
| Conector 2 pinos 0,78 mm | comprado | 2,7 |
| Espuma frontal PU reticulada 3 mm, fibra de poliéster enchendo a concha | compradas | 0,7 |

Massa por lado, com metade da faixa: 61,3 g + driver. Com drivers típicos [A]: 40 mm 76 g, 50 mm 87 g, 60 mm 101 g.
(A conta anterior, 74/85/99 g, pesava a faixa por baixo: o arame calculado é de 1,8 mm e a capa grossa não entrava.
Com o tubo de 4 mm a faixa ficou 6 g mais leve do que seria com a capa de 5,8 mm.)

## 3. Como foi verificado

Mesmo modelo de contato do UMEH-2: almofada em 16 setores, sela do gancho em dois apoios na raiz da orelha, lado da
hélice, sulco atrás da orelha, lóbulo, aperto da palheta e a faixa como mola com pré-carga de 2 N. O fio do gancho é
flexível (calculado). Atrito: veludo/pele 0,5, silicone/pele 0,7 [A].

Corrida na esteira (5400 casos por tamanho): cabeça subindo até +1,5 g no impacto do pé, queda livre (-1 g) na fase de
voo, ±0,6 g para frente e para trás, ±0,4 g para os lados, inclinação até 15°, aceleração angular de corrida, e cabo
puxando 1 N em qualquer direção até 80° da vertical. "Solta" quer dizer escorregar ou mover mais de 3 mm ou 5°.

Corrida longa: todos os casos aplicados e retirados, passada após passada, até o fone se acomodar (é aí que ele vai
ficar depois de alguns minutos correndo). Depois mais uma volta completa, contando quantas passadas o deslocam.

## 4. Resultados

| Driver | 40 mm | 50 mm | 60 mm | Meta |
|---|---|---|---|---|
| Casos de corrida em que solta | 0 | 0 | 0 | 0 |
| Vinco da orelha parado (kPa) | 0,8 | 0,9 | 1,0 | 4 |
| Vinco a cada passada, pico (kPa) | 6,4 | 7,2 | 8,2 | 8 |
| Puxão de cabo que derruba (N) | 2,4 | 2,4 | 2,6 | > 1 |
| Vinco depois de correr um tempo (kPa) | | | 3,8 | 4 |
| Passadas que deslocam, depois de acomodado | | | 0 de 1080 | 0 |

A corrida longa foi rodada só com 60 mm, o caso mais pesado. Com 60 mm o vinco a cada passada fica 2% acima da
meta de 8 kPa (que já é um valor de conforto assumido); veio dos 6 g a mais da trava do gancho e do copo mais fundo.

### Atrito do gancho na orelha (60 mm, depois de acomodado)

| Contato | Passadas em que escorrega | Escorregamento médio |
|---|---|---|
| Sela na raiz da orelha | 1% | menos de 0,01 mm |
| Lado da sela na hélice | todas | 1,0 mm (força ~0,02 N) |
| Perna no sulco atrás da orelha | 2% | menos de 0,01 mm |
| Ponta sob o lóbulo | não encosta enquanto corre | |

A sela fica parada na raiz da orelha, que é onde o peso apoia, então ali não há esfregação. O lado da sela roça a
hélice cerca de 1 mm por passada, mas com força muito pequena (uns 2 gramas), em veludo. A almofada escorrega em 77%
das passadas (0,15 mm em média), o que é normal num fone sobre a orelha.

O que reduziu o atrito em relação ao primeiro desenho: a sela larga de espuma em veludo no lugar do tubo de silicone
(menos atrito e menos pressão), o tubo de PTFE dentro do berço (o gancho gira sem arrastar a pele quando você ajusta)
e a faixa da nuca, que tira do gancho quase todo o puxão do cabo.

### Vedação acústica (fundo fechado, 60 mm)

Parado, a almofada encosta em toda a volta (16 de 16 setores). Correndo, a almofada levanta um pouco em 72% dos
casos: na metade deles menos de 0,35 mm, em 1 de cada 10 mais de 1,6 mm em metade da volta. Com abertura leve o grave
quase não muda; com a forte cai bastante por um instante (o grave "respira" no ritmo da corrida). Decisão: manter a
faixa de 2 N.

### Acústica do fundo fechado (valores de driver típicos [A])

| Driver | Volume atrás (cm³) | Pico de médios acima do nível em 100 Hz |
|---|---|---|
| 40 mm | 60 | +2,2 dB perto de 390 Hz |
| 50 mm | 55 | +5,5 dB perto de 575 Hz |
| 60 mm | 47 | +8,7 dB perto de 760 Hz |

Com o copo raso do primeiro desenho os picos eram +6,4, +11,4 e +16,6 dB. O grave é plano até 30 Hz com a vedação
fechada. O valor real depende dos dados do driver; com eles na mão dá para afinar a fibra.

### Tolerâncias, vibração e resistência

- Encaixe sem cola: o flap do adaptador fica com 0,05 a 0,55 mm de aperto em 99,7% das impressões (aceita 0,05 a 0,9).
- Bucha do gancho: interferência de 0 a 0,3 mm conforme a impressora; imprimir 3 buchas (furo 1,35, 1,45 e 1,55 mm) e
  ficar com a que desliza firme.
- Trava de giro: o giro do gancho na corrida (até 67 N·mm, 4 vezes o que a bucha segura) vai para o pino; furo com
  folga de 14 vezes, fio com 9 vezes.
- Fio do gancho: folga de 8 vezes na corrida; abre uns 10 mm para trás ou para baixo antes de entortar.
- Baioneta (ressaltos de 14 mm): segura 440 g de desaceleração com driver de 60 mm e 1100 g com 40 mm.
- Canal da faixa na tampa e placa da almofada: folga de 8 vezes ou mais (detalhe em strength.json).
- Vibração: o fone na cabeça vibra em 21 a 56 Hz, longe do ritmo da passada (2 a 3 Hz). O driver não fica isolado da
  concha (a borda de TPU é rígida demais para isso), o que é normal.

### Queda, faixa ao colocar, fadiga e calor (studies/durability.py)

| Verificação | Resultado |
|---|---|
| Queda de 1 m de frente, sobre a almofada | a espuma amortece: 200 a 330 g de desaceleração; a baioneta segura (folga 1,3 com 60 mm no pior caso, 2 a 6 nos outros) |
| Queda de costas, desenho anterior (presilha no meio da tampa) | a pancada concentrava num ponto de uma tampa plana de 1,2 mm: pelo cálculo trincaria (aguenta 0,15 J, a queda dá 0,6 a 0,8 J). Engrossar a tampa quase não ajuda (2 mm: 0,25 J) |
| Queda de costas, desenho refinado | nada fica em pé na tampa: o tubo da faixa (0,8 mm saliente, silicone) encosta primeiro e a tampa inteira apoia no chão; as paredes recebem a pancada em compressão |
| Driver contra o encosto traseiro na queda de costas | folga 2,8 (60 mm) a 6,7 (40 mm) |
| Queda de quina (borda arredondada) | não dá para calcular de forma confiável (o PETG amassa antes); decidir no teste de queda |
| Faixa aberta para passar pela cabeça | abre ~50 mm por lado além da cabeça maior antes de entortar; folga 1,65 ao vestir e 2,4 em fadiga (10 mil vezes) |
| Fadiga por passada (10 milhões) | fio do gancho 5,0; dobras da trava 4,4; furo da trava 5,9; fio da faixa 3,7 |
| Encaixe do driver depois de envelhecer e de um carro quente (TPU perde 1/3 da pressão) | o driver só começa a bater com 1,8 g de lado (60 mm, pior impressão); na corrida são 0,4 g |
| Bucha do gancho depois de relaxar | ainda segura 6,5 vezes o que a corrida pede |
| Calor | PETG amolece a 80 °C: banco do carro (até ~60 °C) ok; não deixar no painel ao sol |

### Cargas fora da corrida (categorias do UMEH-2)

| Categoria | 40 mm | 50 mm | 60 mm | Meta de pressão |
|---|---|---|---|---|
| 1 g normal (cabeça inclinada até 45°, cabo 0,5 N): soltou | 0% | 0% | 0% | |
| 1 g normal: vinco, pior caso | 2,9 kPa | 3,3 kPa | 3,8 kPa | 4 kPa |
| 2 g (andar rápido, virar a cabeça, cabo 1 N): soltou | 0% | 0% | 0% | |
| 2 g: vinco, pior caso | 5,5 kPa | 6,2 kPa | 7,3 kPa | 8 kPa |
| 3 g severo (pulo, tranco, cabo 2 N): soltou | 3,2% | 4,7% | 8,3% | |
| 3 g severo: vinco / ponta sob o lóbulo | 11 / 19 kPa | 12 / 20 kPa | 12 / 24 kPa | 8 kPa |
| 5 g acidental com cabo enganchado (20 N) | sai sempre | sai sempre | sai sempre | |

Parado, andando e correndo o fone fica preso e as pressões ficam dentro das metas. Em trancos fortes (3 g, cabo
puxando 2 N) ele se desloca em 3 a 8% dos casos e a ponta do gancho aperta o lóbulo com força por um instante. Com o
cabo enganchado de verdade o fone sai da cabeça, o que é o desejado: ele solta antes de quebrar algo ou machucar.

### Massa máxima de driver (esteira, sem soltar)

| Tamanho | Driver típico | Máximo que segura sem soltar | Máximo dentro da meta de conforto (vinco 8 kPa) |
|---|---|---|---|
| 40 mm | 15 g | 45 g | ~33 g |
| 50 mm | 26 g | 46 g | ~35 g |
| 60 mm | 40 g | 55 g | ~38 g |

O limite de conforto é estimado entre os pontos calculados. Ou seja: o fone segura drivers bem mais pesados que os
típicos, mas acima de ~35 g o vinco da orelha passa da meta de conforto a cada passada.

## 5. Mudanças desta rodada

- Faixa da nuca refeita: passa por cima da concha e contorna a almofada por fora, sem encostar em nenhuma peça.
- Espuma da sela de 20 para 25 kPa e berço mais leve (3,3 g).
- Trava de giro do gancho: a ponta do fio dobra num braço de 12 mm com pino, que entra num de 9 furos a cada 16°
  (±64°). Para ajustar: puxe o pino, gire, encaixe em outro furo; ajuste fino dobrando o fio.
- Copo 10 mm mais fundo (31 mm) e cheio de fibra de poliéster.
- Ressaltos da baioneta de 9 para 14 mm de largura.

### Refino final do desenho

- Presilha da faixa removida: a ponta da faixa encaixa num canal na tampa (perfil fechadura, entra por pressão) com a
  ponta do arame dobrada num furo cego. Tampa lisa, uma peça a menos, e a queda de costas não bate mais num ponto.
- Faixa com arame de 1,8 mm sem espiras (o que os cálculos sempre usaram) e tubo de silicone 2 × 4 mm, mais fino e leve.
- Caixa do conector com cantos arredondados, parede da trava e topo da bucha do gancho com bordas suavizadas.
- Acabamento comercial: logo UMEH em relevo de 0,4 mm na tampa e a letra do lado (L/R), em bronze. Na impressão,
  pausar e trocar o filamento na camada onde as letras começam (a tampa é o topo da peça). Um friso de 0,4 mm
  emoldura a tampa e o copo encontra a placa com um filete côncavo de 3 mm. No lado esquerdo as letras saem
  espelhadas no CAD de propósito, para lerem certo depois do espelhamento.
- A corrida com 60 mm foi refeita com a faixa nova: 0 de 5400 soltam, vinco 8,2 kPa, puxão que derruba 2,6 N.

### Almofada real e compras no Brasil

A almofada de 110 mm encontrada à venda tem furo de ~68 mm e 23 mm de altura (o cálculo assumia 60 e 25 mm). Refiz a
corrida com 60 mm e furo de 68 mm: 0 de 5400 soltam, vinco a cada passada 8,4 kPa, puxão que derruba 2,6 N
(studies/pad68_check.py). A diferença de altura é compensada pelo ajuste da bucha. Onde comprar cada peça no Brasil:
docs/02_lista_de_compras.md.

## 6. O que fica em aberto

- Valores [A] (almofada, drivers, atritos, rigidez da pele) são típicos; confirmar com as peças na mão.
- A forma da faixa atrás da cabeça no modelo 3D é aproximada; o ajuste final é dobrando o fio.
- Acabamento visual (caixa do conector, forma do copo) ainda não foi refinado.
- Corrida longa só foi calculada com 60 mm (decisão: não precisa com 40 e 50).
- Teste de queda: imprimir uma concha e soltar 10 vezes de 1 m em piso de cerâmica (frente, costas, quinas). Se a
  quina trincar, a saída é parede de 1,6 mm (+~2 g por lado).
- Teste real: pesar as peças, medir a pressão no vinco com filme sensível depois de 20 minutos de esteira, e ouvir a
  vedação correndo.
