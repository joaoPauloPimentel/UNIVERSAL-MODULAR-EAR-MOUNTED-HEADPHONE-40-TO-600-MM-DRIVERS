# UMEH-2 — Relatório de projeto de engenharia (drivers de 40–60 mm)

> **Tradução para o português** de `report/ENGINEERING_REPORT.md`, gerado por `calc/make_report.py` em 2026-09-30.
> Todos os números são os da versão em inglês, sem alteração; em caso de dúvida, vale o original. Rodar
> `make_report.py` de novo gera apenas a versão em inglês. Nomes de arquivos, variáveis e rótulos de dados
> (por exemplo `static`, `1 g normal`) foram mantidos como estão no código.

Universal Modular Ear-mounted Headphone, segunda iteração de projeto. Escopo: drivers dinâmicos de **somente 40, 45, 50, 55 e 60 mm**; nada acima de 60 mm é projetado nem afirmado.

Todo número deste relatório é escrito por `calc/make_report.py` a partir de `results/*.json`, que `calc/run_all.py`, `calc/legs_liner.py`, `calc/tune_eye.py`, `calc/shakedown.py` e `calc/sweeps.py` calculam. O CAD (`cad/umeh2.scad`) lê `cad/generated_params.scad` / `cad/params_<D>.scad`, que o mesmo cálculo escreve, e as propriedades de massa são integradas sobre as malhas que esse CAD exporta — portanto a geometria impressa é a geometria calculada, e as massas calculadas são as dessa geometria com as densidades e fatores de preenchimento declarados (uma peça impressa vai variar em torno delas; pese a primeira impressão). Rodar de novo: `cd calc && python3 legs_liner.py && python3 tune_eye.py && python3 run_all.py && python3 shakedown.py && python3 sweeps.py && python3 figures.py && python3 build_stl.py && python3 bom.py && python3 make_report.py`.

**O que NÃO foi feito, dito logo de início:** nenhuma análise por elementos finitos (estrutural ou acústica), nenhuma análise por elementos de contorno e nenhum teste físico foi feito. A estrutura usa teoria fechada de vigas, juntas e contato com fatores de concentração de tensão de Peterson; a fixação na orelha é um modelo de corpo rígido com 6 graus de liberdade e braços elásticos sobre contatos unilaterais, flexíveis e com atrito, resolvido por minimização incremental de energia sem linearizar as leis de contato ou de atrito (§6); a acústica é um modelo concentrado eletro-mecano-acústico com radiação exata de pistão em baffle. O §21 lista exatamente onde FEA/BEM ou um teste é necessário. Parâmetros Thiele/Small dos drivers, propriedades dos tecidos e coeficientes de atrito são faixas da literatura ou suposições e estão marcados como tal em todo lugar. A precisão completa é mantida no cálculo; apenas as dimensões finais são arredondadas (o §3 dá cada arredondamento e sua justificativa).

## Marcas de origem

| marca | significado |
|---|---|
| STD | valor de norma / manual (ISO, ASTM, Shigley, Peterson, Roark) |
| DS | ficha técnica típica de fabricante (grau genérico — seu carretel/peça pode diferir) |
| LIT | literatura de ensaios publicada, faixa aproximada |
| A | suposição de engenharia — sem dados confiáveis; escolhida de forma conservadora; substituir por medição |
| C | calculado neste relatório |
| CAD | medido na malha do CAD (integração exata de volume) |
| E | estimativa (ordem de grandeza, método declarado) |
| EMP | relação empírica (ex.: Gent E(Shore), fluência de Findley, fator de porca) |
| SIM | simulado — nenhum: não foi feita FEA/BEM (§21) |
| M | medido — nenhum ainda; o plano de testes do §22 os produz |


## 1. Resumo

Projeto final, por tamanho de driver (massas e geometria dos drivers são provisórias [A] até serem medidas):

| driver | massa/lado g [CAD+DS] | CG afastado da pele mm [C] | critérios de uso normal [C] | p na raiz da orelha em uso kPa (≤ 4) [C] | demanda de μ estático / μ de projeto [C] | 2 g: % combinações soltas | 3 g: % | 5 g: % | início 5 g λ mín | manuseio 10 N FS mín | envelope 5 g FS mín | driver máx. g: normal (grade 1 g) | driver máx. g: dinâmico (≤ 10 % soltas) | driver máx. g: projeto máx. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 40 mm | 156 | 29.6 | PASSA | 18.0 | 0.846 | 1.94 | 35.4 | 96.8 | 0.0625 | 1.72 | 1.87 | 27.7 | 27.7 | 126.0 |
| 45 mm | 163 | 30.4 | PASSA | 18.4 | 0.785 | 1.26 | 33.4 | 96.7 | 0.0625 | 1.72 | 1.79 | 34.4 | 34.4 | 122.9 |
| 50 mm | 173 | 31.3 | PASSA | 19.4 | 0.799 | 1.42 | 34.9 | 96.7 | 0.0625 | 1.72 | 1.58 | 31.8 | 31.8 | 84.6 |
| 55 mm | 182 | 32.2 | PASSA | 20.5 | 0.848 | 2.08 | 37.9 | 96.7 | 0.0625 | 1.72 | 1.40 | 41.2 | 41.2 | 54.9 |
| 60 mm | 190 | 33.0 | PASSA | 21.4 | 0.874 | 2.52 | 39.7 | 96.7 | 0.0625 | 1.72 | 1.44 | 45.2 | 45.2 | 109.2 |


Definições: *critérios de uso normal* = todas as almofadas carregadas em repouso, pressão sustentada na pele e na raiz da orelha ≤ 4 kPa logo após colocar (A), demanda de atrito estático ≤ μ de projeto, a grade de 1 g, sua verificação densa e o refinamento local sem escorregamento grosseiro, com o tripé mantido e inclinação ≤ 2° (§8), e o fio da ligação dentro dos seus critérios no módulo (§11). *Driver máx. g*: 'normal' = os critérios estáticos + a grade de 1 g, 'dinâmico' = isso + o conjunto de 2 g, 'projeto máx.' = fixação estática + o envelope estrutural de 5 g (§10); a verificação densa e seu refinamento rodam apenas no driver nominal. *Solta* = nenhum equilíbrio limitado dentro de 3 mm / 5° (escorregamento grosseiro). *Início λ* = fração do incremento de carga de 5 g em que o escorregamento grosseiro começa (§12). *Manuseio* = 10 N numa almofada em qualquer uma de 302 direções (§12). *p na raiz da orelha em uso* = depois da acomodação (shakedown) do conjunto de 1 g pelo movimento da cabeça (§6), o estado sustentado quando o fone está em uso. FS exigido ≥ γM = 1.6.

Principais conclusões (cada uma é deduzida na seção indicada):

1. **O projeto B não conseguia ficar na cabeça** (§4, §6): fixação estática **FALHA**, 1 g soltas 89.5 % — o olhal da ligação na almofada mastoide faz a pré-carga passar pelo contato mais baixo, então nada resiste ao momento de tombamento do CG; o projeto A (massa do UMEH-1) é pior.
2. **O uso normal (estático + a grade de 1 g, sua verificação densa e o refinamento local) passa em 40, 45, 50, 55, 60 mm** (os cinco tamanhos), com uma posição de olhal por módulo e uma pré-carga comum da ligação de 5.00 N ajustadas juntas (§7). O primeiro Final, ajustado numa amostra quase uniforme de 1 g a 4.20 N, falha na grade de 1 g em 5 de 5 módulos (§4 mudança 19, §8).
3. **Em uso, a raiz da orelha carrega o peso — a meta de pressão sustentada na raiz NÃO é atendida** (§6): as almofadas micro-escorregam com o movimento normal da cabeça e passam o peso do lado para a sela; depois dessa acomodação a raiz carrega 18.0–21.4 kPa (4.50–5.35 × 4 kPa), contra 2.96–3.61 kPa logo após colocar. Nenhuma das alavancas estudadas (atrito das almofadas, pré-carga, área de apoio na raiz, revestimento, braços, posição do olhal) atende a 60 mm; o lado de 60 mm teria de pesar ≤ 60.3 g. Este é o limite de um suporte montado na orelha com esta massa. Os testes de uso devem medir isso primeiro (§22).
4. **A retenção montada na orelha tem um limite físico rígido acima de 1 g** (§8, §10): no conjunto de 2 g, 1.26–2.52 % das combinações soltam; os casos de movimento da cabeça com mais solturas são rolagem (inclinação) alfa 94.7 %, guinada (giro) alfa 4.99 %, arfagem (aceno) alfa 0.217 % de todas as solturas em 2 g. A condição estrita 'nenhuma combinação de 2 g pode escorregar' falha mesmo com um driver sem massa (40, 45, 50, 55, 60 mm). As frações soltas são relatadas, não escondidas. Depois de soltar, o suporte ainda envolve o pavilhão e fica pendurado na ligação; essa retenção não é modelada (§22), então nenhum crédito de retenção é tomado por ela.
5. **Estrutura:** a carga estrutural que governa é o envelope de início de 5 g (menor FS 1.40, §12); a carga de manuseio de 10 N numa almofada dá FS 1.72.
6. **Juntas:** as serrilhas carregam a carga radial, as arruelas onduladas mantêm o aperto depois que o PETG sofre fluência, e a ancoragem do cabo mantém insertos M3 (FS 1.16 na maior carga de cabo, §13, §14); insertos M2.5 chegariam a FS 0.699 ali (§5, W1b).
7. **Faixa de massa do driver** (§10), uso normal: 40 mm 0.0–27.7 g, 45 mm 0.0–34.4 g, 50 mm 0.0–31.8 g, 55 mm 0.0–41.2 g, 60 mm 0.0–45.2 g; condição máxima de projeto: 40 mm 0.0–126.0 (um ponto intermediário falha!) g, 45 mm 0.0–122.9 (um ponto intermediário falha!) g, 50 mm 0.0–84.6 (um ponto intermediário falha!) g, 55 mm 0.0–54.9 g, 60 mm 0.0–109.2 (um ponto intermediário falha!) g.
8. **Componentes limitantes** (§19): atrito de retenção a partir de 2 g (frações soltas, não uma utilização); depois, por utilização (demanda / admissível): pressão na raiz da orelha em uso, após a acomodação pelo movimento da cabeça (60 mm) — zonas do arco: 5.35 (≤ 4.00 kPa sustentado; NÃO atendido (§6)); pressão na raiz se pendurado na orelha antes de prender (colocação B, 60 mm) — zonas do arco: 4.65 (≤ 4.00 kPa sustentado (logo após colocar); não atendido → a instrução é prender primeiro (colocação A)); seção do braço, envelope de início de 5 g, 40 °C — 55 mm, mastoide: barra na borda da braçadeira (fim do rasgo) (vM): 1.14 (FS ≥ γM 1.60); seção do braço, fadiga 1e7 ciclos (envelope de 2 g mantido, de zero ao pico) — 60 mm, mastoide: barra na borda da braçadeira (fim do rasgo): 0.938.

