# UMEH-2 — suporte de fone montado na orelha para drivers de 40–60 mm

> Tradução para o português do README gerado por `calc/make_report.py` (branch `claude/umeh2-docs-pt`). Os números são
> os mesmos da versão em inglês; rodar `make_report.py` de novo gera o texto em inglês.

Segunda iteração de projeto do Universal Modular Ear-mounted Headphone: um suporte comum (anel, quatro braços, almofadas, sela arqueada, mola de ligação occipital) que fica em volta da orelha, e um módulo de driver por tamanho (somente 40, 45, 50, 55 e 60 mm) que se encaixa nele com trava de giro. Tudo neste pacote é gerado a partir dos cálculos: o CAD lê os arquivos de parâmetros que o cálculo escreve, e as massas e centros de massa usados nos casos de carga são integrados sobre as malhas que esse CAD exporta.

**Leia primeiro:** `report/ENGINEERING_REPORT.md` (deduções, todos os casos de carga, fatores de segurança, limitações). Não foi feita nenhuma análise por elementos finitos (FEA), por elementos de contorno (BEM) nem teste físico; o relatório diz onde cada um é necessário. Dados dos drivers, propriedades dos tecidos e coeficientes de atrito são suposições ou faixas da literatura e estão marcados como tal; meça seus drivers e rode de novo.

## Resultados principais (projeto final)

| driver | massa por lado g | uso normal (estático + 1 g + ligação) | pressão na raiz da orelha em uso kPa (meta ≤ 4) | 2 g: % das combinações que soltam | manuseio 10 N, FS mín. | driver máx. g, uso normal (grade 1 g) | driver máx. g, projeto máximo |
|---|---|---|---|---|---|---|---|
| 40 mm | 156 | PASSA | 18.0 | 1.94 | 1.72 | 27.7 | 126.0 |
| 45 mm | 163 | PASSA | 18.4 | 1.26 | 1.72 | 34.4 | 122.9 |
| 50 mm | 173 | PASSA | 19.4 | 1.42 | 1.72 | 31.8 | 84.6 |
| 55 mm | 182 | PASSA | 20.5 | 2.08 | 1.72 | 41.2 | 54.9 |
| 60 mm | 190 | PASSA | 21.4 | 2.52 | 1.72 | 45.2 | 109.2 |


Uso normal significa: todas as almofadas carregadas em repouso, pressão na pele e na raiz da orelha ≤ 4 kPa logo após colocar (primeiro prender; em uso: veja abaixo), atrito estático dentro do coeficiente de projeto, e nenhum escorregamento grosseiro, perda do tripé ou inclinação > 2° em qualquer ponto da grade de 1 g de orientações da cabeça (até a borda do cone de inclinação), rotações da cabeça e puxões do cabo, nem numa verificação densa mais fina e no seu refinamento local (relatório §8), e o fio da ligação dentro dos seus critérios naquele módulo (relatório §11). Acima de 1 g o suporte, preso por atrito, solta numa parte das combinações (40 mm: 1.94 %, 45 mm: 1.26 %, 50 mm: 1.42 %, 55 mm: 2.08 %, 60 mm: 2.52 % do conjunto de 2 g); o relatório dá as frações por caso e o porquê (§8, §10).

**Não atendido: a pressão na raiz da orelha em uso.** O uso normal é julgado logo após colocar. Quando a cabeça se move, as almofadas micro-escorregam e a sela acaba carregando o peso do lado sobre a raiz da orelha a 18.0–21.4 kPa, acima da meta de conforto sustentado de 4 kPa em todos os tamanhos. Nenhuma das alavancas de projeto estudadas atende (relatório §6). Espere pressão no alto da orelha em sessões longas, e meça isso primeiro (relatório §22).

## Montagem e uso (fazem parte do projeto)

* **Colocar:** segure o suporte no lugar em volta da orelha, prenda a ligação e depois solte. Pendurar primeiro na orelha e só depois prender coloca 5.15–5.21 × a pressão na raiz da orelha (relatório §6).
* **Cabo:** passe-o descendo pelo pescoço. Puxões quase horizontais de 1.34–2.02 N soltam o suporte antes que o plugue ceda (relatório §14). Conecte e desconecte com o fone fora da cabeça.
* **Parafusos dos braços:** chave de torque no valor do `BOM.csv`, com uma arruela ondulada sob cada cabeça; as serrilhas carregam
  a carga, a arruela mantém o aperto depois que o PETG sofre fluência (relatório §13).
