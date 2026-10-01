# UMEH-3, modelo A final: relatório

1º de outubro de 2026. Modelo 3D: https://claude.ai/artifact/Sx1FKkQEhf4qXN1DecbGXC

## 1. O que é

Fone circumaural de fundo fechado, uma concha só para drivers de 40 a 60 mm, sem cola. Fica preso por um gancho atrás
da orelha (estilo KSC75, com mais apoio) e por uma faixa fina na nuca que liga os dois lados. Todas as peças próprias
são impressas em FDM; o resto é comprado pronto.

## 2. Peças

| Peça | Material | Como se obtém | Massa (g) |
|---|---|---|---|
| Concha (placa + copo 31 mm + bucha do gancho + parede da trava + caixa do conector) | PETG grafite | impressa | 25,8 |
| Anel de travamento do driver (baioneta) | PETG bronze | impresso | 1,7 |
| Adaptador do driver, um por tamanho | TPU 95A | impresso | 1,2 |
| Bucha de fricção do gancho | TPU 95A | impressa | 0,1 |
| Palheta atrás da orelha, 14 × 36 mm | TPU 95A | impressa | 1,4 |
| Berço da sela (placa fina + clipe no tubo) | TPU 95A | impresso | 3,3 |
| Presilha da faixa na concha (encaixe) | PETG bronze | impressa | 0,4 |
| Almofada redonda 110 mm, veludo | comprada | 11 [A] |
| Fio do gancho, aço mola (corda de piano) 1,6 mm | comprado | 2,3 |
| Tubo de PTFE 2 × 4 mm no arco + tubo de silicone 4 × 7 mm na perna | comprados | 3,6 |
| Espuma da sela 6 mm (viscoelástica média, ~25 kPa) em capa de veludo | comprada | 0,6 |
| Faixa da nuca: aço mola 1,6 mm em capa de silicone de 5,6 mm | comprada | 7,5 o par |
| Conector 2 pinos 0,78 mm | comprado | 2,7 |
| Espuma frontal PU reticulada 3 mm, fibra de poliéster enchendo a concha | compradas | 0,7 |

Massa por lado, com metade da faixa: 59,0 g + driver. Com drivers típicos [A]: 40 mm 74 g, 50 mm 85 g, 60 mm 99 g.

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
| Puxão de cabo que derruba (N) | 2,4 | 2,4 | 2,4 | > 1 |
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
- Presilha da faixa, placa da almofada: folga de 11 a 14 vezes.
- Vibração: o fone na cabeça vibra em 21 a 56 Hz, longe do ritmo da passada (2 a 3 Hz). O driver não fica isolado da
  concha (a borda de TPU é rígida demais para isso), o que é normal.

## 5. Mudanças desta rodada

- Faixa da nuca refeita: passa por cima da concha e contorna a almofada por fora, sem encostar em nenhuma peça.
- Espuma da sela de 20 para 25 kPa e berço mais leve (3,3 g).
- Trava de giro do gancho: a ponta do fio dobra num braço de 12 mm com pino, que entra num de 9 furos a cada 16°
  (±64°). Para ajustar: puxe o pino, gire, encaixe em outro furo; ajuste fino dobrando o fio.
- Copo 10 mm mais fundo (31 mm) e cheio de fibra de poliéster.
- Ressaltos da baioneta de 9 para 14 mm de largura.

## 6. O que fica em aberto

- Valores [A] (almofada, drivers, atritos, rigidez da pele) são típicos; confirmar com as peças na mão.
- A forma da faixa atrás da cabeça no modelo 3D é aproximada; o ajuste final é dobrando o fio.
- Acabamento visual (caixa do conector, forma do copo) ainda não foi refinado.
- Cálculos pesados ainda não rodados: cargas fora da corrida, corrida longa com 40 e 50 mm, massa máxima de driver.
- Teste real: pesar as peças, medir a pressão no vinco com filme sensível depois de 20 minutos de esteira, e ouvir a
  vedação correndo.