## 2. Entradas e suposições

### 2.1 Materiais

| material | propriedade | valor (SI) | marca | nota |
|---|---|---|---|---|
| PETG | rho | 1270 | DS | densidade do material maciço, kg/m3 |
| PETG | E_xy | 1.9e+09 | LIT | módulo de tração no plano da camada, PETG FDM, típico 1.7–2.1 GPa |
| PETG | E_z | 1.6e+09 | LIT | entre camadas, ~0.8–0.9 x E_xy |
| PETG | nu | 0.380 | LIT |  |
| PETG | S_xy | 4.5e+07 | LIT | resistência à tração no plano da camada (dominada pelos perímetros), impresso; faixa 40–50 MPa, perto do limite inferior |
| PETG | S_z | 2.2e+07 | LIT | resistência à tração entre camadas, impresso; faixa 15–35 MPa, conservador |
| PETG | S_shear_il | 1.4e+07 | LIT | resistência ao cisalhamento entre camadas, conservador (~0.6 x S_z) |
| PETG | S_bear | 5.5e+07 | DS | escoamento em compressão, curto prazo |
| PETG | Tg | 80.0 | DS | transição vítrea, °C |
| PETG | kT_40C | 0.850 | LIT | retenção de resistência/módulo a 40 °C em relação a 23 °C |
| PETG | kT_55C | 0.700 | LIT | retenção a 55 °C (carro / sol direto) |
| PETG | fat_ratio | 0.200 | A | Se/S_xy a 1e7 ciclos; dados de fadiga de PETG impresso são escassos, 0.2 é conservador |
| PETG | fat_b | -0.0850 | A | expoente de Basquin da curva S-N normalizada (termoplásticos típicos −0.07…−0.12) |
| PETG | creep_n | 0.200 | LIT | expoente de Findley para copoliésteres amorfos, 0.15–0.25 |
| PETG | creep_tau_h | 40.0 | A | tempo (h) em que a deformação por fluência iguala a elástica a 23 °C; a 40 °C divide-se por 4 |
| PETG | cte | 6.8e-05 | DS | 1/K |
| PETG | shrink | 0.004 | LIT | contração linear após impressão, 0.2–0.6 % |
| TPU 95A | rho | 1210 | DS |  |
| TPU 95A | E | 2.6e+07 | DS | módulo de Young do 95A em pequena deformação, típico 20–35 MPa |
| TPU 95A | nu | 0.480 | LIT |  |
| TPU 95A | elong | 4.50 | DS | alongamento na ruptura, 450 % |
| TPU 95A | compression_set | 0.250 | DS | 22 h a 70 °C, ISO 815 típico 20–35 %; a 40 °C por 8 h usar 0.10 (A) |
| TPU 95A | creep_n | 0.120 | LIT |  |
| TPU 95A | creep_tau_h | 8.00 | A |  |
| fio de aço para molas (music wire) | E | 2.07e+11 | STD |  |
| fio de aço para molas | rho | 7850 | STD |  |
| fio de aço para molas | Sy_ratio | 0.750 | STD | escoamento em flexão ~0.75 Sut para fio trefilado a frio (Shigley, torção 0.45, flexão ~0.75) |
| fio de aço para molas | Se_bend_ratio | 0.300 | A | resistência à fadiga em flexão alternada / Sut para fio sem jateamento, conservador |
| fio de aço para molas | min_bend_radius_d | 1.50 | STD | raio interno mínimo de dobra ~ 1–2 x d (prática dos fornecedores) |
| fio de aço para molas | nu | 0.290 | STD | coeficiente de Poisson do aço carbono para molas |
| fio de aço para molas | Sut_A | 2.21e+09 | STD | resistência à tração ASTM A228 Sut = A / d^m (d em mm), A em Pa·mm^m (Shigley Tabela 10-4) |
| fio de aço para molas | Sut_m | 0.145 | STD | expoente m de Sut = A / d^m, ASTM A228, 0.10–6.5 mm |
| silicone Shore 10–30A (face das almofadas, luva da ligação) | rho | 1100 | DS | silicone de moldagem cura platina Shore 10-30A, 1.07-1.15 g/cm3 |
| silicone Shore 10–30A (face das almofadas, luva da ligação) | E | 600000 | LIT | módulo de Young de silicone Shore ~20A, 0.3-1.0 MPa (Gent: E = 0.0981(56+7.62336 S)/(0.137505(254-2.54 S)) MPa) |
| silicone Shore 00-30 (revestimento da sela) | rho | 1070 | DS | silicone platina Shore 00-30, densidade relativa 1.07 |
| silicone Shore 00-30 (revestimento da sela) | sigma100 | 68900 | DS | módulo de tração a 100 % de 10 psi (boletim técnico Ecoflex 00-30) |
| silicone Shore 00-30 (revestimento da sela) | E | 118114 | C | módulo de Young em pequena deformação pelo ajuste neo-Hookeano ao módulo a 100 % |
| silicone Shore 00-30 (revestimento da sela) | k_gent | 1.00 | LIT | constante de camada colada de Gent-Lindley, limite incompressível |
| latão | rho | 8500 | DS | latão CuZn37 / CuZn39Pb3, 8.4–8.5 g/cm3 |
| latão | E | 1e+11 | LIT | módulo de Young do latão, 97–110 GPa |
| latão | nu | 0.340 | LIT |  |
| latão | Sy | 2.5e+08 | LIT | tubo de latão meio-duro, escoamento ~200–300 MPa |
| espuma | rho | 240 | A | placa de espuma PU microcelular, 200–400 kg/m3; massa desprezível (< 0.1 g) |
| espuma | cfd_exp | 0.300 | A | forma do patamar sigma(eps) = CFD25*(eps/0.25)^n, n 0.2–0.5 para PU microcelular, 10–60 % de deformação |
| espuma | eps_dens | 0.750 | A | início da densificação (deformação) |
| espuma | comp_set | 0.100 | A | deformação permanente após compressão longa a 40 °C (PU microcelular: 2–10 % típico) |
| espuma | mu | 0.800 | A | atrito espuma PU / PETG impresso, 0.5–1.0 (valor superior usado para o torque de montagem) |
| espuma | t_tol_rel | 0.100 | A | tolerância de espessura da placa cortada +-10 % |
| PETG | fator parcial γM | 1.60 | A | cobre defeitos de perímetro, vazios, umidade, variação de carretel |
| PETG | fator de carga sustentada | 0.500 | LIT | ruptura por fluência, 1e4 h |
| insertos | fator parcial γ_insert | 2.00 | A | fator parcial no arrancamento do inserto (a qualidade da instalação domina) |
| parafusos | fator de porca K | 0.280 | LIT | T = K F d para inox seco em latão, 0.2–0.35 |


| inserto | arrancamento N (característico) | marca | nota |
|---|---|---|---|
| M2 | 250 | LIT | N característico; testes publicados amadores/industriais 200–500 N |
| M2.5 | 380 | LIT | N; 300–700 N |
| M3 | 550 | LIT | N; 400–1000 N em PLA/PETG na temperatura de instalação correta |
| M4 | 900 | LIT | N |


Resistência do fio de aço para molas: Sut = 2211 MPa / d^0.145 (d em mm) [STD, ASTM A228, Shigley Tabela 10-4]. Anisotropia FDM: resistência no plano da camada S_xy, tração entre camadas S_z e cisalhamento entre camadas são admissíveis separados; cada verificação de seção diz qual se aplica a partir da orientação de impressão da peça (§20).

### 2.2 Tecido, limites de conforto e atrito

| grandeza | valor | marca | nota |
|---|---|---|---|
| E_mastoid | 120000 | LIT | tecido mole sobre osso, módulo de indentação 50–300 kPa |
| t_mastoid | 0.004 | LIT | pele + subcutâneo sobre a mastoide, 3–6 mm |
| E_temporal | 100000 | LIT |  |
| t_temporal | 0.006 | LIT | inclui a borda da fáscia temporal, 4–10 mm |
| E_root | 150000 | LIT | pele da raiz da orelha / sulco sobre a junção cartilagem-osso |
| t_root | 0.003 | LIT |  |
| p_sustained | 4000 | LIT | meta de pressão de contato sustentada; fechamento capilar ~4.3 kPa (32 mmHg) |
| p_transient | 8000 | A | tolerada por segundos (picos ao caminhar) |
| p_pain | 150000 | LIT | limiar de dor à pressão sobre osso ~150–400 kPa (algometria) |


