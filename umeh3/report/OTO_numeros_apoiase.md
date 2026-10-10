# OTO: números do projeto para a campanha (Apoia-se)

Data: 10/10/2026. Todos os valores abaixo são **calculados** (simulação e contas do projeto), não medidos em protótipo físico, exceto onde estiver escrito "medido". Os cálculos usam valores típicos para almofada, drivers e atrito, marcados com [A] nos relatórios. Fonte: `umeh3/results/` (versão oval "AO") e `umeh3/report/RELATORIO_UMEH3_modelo_A.md`.

## 1. Peso (calculado, versão oval)

| Driver | Um lado montado (com metade da faixa) | Par, sem cabo |
|---|---|---|
| 40 mm (15 g) | cerca de 74 g | cerca de 149 g |
| 50 mm (26 g) | cerca de 84 g | cerca de 169 g |
| 60 mm (40 g) | cerca de 97 g | cerca de 194 g |

Como chegou: concha 22,4 g, anel e peças pequenas de PETG ~5 g, gancho e berço da sela ~11 g, almofada oval 10 g, soquete e fios 2,3 g, assento de EVA 0,3 a 1 g, mais o driver, mais a faixa da nuca (arame de inox 1,8 mm em tubo de silicone, cerca de 12 g a faixa inteira, ou 6 g por lado).

O que pode mudar: a almofada de 10 g e os drivers de 15/26/40 g são valores típicos. Almofada de couro e drivers mais pesados somam grama por grama. O cabo não entra na conta. Peso real só depois de pesar o protótipo (roteiro em `umeh3/docs/04_testes.md`).

Driver mais pesado que o previsto: o cálculo diz que o fone ainda segura na esteira até cerca de 45 g (40 mm), 51 g (50 mm) e 50 g (60 mm) por driver. Para ficar confortável, o ideal é ficar abaixo de ~35 g.

## 2. Firmeza em movimento (simulação)

Esteira (caminhar e correr), 5.400 combinações de movimento da cabeça, balanço do cabo e inclinação, com a faixa de 2 N por lado:

| Driver | Soltou | Pressão máxima na raiz da orelha por passada | Deslocamento máximo |
|---|---|---|---|
| 40 mm | 0 de 5.400 | 6,1 a 6,4 kPa | cerca de 2,1 mm |
| 50 mm | 0 de 5.400 | 7,2 a 7,3 kPa | cerca de 2,4 mm |
| 60 mm | 0 de 5.400 | 8,2 a 8,7 kPa | cerca de 2,6 a 2,8 mm |

Foi rodado com três arames diferentes (corda de piano 1,6 mm, inox 1,8 mm reto na versão redonda, e inox no modelo oval com a faixa que o programa dimensiona sozinho). Em todos, nenhum caso soltou. O limite de conforto usado no projeto é 8 kPa por passada: o de 60 mm fica no limite ou um pouco acima, o de 40 mm e o de 50 mm ficam abaixo. Depois de muitas passadas, a pressão que fica sustentada na raiz (60 mm) é de cerca de 4,4 kPa, perto do alvo de 4 kPa.

Puxão no cabo: o fone aguenta no mínimo cerca de 2,3 N antes de sair do lugar.

Cargas maiores (simulação do modelo oval, com arame de corda de piano; 5.610 a 21.000 casos por linha):

| Carga | 40 mm | 50 mm | 60 mm |
|---|---|---|---|
| 1 g (uso normal) | 0 % solta | 0 % solta | 0 % solta |
| 2 g (movimento forte) | 0 % solta | 0 % solta | 0 % solta |
| 3 g (sacudida severa) | 1,3 % solta | 3,4 % solta | 7,6 % solta |
| 5 g ou puxão de 20 N (acidente) | sempre sai | sempre sai | sempre sai |

O fone sair em acidente é proposital: ele solta em vez de puxar a orelha.

## 3. Resistência (calculada)

