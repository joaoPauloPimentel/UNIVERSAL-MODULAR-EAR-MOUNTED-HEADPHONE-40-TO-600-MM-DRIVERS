# UMEH-3, modelo A final: relatório

1º de outubro de 2026. Modelo 3D: https://claude.ai/artifact/Sx1FKkQEhf4qXN1DecbGXC

## 1. O que é

Fone circumaural de fundo fechado, uma concha só para drivers de 40 a 60 mm, sem cola. Fica preso por um gancho atrás
da orelha (estilo KSC75, com mais apoio) e por uma faixa fina na nuca que liga os dois lados. Todas as peças próprias
são impressas em FDM; o resto é comprado pronto.

## 2. Peças

| Peça | Material | Como se obtém | Massa (g) |
|---|---|---|---|
| Concha (placa + copo + bucha do gancho + caixa do conector) | PETG grafite | impressa | 20,1 |
| Anel de travamento do driver (baioneta) | PETG bronze | impresso | 1,7 |
| Adaptador do driver, um por tamanho | TPU 95A | impresso | 1,2 |
| Bucha de fricção e tampinha do gancho | TPU 95A / PETG | impressas | 0,2 |
| Palheta atrás da orelha, 14 × 36 mm | TPU 95A | impressa | 1,4 |
| Berço da sela (placa fina + clipe no tubo) | TPU 95A | impresso | 3,3 |
| Presilha da faixa na concha (encaixe) | PETG bronze | impressa | 0,4 |
| Almofada redonda 110 mm, veludo | comprada | 11 [A] |
| Fio do gancho, aço mola (corda de piano) 1,6 mm | comprado | 2,3 |
| Tubo de PTFE 2 × 4 mm no arco + tubo de silicone 4 × 7 mm na perna | comprados | 3,6 |
| Espuma da sela 6 mm (viscoelástica média, ~25 kPa) em capa de veludo | comprada | 0,6 |
| Faixa da nuca: aço mola 1,6 mm em capa de silicone de 5,6 mm | comprada | 7,5 o par |
| Conector 2 pinos 0,78 mm | comprado | 2,7 |
| Espuma frontal PU reticulada 3 mm, fibra de poliéster na concha | compradas | 0,4 |

Massa por lado, com metade da faixa: 52,8 g + driver. Com drivers típicos [A]: 40 mm 68 g, 50 mm 79 g, 60 mm 93 g.

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
| Vinco da orelha parado (kPa) | 0,7 | 0,8 | 0,9 | 4 |
| Vinco a cada passada, pico (kPa) | 6,2 | 6,9 | 7,7 | 8 |
| Puxão de cabo que derruba (N) | 2,7 | 2,8 | 2,8 | > 1 |
| Vinco depois de correr um tempo (kPa) | | | 3,9 | 4 |
| Passadas que deslocam, depois de acomodado | | | 0 de 1080 | 0 |

A corrida longa foi rodada só com 60 mm, o caso mais pesado.

### Atrito do gancho na orelha (60 mm, depois de acomodado)

| Contato | Passadas em que escorrega | Escorregamento médio |
|---|---|---|
| Sela na raiz da orelha | 1% | menos de 0,01 mm |
| Lado da sela na hélice | todas | 1,0 mm |
| Perna no sulco atrás da orelha | 2% | menos de 0,01 mm |
| Ponta sob o lóbulo | não encosta enquanto corre | |

A sela fica parada na raiz da orelha, que é onde o peso apoia, então ali não há esfregação. O lado da sela roça a
hélice cerca de 1 mm por passada, mas com força muito pequena (uns 2 gramas), em veludo. A almofada escorrega em 77%
das passadas (0,15 mm em média), o que é normal num fone sobre a orelha.

O que reduziu o atrito em relação ao primeiro desenho: a sela larga de espuma em veludo no lugar do tubo de silicone
(menos atrito e menos pressão), o tubo de PTFE dentro do berço (o gancho gira sem arrastar a pele quando você ajusta)
e a faixa da nuca, que tira do gancho quase todo o puxão do cabo.

### Vedação acústica (fundo fechado, 60 mm)

Parado, a almofada encosta em toda a volta (16 de 16 setores), com 0,46 kPa em média e 2,2 N de força. Correndo, no
pico de algumas passadas parte da almofada desencosta por um instante:

| Faixa | Almofada | Passadas com abertura momentânea |
|---|---|---|
| 2 N | típica (20 kPa) | 56% |
| 2,5 N | macia (10 kPa) | 41% |
| 3 N | típica (20 kPa) | 34% |

Na prática: andando ou parado, a vedação é completa. Correndo, o grave deve "respirar" um pouco a cada passada. Uma
faixa mais firme ou uma almofada mais macia reduzem isso, mas não eliminam; eliminar pediria um aperto de fone de
estúdio (4 a 6 N), que pesa mais e cansa.

## 5. Mudanças desta rodada

- Faixa da nuca refeita: passa por cima da concha e contorna a almofada por fora. Sem interferência com nenhuma peça
  (folga medida contra as malhas); a presilha agora segura a capa de silicone por encaixe.
- Espuma da sela de 20 para 25 kPa: com a mais macia, no impacto do pé com a cabeça inclinando, o fone afundava pouco
  mais de 3 mm e cerca de 4% das passadas o deslocavam depois de acomodado. Com 25 kPa, nenhuma.
- Berço da sela mais leve (4,2 para 3,3 g): placa fina sob a espuma e um clipe em volta do tubo do fio.

## 6. O que fica em aberto

- Valores [A] (almofada, drivers, atritos, rigidez da pele) são típicos; confirmar com as peças na mão.
- A forma da faixa atrás da cabeça no modelo 3D é aproximada; o ajuste final é dobrando o fio.
- Acabamento visual (caixa do conector, forma do copo) ainda não foi refinado.
- Teste real: pesar as peças, medir a pressão no vinco com filme sensível depois de 20 minutos de esteira, e ouvir a
  vedação correndo.