| par | μ baixo | μ nominal | μ alto | marca |
|---|---|---|---|---|
| TPU/pele seca | 0.350 | 0.550 | 0.800 | LIT |
| silicone/pele seca | 0.450 | 0.700 | 1.00 | LIT |
| TPU/pele suada ou oleosa | 0.200 | 0.350 | 0.500 | LIT |
| TPU/cabelo (sobre o temporal) | 0.150 | 0.250 | 0.350 | LIT |
| TPU/silicone (luva sobre o fio) | 0.500 | 0.800 | 1.10 | LIT |
| PETG/PETG (baioneta) | 0.180 | 0.250 | 0.350 | LIT |


Atrito de projeto = nominal / γ_μ = nominal / 1.25 [A]; os valores baixo e alto e vários estados da pele são rodados como sensibilidade (§9).

### 2.3 Drivers (provisórios — meça e rode de novo)

| D mm | DE da borda mm [A] | abertura frontal mm [A] | t da borda [A] | profundidade [A] | Ø traseiro [A] | massa g [A] | Fs Hz [A] | Mms g [A] | Sd cm² [C] | Vas cm³ [C] | Qts [A] | Bl T·m [C] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 40.0 | 40.5 | 35.2 | 1.80 | 10.0 | 33.6 | 15.0 | 120 | 0.300 | 8.04 | 536 | 0.400 | 3.68 |
| 45.0 | 45.5 | 39.6 | 1.80 | 11.0 | 37.8 | 19.0 | 104 | 0.375 | 10.2 | 916 | 0.400 | 3.83 |
| 50.0 | 50.5 | 44.0 | 2.00 | 12.0 | 42.0 | 26.0 | 90.0 | 0.450 | 12.6 | 1551 | 0.400 | 3.91 |
| 55.0 | 55.5 | 48.4 | 2.00 | 13.0 | 46.2 | 33.0 | 79.4 | 0.535 | 15.2 | 2456 | 0.400 | 4.00 |
| 60.0 | 60.5 | 52.8 | 2.00 | 14.0 | 50.4 | 40.0 | 70.0 | 0.620 | 18.1 | 3859 | 0.400 | 4.04 |


Base T/S [A]: D_eff = 0.8 D, Qms = 2, Qes = 0.5, Re = 30 Ω, Le = 50 µH; Mms/Fs ancorados em 40/50/60 mm e interpolados (Mms linear, Fs log-linear em D). Cms = 1/((2πFs)² Mms), Rms = 2πFs Mms/Qms, Bl = √(2πFs Mms Re/Qes), Vas = ρc² Sd² Cms [C].

### 2.4 Antropometria [A/LIT]

| grandeza | valor mm |
|---|---|
| pinna_protrusion_mean (projeção média do pavilhão) | 20.0 |
| pinna_protrusion_p95 (projeção do pavilhão, p95) | 26.0 |
| pinna_length_p95 (comprimento do pavilhão, p95) | 72.0 |
| concha_depth (profundidade da concha) | 12.0 |
| head_half_width (meia largura da cabeça) | 75.0 |
| occiput_r (raio do occipital) | 95.0 |

## 3. Referencial, arquitetura e dimensões finais (com arredondamento)

Referencial: origem no eixo do anel, no plano da pele das almofadas; x para a frente, y para cima, z lateral (para longe da cabeça); lado direito (o esquerdo espelha x). Arquitetura (Final): suporte comum = anel de PETG com a trava de giro UMI-2 + quatro braços (sela, temporal, mastoide, póstero-superior) com braçadeiras serrilhadas; almofadas de TPU (temporal e mastoide com face de silicone moldado); tampa da sela em arco de TPU com revestimento de silicone macio moldado sobre a raiz da orelha; módulo do driver = baffle + concha (+ feltro traseiro colado) travados no anel; mola de ligação occipital presa na ponta da concha num olhal próprio de cada módulo; ancoragem do cabo + clipe no anel.

| item | valor | valor 2 | arredondamento / origem |
|---|---|---|---|
| Ø do pino / furo da interface | 77.0 | 77.4 | grade de 0.5 mm no raio (FDM ±0.15 mm; o ajuste é definido pela folga radial, §17) |
| DE do anel | 88.7 |  | segue a ranhura + lábio (C) |
| raio / espessura da aba | 63.2 | 11.0 | C: passo dos insertos + paredes; não arredondado (derivado) |
| afastamento pele → face do anel | 29.0 |  | C: projeção p95 do pavilhão 26 + 3 mm, grade de 0.5 mm |
| ângulo / raio da almofada temporal | 20.0 | 57.5 | busca de layout máx–mín (§7), arredondado 0.5°/0.5 mm; reverificado com o modelo atual (§8) |
| ângulo / raio da almofada mastoide | 229 | 58.0 | idem |
| ângulo / raio da almofada póstero-superior | 164 | 59.0 | idem |
| tamanhos das almofadas T / M (a×b) | 33.8×39.0 / 39.0×49.4 | P 33.8×39.0 | pad_scale 1.3 (passos de 0.1) sobre as almofadas Base: pressão na pele ≤ 4 kPa |
| altura da almofada (TPU giroide 15 %) / face de silicone | 6.00 | 0.800 | varredura §18 / §9 (0.1 mm: moldagem) |
| R do arco da sela / meio-ângulo | 22.0 | 35.0 | A (antropometria) + varredura §18 |
| revestimento da sela (silicone Shore 00-30) | 2.50 | E 118 kPa | revestimento mais fino em passos de moldagem de 0.5 mm com margem ≥ 5 % na raiz a 60 mm (tabela de alavancas §6: 2 mm → 3.96 kPa); mais grosso passa peso ao atrito das almofadas (3 mm → demanda de μ 0.899) e afrouxa a localização da sela (§18: inclinação 1 g 0.405 → 0.405°, 2 g soltas 3.52 → 3.60 %) |
| pré-carga da ligação no módulo de 50 mm (N) | 5.00 |  | ajuste do olhal (§7): o menor dos níveis de pré-carga (layout 4.20 N + passos de 0.400 N) em que todo módulo tem um olhal que atende os critérios de uso normal do ajuste (estático + a grade de 1 g) e que também passa na verificação densa e no seu refinamento local (etapa 4); P(D) por módulo abaixo |
| Ø do fio da ligação / espiras do ápice | 2.50 | 4.00 | Ø comercial de fio de aço para molas (A: supõe-se em estoque, confirmar com o fornecedor); para cada Ø, o menor número de voltas no ápice que atende todos os critérios da ligação nos cinco módulos nos seus olhais, depois o Ø com a maior das menores margens (§11) |
| t da barra / perna / pé do braço | 5.50 | 5.5 / 4.5 | barra: FS de manuseio com tolerância de −0.15 mm (§5, §12); pernas e revestimento escolhidos juntos (§6); 0.1 mm |
| parafusos dos braços / torque N·m | M3 | 0.100 | §13: arrancamento do inserto na maior pré-carga da dispersão de torque (resolução da chave de torque 0.01 N·m) |
| passo dos insertos dos parafusos do braço / arruela ondulada | 11.0 | ≥ 100 N achatada, ≤ 200 N/mm | §13: alavanca de alavancamento da braçadeira (0.5 mm); a arruela mantém as serrilhas engatadas após a fluência do PETG |
| feltro traseiro: furo no ressalto do olhal / aro adesivo (PSA) | Ø7.50 | 2.00 | furo 0.500 mm abaixo do Ø do ressalto (veda, §17); aro fora da grade (§13) |
| parafusos da ancoragem / torque N·m | M3 | 0.100 | §14 |
| passo / altura da serrilha | 1.20 | 0.600 | regra de 3 × largura do bico (C) |
| parede da concha | 1.20 |  | 3 perímetros de linhas de 0.42 mm (§5, §20) |
| folga do alojamento do driver / lado | 0.220 |  | centra a faixa MC do ajuste (§17), 0.01 mm |


Valores por módulo (o suporte e a ligação são comuns; cada módulo tem o seu olhal e, portanto, a sua pré-carga P(D) = P_ref + k_lado·Δz_topo_concha, §7):

| D | olhal x mm | olhal y mm | olhal r_máx mm | P(D) N [C] | R_ext da concha mm | h da concha mm | z do topo da concha mm |
|---|---|---|---|---|---|---|---|
| 40 | -15.0 | 7.00 | 17.2 | 4.67 | 21.7 | 18.2 | 53.1 |
| 45 | -18.0 | 7.00 | 19.7 | 4.84 | 24.2 | 19.2 | 54.1 |
| 50 | -19.0 | 7.00 | 22.2 | 5.00 | 26.7 | 20.0 | 55.1 |
| 55 | -18.0 | 7.00 | 24.7 | 5.16 | 29.2 | 21.0 | 56.1 |
| 60 | -18.0 | 7.00 | 27.2 | 5.33 | 31.7 | 22.0 | 57.1 |


## 4. Registro de iterações: Projeto A → Projeto B → Final