- Queda de frente (da almofada) de 0,75 a 1 m: o anel de encaixe aguenta com folga de 2 a 6 vezes, dependendo do driver (mais folga com driver pequeno).
- Gancho (arame de inox): fator de segurança 6,9 em uso e 4,2 na fadiga (10 mil vezes). O gancho só entorta de vez se for aberto mais de 9,5 mm para trás.
- Faixa da nuca vestindo: fator de segurança 1,18 com o arame de inox (era 1,65 com corda de piano). É a margem mais curta do projeto: não abra a faixa além do necessário ao colocar. O arame de inox ainda precisa de teste real de dobra.
- Calor: o PETG amolece a 80 °C. Banco de carro (até ~60 °C) ok; não deixar no painel ao sol.
- Queda de quina ou de costas: não é calculável no papel. Falta teste físico (roteiro de queda em `docs/04_testes.md`). Se a quina trincar, a parede passa para 1,6 mm (cerca de 2 g a mais por lado).

## 4. Som (cálculo simples de caixa fechada)

- A concha é fechada atrás, com fibra: o volume de ar atrás do driver fica entre 22 cm³ (60 mm) e 31 cm³ (40 mm).
- Com a almofada vedada, o graves aguenta bem. Com uma abertura leve (0,2 mm em 1/4 da volta, o que acontece em parte das passadas), o graves cai só 2 a 3 dB.
- Com abertura forte (0,5 mm em metade da volta), o graves some: em 100 Hz a queda é de 10 a 17 dB. É o risco real de correr com o fone mal ajustado.
- Em 60 mm, a caixa pequena cria uma ressonância de cerca de +11 dB perto de 1 kHz sem feltro atrás do driver; um feltro de 2 a 4 mm reduz. Depende do driver real.
- Não há medição de som. A qualidade só vale depois de testar com o driver escolhido.

## 5. Custo e preço (R$)

- Peças compradas: R$ 67,70 (almofada de couro) a R$ 109,20 (veludo), com imposto de importação do AliExpress, por par.
- Impressão por serviço: R$ 101,60 (Neo3DPrint, cotação de 9/10) a R$ 143 a 161 (fábrica3D): total por par entre R$ 164 e R$ 252, antes de frete, embalagem e sua mão de obra.
- Impressão em casa (impressora com extrusora direta, para o TPU): R$ 72 a R$ 113 por par.
- Preço: pré-venda R$ 349 para os 20 primeiros pares, preço final previsto R$ 400. Com impressão em serviço a sobra é pequena; em casa fica bem melhor.
- A taxa do Apoia-se e do meio de pagamento não foi conferida.

## 6. O que ainda não foi feito (diga isso na campanha)

- Peso medido do protótipo oval (os 74/84/97 g são calculados).
- Corrida real, queda de quina e dobra do arame de inox.
- Uso com óculos.
- Som medido com o driver escolhido.
- As cargas de 1 a 5 g foram calculadas com corda de piano; com o arame de inox só a esteira foi refeita (a rigidez do fio muda cerca de 7 %).

## 7. Texto pronto para colar na campanha

**Números do projeto (calculados, ainda sem protótipo medido)**

- Peso por lado: cerca de 74 g (driver de 40 mm), 84 g (50 mm) ou 97 g (60 mm). Par: 149 a 194 g, sem o cabo.
- Firmeza: em simulação de esteira, 5.400 combinações de movimento, o OTO não soltou em nenhum caso com 40, 50 e 60 mm. Em sacudidas severas (3 g), soltou em 1 a 8 % dos casos, dependendo do driver. Num acidente (puxão forte ou queda da cabeça) ele sai de propósito, em vez de puxar a orelha.
- Resistência: gancho de inox com folga de 4 a 7 vezes sobre o limite; queda de frente de 1 m calculada sem quebrar; queda de quina ainda precisa de teste real.
- Som: concha fechada com fibra; se a almofada abrir muito durante a corrida, o grave diminui.
- Todos esses números são cálculos. Peso real, corrida e queda serão testados e publicados aqui, inclusive os resultados ruins.