* **Faces das almofadas:** moldar a face de silicone nas almofadas temporal e mastoide (geometria de referência em
  `stl/common/cast_reference/`).
* **Revestimento da sela:** moldar o revestimento macio de silicone (Shore 00-30) na face de apoio rebaixada da tampa da sela; sem ele a raiz da orelha carrega 4.41 kPa a 55 mm e 4.63 kPa a 60 mm em repouso, acima da meta de 4 kPa (relatório §6).
* **Orientação e ajustes de impressão:** relatório §20 e a coluna `spec` do `BOM.csv`. Os STLs são exportados na orientação
  de impressão.


## Conteúdo

* `report/ENGINEERING_REPORT.md`, `report/fig/` — o relatório de engenharia e suas figuras (tradução em
  `report/RELATORIO_ENGENHARIA.md`).
* `cad/umeh2.scad` — modelo paramétrico OpenSCAD; `cad/generated_params.scad` (padrão 50 mm) e `cad/params_<D>.scad` são
  escritos pelo cálculo.
* `stl/common/` — peças do suporte (iguais para todos os tamanhos de driver); `stl/module_<D>mm/` — peças do módulo por tamanho (as conchas
  têm lado, porque o olhal da ligação fica numa posição própria de cada módulo).
* `calc/` — os modelos (`calc/umeh2/*.py`) e os scripts que produzem todos os resultados.
* `results/*.json` — todos os números calculados que o relatório cita.
* `BOM.csv`, `docs/bom_table.md` — lista de materiais para um par, massas do CAD.

## Rodar de novo

Requisitos: Python 3 com numpy, scipy e matplotlib, e OpenSCAD no PATH. Esta entrega foi rodada com
Python 3.11.15, numpy 2.4.6, scipy 1.17.1, matplotlib 3.11.2, OpenSCAD versão 2021.01.

```
cd calc
python3 legs_liner.py    # espessura das pernas dos braços e do revestimento da sela, escolhidas juntas (results/legs_liner.json)
python3 tune_eye.py      # posição do olhal da ligação por módulo e a pré-carga da ligação (escreve calc/final_layout.json)
python3 run_all.py       # ligação, projetos B/A/Final, juntas, cabo, peso, dinâmica, tolerâncias, acústica, massa máx.
python3 shakedown.py     # o estado sustentado em uso: acomodação das forças de contato com o movimento da cabeça (results/shakedown.json)
python3 sweeps.py        # varreduras de parâmetros
python3 figures.py
python3 build_stl.py     # STLs + cad/params_<D>.scad
python3 bom.py
python3 make_report.py   # report/ENGINEERING_REPORT.md e este README (em inglês)
```

Os registros das mudanças de iteração 19–21 vêm de estados anteriores do projeto, mantidos como entradas:
`calc/final_layout_before_grid.json` (run_all seção 3d → results/grid_1g_before_grid.json), e
`calc/final_layout_grid45.json` (`python3 check_stall.py` → results/solver_stall_check.json;
`python3 dense_check_grid45.py` → results/dense_1g_grid45.json). Eles não são necessários para rodar o projeto de novo.

`legs_liner.py`, `tune_eye.py`, `run_all.py`, `shakedown.py` e `sweeps.py` usam quatro processos e são as etapas longas (o modelo de contato
resolve todas as combinações de carga de todos os candidatos). Mude uma entrada (dados do driver
em `calc/umeh2/design.py`, materiais em `calc/umeh2/materials.py`, decisões de projeto em `calc/umeh2/configs.py`) e
rode a cadeia de novo; nada no relatório é digitado à mão.

Nesta entrega, a saída original do ajuste dos olhais (`tune_eye.py`) se perdeu com a máquina que o rodou;
`calc/eye_record.py` escreve `results/eye_tuning.json` como registro, e a verificação densa de 1 g do `run_all.py` é a
prova de que os olhais passam (relatório §7, §8).