| projeto (50 mm) | massa g | fixação estática | 1 g: % soltas | 1 g pior inclinação graus | 2 g: % soltas | 1 g sem escorregar |
|---|---|---|---|---|---|---|
| A (massa do UMEH-1 na geometria B) | 194 | **FALHA** | 95.2 | 4.98 | 97.8 | **FALHA** |
| B | 147 | **FALHA** | 89.5 | 4.99 | 96.2 | **FALHA** |
| Final | 173 | PASSA | 0 | 0.390 | 1.42 | PASSA |


Cada mudança foi forçada por uma falha calculada, não por gosto:

| # | mudança | falha que a forçou | evidência |
|---|---|---|---|
| 1 | Módulo redimensionado só para 40–60 mm (Ø da interface a partir do driver de 60 mm + paredes dos insertos) | a interface Ø118 do UMEH-1 servia 40–600 mm: massa | §5 |
| 2 | Olhal da ligação movido da almofada mastoide para a ponta da concha, uma posição de olhal por módulo | pré-carga pelo contato mais baixo não dá momento restaurador → inclina/desliza sob 1 g; módulos mais pesados precisam do olhal mais alto | §6, §7 |
| 3 | Barra da sela curvada no arco da raiz da orelha (R, ±φ) | barra reta: frente–trás preso só por atrito → escorregamento grosseiro | §6 |
| 4 | Almofada póstero-superior adicionada; almofadas reposicionadas e aumentadas; pré-carga reajustada | o polígono de apoio precisa conter a linha da pré-carga com margem; pressão na pele ≤ 4 kPa | §7, §18 |
| 5 | O contato com a hélice deixou de ser considerado | sua rigidez é desconhecida (150–1000 N/m [A]) | §9 |
| 6 | Braçadeiras serrilhadas, torque baixo, arruelas onduladas | a braçadeira por atrito perde a maior parte da pré-carga por fluência; o arrancamento do inserto limita a pré-carga | §13 |
| 7 | Fio da ligação re-deduzido (Ø, voltas no ápice) | pré-carga maior + caminho mais longo em volta do módulo | §11 |
| 8 | Clipe do cabo virou guia de passagem; o plugue de 2 pinos é o fusível; a ancoragem mantém M3 | a fixação por interferência não se controla dentro da tolerância FDM; insertos M2.5 da ancoragem falham na carga do fusível | §14 |
| 9 | Solver trocado por minimização incremental convexa de energia (resíduo verificado); sequências de colocação A/B | o solver anterior (return mapping) travava no piso de arredondamento e relatava solturas falsas | §6 |
| 10 | Face de silicone moldada nas almofadas temporal e mastoide | demanda de atrito estático da almofada mastoide acima do μ de projeto do TPU | §9 |
| 11 | Barra do braço 4.0 → 5.5 mm; pés 5.0 → 4.5 mm; parede da concha 1.6 → 1.2 mm | carga de manuseio de 10 N numa almofada; depois otimização de peso | §5, §12 |
| 12 | Aba do anel estendida até uma ponta redonda completa em volta do inserto externo | a aba terminava no centro do inserto externo (metade do inserto fora da peça) — defeito de CAD achado pela verificação da malha | §20 |
| 13 | Trava de giro: fundo rígido + tiras de espuma anti-chocalho em vez de uma junta de TPU comprimida | a compressão da junta na cadeia de tolerâncias FDM vai de zero a apertada demais | §13, §17 |
| 14 | Junta do braço de volta a M3 (insertos a 11 mm) a 0.10 N·m; dispersão do aperto tratada explicitamente (fator de porca 0.20–0.35); ancoragem do cabo a 0.10 N·m | a opção de peso M2.5: FS de engate das serrilhas 0.806, FS de arrancamento 0.637 sob a carga de manuseio de 10 N com a dispersão da pré-carga (§5, W1); M3 a 0.15 N·m: FS de arrancamento 0.854 na maior pré-carga (§13) | §5, §13 |
| 15 | Braços modelados como vigas elásticas em série com os contatos; pernas 5.0 → 5.5 mm | a suposição de braço rígido era falsa: a flexão no plano da perna mastoide deixava a almofada passar peso para a raiz da orelha (pressão na raiz por espessura de perna: tabela de peso §5, tabela de alavancas §6) | §5, §6, §12 |
| 16 | Ressalto do olhal restaurado dentro da concha; feltro traseiro colado por um aro adesivo em vez de um anel prensado | defeito de CAD: o corte do furo removia o ressalto acima da ponta de 2 mm da concha, deixando 2 mm de material ao inserto de 4 mm do olhal; o FS circunferencial sustentado do anel de PETG ficava abaixo de 1 na tolerância superior de interferência e ele colidiria com o ressalto | §13, §20 |
| 17 | Solver: passos de Newton abaixo da resolução de ponto flutuante de Π aceitos pela palavra do modelo | com os graus de liberdade dos braços a busca linear de energia travava no piso de arredondamento de Π em vez de convergir | §6 |
| 18 | Revestimento de silicone macio de 2.5 mm (Shore 00-30) moldado na face de apoio da barra da sela | sem revestimento, a pressão na raiz na colocação A fica acima do limite de 4 kPa em qualquer posição de olhal na concha (grade de 4 mm) a 55 mm (melhor olhal 4.33 kPa) e 60 mm (melhor olhal 4.54 kPa). Das outras alavancas isoladas (braços mais grossos, almofadas maiores, ângulo do arco, pré-carga) nenhuma alcança a margem de 5 % na raiz a 60 mm (tabela de alavancas §6) | §6 |
| 19 | Conjunto de carga de 1 g transformado numa grade determinística (bordas dos cones de inclinação e de cabo incluídas) com verificação densa; pré-carga da ligação ajustada junto com os olhais (4.20 → 5.00 N), olhais movidos Δy -7.00–-5.00 mm, Δx -3.00–1.00 mm; fio da ligação Ø2.00 mm / 8 espiras → Ø2.50 mm / 4 espiras (A: supõe-se em estoque, confirmar com o fornecedor), redimensionado para a pré-carga (§11) | na grade de 1 g (§8) o primeiro Final falha em 5 de 5 módulos (54 soltas, 153 com tripé perdido, 135 inclinadas demais de 28050 combinações; pior inclinação 4.98°): cabeça inclinada 45.0–45.0° da vertical; 331 de 331 com este lado pendendo para fora (cabeça inclinada para ele, esta orelha para baixo) e 317 de 331 com o cabo puxando para fora (317 ambos); o seu ajuste tinha aprovado esses olhais numa amostra quase uniforme (§8); com a grade (e o fio de cada nível, §11), níveis de pré-carga mais baixos deixaram módulos sem olhal aprovado: 4.20 N (todos os módulos); 4.60 N (todos os módulos) | §7, §8, §11 |
| 20 | Solver: um incremento de carga cuja minimização para numa posição limitada é cortado ao meio (até 3 vezes) antes de declarar uma soltura | sem os cortes o solver soltava estas combinações da verificação densa de 1 g, que se mantêm com mais incrementos ou com a carga alterada em 1e-4 — minimizações travadas, não solturas: 40 mm: soltou com 4 incrementos (parou numa posição limitada, 0.175 mm / 0.113°), manteve com 5, 8, 16, 32 incrementos e com a carga × (1 ± 1e-4); com os cortes ele se mantém (inclinação 0.146°); 45 mm: soltou com 4 incrementos (parou numa posição limitada, 0.178 mm / 0.0671°), manteve com 5, 8, 16, 32 incrementos e com a carga × (1 ± 1e-4); com os cortes ele se mantém (inclinação 0.0243°) (`results/solver_stall_check.json`, `calc/check_stall.py`) | §6, §8 |
| 21 | Passos de azimute da grade de 1 g reduzidos à metade; refinamento local adicionado à verificação densa; o ajuste dos olhais verifica sua escolha nos dois (etapa 4) e foi rodado de novo | com a grade a cada 45.0° (gravidade) / 45.0° (cabo) os olhais ajustados falharam a 60 mm (verificação densa: 0 soltas, 1 tripé perdido, 0 inclinadas demais, menor margem de assento -0.000789 N; refinamento: 46 de 3102 falhando, menor -0.0121 N); a pior combinação não é um ponto daquela grade (§8), olhais movidos Δy 0–2.00 mm, Δx 0–1.00 mm | §7, §8 |

Depois da última iteração o Final foi verificado no estado de uso (§6, acomodação por atrito sob o conjunto de movimentos da cabeça de 1 g): a raiz da orelha então carrega 18.0–21.4 kPa, acima da meta sustentada de 4 kPa que as mudanças de perna e revestimento (15, 18) tinham atendido logo após colocar. O estudo de alavancas ali não acha nenhuma mudança dentro deste conceito que atenda, então a iteração para aqui com esse requisito em aberto.

## 5. Propriedades de massa pelo CAD, divisão do peso e otimização

Método: cada peça é exportada pelo OpenSCAD na sua posição montada; volume V, centroide e o tensor de inércia completo são integrados exatamente sobre a malha de triângulos (tetraedros com sinal, teorema da divergência) [CAD]. Massa impressa m = ρ f V com o fator de preenchimento casca + enchimento f = s + (1 − s)·infill, s = min(1, A_sup·n_perím·w_linha / V) (A_sup da malha) [C]. Ferragens são massas pontuais nas suas posições do CAD [DS]. O driver é um sólido de massa equivalente do seu envelope no CAD, escalado para a massa do driver [A]. O CG usado por todos os casos de carga é este CG do CAD.

Final, 50 mm (um lado):

| peça | massa g | preench. f | x mm | y mm | z mm | origem |
|---|---|---|---|---|---|---|
| ring (anel) | 33.9 | 1.00 | -3.07 | -0.494 | 34.7 | CAD |
| gasket_umi (junta UMI) | 0.0350 | 1.00 | 5.05 | 6.54e-06 | 35.9 | CAD |
| arm_saddle (braço da sela) | 8.47 | 1.00 | -4.94 | 56.4 | 13.0 | CAD |
| arm_temporal (braço temporal) | 3.16 | 1.00 | 58.1 | 21.1 | 18.8 | CAD |
| arm_mastoid (braço mastoide) | 3.36 | 1.00 | -40.4 | -46.5 | 18.3 | CAD |
| arm_post (braço póstero-superior) | 3.08 | 1.00 | -59.6 | 17.1 | 19.1 | CAD |
| pad_post (almofada póstero-superior) | 2.75 | 0.559 | -56.7 | 16.3 | 3.74 | CAD |
| saddle_cap (tampa da sela) | 6.83 | 0.830 | -2.20 | 25.2 | 2.66 | CAD |
| pad_temporal (almofada temporal) | 2.40 | 0.618 | 54.0 | 19.7 | 4.04 | CAD |
| pad_mastoid (almofada mastoide) | 3.49 | 0.602 | -38.1 | -43.8 | 4.05 | CAD |
| baffle | 15.3 | 1.00 | 0.204 | 0.278 | 33.0 | CAD |
| gasket_driver (junta do driver) | 0.556 | 1.00 | 4.17e-14 | -8.87e-14 | 33.9 | CAD |
| cup (concha) | 23.5 | 1.00 | -0.162 | 0.135 | 46.4 | CAD |
| cable_anchor (ancoragem do cabo) | 3.92 | 1.00 | 15.6 | -58.2 | 22.0 | CAD |
| cable_clip (clipe do cabo) | 0.933 | 1.00 | 20.7 | -77.2 | 16.0 | CAD |
| pad_face_temporal (face da almofada temporal) | 0.948 | 1.00 | 54.0 | 19.7 | 2.61 | CAD |
| pad_face_mastoid (face da almofada mastoide) | 1.30 | 1.00 | -38.1 | -43.8 | 2.52 | CAD |
| saddle_liner (revestimento da sela) | 0.922 | 1.00 | -1.19 | 13.7 | 3.31 | CAD |
| driver | 26.0 | 1468 | -4.55e-16 | -7.24e-16 | 39.8 | CAD |
| parafuso M3 + inserto @95° | 1.28 | 1.00 | -4.55 | 52.0 | 34.5 | DS |
| arruela ondulada M3 @95° | 0.0476 | 1.00 | -4.55 | 52.0 | 40.0 | C |
| parafuso M3 + inserto @95° | 1.28 | 1.00 | -5.51 | 63.0 | 34.5 | DS |
| arruela ondulada M3 @95° | 0.0476 | 1.00 | -5.51 | 63.0 | 40.0 | C |
| parafuso M3 + inserto @20° | 1.28 | 1.00 | 49.1 | 17.9 | 34.5 | DS |
| arruela ondulada M3 @20° | 0.0476 | 1.00 | 49.1 | 17.9 | 40.0 | C |
| parafuso M3 + inserto @20° | 1.28 | 1.00 | 59.4 | 21.6 | 34.5 | DS |
| arruela ondulada M3 @20° | 0.0476 | 1.00 | 59.4 | 21.6 | 40.0 | C |
| parafuso M3 + inserto @229° | 1.28 | 1.00 | -34.2 | -39.4 | 34.5 | DS |
| arruela ondulada M3 @229° | 0.0476 | 1.00 | -34.2 | -39.4 | 40.0 | C |
| parafuso M3 + inserto @229° | 1.28 | 1.00 | -41.5 | -47.7 | 34.5 | DS |
| arruela ondulada M3 @229° | 0.0476 | 1.00 | -41.5 | -47.7 | 40.0 | C |
| parafuso M3 + inserto @285° | 1.28 | 1.00 | 14.5 | -54.2 | 34.5 | DS |
| arruela ondulada M3 @285° | 0.0476 | 1.00 | 14.5 | -54.2 | 40.0 | C |
| parafuso M3 + inserto @285° | 1.28 | 1.00 | 16.4 | -61.0 | 34.5 | DS |
| arruela ondulada M3 @285° | 0.0476 | 1.00 | 16.4 | -61.0 | 40.0 | C |
| parafuso M3 + inserto @164° | 1.28 | 1.00 | -50.2 | 14.4 | 34.5 | DS |
| arruela ondulada M3 @164° | 0.0476 | 1.00 | -50.2 | 14.4 | 40.0 | C |
| parafuso M3 + inserto @164° | 1.28 | 1.00 | -60.8 | 17.4 | 34.5 | DS |
| arruela ondulada M3 @164° | 0.0476 | 1.00 | -60.8 | 17.4 | 40.0 | C |
| parafuso M3 + porca do clipe | 1.23 | 1.00 | 17.8 | -66.4 | 12.0 | DS |
| parafuso M2.5 + porca da almofada @20° | 0.720 | 1.00 | 54.0 | 19.7 | 10.5 | DS |
| parafuso M2.5 + porca da almofada @229° | 0.720 | 1.00 | -38.1 | -43.8 | 10.5 | DS |
| parafuso M2.5 + porca da almofada @164° | 0.720 | 1.00 | -56.7 | 16.3 | 10.5 | DS |
| pino M2 + porca da tampa da sela | 0.450 | 1.00 | -2.79 | 31.9 | 3.25 | DS |
| parafuso M2.5 + inserto da concha | 1.30 | 1.00 | 29.7 | 17.1 | 46.1 | DS |
| parafuso M2.5 + inserto da concha | 1.30 | 1.00 | -29.7 | 17.1 | 46.1 | DS |
| parafuso M2.5 + inserto da concha | 1.30 | 1.00 | -6.3e-15 | -34.3 | 46.1 | DS |
| disco de feltro | 0.584 | 1.00 | 0 | 0 | 52.1 | C |
| soquete de 2 pinos + fios + JST | 2.00 | 1.00 | 15.3 | -57.2 | 24.0 | A |
| olhal da ligação: parafuso M2.5 + inserto + arruela + luva | 2.16 | 1.00 | -19.0 | 7.00 | 56.1 | DS |
| ligação occipital, parte carregada pelo suporte | 6.17 | 1.00 | -44.0 | -3.00 | 41.1 | C |


| D | M g | x̄ mm | ȳ mm | z̄ mm | Ixx g·mm² | Iyy | Izz | Ixy | Ixz | Iyz |
|---|---|---|---|---|---|---|---|---|---|---|
| 40 | 156 | -4.54 | 0.0313 | 29.6 | 204915 | 178708 | 322413 | -11115 | -1891 | 4863 |
| 45 | 163 | -4.51 | 0.0271 | 30.4 | 208964 | 184351 | 327765 | -11118 | -1803 | 4872 |
| 50 | 173 | -4.30 | 0.0266 | 31.3 | 214904 | 191055 | 334904 | -11112 | -2050 | 4869 |
| 55 | 182 | -4.07 | 0.0266 | 32.2 | 221076 | 196898 | 341514 | -11095 | -2405 | 4856 |
| 60 | 190 | -3.89 | 0.0215 | 33.0 | 228223 | 204202 | 350273 | -11089 | -2686 | 4856 |


![massa](fig/mass_breakdown.png)

Otimização de peso a 50 mm — cada opção sozinha contra a linha de base antes da otimização (massa do CAD), com a verificação que ela afeta:

| opção | massa g | Δ g | verificação afetada | decisão |
|---|---|---|---|---|
| linha de base (parafusos M3 dos braços 0.15 N·m, parede da concha 1.6, pernas/pés 5/5; revestimento da sela como no Final) | 175 |  | FS de manuseio 1.72 (sela: barra na borda da braçadeira (fim do rasgo)); p na raiz a 60 mm 3.83 kPa |  |
| W1 parafusos dos braços M3 -> M2.5 (passo dos insertos 11 -> 7 mm) a 0.10 N·m | 165 | -9.91 | F_i 114–200 N (dispersão de torque), FS de arrancamento 0.950 só na maior pré-carga; manuseio 10 N: FS mín. de engate 0.806, FS mín. de arrancamento 0.637 (≥ 1) | rejeitada: FS de arrancamento 0.950 < 1 na maior pré-carga; FS da junta do braço 0.637 < 1 |
| W1b parafusos da ancoragem M3 -> M2.5 a 0.10 N·m | 174 | -1.43 | F_i 114–200 N (dispersão de torque), FS de arrancamento 0.950 só na maior pré-carga; FS do inserto da ancoragem 0.699 na carga superior do fusível | rejeitada: FS de arrancamento 0.950 < 1 na maior pré-carga; FS do inserto da ancoragem 0.699 < 1 na carga superior do fusível |
| W3 parede da concha 1.6 -> 1.2 mm | 173 | -1.62 | 2.86 perímetros; olhal r_máx 22.2 mm | adotada |
| W4a pés 5 -> 4.5 mm | 174 | -0.863 | FS de manuseio 1.72 (sela: barra na borda da braçadeira (fim do rasgo)) | adotada |
| W4b pernas 5 -> 4.5 mm | 175 | -0.299 | FS de manuseio 1.72 (sela: barra na borda da braçadeira (fim do rasgo)); p na raiz a 60 mm 4.06 kPa (≤ 4) | rejeitada: p na raiz 4.06 > 4 kPa |
| W4c pernas 5 -> 6.5 mm | 176 | 0.898 | FS de manuseio 1.72 (sela: barra na borda da braçadeira (fim do rasgo)); p na raiz a 60 mm 3.46 kPa (≤ 4) | não adotada |
| W4e pernas 5 -> 5.5 mm | 175 | 0.299 | FS de manuseio 1.72 (sela: barra na borda da braçadeira (fim do rasgo)); p na raiz a 60 mm 3.66 kPa (≤ 4) | adotada (massa acrescentada) |
| W4d pernas/pés 5/5 -> 4/4 mm | 173 | -2.35 | FS de manuseio 1.45 (sela: filete da base da perna); p na raiz a 60 mm 4.34 kPa (≤ 4) | rejeitada: FS de manuseio 1.45 < γM 1.6; p na raiz 4.34 > 4 kPa |
| W5 passo dos insertos dos parafusos do braço 11 -> 10 mm a 0.10 N·m | 173 | -1.49 | ; manuseio 10 N: FS mín. de engate 1.08, FS mín. de arrancamento 1.13 (≥ 1) | não adotada: menor FS da junta 1.08 contra 1.15 no Final (§13) |
| W2 enchimento do anel 30 -> 20 % |  | 0 | fração de casca do anel 1.00 | não adotada: sem economia de massa (fração de casca do anel 1.00) |
| Final (W3 + W4a + W4e, parafusos M3 dos braços a 0.10 N·m, parafusos M3 da ancoragem a 0.10 N·m, correção da aba, revestimento da sela) | 173 | -2.17 | FS de manuseio 1.72 (sela: barra na borda da braçadeira (fim do rasgo)); p na raiz a 60 mm 3.61 kPa; juntas FS mín. de engate 1.15, arrancamento 1.15 |  |


Espessura da barra do braço contra a carga de manuseio de 10 N: 5.50 mm → FS 1.72, 5.35 mm → FS 1.64, 5.40 mm → FS 1.66, 5.25 mm → FS 1.58. Na tolerância de impressão XY de −0.15 mm a barra de 5.5 mm mantém FS 1.64 (≥ γM 1.6); um passo de 0.1 mm mais fina, a sua seção na tolerância dá 1.58 (< γM), então a barra é o passo de 0.1 mm mais fino que mantém γM na tolerância.

## 6. Fixação na orelha — o modelo de contato com atrito estaticamente indeterminado

O anel é um corpo rígido; cada braço é uma viga elástica (pé, perna e barra com flexibilidades axial, nos dois cisalhamentos, em torção
e nas duas flexões, E e G a 40 °C, engastada na sua braçadeira) em série com os seus contatos, que são flexíveis, **unilaterais** e
com atrito; mais a ligação occipital (mola lateral k_lado com pré-carga P, pequena rigidez no plano de 40 N/m). Um braço que carrega uma
almofada acrescenta um nó de 3 graus de liberdade no contato da almofada com rigidez K = (L C_ponta Lᵀ)⁻¹; o braço da sela (as duas zonas da raiz e o contato no couro cabeludo
numa mesma tampa) acrescenta um nó de 6 graus de liberdade na sua ponta com K = C_ponta⁻¹ (C_ponta: método da carga unitária ao longo da linha média do braço,
`structure.arm_tip_compliance`; L leva o movimento da ponta ao ponto de contato). Deslocamento generalizado q = [u, θ, nós dos braços]
(6 + 15 graus de liberdade no Final); para o contato i com normal n_i e braço de alavanca r_i a linha j_i = [n_i, r_i × n_i, n_i·L_i], compressão
δ_i = −j_i·q, escorregamento tangencial t_i = J_t,i q. O problema é estaticamente indeterminado (6 contatos no Final × 3 componentes de força +
ligação contra 6 equações), então a divisão da carga vem da compatibilidade e da rigidez de cada contato em série com o seu
braço — não se supõe que um apoio carregue uma parte igual. A flexibilidade dos braços importa (calculado abaixo, "O que define a carga na raiz
da orelha", e a tabela do §12 de flexibilidade do braço contra a do contato).

**Solução (por passo de carga):** o potencial incremental

    Π(q) = ½ qᵀ K_L q − q·W + Σ_i ½ k_n,i ⟨δ_i⟩₊² + Σ_i H_i(|J_t,i q − s_i|)

é minimizado, onde ⟨·⟩₊ mantém só a compressão (contato unilateral), s_i é o escorregamento acumulado e H é a função de Huber
da mola tangencial com o limite de atrito g_i = μ F_n,i (aderência ½ k_t t², deslizamento g t − g²/2k_t). Para um dado limite de atrito
Π é convexa e C¹, então um ponto estacionário é o seu mínimo global e satisfaz as seis equações de equilíbrio ΣF = 0, ΣM = 0
junto com as leis de contato e de atrito; o resíduo impresso é a verificação. O limite de atrito segue F_n por um ponto fixo (Tresca → Coulomb). Os passos de Newton são truncados
na primeira mudança de contato ou de aderência/deslizamento (retrocesso só como salvaguarda; um passo cuja variação de energia prevista está abaixo da
resolução de ponto flutuante de Π é aceito pela palavra do modelo e o gradiente decide a convergência); a carga é aplicada em 4
passos de rampa com um return mapping do escorregamento. **Escorregamento grosseiro /
soltura** = nenhum minimizador limitado (a minimização dispara além de 9 mm ou 15°), ou o minimizador
convergido além de 3 mm ou 5° (o suporte saiu do seu assento). Uma minimização que para numa posição limitada
sem convergir (busca linear sem decréscimo representável, limite de iterações ou do ponto fixo de Coulomb) é uma falha numérica do
incremento, não uma soltura: esse incremento é cortado ao meio, resolvido por partes a partir do último estado convergido, até 1/8 de um
passo (mudança 20); um que ainda falha é contado como soltura e marcado como numérico.

**Colocação:** um suporte montado na cabeça é colocado com a mão, então o estado estático depende da sequência. A: a mão segura o suporte
no lugar enquanto a ligação é presa (a pré-carga se acomoda sem atrito), e depois solta — o peso é somado com o atrito
ativo (conservador para escorregamento; estado de base de todos os casos de carga). B: o suporte é pendurado primeiro na raiz da orelha e depois preso — o
limite superior da carga na raiz (sela). Os dois são relatados.

Rigidez de contato = núcleo da almofada em série com a face e o tecido: k = 1/(h_núcleo/(E_núcleo A) + t_face/(E_face A) + t_tecido/(E_tecido A)),
E_núcleo = 0.045·E_TPU (giroide 15 % [LIT]), A = 50 % da elipse da almofada [A]; k_t = 0.5 k_n [A] (abaixo da razão de Mindlin
2(1−ν)/(2−ν) = 0.67 de um semiespaço incompressível, ν = 0.5, para a camada flexível de cisalhamento da pele). Sela: duas zonas de apoio no arco da raiz da orelha a ±φ, normais inclinadas para a frente/trás; cada zona é a parede de TPU da tampa,
o revestimento de silicone macio moldado e o tecido da raiz em série, k = 1/(t_tampa/(E_tampa A) + t_L/(E_c A) + t_raiz/(E_raiz A)). O revestimento
é uma camada fina, quase incompressível, colada à tampa e presa à pele, então o seu módulo de compressão é E_c = E (1 + 2 k S²)
(Gent–Lindley, k = 1 no limite incompressível, o extremo mais rígido), S = w l / (2 (w + l) t_L) para a área carregada w × l; E = 3 σ₁₀₀ / 1.75
a partir do módulo a 100 % da ficha técnica (neo-Hookeano) [DS → C]. O revestimento faz do contato na raiz um contato silicone sobre pele.

Pressão: a meta sustentada de 4 kPa é aplicada à pressão MÉDIA de contato F_n/A [A: convenção de projeto]. O centro da cúpula
carrega mais: um paraboloide sobre uma camada fina e macia sobre osso (base de Winkler, p = k(δ − r²/2R)) tem pico de 2 × a média [C] (um semiespaço de Hertz
daria 1.5). Os picos são relatados em todas as tabelas; onde passam de 4 kPa isso é um risco de conforto a verificar em testes de
uso, não uma aprovação.

| contato | x mm | y mm | z mm | normal | k_n N/m [C] | área mm² [A] | μ de projeto | par |
|---|---|---|---|---|---|---|---|---|
| T temporal | 54.0 | 19.7 | 0 | (0.00, 0.00, 1.00) | 7870 | 518 | 0.560 | silicone/pele seca |
| M mastoide | -38.1 | -43.8 | 0 | (0.00, 0.00, 1.00) | 19344 | 757 | 0.560 | silicone/pele seca |
| P póstero-sup. | -56.7 | 16.3 | 0 | (0.00, 0.00, 1.00) | 7948 | 518 | 0.200 | TPU/cabelo (sobre o temporal) |
| S raiz F (frente) | 11.6 | 11.8 | 3.25 | (0.50, 0.87, 0.00) | 2417 | 70.0 | 0.560 | silicone/pele seca |
| S raiz B (trás) | -13.5 | 9.63 | 3.25 | (-0.64, 0.77, 0.00) | 2417 | 70.0 | 0.560 | silicone/pele seca |
| S couro cabeludo | -2.09 | 23.9 | 0 | (0.00, 0.00, 1.00) | 3725 | 224 | 0.200 | TPU/cabelo (sobre o temporal) |


Estático, cabeça ereta, 1 g, Final 40 mm, colocação A — força da ligação (5.72e-05, 0.000725, -4.65) N, rotação (-0.0746, -0.00591, -0.0268) graus, resíduo de equilíbrio 4.43e-09 (N, N·m):

| contato | Fn N | Ft N | μ exigido | p média kPa | p pico kPa | deslizando |
|---|---|---|---|---|---|---|
| T temporal | 1.29 | 0.415 | 0.323 | 2.49 | 4.97 | Não |
| M mastoide | 1.59 | 0.503 | 0.317 | 2.10 | 4.20 | Não |
| P póstero-sup. | 1.38 | 0.233 | 0.169 | 2.67 | 5.33 | Não |
| S raiz F | 0.207 | 0.0724 | 0.350 | 2.96 | 5.92 | Não |
| S raiz B | 0.185 | 0.0608 | 0.329 | 2.64 | 5.27 | Não |
| S couro cabeludo | 0.360 | 0.0720 | 0.200 | 1.61 | 3.21 | Sim |


Estático, cabeça ereta, 1 g, Final 50 mm, colocação A — força da ligação (0.00097, 0.000469, -4.97) N, rotação (-0.0859, -0.0296, -0.0300) graus, resíduo de equilíbrio 5.15e-09 (N, N·m):

| contato | Fn N | Ft N | μ exigido | p média kPa | p pico kPa | deslizando |
|---|---|---|---|---|---|---|
| T temporal | 1.19 | 0.461 | 0.388 | 2.30 | 4.60 | Não |
| M mastoide | 1.76 | 0.551 | 0.313 | 2.33 | 4.65 | Não |
| P póstero-sup. | 1.61 | 0.257 | 0.160 | 3.11 | 6.21 | Não |
| S raiz F | 0.229 | 0.0808 | 0.353 | 3.27 | 6.53 | Não |
| S raiz B | 0.202 | 0.0672 | 0.333 | 2.88 | 5.76 | Não |
| S couro cabeludo | 0.378 | 0.0757 | 0.200 | 1.69 | 3.38 | Sim |


Estático, cabeça ereta, 1 g, Final 60 mm, colocação A — força da ligação (0.000619, 0.00118, -5.30) N, rotação (-0.0757, -0.0205, -0.0339) graus, resíduo de equilíbrio 5.98e-09 (N, N·m):

| contato | Fn N | Ft N | μ exigido | p média kPa | p pico kPa | deslizando |
|---|---|---|---|---|---|---|
| T temporal | 1.31 | 0.511 | 0.391 | 2.52 | 5.05 | Não |
| M mastoide | 1.96 | 0.601 | 0.307 | 2.59 | 5.17 | Não |
| P póstero-sup. | 1.60 | 0.280 | 0.175 | 3.10 | 6.20 | Não |
| S raiz F | 0.253 | 0.0898 | 0.355 | 3.61 | 7.22 | Não |
| S raiz B | 0.223 | 0.0740 | 0.331 | 3.19 | 6.38 | Não |
| S couro cabeludo | 0.391 | 0.0782 | 0.200 | 1.75 | 3.49 | Sim |


Sequência de colocação B (pendurado na raiz da orelha, depois preso) — a maior carga na raiz que uma sequência de colocação dá (o movimento da cabeça depois desloca ainda mais a carga, veja a acomodação abaixo):

| D | ΣFn na raiz N | p média na raiz kPa | p pico na raiz kPa | p máx. na pele kPa |
|---|---|---|---|---|
| 40 | 1.93 | 15.4 | 30.8 | 2.70 |
| 45 | 2.00 | 16.0 | 32.0 | 3.02 |
| 50 | 2.12 | 17.0 | 33.9 | 3.14 |
| 55 | 2.23 | 17.8 | 35.6 | 3.09 |
| 60 | 2.33 | 18.6 | 37.2 | 3.13 |


Na sequência B a pressão média na raiz passa da meta sustentada de 4.00 kPa em 40, 45, 50, 55, 60 mm mesmo com o revestimento, então a instrução de colocação é prender primeiro e depois soltar (sequência A). Nenhum dos dois estados após colocar dura quando a cabeça se move: veja *O estado sustentado em uso* no fim desta seção.

**O que define a carga na raiz da orelha.** Em repouso (colocação A) o peso é dividido por compatibilidade: as zonas da raiz o carregam por força normal, as almofadas pelas suas molas tangenciais através dos braços. A parte da raiz, portanto, segue a sua rigidez normal contra a rigidez tangencial das almofadas, e as camadas de tecido mole dominam as duas, de modo que braços mais rígidos a mudam pouco. Cada linha mantém as propriedades de massa do CAD do Final para o seu tamanho; estático, cabeça ereta:

| variante | p raiz 55 mm kPa | p raiz 60 mm kPa | parte do peso na raiz % (60) | p máx. na pele kPa (60) | demanda de μ estático (60) | 60 mm: raiz ≤ 4.00 kPa e μ ≤ 1 |
|---|---|---|---|---|---|---|
| Final (revestimento 2.5 mm) | 3.44 | 3.61 | 20.9 | 3.10 | 0.874 (póstero-superior) | PASSA |
| sem revestimento (resto como o Final) | 4.41 | 4.63 | 26.9 | 3.10 | 0.800 (póstero-superior) | **FALHA** |
| revestimento 2 mm | 3.77 | 3.96 | 22.9 | 3.10 | 0.849 (póstero-superior) | PASSA |
| revestimento 3 mm | 3.12 | 3.28 | 19.0 | 3.10 | 0.899 (póstero-superior) | PASSA |
| sem revestimento, braços rígidos | 3.37 | 3.54 | 20.4 | 2.99 | 0.811 (póstero-superior) | PASSA |
| revestimento 2.5 mm, braços rígidos | 2.55 | 2.68 | 15.5 | 2.97 | 0.880 (póstero-superior) | PASSA |
| revestimento 2.5 mm, pernas 5 mm | 3.60 | 3.78 | 21.9 | 3.11 | 0.886 (póstero-superior) | PASSA |
| sem revestimento, pernas 5.0 mm | 4.60 | 4.83 | 28.1 | 3.12 | 0.811 (póstero-superior) | **FALHA** |
| sem revestimento, pernas 8.0 mm | 4.03 | 4.22 | 24.4 | 3.06 | 0.791 (póstero-superior) | **FALHA** |
| sem revestimento, pernas 9.0 + barra 7.5 mm | 3.80 | 3.99 | 23.1 | 3.05 | 0.786 (póstero-superior) | PASSA |
| sem revestimento, meio-ângulo do arco 45° | 4.01 | 4.21 | 21.1 | 3.11 | 0.828 (póstero-superior) | **FALHA** |
| sem revestimento, almofada temporal 1.1 × 1.5 maior (precisa de placa de apoio) | 3.82 | 4.01 | 23.4 | 3.16 | 0.834 (póstero-superior) | **FALHA** |
| sem revestimento, pré-carga +0.8 N | 4.41 | 4.63 | 26.8 | 3.79 | 0.650 (póstero-superior) | **FALHA** |


Com braços rígidos a raiz carregaria 20.4 % do peso em vez de 26.9 % (sem revestimento, 60 mm) — mas a almofada mastoide então precisaria de 0.811 × o seu atrito de projeto: a flexibilidade dos braços não é um erro gratuito. O revestimento baixa a parte da raiz para 20.9 % e passa a diferença para o atrito das almofadas; por isso o Final usa o revestimento mais fino que deixa margem de 5 % na raiz a 60 mm (2.5 mm). A linha da almofada temporal é a resposta do modelo para uma almofada totalmente apoiada; com o pé atual de 10 mm de largura a área extra não carregaria carga, então ela precisaria de uma placa de apoio de PETG (e chegaria ao arco zigomático).
 Linhas que passam com menos de 5 % de margem na raiz a 60 mm não foram adotadas, porque as rigidezes dos tecidos por trás da divisão são valores da literatura [A]: sem revestimento, pernas 9.0 + barra 7.5 mm (0.272 %).
 Linhas que acrescentam material (pernas ou barra mais grossas) mantêm as propriedades de massa do Final, então são otimistas pela própria massa acrescentada.
 Mudanças isoladas no layout das almofadas sem o revestimento (cada ângulo de almofada ±10°, cada raio −4 mm ou até o limite da busca; 10 de 12 dentro das restrições de layout do §7) dão no melhor caso 4.46 kPa a 60 mm (mastoid_a 229 → 239, demanda de μ estático 0.739; todas as linhas em results/root_levers.json).
 Sem o revestimento nenhuma posição de olhal na concha de 60 mm (82 posições, grade de 4 mm) leva a raiz abaixo de 4.54 kPa.


**Pernas dos braços e revestimento da sela, escolhidos juntos** (`calc/legs_liner.py`, results/legs_liner.json). Os dois movem peso entre a raiz da orelha e o atrito das almofadas: pernas mais finas mandam peso para a raiz, um revestimento mais grosso manda para as almofadas. Cada par recebeu as suas próprias propriedades de massa do CAD e os critérios estáticos do ajuste do olhal na grade de olhais de 4 mm das conchas de 55 e 60 mm (onde o limite da raiz aperta). Células: menor margem estática no melhor olhal, a pior entre 55/60 mm (margem da raiz / do atrito entre parênteses; ≥ 0 passa, a regra do revestimento pede ≥ 5 % na raiz):

| pernas \ revestimento | 1.5 mm | 2 mm | 2.5 mm | 3 mm |
|---|---|---|---|---|
| pernas 4.5 mm | -16.4 % (-16.4 / 24.5) | -8.28 % (-8.28 / 21.7) | 0.714 % (0.714 / 19.6) | 9.57 % (9.57 / 18.7) ◀ |
| pernas 5 mm | -9.47 % (-9.47 / 18.4) | -1.67 % (-1.67 / 16.5) | 6.95 % (6.95 / 13.6) ◀ | 14.5 % (14.5 / 15.1) |
| pernas 5.5 mm | -4.70 % (-4.70 / 14.0) | 2.90 % (2.90 / 12.2) | 10.8 % (11.4 / 11.3) ◀ | 16.0 % (18.3 / 16.0) |
| pernas 6 mm | -1.17 % (-1.17 / 11.7) | 6.28 % (6.28 / 9.90) ◀ | 13.8 % (13.8 / 21.0) | 16.5 % (21.0 / 16.5) |
| pernas 6.5 mm | 1.26 % (1.26 / 9.38) | 8.65 % (8.65 / 8.74) ◀ | 15.0 % (15.0 / 18.9) | 16.6 % (23.0 / 16.6) |


◀ = a regra do revestimento para aquela espessura de perna (revestimento mais fino com margem ≥ 5 % na raiz nos dois tamanhos). Esses pares foram então rodados pela avaliação do ajuste do olhal (estático + o seu conjunto de 1 g) em todo olhal que atende os critérios estáticos com a margem de 5 % na raiz, e pela sua avaliação completa (+ o conjunto reduzido de 2 g) nos 3 melhores olhais de cada tamanho que atendem o uso normal, com pré-carga da ligação de 5.00 N, o fio que o ajuste usa nessa pré-carga (Ø2.50 mm, 4 espiras) e a grade de 1 g de 5610 combinações:

| pernas / revestimento mm | massa a 60 mm g | olhal 55 mm | 55 mm margem mín. de uso normal | 55 mm 2 g soltas % (subconjunto) | olhal 60 mm | 60 mm margem mín. de uso normal | 60 mm 2 g soltas % (subconjunto) | uso normal | nota do ajuste, pior tamanho |
|---|---|---|---|---|---|---|---|---|---|
| 4.5 / 3 | 189.64 | (-19, 8) | 0.0806 | 5.31 | (-15, 8) | 0.0223 | 6.56 | PASSA | 2.05 |
| 5 / 2.5 | 189.85 | (-19, 8) | 0.104 | 4.62 | (-15, 8) | 0.0583 | 5.69 | PASSA | 2.12 |
| 5.5 / 2.5 | 190.15 | (-19, 8) | 0.143 | 4.50 | (-19, 8) | 0.0835 | 4.56 | PASSA | 2.17 |
| 6 / 2 | 190.36 | (-19, 8) | 0.0906 | 4.25 | (-7, 16) | -1.05 | – | **FALHA** | -1.05 |
| 6.5 / 2 | 190.67 | (-19, 8) | 0.111 | 4.25 | (-19, 8) | 0.0675 | 4.31 | PASSA | 2.17 |


Escolha: pernas de 5.5 mm com revestimento de 2.5 mm — todos os critérios de uso normal atendidos nos dois tamanhos e a maior nota do ajuste no pior tamanho (pares a menos de 0.02 dela contam como iguais e o mais leve deles vence). Os pares mais leves economizam até 0.51 g por lado, mas soltam 5.7–6.6 % do conjunto reduzido de 2 g no pior tamanho, contra 4.6 %. O próprio olhal é então ajustado por módulo para este par (§7).

**O estado sustentado em uso: acomodação por atrito sob o movimento da cabeça** (`calc/shakedown.py`, `support.shakedown`, results/shakedown.json). O estado logo após colocar é só onde o atrito começa. Em uso, a cabeça se move: cada combinação do conjunto normal de 1 g que o ajuste do olhal usa (5610 combinações: 33 direções da gravidade dentro do cone de inclinação da cabeça de 45°, 10 fases de rotação da cabeça, 17 direções do cabo) é aplicada a partir do estado atual e retirada de novo, ciclo após ciclo, com o mesmo atrito dependente do caminho (no máximo 25 ciclos; convergido quando nenhuma força normal de contato muda mais de 0.2 % do peso ao longo de um ciclo). Sempre que uma almofada chega ao seu limite de atrito durante uma combinação, ela escorrega um pouco e mantém esse deslocamento quando a carga é retirada, então o peso que as almofadas seguravam por atrito é passado, ciclo a ciclo, para os únicos apoios que o carregam por força normal: as zonas da raiz na sela, até que as forças de contato se repitam de um ciclo para o outro (as almofadas podem continuar escorregando para lá e para cá, mas a carga não se move mais). Verificações do procedimento a 60 mm: amplitude zero: raiz 3.61 → 3.61 kPa; almofadas sem escorregamento (μ = 10): raiz 3.61 → 11.3 kPa (uma almofada na pele ainda escorrega em 5–6 das 5610 combinações por ciclo, então μ = 10 não torna as almofadas antiderrapantes neste conjunto).

| D | p raiz após colocar (A) kPa | p raiz em uso (a partir de A) kPa | parte vertical do peso na raiz em uso % | ciclos | p raiz após colocar (B) kPa | p raiz em uso (a partir de B) kPa | p máx. nas almofadas em uso kPa | aplicações soltas |
|---|---|---|---|---|---|---|---|---|
| 40 | 2.96 | 18.0 | 117 | 6 | 15.4 | 18.0 | 2.72 | 0 de 33660 |
| 45 | 3.07 | 18.4 | 116 | 5 | 16.0 | 18.3 | 3.04 | 0 de 28050 |
| 50 | 3.27 | 19.4 | 116 | 5 | 17.0 | 19.4 | 3.16 | 0 de 28050 |
| 55 | 3.44 | 20.5 | 115 | 5 | 17.8 | 20.5 | 3.12 | 0 de 28050 |
| 60 | 3.61 | 21.4 | 114 | 5 | 18.6 | 21.4 | 3.16 | 0 de 28050 |


Em uso as zonas da raiz carregam 114–117 % do peso do lado (componente vertical) a 18.0–21.4 kPa de pressão média, 4.50–5.35 × a meta sustentada de 4 kPa — **o requisito de pressão sustentada na raiz NÃO é atendido em uso em 40, 45, 50, 55, 60 mm**; o valor logo após colocar (A) só vale até a cabeça se mover. A partir da sequência B o estado final é 18.0–21.4 kPa: a ordem de colocação deixa de importar depois que a cabeça se moveu. A 60 mm as zonas da raiz então carregam 2.59 N; a 4 kPa isso exige 6.46 cm² de apoio, contra os 1.40 cm² das duas zonas da raiz (support.ROOT_W × ROOT_LEN da raiz superior da orelha [A]).

Alavancas a 60 mm, cada linha é o Final com a mudança indicada (acomodação a partir de A):

| alavanca | p raiz após colocar kPa | p raiz em uso kPa | parte vertical na raiz % | p máx. nas almofadas em uso kPa | raiz e almofadas ≤ 4 kPa em uso |
|---|---|---|---|---|---|
| Final | 3.61 | 21.4 | 114 | 3.16 | **FALHA** |
| atrito das almofadas × 1.25 (o μ nominal: sem γμ) | 3.61 | 23.0 | 108 | 3.11 | **FALHA** |
| atrito das almofadas × 2 (almofadas com face μ 1.12, acima do valor superior da literatura de 1.00 para silicone em pele seca) | 3.61 | 20.4 | 86.4 | 3.09 | **FALHA** |
| almofada póstero-sup. também com face (μ 0.56) | 3.61 | 19.8 | 102 | 3.13 | **FALHA** |
| pré-carga da ligação × 1.2 | 3.61 | 21.2 | 105 | 3.99 | **FALHA** |
| pré-carga da ligação × 1.4 | 3.60 | 19.3 | 90.7 | 4.82 | **FALHA** |
| área de apoio na raiz × 2 (rigidez proporcional) | 2.92 | 10.3 | 116 | 3.14 | **FALHA** |
| área de apoio na raiz × 3 (rigidez proporcional) | 2.46 | 6.62 | 113 | 3.13 | **FALHA** |
| área de apoio na raiz × 2 e atrito das almofadas × 2 | 2.92 | 10.7 | 92.1 | 3.09 | **FALHA** |
| raiz sem atrito | 3.74 | 15.1 | 91.2 | 3.17 | **FALHA** |
| raiz 4 × mais macia (revestimento) | 1.13 | 20.9 | 102 | 3.20 | **FALHA** |
| braços rígidos | 2.68 | 19.9 | 109 | 3.00 | **FALHA** |


Nenhuma alavanca da tabela atende a meta em uso; a menor é 'área de apoio na raiz × 3 (rigidez proporcional)' com 6.62 kPa. Escalando a massa e a inércia do lado (mantendo o CG), o lado de 60 mm atende a meta de 4 kPa em uso só até 60.3 g, 31.7 % dos seus 190 g. As almofadas micro-escorregam no uso normal (§8: o critério de 1 g é nenhum escorregamento grosseiro, não nenhum escorregamento; no primeiro ciclo uma almofada na pele desliza no pico de 17.3–20.7 % das combinações, no último 16.9–20.2 %), e cada micro-escorregamento passa peso para a raiz; um suporte montado na orelha com esta massa precisa, portanto, ou de almofadas que não escorregam nada com o movimento da cabeça ou de um apoio de sustentação de peso com a área acima. Nenhum dos dois existe neste projeto, então este é o limite do conceito com esta massa, e a primeira coisa que os testes de uso devem medir (filme de pressão na raiz da orelha depois do uso com movimento da cabeça, §22).

Projeto B, mesmo caso: **nenhum equilíbrio estático** (o suporte tomba para fora da orelha).

