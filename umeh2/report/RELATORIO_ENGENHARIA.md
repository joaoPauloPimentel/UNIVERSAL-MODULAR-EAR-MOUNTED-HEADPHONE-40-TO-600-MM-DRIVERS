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

## 7. Layout dos apoios, linha da pré-carga e o olhal da ligação por módulo

Momento de tombamento por g: M₁ = m g z̄. Para que a pré-carga P (agindo ao longo de −z no olhal) e o peso deixem todas as almofadas carregadas,
a resultante de P e do binário do peso precisa ficar dentro do polígono das almofadas com margem: y_olhal ≈ y_centroide + M₁/P. Sob um fator
dinâmico n a resultante se move (n−1)M₁/P, então um P maior dá robustez, limitado pela pressão na pele. A borda do anel não
alcança esse ponto; a ponta da concha alcança. O layout do suporte (ângulos/raios e tamanho das almofadas) é comum a todos os módulos (busca máx–mín,
`umeh2/layout.py`: amostragem aleatória dos seus limites, depois uma busca por padrões nas coordenadas). Essa busca rodou durante as iterações com o modelo e a amostra de carga da época; `calc/final_layout.json` guarda o seu resultado arredondado a 0.5°/0.5 mm (a sua pré-carga, 4.20 N, é o primeiro nível de pré-carga do ajuste do olhal), ela não faz parte da cadeia que se roda de novo, e todo resultado deste relatório reverifica o layout com o modelo atual. O olhal faz parte do módulo e foi ajustado para cada tamanho de driver por `calc/tune_eye.py` com o modelo atual, junto com a pré-carga da ligação (um valor para todos os módulos: a ligação é comum). A pré-carga percorre níveis a partir dos 4.20 N do layout em passos de 0.400 N, cada um com o fio da ligação dimensionado para ele; toma-se o menor nível em que todo módulo tem candidatos na grade de olhais de 4 mm da etapa 1 que atendem todos os critérios de uso normal do ajuste (estático + a grade de 1 g) e um olhal das etapas 1–3 (ponto da grade ou do refinamento) que também passa na verificação densa e no seu refinamento [regra de projeto: a menor pré-carga mantém as pressões nas almofadas e a tensão no fio mais baixas], e as etapas seguintes rodam nesse nível: uma grade de 4 mm sobre a ponta da concha
(estático + a grade de 1 g de 33 direções da gravidade × 10 casos de movimento da cabeça × 17 direções do cabo = 5610 casos de carga por candidato, §8), o conjunto de 2 g para os melhores candidatos que atendem o uso normal (no máximo 10: 2 no módulo de 40 mm, 3 no de 45 mm, 3 no de 50 mm, 2 no de 55 mm, 2 no de 60 mm), depois refinamento de 2 e 1 mm em volta do melhor; por fim (etapa 4) a verificação densa de 1 g e o seu refinamento local (§8) nos melhores candidatos em ordem de nota até que um passe (no máximo 4 por módulo) — esse candidato é o olhal do módulo;
nota = a menor margem normalizada de uso normal, depois a fração solta em 2 g (peso 2) e a fração de micro-escorregamento das almofadas em 1 g (0.5).
Um candidato para no seu primeiro caso de 1 g que falha (ele não pode mais passar). As posições dos olhais ficam, portanto, numa grade de 1 mm (sem arredondamento adicional; tolerância de impressão XY ±0.15 mm). A coluna de 2 g é
o subconjunto reduzido do ajuste (10 direções dinâmicas × 4 gravidade × 10 movimento da cabeça × 4 cabo = 1600 casos de carga); o §8 dá o conjunto completo de 2 g do Final.

Níveis de pré-carga do ajuste (etapa 1, toda a grade de olhais de 4 mm de cada módulo; o fio da ligação de cada nível dimensionado em todos os módulos no olhal de referência do layout, trazido para dentro do limite de olhal do módulo quando fica fora; candidatos que atendem todos os critérios de uso normal / avaliados):

| P N | fio da ligação | 40 mm | 45 mm | 50 mm | 55 mm | 60 mm |  |
|---|---|---|---|---|---|---|---|
| 4.20 | Ø2.50 mm, 3 espiras | 0/– | 0/– | 0/– | 0/– | 0/– |  |
| 4.60 | Ø2.50 mm, 3 espiras | 0/– | 0/– | 0/– | 0/– | 0/– |  |
| 5.00 | Ø2.50 mm, 4 espiras | 2/– | 3/– | 3/– | 2/– | 2/– | **escolhido** |


Restrições de layout [A] (`layout.geometric_ok`, `layout.BOUNDS`): almofadas, sela e clipe do cabo a pelo menos 30° um do outro no anel (largura das abas, acesso aos parafusos); centros das almofadas dentro dos limites da busca. Verificado no Final: a borda interna de cada almofada (raio do centro − a/2) livra o meio comprimento p95 do pavilhão 36 mm + 2 mm = 38.0 mm do eixo do canal — temporal 40.6, mastoide 38.5, póstero-superior 42.1 mm.

**Registro do ajuste do olhal.** A saída própria do ajuste (results/eye_tuning.json) se perdeu com a máquina que o rodou. Olhais escolhidos e pré-carga: calc/final_layout.json; níveis de pré-carga e contagens de aprovação da etapa 1: results/eye_tuning_partial.log; valores por módulo: o objetivo do ajuste recalculado no olhal escolhido com as entradas do Final (results/eye_check.json); verificação: verificação densa de 1 g + refinamento do run_all.py (results/dense_1g.json). O ajuste rodou com fio Ø2.50 mm / 4 espiras, pernas 5.50 mm, revestimento 2.50 mm; as tabelas por candidato do ajuste (candidatos avaliados, cinco melhores, verificações da etapa 4 dos outros módulos) não estão disponíveis. A tabela abaixo é o objetivo do ajuste em cada olhal escolhido com as entradas do próprio Final; a verificação densa do §8 é a prova de aprovação/reprovação.

| D | olhal x mm | olhal y mm | margem mín. de uso normal | 2 g soltas (subconjunto) | micro-escorregamento das almofadas em 1 g | margem de atrito estático | margem de inclinação | margem de assento |
|---|---|---|---|---|---|---|---|---|
| 40 | -15.0 | 7.00 | 0.141 | 0.0475 | 0.663 | 0.154 | 0.794 | 0.141 |
| 45 | -18.0 | 7.00 | 0.215 | 0.0406 | 0.635 | 0.215 | 0.814 | 0.410 |
| 50 | -19.0 | 7.00 | 0.183 | 0.0394 | 0.641 | 0.201 | 0.805 | 0.232 |
| 55 | -18.0 | 7.00 | 0.140 | 0.0425 | 0.646 | 0.152 | 0.803 | 0.181 |
| 60 | -18.0 | 7.00 | 0.0978 | 0.0450 | 0.650 | 0.126 | 0.797 | 0.175 |


## 8. Casos de carga, combinação vetorial e busca da pior orientação

| caso | gravidade a até ° da vertical | aceleração dinâmica (g, qualquer direção) | α da cabeça rad/s² [A] | ω da cabeça rad/s [A] | puxão do cabo N [A] |
|---|---|---|---|---|---|
| 1 g normal | 45.0 | 0 | 50.0 | 3.00 | 0.500 |
| 2 g dinâmico | 30.0 | 1.00 | 100 | 6.00 | 1.00 |
| 3 g severo | 30.0 | 2.00 | 200 | 10.0 | 2.00 |
| 5 g acidental | qualquer (resultante) | 5.00 | 1000 | 20.0 | 20.0 |


Gravidade efetiva g_ef = g + a (soma vetorial, cada direção de a numa esfera de Fibonacci); o movimento angular da cabeça em torno dos
eixos de guinada/arfagem/rolagem por pivôs antropométricos [A] acrescenta as cargas de d'Alembert F = −m[α×ρ + ω×(ω×ρ)] e M = −I_G α − ω×(I_G ω).
Para movimento oscilatório da cabeça o pico de aceleração angular e o pico de velocidade angular estão em quadratura, então são aplicados
como duas fases separadas (pico de α com ω = 0, pico de ω com α = 0); a carga inercial ao quadrado é convexa na fase, então as duas fases
extremas limitam todas as intermediárias. Peso do cabo (0.35 m × 22 g/m [A]) ao longo de g_ef mais um puxão do cabo no clipe em qualquer
direção a até 80° da vertical para baixo [A]. **Toda** combinação de um conjunto (direção da gravidade × direção dinâmica × eixo/sinal/fase × direção do cabo)
é resolvida; a pior orientação é buscada, não suposta. Como as direções são escolhidas depende do uso da categoria:

* **1 g (critérios de aprovação/reprovação): uma grade determinística** que contém as bordas dos dois cones (`support.GRID_1G`): vertical + inclinação da cabeça
  22.5, 45° × a cada 22.5° de azimute; cabo para baixo + a 80° da
  vertical × a cada 22.5°. A sua resolução é verificada em todo módulo por uma **verificação densa** (`support.DENSE_1G`, aninhada: inclinação da cabeça
  11.25, 22.5, 33.75, 45° × a cada 11.25°, cabo 20, 40, 60, 80° × a cada 11.25°) e um **refinamento
  local** da verificação densa (`analysis.refine_1g_chunk`): em volta de cada combinação densa que falha e de cada uma das 8 de menor margem de assento e das 8
  de maior inclinação, a sua célula da grade densa (± meio passo denso na inclinação da cabeça, azimute da gravidade, ângulo e azimute do cabo) é
  explorada numa grade de 5 pontos por coordenada com o mesmo movimento da cabeça; a mudança dos piores valores densos para os refinados
  mede o que uma busca ainda mais fina poderia acrescentar. Ambos fazem parte dos critérios de uso normal do Final (tabelas abaixo).
* **2 g, 3 g, 5 g (relatados como frações soltas): uma amostra quase uniforme (Fibonacci)** das direções da gravidade, dinâmica e do cabo;
  uma fração solta é uma propriedade dessa amostra, não um pior caso. Onde uma varredura ou tabela de massa dá "1 g %", é a fração solta
  da grade de 1 g (5610 combinações por avaliação).

Verificação densa do Final (`results/dense_1g.json`; azimute 0° = para a frente, 90° = para fora, longe da cabeça: gravidade no azimute 90° significa a cabeça inclinada para este lado, esta orelha para baixo, então o lado pende para fora; margem de assento = terceira maior força de contato na pele − 0.1 N):

| D | combinações | soltas | tripé perdido | inclinação > 2° | pior inclinação ° | caso da pior inclinação | menor margem de assento N | o seu caso |
|---|---|---|---|---|---|---|---|---|
| 40 | 166410 | 0 | 0 | 0 | 0.411 | inclinação 45.0° no azimute 90.0°, rolagem +alfa, cabo 80° a 90.0° | 0.0337 | inclinação 45.0° no azimute 56.3°, rolagem −alfa, cabo 80° a 281.2° |
| 45 | 166410 | 0 | 0 | 0 | 0.373 | inclinação 45.0° no azimute 180.0°, rolagem +alfa, cabo 80° a 101.2° | 0.116 | inclinação 45.0° no azimute 33.7°, rolagem −alfa, cabo 80° a 281.2° |
| 50 | 166410 | 0 | 0 | 0 | 0.391 | inclinação 45.0° no azimute 180.0°, rolagem +alfa, cabo 80° a 101.2° | 0.0631 | inclinação 45.0° no azimute 123.7°, rolagem −alfa, cabo 80° a 112.5° |
| 55 | 166410 | 0 | 0 | 0 | 0.395 | inclinação 45.0° no azimute 180.0°, rolagem +alfa, cabo 80° a 101.2° | 0.0513 | inclinação 33.7° no azimute 45.0°, rolagem −alfa, cabo 80° a 281.2° |
| 60 | 166410 | 0 | 0 | 0 | 0.406 | inclinação 45.0° no azimute 180.0°, rolagem +alfa, cabo 80° a 101.2° | 0.0387 | inclinação 33.7° no azimute 56.3°, rolagem −alfa, cabo 80° a 281.2° |


Refinamento local em volta das combinações críticas da verificação densa (`results/dense_1g.json` "refine"; pior valor denso → refinado):

| D | sementes | combinações | falhando | pior inclinação ° | menor margem de assento N |
|---|---|---|---|---|---|
| 40 | 16 | 3279 | 0 | 0.411 → 0.415 | 0.0337 → 0.0308 |
| 45 | 16 | 3873 | 0 | 0.373 → 0.374 | 0.116 → 0.115 |
| 50 | 16 | 2790 | 0 | 0.391 → 0.391 | 0.0631 → 0.0604 |
| 55 | 16 | 3366 | 0 | 0.395 → 0.396 | 0.0513 → 0.0476 |
| 60 | 16 | 3438 | 0 | 0.406 → 0.407 | 0.0387 → 0.0379 |


Histórico (§4 mudança 21): os olhais ajustados na grade de 1 g a cada 45.0° (gravidade) / 45.0° (cabo) — pré-carga 5 N, fio Ø2.5 mm / 4 espiras, olhais 40 mm (-15, 7), 45 mm (-18, 6), 50 mm (-19, 5), 55 mm (-19, 6), 60 mm (-19, 6) — na verificação densa da época (a cada 22.5° / 22.5°) e no seu refinamento local (`results/dense_1g_grid45.json`; soltas / tripé perdido / inclinadas demais):

| D | falhas densas | margem de assento densa N | refinamento falhando | margem de assento refinada N |  |
|---|---|---|---|---|---|
| 40 | 0 / 0 / 0 | 0.0451 | 0 de 3159 | 0.0417 | passa |
| 45 | 0 / 0 / 0 | 0.0676 | 0 de 3114 | 0.0574 | passa |
| 50 | 0 / 0 / 0 | 0.0422 | 0 de 3858 | 0.0335 | passa |
| 55 | 0 / 0 / 0 | 0.0338 | 0 de 3243 | 0.0246 | passa |
| 60 | 0 / 1 / 0 | -0.000789 | 46 de 3102 | -0.0121 | **falha** |


A mudança 21 reduziu à metade os passos de azimute da grade e da verificação densa e rodou de novo o ajuste com a verificação da etapa 4 (§7): com a grade a cada 45.0° (gravidade) / 45.0° (cabo) os olhais ajustados falharam a 60 mm (verificação densa: 0 soltas, 1 tripé perdido, 0 inclinadas demais, menor margem de assento -0.000789 N; refinamento: 46 de 3102 falhando, menor -0.0121 N); a pior combinação não é um ponto daquela grade (§8), olhais movidos Δy 0–2.00 mm, Δx 0–1.00 mm.

O Final antes da mudança de iteração 19 na grade de 1 g (§4; `results/grid_1g_before_grid.json`): olhais ajustados numa amostra quase uniforme de 1 g (17 gravidade × 10 movimento da cabeça × 5 direções do cabo = 850 combinações) na pré-carga do layout de 4.20 N, fio da ligação Ø2.00 mm:

| D | combinações | soltas | tripé perdido | inclinação > 2° | pior inclinação ° | caso da pior inclinação | menor margem de assento N | o seu caso |
|---|---|---|---|---|---|---|---|---|
| 40 | 5610 | 15 | 0 | 51 | 4.66 | inclinação 45.0° no azimute 45.0°, rolagem +alfa, cabo 80° a 67.5° | 0.00115 | inclinação 45.0° no azimute 112.5°, rolagem −alfa, cabo 80° a 112.5° |
| 45 | 5610 | 9 | 7 | 20 | 4.97 | inclinação 45.0° no azimute 135.0°, rolagem +alfa, cabo 80° a 90.0° | -0.0897 | inclinação 45.0° no azimute 112.5°, guinada +alfa, cabo 80° a 90.0° |
| 50 | 5610 | 12 | 28 | 31 | 4.72 | inclinação 45.0° no azimute 45.0°, rolagem +alfa, cabo 80° a 112.5° | -0.100 | inclinação 45.0° no azimute 90.0°, guinada +alfa, cabo 80° a 90.0° |
| 55 | 5610 | 8 | 57 | 14 | 4.89 | inclinação 45.0° no azimute 67.5°, rolagem +alfa, cabo 80° a 67.5° | -0.100 | inclinação 45.0° no azimute 90.0°, guinada +alfa, cabo 80° a 67.5° |
| 60 | 5610 | 10 | 61 | 19 | 4.98 | inclinação 45.0° no azimute 45.0°, rolagem +alfa, cabo 80° a 90.0° | -0.100 | inclinação 45.0° no azimute 90.0°, guinada +alfa, cabo 80° a 67.5° |


As 331 combinações que falham: cabeça inclinada 45.0–45.0° da vertical; 331 de 331 com este lado pendendo para fora (cabeça inclinada para ele, esta orelha para baixo) e 317 de 331 com o cabo puxando para fora (317 ambos). Na sua própria amostra o primeiro ajuste tinha aprovado esses olhais (menor margem de uso normal 0.0760–0.166 entre os módulos, `results/eye_tuning_before_grid.json`). Com a grade (mudança 19; o fio da ligação redimensionado para cada nível de pré-carga, §11) o ajuste passou de 4.20 N para 5.00 N, com os olhais mais baixos (Δy -7.00–-5.00 mm) (§7).

| D | caso | combinações | soltas | % | micro-escorregamento das almofadas % das mantidas | tripé perdido | pior inclinação graus* | pior deslocamento mm* | p pico kPa* |
|---|---|---|---|---|---|---|---|---|---|
| 40 | 1 g normal | 5610 | 0 | 0 | 66.3 | 0 | 0.411 | 1.25 | 48.0 |
| 40 | 2 g dinâmico | 10000 | 194 | 1.94 | 74.2 | 986 | 4.99 | 2.99 | 88.6 |
| 40 | 3 g severo | 10000 | 3535 | 35.4 | 80.8 | 1890 | 4.99 | 2.99 | 137 |
| 40 | 5 g acidental | 6000 | 5807 | 96.8 | 79.8 | 4646 | 5.00 | 3.00 | 199 |
| 45 | 1 g normal | 5610 | 0 | 0 | 63.5 | 0 | 0.372 | 1.32 | 51.5 |
| 45 | 2 g dinâmico | 10000 | 126 | 1.26 | 73.4 | 847 | 4.96 | 2.35 | 91.7 |
| 45 | 3 g severo | 10000 | 3336 | 33.4 | 80.6 | 1951 | 4.98 | 3.00 | 137 |
| 45 | 5 g acidental | 6000 | 5800 | 96.7 | 79.5 | 4564 | 5.00 | 3.00 | 198 |
| 50 | 1 g normal | 5610 | 0 | 0 | 64.1 | 0 | 0.390 | 1.41 | 55.2 |
| 50 | 2 g dinâmico | 10000 | 142 | 1.42 | 73.8 | 880 | 4.98 | 2.51 | 97.2 |
| 50 | 3 g severo | 10000 | 3495 | 34.9 | 80.3 | 1926 | 4.98 | 3.00 | 135 |
| 50 | 5 g acidental | 6000 | 5802 | 96.7 | 81.8 | 4456 | 4.99 | 3.00 | 196 |
| 55 | 1 g normal | 5610 | 0 | 0 | 64.6 | 0 | 0.394 | 1.44 | 56.3 |
| 55 | 2 g dinâmico | 10000 | 208 | 2.08 | 74.0 | 978 | 4.98 | 2.84 | 102 |
| 55 | 3 g severo | 10000 | 3789 | 37.9 | 80.3 | 1822 | 4.99 | 2.99 | 137 |
| 55 | 5 g acidental | 6000 | 5801 | 96.7 | 82.4 | 4406 | 5.00 | 3.00 | 196 |
| 60 | 1 g normal | 5610 | 0 | 0 | 65.0 | 0 | 0.405 | 1.49 | 58.4 |
| 60 | 2 g dinâmico | 10000 | 252 | 2.52 | 74.2 | 1020 | 4.96 | 2.77 | 105 |
| 60 | 3 g severo | 10000 | 3972 | 39.7 | 80.1 | 1767 | 4.96 | 2.99 | 139 |
| 60 | 5 g acidental | 6000 | 5799 | 96.7 | 83.6 | 4331 | 5.00 | 3.00 | 196 |


*sobre as combinações que ficaram em equilíbrio. Inclinação = rotação em torno de x e y (muda a geometria driver–orelha). Micro-escorregamento das almofadas = uma almofada na pele desliza localmente enquanto o suporte como um todo fica em equilíbrio; cada combinação aqui parte do estado logo após colocar, então os micro-escorregamentos não se somam nesta tabela — repetidos, eles se somam (§6, o estado sustentado em uso).

O que causa as solturas — combinações soltas por caso de movimento da cabeça, somando os cinco tamanhos (parte das solturas da categoria). 'alfa' = pico de aceleração angular, 'ômega' = pico de velocidade angular; 'gravidade inclinada' = cabeça inclinada dentro do cone da categoria (não dividido para 5 g: a sua aceleração resultante tem qualquer direção):

| movimento da cabeça | 1 g normal | 2 g dinâmico | 3 g severo | 5 g acidental |
|---|---|---|---|---|
| sem rotação da cabeça | 0 (– %) | 0 (0 %) | 710 (3.92 %) | 2977 (10.3 %) |
| arfagem (aceno) alfa | 0 (– %) | 2 (0.217 %) | 2649 (14.6 %) | 5946 (20.5 %) |
| arfagem (aceno) ômega | 0 (– %) | 0 (0 %) | 689 (3.80 %) | 2947 (10.2 %) |
| rolagem (inclinação) alfa | 0 (– %) | 873 (94.7 %) | 5998 (33.1 %) | 5144 (17.7 %) |
| rolagem (inclinação) ômega | 0 (– %) | 1 (0.108 %) | 2180 (12.0 %) | 2995 (10.3 %) |
| guinada (giro) alfa | 0 (– %) | 46 (4.99 %) | 4497 (24.8 %) | 6000 (20.7 %) |
| guinada (giro) ômega | 0 (– %) | 0 (0 %) | 1404 (7.75 %) | 3000 (10.3 %) |
| das quais: gravidade vertical | 0 (– %) | 191 (20.7 %) | 3681 (20.3 %) | – |
| das quais: gravidade inclinada | 0 (– %) | 731 (79.3 %) | 14446 (79.7 %) | – |


Pior orientação de 1 g encontrada (50 mm): direção da gravidade (-0.707, -0.707, 8.66e-17), rolagem da cabeça +alfa, puxão do cabo ao longo de (6.03e-17, -0.174, 0.985).

## 9. Atrito, força normal mínima, sensibilidade

Demanda de atrito estático (colocação A, almofadas da pele tornadas antiderrapantes, raiz e couro cabeludo no μ de projeto): μ_exigido / μ_projeto por almofada; > 1 significa que a almofada escorrega lentamente em repouso com o coeficiente de projeto:

| D | T temporal | M mastoide | P póstero-sup. |
|---|---|---|---|
| 40 | 0.576 | 0.566 | 0.846 |
| 45 | 0.643 | 0.561 | 0.785 |
| 50 | 0.692 | 0.560 | 0.799 |
| 55 | 0.684 | 0.554 | 0.848 |
| 60 | 0.699 | 0.548 | 0.874 |


| caso de atrito (50 mm) | 1 g: % soltas | 1 g inclinação graus | 2 g: % soltas | demanda de μ estático |
|---|---|---|---|---|
| projeto: nominal/1.25 | 0 | 0.390 | 3.05 | 0.799 |
| cabelo em todo lugar | 0 | 0.395 | 6.60 | 1.55 |
| alto | 0 | 0.385 | 2.57 | 0.445 |
| baixo | 0 | 0.391 | 3.92 | 1.07 |
| sem face (cúpulas de TPU), 50 mm | 0 | 0.392 | 3.08 | 0.883 |
| sem face (cúpulas de TPU), 60 mm | 0 | 0.407 | 3.75 | 0.891 |
| nominal | 0 | 0.388 | 2.73 | 0.634 |
| silicone em todo lugar, nominal | 0 | 0.388 | 2.88 | 0.526 |
| pele suada, todos os contatos | 0 | 0.392 | 3.62 | 1.07 |
| suada, baixo | 1.03 | 0.397 | 11.6 | 1.98 |


Varredura da pré-carga — a força normal mínima é o menor P com zero solturas em 1 g (μ de projeto, depois a coluna de μ baixo):

| P N | 1 g % (μ projeto) | 1 g % (μ baixo) | 2 g % (μ projeto) | demanda de μ estático | p mastoide kPa |
|---|---|---|---|---|---|
| 2.00 | 7.01 | 11.8 | 25.9 | 5.27 | 1.57 |
| 2.50 | 3.05 | 6.35 | 19.0 | 2.76 | 1.71 |
| 3.00 | 0.624 | 2.78 | 13.4 | 1.86 | 1.84 |
| 3.50 | 0.107 | 0.642 | 9.50 | 1.40 | 1.96 |
| 4.00 | 0 | 0.160 | 6.60 | 1.12 | 2.08 |
| 4.50 | 0 | 0 | 4.50 | 0.934 | 2.21 |
| 5.00 | 0 | 0 | 3.05 | 0.799 | 2.33 |
| 5.50 | 0 | 0 | 2.12 | 0.697 | 2.45 |
| 6.00 | 0 | 0 | 1.55 | 0.617 | 2.57 |


| caso de tecido / hélice | 1 g % | 1 g inclinação graus | 2 g % |
|---|---|---|---|
| contato com a hélice também presente (k=400 N/m) | 0 | 0.390 | 2.73 |
| nominal | 0 | 0.390 | 3.05 |
| tecido macio x0.5 | 0 | 0.698 | 4.23 |
| tecido rígido x2 | 0 | 0.231 | 2.77 |


## 10. Massa máxima do driver

Faixa de massa do driver em que uma condição vale (o resto do lado mantém as propriedades de massa do CAD;
o driver mantém o seu centroide do CAD, com a inércia escalada pela massa).
estático: o lado fica no lugar em repouso com o mu de projeto (equilíbrio estático, sem escorregamento grosseiro)
normal:   assentado em repouso (todas as almofadas >= F_min) + pressão na pele e na raiz da orelha <= 4 kPa logo após colocar + demanda de
atrito estático <= mu de projeto E o conjunto de 1 g: sem escorregamento grosseiro, assentado, inclinação <= 2 graus
dinâmico: 'normal' E o conjunto de 2 g com fração solta <= permitido (permitido = 0: estrito); a varredura de 2 g
para assim que o número de solturas passa de permitido x n_casos
máximo:   'estático' E, no conjunto acidental de 5 g (n_acc direções), a estrutura sobrevive às cargas do envelope
(casos mantidos + forças de contato no início do escorregamento grosseiro para os casos que soltam):
structural_ok(). Escorregamento/soltura permitidos.
A condição NÃO é monótona na massa: o olhal da ligação de cada módulo é ajustado para o seu driver nominal, então um
driver mais leve também tira a resultante da carga da linha ajustada. Por isso a busca é ancorada na
massa nominal do driver m0 (design.DRIVERS): a condição é avaliada primeiro em m0; depois bisseção (até tol) em
[m0, hi_g] para a maior massa aprovada e em [lo_g, m0] para a menor (pulada quando hi_g / lo_g passam).
Supõe-se que as massas aprovadas formem um intervalo em volta de m0; isso é verificado nos quartis do intervalo
('interval_checked'). Se o próprio m0 falha, o resultado diz isso, e a faixa aprovada abaixo de m0 (se lo_g
passa) é achada por bisseção em [lo_g, m0]. 'máximo': o limite estático é achado primeiro (barato) e a
estrutura é verificada ali; só se ela falhar ali a verificação estrutural é feita por bisseção.
Retorna dict(nominal_g, holds_at_nominal, max_driver_g, min_driver_g, capped (max = hi_g), governs,
interval_checked, n_eval).

| D | driver nominal g [A] | estático: driver aprovado g | normal: driver aprovado g | dinâmico (soltas <= 0%): driver aprovado g | dinâmico (soltas <= 10%): driver aprovado g | máximo: driver aprovado g |
|---|---|---|---|---|---|---|
| 40 | 15.0 | 0.0–150.0+ | 0.0–27.7 | falha no nominal de 15 g; falha também com 0 g | 0.0–27.7 | 0.0–126.0 (um ponto intermediário falha!) |
| 45 | 19.0 | 0.0–150.0+ | 0.0–34.4 | falha no nominal de 19 g; falha também com 0 g | 0.0–34.4 | 0.0–122.9 (um ponto intermediário falha!) |
| 50 | 26.0 | 0.0–150.0+ | 0.0–31.8 | falha no nominal de 26 g; falha também com 0 g | 0.0–31.8 | 0.0–84.6 (um ponto intermediário falha!) |
| 55 | 33.0 | 0.0–150.0+ | 0.0–41.2 | falha no nominal de 33 g; falha também com 0 g | 0.0–41.2 | 0.0–54.9 |
| 60 | 40.0 | 0.0–150.0+ | 0.0–45.2 | falha no nominal de 40 g; falha também com 0 g | 0.0–45.2 | 0.0–109.2 (um ponto intermediário falha!) |


Cada célula é a faixa de massas de driver para a qual a condição vale, achada a partir do driver nominal para fora. '+' = o limite superior da busca (150 g) foi alcançado, então a condição não limita a massa do driver ali. 'falha no nominal' = a condição não é atendida com o driver para o qual o módulo foi projetado; a faixa depois disso, se houver, é onde ela valeria. Verificação que governa a condição máxima de projeto: 40 mm: estrutura (envelope de 5 g); 45 mm: estrutura (envelope de 5 g); 50 mm: estrutura (envelope de 5 g); 55 mm: estrutura (envelope de 5 g); 60 mm: estrutura (envelope de 5 g).

Estas faixas usam os critérios de uso normal logo após colocar. A pressão na raiz da orelha em uso (acomodação do §6) impõe um limite ao lado inteiro: a 60 mm ela só é atendida até 60.3 g por lado (massa e inércia escaladas, CG mantido), enquanto o lado de 60 mm sem o driver já pesa 150 g — nenhuma massa de driver a atende.

| driver g (50 mm) | total g | fixação estática | 1 g % soltas | 2 g % | 3 g % |
|---|---|---|---|---|---|
| 0 | 147 | PASSA | 0 | 2.81 | 33.8 |
| 10.0 | 157 | PASSA | 0 | 2.96 | 36.6 |
| 20.0 | 167 | PASSA | 0 | 3.23 | 39.7 |
| 26.0 | 173 | PASSA | 0 | 3.42 | 41.6 |
| 40.0 | 187 | PASSA | 0 | 4.19 | 45.5 |
| 60.0 | 207 | PASSA | 0 | 5.58 | 50.8 |
| 80.0 | 227 | PASSA | 0 | 8.12 | 55.8 |


![escorregamento contra massa](fig/slip_vs_mass.png)
![massa máxima do driver](fig/max_driver_mass.png)

## 11. Mola de ligação occipital — fio deduzido, não escolhido


Mola de ligação occipital — o diâmetro do fio é DEDUZIDO, não escolhido.

Geometria: um fio plano no plano transversal da cabeça (X lateral, Y frente-trás), simétrico em relação à linha média.
  * Final, olhal na ponta da concha (support.link_path): do olhal o fio corre para trás pela face da concha até
    hook_y, para dentro ao longo do lado do módulo até a cabeça (side_x), depois em volta do occipital como um arco circular cujo
    ápice fica `apex` atrás da linha dos olhais (SAGITTA + 15 mm [A]).
  * Projeto B, olhal na almofada mastoide: um arco circular pelos dois olhais; meia distância entre olhais w = meia largura da cabeça +
    altura do olhal sobre a pele, o occipital uma flecha s = SAGITTA [A] atrás da linha dos olhais, R = (w^2 + s^2) / (2 s).

As forças nas pontas +-P agem ao longo da corda (de olhal a olhal). O momento num ponto do
fio é  M = P * x  com x a distância à corda, então por Castigliano
    delta_par = (P / EI) * integral( x^2 ds )      (flexão; a parcela axial e de cisalhamento é limitada abaixo das tabelas)
    k_par = P / delta_par ,  k_lado = 2 k_par  (cada olhal se move delta_par/2)
Momento fletor máximo  M_max = P * x_max  no ápice (x_max: distância do ápice à corda).
A espira de torção do ápice (n voltas, diâmetro médio Dc) fica onde M = P x_max, então ela acrescenta
    delta_espira = P x_max^2 L_espira / (E I),  L_espira = pi Dc n
e k_par = EI / (int x^2 ds + x_max^2 L_espira). A espira baixa a rigidez (a pré-carga
fica quase constante entre tamanhos de cabeça) sem aumentar a tensão, a não ser
pelo fator de curvatura da espira Ki = (4C^2 - C - 1)/(4C(C - 1)), C = Dc/d.
Tensão de flexão      sigma = 32 M / (pi d^3)
Tensão no olhal (laço da ponta), fórmula de gancho de Shigley com braço de momento = raio médio do olhal r1:
    sigma_olhal = P [ K_A * 32 r1 / (pi d^3) + 4 / (pi d^2) ],
    K_A = (4 C1^2 - C1 - 1) / (4 C1 (C1 - 1)),  C1 = 2 r1 / d
Resistência: fio de aço para molas ASTM A228, Sut = 2211 / d^0.145 MPa [STD]; escoamento
em flexão ~0.75 Sut [STD]; resistência à fadiga em flexão alternada 0.3 Sut [A].


**B** (P = 1.20 N): escolhido Ø1.50 mm, 3 espiras no ápice (Ø médio 12 mm).

| grandeza | valor |
|---|---|
| rigidez por lado k (N/m) | 57.4 |
| faixa de pré-carga (cabeça p5–p95) N | 0.856 – 1.54 |
| razão pré-carga máx/mín | 1.81 |
| força para colocar N | 2.69 |
| Sut MPa (d) | 2085 |
| σ em uso / σ ao colocar MPa | 437 / 762 |
| tensão no olhal (ao colocar) MPa, K_A | 31.5, 1.23 |
| raio interno do olhal mm (≥ 1.5 d = raio mínimo de dobra) | 2.25 |
| FS escoamento (≥ 1.5) | 2.05 |
| FS fadiga Goodman, 10 000 ciclos de colocação (≥ 1.5) | 2.97 |
| meia abertura livre mm (conformar o fio para isso) | 66.1 |
| comprimento do fio m | 0.269 |
| massa g | 5.31 |


**Final** (P = 5.00 N): escolhido Ø2.50 mm, 4 espiras no ápice (Ø médio 12 mm).

| grandeza | valor |
|---|---|
| rigidez por lado k (N/m) | 164 |
| faixa de pré-carga (cabeça p5–p95) N | 4.02 – 5.98 |
| razão pré-carga máx/mín | 1.49 |
| força para colocar N | 9.26 |
| Sut MPa (d) | 1936 |
| σ em uso / σ ao colocar MPa | 570 / 882 |
| tensão no olhal (ao colocar) MPa, K_A | 39.0, 1.23 |
| raio interno do olhal mm (≥ 1.5 d = raio mínimo de dobra) | 3.75 |
| FS escoamento (≥ 1.5) | 1.65 |
| FS fadiga Goodman, 10 000 ciclos de colocação (≥ 1.5) | 2.35 |
| meia abertura livre mm (conformar o fio para isso) | 101 |
| comprimento do fio m | 0.443 |
| massa g | 22.9 |


Só flexão: tomando as forças axial e de cisalhamento como P ao longo de todo o arco de 0.443 m (um limite superior), a flexibilidade delas é 0.0138 % da flexibilidade de flexão do fio do Final (fator de cisalhamento 1.11, ν = 0.29) [C].

A ligação comum é conformada no módulo de 50 mm; nos outros módulos a ponta da concha fica Δz mais funda ou mais rasa, então P(D) = P_ref + k_lado Δz (tabela no §3). O menor FS de escoamento entre os cinco módulos é 1.59 (60 mm) contra o exigido de 1.5: 6.05 % de folga. A própria pré-carga vem do ajuste do olhal (§7); diâmetros comerciais 1, 1.2, 1.4, 1.5, 1.6, 1.8, 2 mm [DS] e 2.25, 2.5 mm [A: supõe-se em estoque, confirmar com o fornecedor] são considerados.

O mesmo fio em todos os módulos: o olhal de cada módulo define o seu próprio caminho pela face da concha (e o seu próprio P(D)), então o fio é verificado em cada um (link_design com o caminho daquele módulo):

| D | olhal x mm | olhal y mm | P(D) N | k_lado N/m | pré-carga máx/mín | FS escoamento (≥ 1.5) | FS fadiga (≥ 1.5) | todos |
|---|---|---|---|---|---|---|---|---|
| 40 | -15.0 | 7.00 | 4.67 | 152 | 1.48 | 1.71 | 2.44 | PASSA |
| 45 | -18.0 | 7.00 | 4.84 | 161 | 1.50 | 1.68 | 2.39 | PASSA |
| 50 | -19.0 | 7.00 | 5.00 | 164 | 1.49 | 1.65 | 2.35 | PASSA |
| 55 | -18.0 | 7.00 | 5.16 | 161 | 1.46 | 1.62 | 2.30 | PASSA |
| 60 | -18.0 | 7.00 | 5.33 | 161 | 1.44 | 1.59 | 2.26 | PASSA |


![ligação](fig/link_wire.png)

## 12. Análise estrutural dos braços do suporte


Verificações estruturais dos braços do suporte, juntas, fixadores, insertos,
trava de giro, olhal da ligação, encaixes por pressão/clique, fluência, temperatura e fadiga.

NENHUMA FEA FOI RODADA. Tudo abaixo é teoria de vigas / juntas em forma fechada com
fatores de concentração de tensão de Peterson. Onde a geometria não é de viga
(raiz da aba do anel, raiz da lingueta, lábio de 45°, ressalto do inserto) o resultado é marcado
como "FEA recomendada" no relatório.

Modelo de viga de um braço
--------------------------
Linha média no plano (r, z) do próprio braço, no ângulo a:
    almofada (r_tip, z=0)  ->  pé (z_f = pad_h + ft/2) para fora até a perna
    perna (r_l = leg_r + leg_t/2) subindo até a barra (z_b = S - bar_t/2)
    barra para dentro até a borda de fixação do parafuso externo (extremidade engastada)
Esforços internos numa seção no ponto s, a partir da força F da almofada
aplicada no ponto de contato p da almofada (pele):
    F_int = F ,  M_int = (p - s) x F
decompostos nos eixos da seção (axial a, no plano h, tangencial t):
    sigma = N/A + K_t [ |M_t| 6/(b h^2) + |M_h| 6/(h b^2) ]     (canto, os dois planos de flexão somados)
    tau   = T (3 + 1.8 h/b)/(b h^2)    (Roark, retângulo b >= h)  + 1.5 V/A
Impressão: os braços ficam deitados de lado, camadas paralelas ao plano (r, z), então
toda a tensão de flexão axial fica NA CAMADA (S_xy); os planos entre camadas (normal t)
carregam o cisalhamento transversal V_t e o cisalhamento de torção -> verificados contra
a resistência ao cisalhamento entre camadas.


Tensões admissíveis a 40 °C: S_xy·kT = 38.2 MPa (na camada), cisalhamento entre camadas 11.9 MPa; sustentado (1 g) × 0.5. FS exigido ≥ γM = 1.6. Kt: raio de concordância 1.25, furo em flexão 2.0 [STD Peterson]. Carregamento combinado: σ = |N|/A + Kt(|M_t|/Z_t + |M_h|/Z_h), τ = τ_torção + 1.5 |V|/A, σ_vM = √(σ² + 3τ²); o cisalhamento entre camadas usa o cisalhamento que age nos planos das camadas (braços impressos de lado).

Três definições de carga estrutural:
* **1 g sustentado** — toda combinação de 1 g mantida, tensões admissíveis sustentadas.
* **Envelope acidental de 5 g** — toda combinação de 5 g: quando fica em equilíbrio, as suas forças de contato; quando solta, as forças de contato
  no **início do escorregamento grosseiro** (bisseção no fator de carga λ do incremento a partir do estado estático). Além do início o
  suporte desliza e as cargas nos braços não podem crescer, então o envelope limita as cargas nos braços. λ_mín por tamanho está no §1.
* **Manuseio 10 N** — 10 N numa almofada em qualquer uma de 302 direções (uma mão pegando uma almofada, uma gola, cabelo) [A]: a carga local que a
  retenção não consegue limitar. Ela dimensionou a barra do braço.
O limite de toda a carga numa almofada do caso de 5 g (m·5g + enganchamento de 20 N numa única almofada) é mostrado só como informação: ele não pode ocorrer
porque o suporte solta antes.

50 mm, 1 g normal (tensões admissíveis sustentadas), 6 seções mais baixas:

| braço | seção | σ MPa | τ MPa | σ_vM MPa | FS vM | τ entre camadas MPa | FS entre camadas | N N | T N·mm | M_t N·mm | M_h N·mm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mastoide | barra na borda da fixação (fim do rasgo) | 4.17 | 0.279 | 4.20 | 4.55 | 0.815 | 7.30 | -1.37 | 7.74 | 65.9 | 3.52 |
| temporal | barra na borda da fixação (fim do rasgo) | 3.37 | 0.238 | 3.39 | 5.64 | 0.562 | 10.6 | -1.06 | 6.86 | 52.8 | 3.25 |
| póstero-sup. | barra na borda da fixação (fim do rasgo) | 3.01 | 0.154 | 3.02 | 6.34 | 0.303 | 19.6 | -0.590 | 1.17 | 49.3 | 0.486 |
| sela | raio de concordância inferior da perna | 0.263 | 0.807 | 1.42 | 13.5 | 0.797 | 7.46 | 0.504 | 103 | 13.3 | -9.55 |
| sela | raio de concordância superior da perna | 0.148 | 0.807 | 1.41 | 13.6 | 0.797 | 7.46 | 0.504 | 103 | -0.710 | -24.7 |
| sela | barra na borda da fixação (fim do rasgo) | 1.92 | 0.144 | 1.94 | 9.86 | 0.379 | 15.7 | 2.25 | -13.1 | -40.8 | -44.2 |


50 mm, 5 g acidental (tensões admissíveis de curto prazo, envelope do início), 6 seções mais baixas:

| braço | seção | σ MPa | τ MPa | σ_vM MPa | FS vM | τ entre camadas MPa | FS entre camadas | N N | T N·mm | M_t N·mm | M_h N·mm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mastoide | barra na borda da fixação (fim do rasgo) | 23.8 | 2.21 | 24.1 | 1.58 | 4.36 | 2.73 | -7.48 | 71.5 | 366 | 32.6 |
| temporal | barra na borda da fixação (fim do rasgo) | 20.8 | 3.26 | 21.6 | 1.77 | 3.20 | 3.72 | -1.78 | 106 | 304 | 50.4 |
| póstero-sup. | barra na borda da fixação (fim do rasgo) | 11.7 | 2.39 | 12.4 | 3.08 | 1.88 | 6.32 | -0.170 | 78.1 | 168 | 32.6 |
| sela | barra na borda da fixação (fim do rasgo) | 11.5 | 0.358 | 11.5 | 3.33 | 0.884 | 13.5 | 9.15 | -31.4 | -317 | -97.0 |
| mastoide | raio de concordância superior da perna | 8.28 | 0.593 | 8.34 | 4.59 | 1.14 | 10.5 | 14.2 | -28.5 | 294 | 53.1 |
| temporal | raio de concordância superior da perna | 7.92 | 0.705 | 8.02 | 4.77 | 0.868 | 13.7 | 20.7 | -44.3 | 261 | 78.9 |


50 mm, manuseio 10 N (tensões admissíveis de curto prazo), 6 seções mais baixas:

| braço | seção | σ MPa | τ MPa | σ_vM MPa | FS vM | τ entre camadas MPa | FS entre camadas | N N | T N·mm | M_t N·mm | M_h N·mm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sela | barra na borda da fixação (fim do rasgo) | 22.2 | 0.520 | 22.2 | 1.72 | 2.81 | 4.24 | 4.56 | -33.0 | -598 | 243 |
| póstero-sup. | barra na borda da fixação (fim do rasgo) | 18.0 | 2.84 | 18.6 | 2.05 | 6.33 | 1.88 | -8.33 | -116 | 255 | -48.4 |
| temporal | barra na borda da fixação (fim do rasgo) | 18.5 | 3.14 | 19.3 | 1.98 | 6.33 | 1.88 | -7.87 | 128 | 254 | 60.7 |
| mastoide | barra na borda da fixação (fim do rasgo) | 18.3 | 3.00 | 19.1 | 2.01 | 6.32 | 1.88 | -7.94 | -122 | 255 | -55.5 |
| sela | raio de concordância inferior da perna | 9.78 | 0.0521 | 9.78 | 3.91 | 4.58 | 2.60 | 9.94 | 4.45 | 580 | -127 |
| sela | raio de concordância superior da perna | 10.1 | 0.305 | 10.1 | 3.79 | 4.58 | 2.60 | 9.66 | -34.9 | 595 | 140 |


Informação: toda a carga de 5 g (28.5 N) numa almofada → menor FS 0.603 (sela: barra na borda da fixação (fim do rasgo) (vM)).

60 mm, 1 g normal (tensões admissíveis sustentadas), 6 seções mais baixas:

| braço | seção | σ MPa | τ MPa | σ_vM MPa | FS vM | τ entre camadas MPa | FS entre camadas | N N | T N·mm | M_t N·mm | M_h N·mm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mastoide | barra na borda da fixação (fim do rasgo) | 4.60 | 0.340 | 4.64 | 4.12 | 0.897 | 6.64 | -1.40 | -9.57 | 72.3 | -4.36 |
| temporal | barra na borda da fixação (fim do rasgo) | 3.71 | 0.295 | 3.74 | 5.11 | 0.612 | 9.72 | -1.13 | 8.94 | 57.6 | 4.24 |
| póstero-sup. | barra na borda da fixação (fim do rasgo) | 3.07 | 0.267 | 3.11 | 6.15 | 0.313 | 19.0 | -0.570 | -6.17 | 48.7 | -2.57 |
| sela | raio de concordância inferior da perna | 0.273 | 0.860 | 1.51 | 12.6 | 0.850 | 7.00 | 0.524 | 110 | 13.7 | -10.2 |
| sela | raio de concordância superior da perna | 0.161 | 0.860 | 1.50 | 12.8 | 0.850 | 7.00 | 0.524 | 110 | -0.978 | -26.4 |
| sela | barra na borda da fixação (fim do rasgo) | 2.04 | 0.142 | 2.06 | 9.31 | 0.405 | 14.7 | 2.40 | -12.9 | -44.6 | -43.7 |


60 mm, 5 g acidental (tensões admissíveis de curto prazo, envelope do início), 6 seções mais baixas:

| braço | seção | σ MPa | τ MPa | σ_vM MPa | FS vM | τ entre camadas MPa | FS entre camadas | N N | T N·mm | M_t N·mm | M_h N·mm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mastoide | barra na borda da fixação (fim do rasgo) | 26.2 | 2.35 | 26.5 | 1.44 | 4.02 | 2.96 | -8.19 | 75.0 | 404 | 34.2 |
| temporal | barra na borda da fixação (fim do rasgo) | 24.7 | 2.02 | 24.9 | 1.53 | 2.42 | 4.91 | -5.07 | 52.1 | 388 | 24.7 |
| póstero-sup. | barra na borda da fixação (fim do rasgo) | 14.0 | 2.63 | 14.8 | 2.59 | 2.06 | 5.78 | -0.784 | 85.3 | 204 | 35.6 |
| sela | barra na borda da fixação (fim do rasgo) | 11.2 | 0.180 | 11.2 | 3.42 | 0.843 | 14.1 | 8.33 | -12.7 | -337 | -32.8 |
| mastoide | raio de concordância superior da perna | 9.10 | 0.631 | 9.16 | 4.17 | 1.05 | 11.3 | 15.8 | -29.9 | 325 | 55.7 |
| temporal | raio de concordância superior da perna | 8.91 | 0.435 | 8.94 | 4.28 | 0.657 | 18.1 | 20.5 | -21.7 | 323 | 38.7 |


60 mm, manuseio 10 N (tensões admissíveis de curto prazo), 6 seções mais baixas:

| braço | seção | σ MPa | τ MPa | σ_vM MPa | FS vM | τ entre camadas MPa | FS entre camadas | N N | T N·mm | M_t N·mm | M_h N·mm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sela | barra na borda da fixação (fim do rasgo) | 22.2 | 0.520 | 22.2 | 1.72 | 2.81 | 4.24 | 4.56 | -33.0 | -598 | 243 |
| póstero-sup. | barra na borda da fixação (fim do rasgo) | 18.0 | 2.84 | 18.6 | 2.05 | 6.33 | 1.88 | -8.33 | -116 | 255 | -48.4 |
| temporal | barra na borda da fixação (fim do rasgo) | 18.5 | 3.14 | 19.3 | 1.98 | 6.33 | 1.88 | -7.87 | 128 | 254 | 60.7 |
| mastoide | barra na borda da fixação (fim do rasgo) | 18.3 | 3.00 | 19.1 | 2.01 | 6.32 | 1.88 | -7.94 | -122 | 255 | -55.5 |
| sela | raio de concordância inferior da perna | 9.78 | 0.0521 | 9.78 | 3.91 | 4.58 | 2.60 | 9.94 | 4.45 | 580 | -127 |
| sela | raio de concordância superior da perna | 10.1 | 0.305 | 10.1 | 3.79 | 4.58 | 2.60 | 9.66 | -34.9 | 595 | 140 |


Informação: toda a carga de 5 g (29.3 N) numa almofada → menor FS 0.586 (sela: barra na borda da fixação (fim do rasgo) (vM)).

Flexibilidade do braço em série com cada contato (Final 60 mm; o modelo de suporte a inclui, §6), no referencial do contato (n = normal ao contato, t1/t2 = tangentes), comparada com a flexibilidade do próprio contato:

| contato | braço | braço n mm/N [C] | braço t1 mm/N | braço t2 mm/N | contato n mm/N [C] | contato t mm/N | maior razão braço/contato |
|---|---|---|---|---|---|---|---|
| T temporal | temporal | 0.0150 | 0.0366 | 0.0376 | 0.127 | 0.254 | 0.148 |
| M mastoide | mastoide | 0.0113 | 0.0329 | 0.0324 | 0.0517 | 0.103 | 0.318 |
| P póstero-sup. | póstero-sup. | 0.0110 | 0.0322 | 0.0365 | 0.126 | 0.252 | 0.145 |
| S raiz F | sela | 0.162 | 0.133 | 0.572 | 0.414 | 0.827 | 0.691 |
| S raiz B | sela | 0.162 | 0.133 | 0.572 | 0.414 | 0.827 | 0.691 |
| S couro cabeludo | sela | 0.285 | 0.0237 | 0.161 | 0.268 | 0.537 | 1.06 |


Onde fica a flexibilidade de cada braço em repouso (60 mm; parcela da energia complementar do braço sob as suas próprias forças de contato, `structure.arm_energy_split`): temporal — flexão da perna no plano 42.2 %, flexão do pé no plano 17.2 %; mastoide — flexão da perna no plano 74.0 %, flexão do pé no plano 10.1 %; póstero-sup. — flexão da perna no plano 58.5 %, flexão do pé no plano 19.6 %; sela — flexão do pé no plano 69.6 %, flexão da perna no plano 28.4 %. 
Entre as almofadas de pele, o braço é mais flexível em relação ao seu contato na almofada mastoide (razão 0.318); onde a flexibilidade do braço é comparável à do contato, a almofada transfere peso para a raiz da orelha (braços rígidos contra flexíveis: tabela de alavancas do §6). Por isso a espessura das pernas e o revestimento da sela foram escolhidos juntos (§6, 'Pernas dos braços e revestimento da sela').

Temperatura: a 55 °C (carro, sol) a resistência é ×0.700 [LIT] contra ×0.850 a 40 °C: todo FS de curto prazo acima escala por 0.824. Fadiga: caminhada/corrida 1e7 ciclos [A]; considera-se que cada seção do braço cicla de zero até a sua maior tensão de von Mises nas combinações de 2 g mantidas (conservador: a parte estável de 1 g não é separada, Kt mantido como fator de entalhe), Goodman na curva S-N normalizada (`structure.fatigue_strength`, razão de fadiga [A]) a 1e7 ciclos, 40 °C: menor FS 1.71 a 60 mm, mastoide barra na borda da fixação (fim do rasgo) (σ_máx 8.67 MPa, S_f 9.16 MPa). A ruptura por fluência dos braços está coberta pelas tensões admissíveis sustentadas (×0.5) nas tabelas de 1 g; a fluência da pré-carga importa nas juntas parafusadas (§13).

### 12.1 Tensões de contato em todas as interfaces

50 mm:

| interface | caso | F N | p médio kPa | p pico kPa | limite kPa | pico/limite | FS curto prazo | FS sustentado |
|---|---|---|---|---|---|---|---|---|
| almofada T temporal na pele | estático (sustentado) | 1.19 | 2.30 | 4.60 | 4.00 | 1.15 | – | – |
| almofada T temporal na pele | 2 g máx. (transitório) | 3.77 | 7.28 | 14.6 | 8.00 | 1.82 | – | – |
| almofada T temporal na pele | 5 g máx. (acidental) | 21.3 | 41.1 | 82.2 | 150 | 0.548 | – | – |
| almofada M mastoide na pele | estático (sustentado) | 1.76 | 2.33 | 4.65 | 4.00 | 1.16 | – | – |
| almofada M mastoide na pele | 2 g máx. (transitório) | 5.50 | 7.27 | 14.5 | 8.00 | 1.82 | – | – |
| almofada M mastoide na pele | 5 g máx. (acidental) | 24.0 | 31.7 | 63.5 | 150 | 0.423 | – | – |
| almofada P póstero-sup. na pele | estático (sustentado) | 1.61 | 3.11 | 6.21 | 4.00 | 1.55 | – | – |
| almofada P póstero-sup. na pele | 2 g máx. (transitório) | 4.06 | 7.85 | 15.7 | 8.00 | 1.96 | – | – |
| almofada P póstero-sup. na pele | 5 g máx. (acidental) | 15.2 | 29.4 | 58.7 | 150 | 0.392 | – | – |
| zona da sela S raiz F na raiz da orelha | estático (sustentado) | 0.229 | 3.27 | 6.53 | 4.00 | 1.63 | – | – |
| zona da sela S raiz F na raiz da orelha | 2 g máx. (transitório) | 3.49 | 49.8 | 99.6 | 8.00 | 12.5 | – | – |
| zona da sela S raiz F na raiz da orelha | 5 g máx. (acidental) | 7.40 | 106 | 211 | 150 | 1.41 | – | – |
| zona da sela S raiz B na raiz da orelha | estático (sustentado) | 0.202 | 2.88 | 5.76 | 4.00 | 1.44 | – | – |
| zona da sela S raiz B na raiz da orelha | 2 g máx. (transitório) | 2.61 | 37.3 | 74.5 | 8.00 | 9.32 | – | – |
| zona da sela S raiz B na raiz da orelha | 5 g máx. (acidental) | 5.55 | 79.3 | 159 | 150 | 1.06 | – | – |
| almofada S couro cabeludo na pele | estático (sustentado) | 0.378 | 1.69 | 3.38 | 4.00 | 0.845 | – | – |
| almofada S couro cabeludo na pele | 2 g máx. (transitório) | 0.897 | 4.01 | 8.01 | 8.00 | 1.00 | – | – |
| almofada S couro cabeludo na pele | 5 g máx. (acidental) | 3.86 | 17.2 | 34.5 | 150 | 0.230 | – | – |
| cabeça do parafuso do braço (M3) no braço de PETG | maior pré-carga (K 0.20) | 167 | – | 11354 | – | – | 4.12 | 2.06 |
| cabeça do parafuso da âncora (M3) na âncora de PETG | maior pré-carga (K 0.20) | 167 | – | 11354 | – | – | 4.12 | 2.06 |
| flancos da serrilha (braço temporal, 10 mm) | maior pré-carga (2 parafusos, K 0.20) | 333 | – | 2525 | – | – | 18.5 | 9.26 |
| flancos da serrilha (braço da sela, 16 mm) | maior pré-carga (2 parafusos, K 0.20) | 333 | – | 1578 | – | – | 29.6 | 14.8 |
| fio da ligação na bucha de latão do olhal (linha de Hertz) | pré-carga ao colocar | 9.50 | – | 220512 | – | – | 1.89 | – |
| inserto do olhal no ressalto de PETG (lateral) | pré-carga ao colocar | 9.50 | – | 4157 | – | – | – | 5.62 |


60 mm:

| interface | caso | F N | p médio kPa | p pico kPa | limite kPa | pico/limite | FS curto prazo | FS sustentado |
|---|---|---|---|---|---|---|---|---|
| almofada T temporal na pele | estático (sustentado) | 1.31 | 2.52 | 5.05 | 4.00 | 1.26 | – | – |
| almofada T temporal na pele | 2 g máx. (transitório) | 4.27 | 8.25 | 16.5 | 8.00 | 2.06 | – | – |
| almofada T temporal na pele | 5 g máx. (acidental) | 22.7 | 43.9 | 87.7 | 150 | 0.585 | – | – |
| almofada M mastoide na pele | estático (sustentado) | 1.96 | 2.59 | 5.17 | 4.00 | 1.29 | – | – |
| almofada M mastoide na pele | 2 g máx. (transitório) | 6.03 | 7.97 | 15.9 | 8.00 | 1.99 | – | – |
| almofada M mastoide na pele | 5 g máx. (acidental) | 24.8 | 32.8 | 65.6 | 150 | 0.438 | – | – |
| almofada P póstero-sup. na pele | estático (sustentado) | 1.60 | 3.10 | 6.20 | 4.00 | 1.55 | – | – |
| almofada P póstero-sup. na pele | 2 g máx. (transitório) | 4.42 | 8.54 | 17.1 | 8.00 | 2.13 | – | – |
| almofada P póstero-sup. na pele | 5 g máx. (acidental) | 17.1 | 32.9 | 65.9 | 150 | 0.439 | – | – |
| zona da sela S raiz F na raiz da orelha | estático (sustentado) | 0.253 | 3.61 | 7.22 | 4.00 | 1.80 | – | – |
| zona da sela S raiz F na raiz da orelha | 2 g máx. (transitório) | 3.80 | 54.3 | 109 | 8.00 | 13.6 | – | – |
| zona da sela S raiz F na raiz da orelha | 5 g máx. (acidental) | 7.46 | 107 | 213 | 150 | 1.42 | – | – |
| zona da sela S raiz B na raiz da orelha | estático (sustentado) | 0.223 | 3.19 | 6.38 | 4.00 | 1.59 | – | – |
| zona da sela S raiz B na raiz da orelha | 2 g máx. (transitório) | 2.73 | 38.9 | 77.9 | 8.00 | 9.74 | – | – |
| zona da sela S raiz B na raiz da orelha | 5 g máx. (acidental) | 5.60 | 80.0 | 160 | 150 | 1.07 | – | – |
| almofada S couro cabeludo na pele | estático (sustentado) | 0.391 | 1.75 | 3.49 | 4.00 | 0.873 | – | – |
| almofada S couro cabeludo na pele | 2 g máx. (transitório) | 0.984 | 4.39 | 8.79 | 8.00 | 1.10 | – | – |
| almofada S couro cabeludo na pele | 5 g máx. (acidental) | 4.31 | 19.3 | 38.5 | 150 | 0.257 | – | – |
| cabeça do parafuso do braço (M3) no braço de PETG | maior pré-carga (K 0.20) | 167 | – | 11354 | – | – | 4.12 | 2.06 |
| cabeça do parafuso da âncora (M3) na âncora de PETG | maior pré-carga (K 0.20) | 167 | – | 11354 | – | – | 4.12 | 2.06 |
| flancos da serrilha (braço temporal, 10 mm) | maior pré-carga (2 parafusos, K 0.20) | 333 | – | 2525 | – | – | 18.5 | 9.26 |
| flancos da serrilha (braço da sela, 16 mm) | maior pré-carga (2 parafusos, K 0.20) | 333 | – | 1578 | – | – | 29.6 | 14.8 |
| fio da ligação na bucha de latão do olhal (linha de Hertz) | pré-carga ao colocar | 9.50 | – | 220512 | – | – | 1.89 | – |
| inserto do olhal no ressalto de PETG (lateral) | pré-carga ao colocar | 9.50 | – | 4157 | – | – | – | 5.62 |


Almofadas na pele: pico de camada fina de Winkler = 2 × média (paraboloide sobre um leito de molas) [C]; cabeças de parafuso e flancos da serrilha: esmagamento no PETG (S_bear) [DS]; fio da ligação na bucha de latão: contato em linha de Hertz [STD]; inserto do olhal: esmagamento lateral no ressalto com o momento da altura da bucha [C].

## 13. Juntas, fixadores, insertos, encaixes, trava de giro

Junta braço–aba com serrilha (projeto Final): n parafusos na linha média do braço com passo p, largura do braço w.
    Esforços na seção da borda de fixação (structure.section_stress, eixo da barra a = radial): F_r = N (radial),
    F_t = V_t (tangencial), F_pull = arrancamento normal à face da junta (V_h > 0), M_tilt = M_t (em torno do
    eixo tangencial), T_twist = T (em torno do eixo radial = a linha dos parafusos), M_inplane = M_h (em torno da
    normal da junta).
    Pré-carga pelo torque de aperto, F_i = T / (K d), com a dispersão do fator de porca K_lo..K_hi
    (materials.NUT_FACTOR_K_RANGE): F_i,max = T/(K_lo d) para o inserto, F_i,min = T/(K_hi d) para o engate.
    Pré-carga retida (envelhecida): retained_preload(F_i,min) (fluência do PETG, arruela ondulada).
    Demanda externa no parafuso mais carregado (regra da alavanca, limites conservadores no fator de carga Phi: o
    parafuso leva toda ela no arrancamento (Phi = 1), a fixação perde toda ela no engate (Phi = 0)):
        cunha      F_sep  = |F_r| tan(flanco - phi), phi = atan(mu)     (carga radial nos flancos dos dentes), dividida por n
        alavanca   |M_t| / p                                          (binário dos dois parafusos em torno do centro da junta)
        torção     2 |T| / (n w)                                      (o braço gira na sua borda, alavanca w/2)
        puxão      F_pull / n
        D_screw = F_sep / n + |M_t| / p + 2 |T| / (n w) + F_pull / n
        SF_engage  = F_i,eff(min) / D_screw          (as cargas externas podem crescer SF vezes antes que os dentes se levantem)
        SF_pullout = (arrancamento / gamma_insert) / (F_i,max + D_screw)
    Tangencial: as ranhuras correm tangencialmente, então F_t e o momento no plano vão para as hastes dos parafusos
    apoiadas nos lados do rasgo ao longo da espessura da barra t_bear: por parafuso |F_t| / n + |M_h| / p.
    Cisalhamento na raiz do dente: tau = F_r / (n_teeth * w * p) (dentes no braço, cisalhamento na camada porque o braço é
    impresso de lado: o perfil do dente fica no plano de impressão).

50 mm — mínimo sobre todas as combinações de carga de cada categoria (faixa de F_i, D_parafuso e o FS de arrancamento na pré-carga nominal mostrados para a combinação com o menor FS de engate):

| caso | braço | faixa de F_i N (K 0.35–0.20) | F_i após fluência (a partir da menor) N | D_parafuso N | FS engate (≥1) | FS arrancamento do inserto na maior F_i (≥1) | FS arrancamento na F_i nominal | FS esmagamento no rasgo (≥1) | FS giro | FS cisalhamento do dente | junta lisa: FS escorregamento |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 g normal | sela | 95.2–167 | 82.8 | 5.31 | 15.6 | 1.60 | 2.21 | 74.6 | 10.0 | 1036 | 0.649 |
| 1 g normal | temporal | 95.2–167 | 82.8 | 5.98 | 13.8 | 1.59 | 2.20 | 525 | 10.0 | 1499 | 3.51 |
| 1 g normal | mastoide | 95.2–167 | 82.8 | 7.69 | 10.8 | 1.58 | 2.17 | 376 | 10.0 | 1747 | 2.19 |
| 1 g normal | póstero-sup. | 95.2–167 | 82.8 | 5.20 | 15.9 | 1.60 | 2.21 | 1078 | 10.0 | 3290 | 5.39 |
| 2 g dinâmico | sela | 95.2–167 | 82.8 | 18.7 | 4.44 | 1.48 | 2.00 | 43.3 | 10.0 | 649 | 0.312 |
| 2 g dinâmico | temporal | 95.2–167 | 82.8 | 10.3 | 8.06 | 1.55 | 2.13 | 284 | 10.0 | 1503 | 1.43 |
| 2 g dinâmico | mastoide | 95.2–167 | 82.8 | 13.7 | 6.04 | 1.52 | 2.07 | 290 | 10.0 | 616 | 1.31 |
| 2 g dinâmico | póstero-sup. | 95.2–167 | 82.8 | 6.42 | 12.9 | 1.59 | 2.19 | 855 | 10.0 | 2291 | 4.62 |
| 3 g severo | sela | 95.2–167 | 82.8 | 28.6 | 2.89 | 1.41 | 1.86 | 33.5 | 10.0 | 342 | 0.116 |
| 3 g severo | temporal | 95.2–167 | 82.8 | 17.0 | 4.87 | 1.50 | 2.02 | 198 | 10.0 | 750 | 0.814 |
| 3 g severo | mastoide | 95.2–167 | 82.8 | 19.0 | 4.35 | 1.48 | 1.99 | 221 | 10.0 | 429 | 0.813 |
| 3 g severo | póstero-sup. | 95.2–167 | 82.8 | 9.33 | 8.87 | 1.56 | 2.14 | 487 | 10.0 | 3427 | 2.52 |
| 5 g acidental | sela | 95.2–167 | 82.8 | 34.9 | 2.37 | 1.36 | 1.79 | 34.5 | 10.0 | 255 | 0.0746 |
| 5 g acidental | temporal | 95.2–167 | 82.8 | 38.9 | 2.13 | 1.34 | 1.74 | 77.8 | 10.0 | 821 | 0.217 |
| 5 g acidental | mastoide | 95.2–167 | 82.8 | 43.0 | 1.92 | 1.31 | 1.70 | 66.2 | 10.0 | 195 | 0.102 |
| 5 g acidental | póstero-sup. | 95.2–167 | 82.8 | 23.1 | 3.58 | 1.45 | 1.93 | 173 | 10.0 | 8584 | 0.756 |
| manuseio 10 N | sela | 95.2–167 | 82.8 | 72.4 | 1.14 | 1.15 | 1.44 | 12.9 | 10.0 | 755 | 0 |
| manuseio 10 N | temporal | 95.2–167 | 82.8 | 41.1 | 2.01 | 1.32 | 1.72 | 47.3 | 10.0 | 244 | 0.166 |
| manuseio 10 N | mastoide | 95.2–167 | 82.8 | 41.0 | 2.02 | 1.32 | 1.72 | 48.7 | 10.0 | 229 | 0.167 |
| manuseio 10 N | póstero-sup. | 95.2–167 | 82.8 | 40.7 | 2.04 | 1.33 | 1.72 | 51.6 | 10.0 | 223 | 0.179 |


60 mm — mínimo sobre todas as combinações de carga de cada categoria (faixa de F_i, D_parafuso e o FS de arrancamento na pré-carga nominal mostrados para a combinação com o menor FS de engate):

| caso | braço | faixa de F_i N (K 0.35–0.20) | F_i após fluência (a partir da menor) N | D_parafuso N | FS engate (≥1) | FS arrancamento do inserto na maior F_i (≥1) | FS arrancamento na F_i nominal | FS esmagamento no rasgo (≥1) | FS giro | FS cisalhamento do dente | junta lisa: FS escorregamento |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 g normal | sela | 95.2–167 | 82.8 | 5.70 | 14.5 | 1.60 | 2.20 | 69.9 | 10.0 | 973 | 0.640 |
| 1 g normal | temporal | 95.2–167 | 82.8 | 6.66 | 12.4 | 1.59 | 2.19 | 474 | 10.0 | 1381 | 3.06 |
| 1 g normal | mastoide | 95.2–167 | 82.8 | 8.48 | 9.76 | 1.57 | 2.16 | 343 | 10.0 | 1508 | 1.98 |
| 1 g normal | póstero-sup. | 95.2–167 | 82.8 | 5.44 | 15.2 | 1.60 | 2.21 | 1044 | 10.0 | 3191 | 5.11 |
| 2 g dinâmico | sela | 95.2–167 | 82.8 | 20.2 | 4.10 | 1.47 | 1.97 | 39.3 | 10.0 | 532 | 0.358 |
| 2 g dinâmico | temporal | 95.2–167 | 82.8 | 11.8 | 6.99 | 1.54 | 2.10 | 261 | 10.0 | 1211 | 1.22 |
| 2 g dinâmico | mastoide | 95.2–167 | 82.8 | 14.9 | 5.56 | 1.51 | 2.05 | 268 | 10.0 | 561 | 1.18 |
| 2 g dinâmico | póstero-sup. | 95.2–167 | 82.8 | 7.03 | 11.8 | 1.58 | 2.18 | 791 | 10.0 | 2332 | 3.90 |
| 3 g severo | sela | 95.2–167 | 82.8 | 32.2 | 2.57 | 1.38 | 1.82 | 33.9 | 10.0 | 323 | 0.0856 |
| 3 g severo | temporal | 95.2–167 | 82.8 | 18.0 | 4.60 | 1.49 | 2.01 | 180 | 10.0 | 773 | 0.720 |
| 3 g severo | mastoide | 95.2–167 | 82.8 | 20.3 | 4.08 | 1.47 | 1.97 | 200 | 10.0 | 401 | 0.731 |
| 3 g severo | póstero-sup. | 95.2–167 | 82.8 | 10.4 | 7.96 | 1.55 | 2.12 | 454 | 10.0 | 1506 | 2.71 |
| 5 g acidental | sela | 95.2–167 | 82.8 | 35.6 | 2.33 | 1.36 | 1.78 | 34.4 | 10.0 | 280 | 0.113 |
| 5 g acidental | temporal | 95.2–167 | 82.8 | 43.3 | 1.91 | 1.31 | 1.69 | 81.4 | 10.0 | 256 | 0.110 |
| 5 g acidental | mastoide | 95.2–167 | 82.8 | 47.1 | 1.76 | 1.29 | 1.66 | 61.6 | 10.0 | 178 | 0.0517 |
| 5 g acidental | póstero-sup. | 95.2–167 | 82.8 | 27.3 | 3.03 | 1.42 | 1.88 | 159 | 10.0 | 1859 | 0.554 |
| manuseio 10 N | sela | 95.2–167 | 82.8 | 72.4 | 1.14 | 1.15 | 1.44 | 12.9 | 10.0 | 755 | 0 |
| manuseio 10 N | temporal | 95.2–167 | 82.8 | 41.1 | 2.01 | 1.32 | 1.72 | 47.3 | 10.0 | 244 | 0.166 |
| manuseio 10 N | mastoide | 95.2–167 | 82.8 | 41.0 | 2.02 | 1.32 | 1.72 | 48.7 | 10.0 | 229 | 0.167 |
| manuseio 10 N | póstero-sup. | 95.2–167 | 82.8 | 40.7 | 2.04 | 1.33 | 1.72 | 51.6 | 10.0 | 223 | 0.179 |


Junta M3 do braço sob a carga de manuseio de 10 N (50 mm, todos os braços): menor FS de engate / arrancamento sobre o passo dos insertos (linhas) e o torque de aperto (colunas). Os dois precisam ser ≥ 1: mais torque ajuda o engate e prejudica o arrancamento, um passo maior ajuda os dois (menor razão de alavanca) e custa 1.49 g por mm por lado (§5, W5):

| passo dos insertos mm | 0.08 N·m: engate / arrancamento | 0.10 N·m: engate / arrancamento | 0.12 N·m: engate / arrancamento | 0.15 N·m: engate / arrancamento |
|---|---|---|---|---|
| 7.10 | 0.673 / 1.19 | 0.842 / 1.04 | 0.884 / 0.922 | 0.884 / 0.789 |
| 8.00 | 0.736 / 1.23 | 0.920 / 1.07 | 0.966 / 0.948 | 0.966 / 0.809 |
| 9.00 | 0.802 / 1.27 | 1.00 / 1.10 | 1.05 / 0.973 | 1.05 / 0.827 |
| 10.0 | 0.863 / 1.31 | 1.08 / 1.13 | 1.13 / 0.994 | 1.13 / 0.842 |
| 11.0 | 0.921 / 1.34 | 1.15 / 1.15 | 1.21 / 1.01 | 1.21 / 0.854 |


Escolhido: 11 mm a 0.10 N·m, menor FS 1.15; a melhor combinação mais estreita (10 mm a 0.10 N·m) mantém 1.08. A margem é desejada no engate, que depende da entrada menos certa (a fluência em 3 anos do PETG apertado).

Carga de manuseio de 10 N numa almofada (302 direções), 50 mm — FS mínimos da junta por braço: sela: engate 1.14, arrancamento 1.15, rasgo 12.9; temporal: engate 2.01, arrancamento 1.32, rasgo 47.3; mastoide: engate 2.02, arrancamento 1.32, rasgo 48.7; póstero-sup.: engate 2.04, arrancamento 1.33, rasgo 51.6.

'Junta lisa' = os mesmos esforços de seção numa fixação com rasgo só por atrito (Projeto A/B): onde o seu FS é < 1 ela escorrega — a razão da serrilha.

Ressaltos dos insertos a quente (as paredes do projeto: a regra ou a parede mínima de 1.6 mm, a que for maior; as abas do anel têm 3.2 mm; e uma parede de 1.00 mm como o contraexemplo que a regra da parede exclui):

| inserto | papel | parede mm | regra parede ≥ 0.5·OD | tangencial MPa | FS (entre camadas) |
|---|---|---|---|---|---|
| M3 | projeto | 2.30 | sim | 11.0 | 1.70 |
| M2.5 | projeto | 2.00 | sim | 10.9 | 1.71 |
| M2.5 | contraexemplo | 1.00 | NÃO | 17.0 | 1.10 |
| M3 | contraexemplo | 1.00 | NÃO | 19.0 | 0.982 |


Feltro traseiro: um disco cortado em faca empurrado sobre o ressalto do olhal da ligação (furo 0.5 mm menor que o diâmetro do ressalto, então nenhum ar contorna o feltro ali; cadeia no §17) e colado no lado de dentro do fundo da concha por uma borda de adesivo acrílico PSA fora da grade. Ele substitui o anel de retenção de PETG por interferência da iteração anterior, que falhou na sua própria verificação (FS tangencial sustentado 0.591–0.898 na tolerância superior de interferência) e colidiria com o ressalto do olhal, que agora fica dentro da concha para que o inserto tenha todo o seu comprimento em material sólido. Cargas que puxam o feltro: a sua inércia a 5 g mais uma amplitude de pressão na cavidade traseira de 89 Pa (130 dB SPL) [A] na sua área livre; capacidade: a borda descola a partir da sua borda interna em toda a volta a ≥ 3 N/cm [A]:

| D | feltro g | furo Ø mm | carga N | capacidade ao descolamento N | FS |
|---|---|---|---|---|---|
| 40 | 0.378 | 7.50 | 0.0840 | 29.4 | 350 |
| 45 | 0.478 | 7.50 | 0.109 | 33.4 | 306 |
| 50 | 0.584 | 7.50 | 0.135 | 37.3 | 276 |
| 55 | 0.721 | 7.50 | 0.170 | 41.9 | 247 |
| 60 | 0.882 | 7.50 | 0.211 | 46.7 | 222 |


Olhal da ligação na concha (módulo de 60 mm: a maior carga ao colocar dos cinco): P = 5.00 N na referência de 50 mm, 9.50 N ao colocar. O olhal do fio envolve uma bucha de latão (r_i = 3.75 mm ≥ 1.5 d): carga em linha q = P_don/r_i (tração do fio no pino, limite de corda; uma distribuição cossenoidal de apoio no pino dá 2/π = 0.64 disso) = 2534 N/m, meia largura de Hertz 7.31 µm, p0 221 MPa, τ_máx ≈ 0.3 p0 → FS 1.89 no escoamento ao cisalhamento do latão (Tresca, 0.5 × 250 MPa [LIT]); o inserto M2.5 apoia lateralmente no ressalto (estaca curta rígida num leito elástico, pico p = P/(d L)·(4 + 6e/L), e = 2 mm, meia altura da bucha) a 4.16 MPa (FS 5.62 sustentado).

Trava de giro (UMI-2): os fundos das linguetas apoiam no fundo rígido da ranhura; tiras de espuma com PSA só no topo das linguetas mantêm o módulo sem folga fora da cabeça e definem o torque de montagem. Especificação deduzida da espuma: janela CFD25 de 42.5–49.8 kPa sobre todos os módulos (viável: sim); especificado 46.0 kPa (governam: 60 mm na extremidade inferior, 40 mm na superior).

| D | módulo g | P N | F da espuma após assentamento N | torque de giro máx. N·m | torque de retenção na cabeça N·m | FS fundo (sustentado) | aceleração de desprendimento g | FS apoio do cone | FS cisalhamento na raiz da lingueta | FS flexão na raiz da lingueta | FS Hertz no pino |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 40 | 61.9 | 4.67 | 2.03 | 0.277 | 0.105 | 496 | 11.0 | 1527 | 425 | 394 | 243 |
| 45 | 68.1 | 4.84 | 2.03 | 0.277 | 0.106 | 479 | 10.3 | 1389 | 386 | 359 | 232 |
| 50 | 78.2 | 5.00 | 2.03 | 0.277 | 0.108 | 464 | 9.17 | 1209 | 353 | 345 | 222 |
| 55 | 87.0 | 5.16 | 2.03 | 0.277 | 0.109 | 449 | 8.43 | 1087 | 318 | 310 | 210 |
| 60 | 95.6 | 5.33 | 2.03 | 0.277 | 0.110 | 435 | 7.85 | 989 | 289 | 282 | 201 |


A junta de TPU comprimida do Projeto B para comparação: compressão nominal 0.05 mm, faixa de Monte Carlo -0.178 … 0.275 mm — de zero (folga) a apertada demais: torque de travamento na extremidade superior 20.7 N·m.

## 14. Cargas do cabo


Cargas do cabo e o "fusível mecânico" do cabo.

Caminho de carga: cabo -> clipe de TPU (aperto por interferência) no pino do clipe da
âncora do cabo -> âncora (2 x M3 na aba do anel em cable_a) -> anel ->
braços -> cabeça. Depois do clipe, o plugue de 2 pinos de 0.78 mm fica no soquete.

Intenção de projeto: num enganchamento o cabo tem de soltar ANTES que algo quebre.
  * o clipe escorrega em F_clip (atrito de interferência),
  * depois o plugue sai em F_plug (retenção do conector, [A] 4–15 N).
Então o suporte nunca vê mais que max(F_clip, F_plug), por mais forte que o cabo
seja enganchado; esse valor, e não o enganchamento de 20 N, é a carga de projeto do cabo
para a estrutura. F_clip é dimensionada abaixo de F_plug para que um puxão
primeiro deslize o cabo no clipe (inofensivo) e o plugue seja o fusível final.

Aperto do clipe (Lamé, ajuste por interferência de um anel de TPU num cabo redondo flexível):
  p = delta_r / ( R [ (1/E_r) ((ro^2 + R^2)/(ro^2 - R^2) + nu_r) + (1 - nu_c)/E_c ] )
  F_clip = mu * p * pi * D * L


B: peso do cabo 0.0755 N; aperto do clipe 20.9 N (p de contato 0.437 MPa); plugue 8.00 N (superior 15.0 N); força que chega ao suporte antes de soltar 20.9 N (superior 20.9 N); aperto do clipe abaixo da retenção do plugue: NÃO.

Final: peso do cabo 0.0755 N; aperto do clipe 5.22 N (p de contato 0.109 MPa); plugue 8.00 N (superior 15.0 N); força que chega ao suporte antes de soltar 8.00 N (superior 15.0 N); aperto do clipe abaixo da retenção do plugue: sim.

Aperto do clipe ao longo da tolerância FDM do furo (interferência 0 / 0.05 / 0.35 mm): 0, 5.22, 36.5 N — o aperto não pode ser definido pela interferência dentro da tolerância de impressão, então o clipe é uma guia de passagem e o plugue é o fusível.

Limites de puxão com o fone na cabeça — o puxão do cabo no clipe que o suporte aguenta antes do escorregamento grosseiro (modelo de suporte, bisseção):

| direção do puxão | 40 mm N | 50 mm N | 60 mm N |
|---|---|---|---|
| para baixo | 9.56 | 9.52 | 9.62 |
| baixo-fora 45 | 2.18 | 2.36 | 2.59 |
| baixo-dentro 45 | 2.83 | 3.22 | 3.24 |
| baixo-frente 45 | 3.97 | 4.12 | 4.37 |
| baixo-trás 45 | 2.16 | 2.30 | 2.48 |
| fora (10 graus abaixo da horizontal) | 1.34 | 1.47 | 1.62 |
| frente (10 graus abaixo) | 1.76 | 1.85 | 2.02 |
| trás (10 graus abaixo) | 1.62 | 1.74 | 1.88 |
| mínimo sobre o hemisfério para baixo | 1.36 | 1.46 | 1.57 |


Puxões quase horizontais (para fora, para a frente, para trás) de 1.34–2.02 N soltam o suporte, menos que os 8.00 N que chegam ao suporte antes que o plugue solte; direto para baixo são precisos 9.52–9.62 N. Por isso o cabo tem de ser passado descendo pelo pescoço — uma instrução ao usuário.
![limites de puxão](fig/tug_limits.png)

| D | ação no plugue com o fone na cabeça | F_z N | suporte preso | Fn mín. nas almofadas de pele N |
|---|---|---|---|---|
| 40 | inserir (empurrar em direção à cabeça) | -10.0 | Não | – |
| 40 | remover a 15 N (puxar) | 15.0 | Não | – |
| 40 | remover a 8 N nominal | 8.00 | Não | – |
| 50 | inserir (empurrar em direção à cabeça) | -10.0 | Não | – |
| 50 | remover a 15 N (puxar) | 15.0 | Não | – |
| 50 | remover a 8 N nominal | 8.00 | Não | – |
| 60 | inserir (empurrar em direção à cabeça) | -10.0 | Não | – |
| 60 | remover a 15 N (puxar) | 15.0 | Não | – |
| 60 | remover a 8 N nominal | 8.00 | Não | – |


Ações no plugue que soltam o suporte na cabeça: inserir (empurrar em direção à cabeça) (40, 50, 60 mm); remover a 15 N (puxar) (40, 50, 60 mm); remover a 8 N nominal (40, 50, 60 mm) — conectar e desconectar o plugue com o fone fora da cabeça (instrução).

Parafusos da âncora do cabo (alavanca em torno dos dois eixos, fator de junta 1; capacidade = arrancamento / γ_inserto):

| caso de carga do cabo | parafuso | torque N·m | T_ext por parafuso N | F_i N | F_i envelhecida N | FS inicial | FS envelhecido | alavanca mm |
|---|---|---|---|---|---|---|---|---|
| plugue nominal (fusível) | M3 | 0.100 | 28.1 | 119 | 86.9 | 1.41 | 2.39 | 21.0 |
| plugue superior (15 N) | M3 | 0.100 | 52.7 | 119 | 86.9 | 1.25 | 1.97 | 21.0 |
| clipe + plugue em série (superior) | M3 | 0.100 | 71.0 | 119 | 86.9 | 1.16 | 1.74 | 21.0 |
| enganchamento 20 N | M3 | 0.100 | 70.3 | 119 | 86.9 | 1.16 | 1.75 | 21.0 |


Pino do clipe (balanço a partir do bloco da âncora): impresso de lado, a flexão fica na camada; em pé ele carregaria as camadas em tração:

| caso de carga do cabo | F N | FS impresso de lado | FS se impresso em pé |
|---|---|---|---|
| plugue nominal (fusível) | 8.00 | 12.7 | 11.6 |
| plugue superior (15 N) | 15.0 | 6.75 | 6.18 |
| clipe + plugue em série (superior) | 20.2 | 5.01 | 4.59 |
| enganchamento 20 N | 20.0 | 5.06 | 4.64 |


## 15. Frequências naturais e isolamento de vibração


Frequências naturais e isolamento de vibração. NENHUMA FEA modal foi rodada.

1. Modos de corpo rígido do fone sobre os seus contatos (6 GDL):
       K q = w^2 M q,   M = [[m I, -m [c]x], [m [c]x, I_O]]
   K = rigidez tangente dos contatos ativos + ligação no equilíbrio estático
   em pé (support.Model), resolvido com scipy.linalg.eigh.
2. Primeiro modo de flexão do braço (balanço) por Rayleigh: f = (1/2pi) sqrt(k_tip / m_eff),
   m_eff = almofada + (33/140) x massa do braço (balanço uniforme, equivalente de massa na ponta de Rayleigh, ARM_MASS_FACTOR).
3. Isolamento do driver no módulo: o aro do driver fica numa junta de TPU; a
   força de reação do driver (massa móvel x aceleração do diafragma) passa
   para o módulo através dela. Transmissibilidade de isolamento de base de 1 GDL
       T(f) = sqrt(1 + (2 zeta r)^2) / sqrt((1 - r^2)^2 + (2 zeta r)^2), r = f/f_n
   (isolamento só acima de sqrt(2) f_n).
4. Transmissibilidade cabeça–fone da excitação de caminhada/corrida
   pelas molas de contato (mesma forma de 1 GDL por modo; sem amortecimento, o que
   limita T por cima abaixo de sqrt(2) f_n), na faixa de movimento da cabeça F_HEAD [A].


| D | modo 1 Hz | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 40 | 34.3 (rotação em torno de x) | 43.4 (translação x) | 58.7 (rotação em torno de z) | 66.8 (translação z) | 87.4 (translação y) | 124 (rotação em torno de y) |
| 45 | 33.4 (rotação em torno de x) | 42.3 (translação x) | 58.2 (rotação em torno de z) | 65.6 (translação z) | 87.0 (translação y) | 123 (rotação em torno de y) |
| 50 | 32.1 (rotação em torno de x) | 40.8 (translação x) | 57.5 (rotação em torno de z) | 63.8 (translação z) | 86.3 (translação y) | 121 (rotação em torno de y) |
| 55 | 31.1 (rotação em torno de x) | 39.6 (translação x) | 56.9 (rotação em torno de z) | 62.3 (translação z) | 85.8 (translação y) | 120 (rotação em torno de y) |
| 60 | 30.1 (rotação em torno de x) | 38.4 (translação x) | 56.2 (rotação em torno de z) | 60.9 (translação z) | 85.1 (translação y) | 119 (rotação em torno de y) |


| D | braço | k_z N/m | m_ef g | f1 Hz |
|---|---|---|---|---|
| todos | temporal | 69795 | 3.15 | 750 |
| todos | mastoide | 92963 | 4.29 | 741 |
| todos | póstero-sup. | 96403 | 3.48 | 838 |
| todos | sela | 5764 | 8.82 | 129 |


| D | k da junta do driver N/m | fator de forma | f_n Hz | isola acima de Hz |
|---|---|---|---|---|
| 40 | 6.41e+07 | 1.79 | 10405 | 14715 |
| 45 | 7.25e+07 | 1.79 | 9834 | 13908 |
| 50 | 8.1e+07 | 1.79 | 8882 | 12561 |
| 55 | 8.94e+07 | 1.79 | 8285 | 11716 |
| 60 | 9.78e+07 | 1.79 | 7872 | 11132 |


Opções de montagem do driver a 50 mm (Gent E(Shore) [EMP] para os anéis de silicone, mesmo fator de forma):

| montagem | E MPa | k N/m | f_n Hz | isola acima de Hz | T(100 Hz) | T(1 kHz) | T(5 kHz) | deflexão em 5 g µm |
|---|---|---|---|---|---|---|---|---|
| TPU 95A (Final) | 26.0 | 8.1e+07 | 8882 | 12561 | 1.00 | 1.01 | 1.45 | 0.0157 |
| silicone 50A | 2.46 | 7.65e+06 | 2730 | 3861 | 1.00 | 1.15 | 0.472 | 0.167 |
| silicone 40A | 1.69 | 5.26e+06 | 2264 | 3202 | 1.00 | 1.24 | 0.305 | 0.242 |
| silicone 30A | 1.14 | 3.56e+06 | 1862 | 2633 | 1.00 | 1.39 | 0.205 | 0.358 |


Anéis de silicone macios colocam a ressonância do driver na montagem em 1.86–2.73 kHz, dentro da faixa de áudio (eles amplificam ali e só isolam acima de √2 f_n); a junta de aro de TPU 95A a coloca em 8.88 kHz, acima da faixa em que o modelo concentrado é afirmado (§21: medir), e ela também veda o aro — ela é mantida. Na pele, o fone inteiro tem os seus modos de corpo rígido em 30.1–124 Hz, acima da faixa de movimento da cabeça (1–10 Hz [A]): o fone segue a cabeça de forma quase estática, amplificado no máximo por T = 1/(1 − r²) = 1.12 (limite sem amortecimento, modo mais baixo, 10 Hz). Primeiros modos do braço livre (Rayleigh, sem contato com a pele): braços das almofadas 741–838 Hz, braço da sela 129 Hz — dentro da faixa de graves; na cabeça os contatos da raiz e do couro cabeludo acrescentam rigidez e amortecimento, que este valor de braço livre deixa de fora, então uma verificação de zumbido na varredura senoidal está no plano de testes (§22).

![isolamento](fig/driver_isolation.png)

## 16. Acústica


Modelo acústico do módulo UMEH-2 — circuito ELETRO-MECÂNICO-ACÚSTICO CONCENTRADO
mais radiação em forma fechada. NENHUM FEM/BEM acústico foi rodado.

Validade: elementos concentrados exigem que toda dimensão de cavidade seja < lambda/4
(concha ~ 60 mm -> ~1.4 kHz estrito, ~3 kHz utilizável); as fórmulas de radiação de
pistão/borda valem até ~8 kHz [A]; acima disso o pavilhão e a cabeça (HRTF)
dominam e nada aqui é afirmado. Tudo acima de 3 kHz é marcado como
"indicativo".

Driver (por tamanho): os valores de Thiele/Small são SUPOSIÇÕES REPRESENTATIVAS [A]
(sem dados do fabricante). Substitua-os por valores medidos
(varredura de impedância, método da massa adicionada, veja o relatório) e rode de novo.

Circuito (analogia de impedância, SI):
  elétrico     Ze  = Re + j w Le
  mecânico     Zm  = Rms + j w Mms + 1/(j w Cms)
  acústico     Z_F (carga frontal) e Z_B (carga traseira) vistas pelo diafragma,
               refletidas como Sd^2 (Z_F + Z_B)
  velocidade do diafragma   u = Bl e / [ Ze (Zm + Sd^2 (Z_F + Z_B)) + Bl^2 ]
  velocidade de volume      U = Sd u
Carga frontal, ABERTA (fora da orelha): impedância de radiação de um pistão com defletor
  Z_rad = rho c / S [ 1 - J1(2ka)/(ka) + j H1(2ka)/(ka) ]            (exata, Bessel/Struve)
  em série com o tubo da abertura (massa do furo do defletor incl. correções de extremidade)
Carga frontal, VEDADA (opção com almofada de vedação): compliância da cavidade C_f = V_f/(rho c^2)
  em paralelo com o vazamento (fresta: massa + resistência viscosa).
Carga traseira: compliância do volume da concha C_b = V_b/(rho c^2) em paralelo com o
  caminho de saída (furos da grade / respiros: massa com correções de extremidade, resistência
  viscosa) em série com a resistência do feltro R_felt = sigma t / A.
Pressão na orelha (frente aberta): campo próximo do pistão no eixo
  p_F = rho c u [exp(-jkz) - exp(-jk sqrt(z^2 + a^2))]  x 2 (superfície rígida da cabeça/pavilhão)
  z = plano de saída da abertura até a entrada do canal auditivo (ear_distance: afastamento do CAD
  e face do módulo, projeção média do pavilhão menos a profundidade da concha [A/LIT])
menos a onda traseira (monopolo de velocidade de volume U_out na grade)
contornando a borda do módulo (caminho L_r) com um fator de difração de borda
D = 1/sqrt(1 + (k r_edge)^2) por borda [estimativa].


| D | Vb cm³ [CAD] | Vas cm³ | α = Vas/Vb | Qts | Qtc (fechada) | Fs Hz | Fc Hz (fechada) | furos da grade | concha (1,1) Hz | concha axial Hz | fresta λ/2 Hz |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 40 | 8.16 | 536 | 65.7 | 0.400 | 3.27 | 120 | 980 | 52.0 | 5762 | 11385 | 5967 |
| 45 | 10.5 | 916 | 87.5 | 0.400 | 3.76 | 104 | 977 | 70.0 | 5148 | 10682 | 5967 |
| 50 | 13.0 | 1551 | 120 | 0.400 | 4.39 | 90.0 | 988 | 86.0 | 4652 | 10179 | 5967 |
| 55 | 16.8 | 2456 | 146 | 0.400 | 4.86 | 79.4 | 964 | 114 | 4182 | 9614 | 5967 |
| 60 | 21.4 | 3859 | 180 | 0.400 | 5.38 | 70.0 | 942 | 142 | 3791 | 9108 | 5967 |


**Consequência:** uma traseira fechada eleva a ressonância para Fc = 942–988 Hz com Qtc = 3.27–5.38 — inutilizável. Daí a traseira aberta amortecida por feltro (padrão) ou uma traseira com muitos respiros.

Abertura do defletor: ressonância de Helmholtz da minicavidade entre diafragma e abertura + tubo da abertura f = c/2π·√(S/(V·L_ef)), L_ef = t + (0.5 + 1)·0.85a: a correção de extremidade externa é a massa de radiação do pistão com defletor, a interna é reduzida pelo chanfro e pelo diafragma próximo [A] (a mesma massa da abertura do modelo de resposta):

| D | abertura 0.60 D | abertura 0.75 D | abertura 0.88 D (escolhida) | abertura 1.00 D |
|---|---|---|---|---|
| 40 | 8.93 kHz | 10.1 kHz | 11.1 kHz | 11.9 kHz |
| 45 | 8.48 kHz | 9.60 kHz | 10.5 kHz | 11.2 kHz |
| 50 | 8.10 kHz | 9.15 kHz | 9.98 kHz | 10.7 kHz |
| 55 | 7.76 kHz | 8.76 kHz | 9.55 kHz | 10.2 kHz |
| 60 | 7.46 kHz | 8.42 kHz | 9.17 kHz | 9.82 kHz |


Abertura = 0.88 D [A] (não D): ela livra o diafragma móvel e metade da suspensão e se sobrepõe ao lábio da armação frontal do driver para que a junta do aro vede; o chanfro de 45° × 1.5 mm remove o degrau vivo. A ressonância da minicavidade frontal fica então em 9.17–11.1 kHz — dentro da faixa de áudio e acima da faixa em que o modelo concentrado é afirmado, então o seu nível e amortecimento ficam para a medição (§21, §22); alargar a abertura para D só a eleva até a última coluna.

Helmholtz do respiro (porta traseira), concha de 50 mm, correções de extremidade 0.85 r (com flange, dentro) + 0.61 r (sem flange, fora) [STD]:

| n respiros | Ø mm | f_b Hz | L_ef mm |
|---|---|---|---|
| 1 | 1.50 | 365 | 3.10 |
| 1 | 2.00 | 461 | 3.46 |
| 1 | 3.00 | 628 | 4.19 |
| 1 | 4.00 | 773 | 4.92 |
| 2 | 1.50 | 517 | 3.10 |
| 2 | 2.00 | 652 | 3.46 |
| 2 | 3.00 | 888 | 4.19 |
| 2 | 4.00 | 1093 | 4.92 |
| 3 | 1.50 | 633 | 3.10 |
| 3 | 2.00 | 798 | 3.46 |
| 3 | 3.00 | 1088 | 4.19 |
| 3 | 4.00 | 1339 | 4.92 |
| 4 | 1.50 | 731 | 3.10 |
| 4 | 2.00 | 922 | 3.46 |
| 4 | 3.00 | 1256 | 4.19 |
| 4 | 4.00 | 1546 | 4.92 |
| 6 | 1.50 | 895 | 3.10 |
| 6 | 2.00 | 1129 | 3.46 |
| 6 | 3.00 | 1539 | 4.19 |
| 6 | 4.00 | 1893 | 4.92 |


Frente vedada (opção com almofada de vedação): V_f = 87.0 cm³ [C: da pele à face do anel dentro do diâmetro interno da vedação mais o rebaixo do módulo no furo, menos 10 cm³ de pavilhão A]; vazamento = fresta entre almofada e pele (R = 12μL/(h³b), M = 1.2ρL/(hb)).

Material × altura da almofada de vedação na pressão que a pré-carga pode ceder (0.5 kPa [A]): a conformidade δ = pH/E contra uma irregularidade da cabeça de 1 mm [A] deixa uma fresta h = max(0.02 mm, a − δ); perda de graves em relação a uma vedação perfeita:

| material | E kPa | H mm | δ mm | fresta mm | perda 50 Hz dB | perda 100 Hz dB |
|---|---|---|---|---|---|---|
| TPU gyroid 10% | 520 | 10.0 | 0.00962 | 0.990 | 22.0 | 16.7 |
| TPU gyroid 10% | 520 | 20.0 | 0.0192 | 0.981 | 21.9 | 16.6 |
| TPU gyroid 10% | 520 | 29.0 | 0.0279 | 0.972 | 21.8 | 16.5 |
| TPU gyroid 15% | 1170 | 10.0 | 0.00427 | 0.996 | 22.1 | 16.7 |
| TPU gyroid 15% | 1170 | 20.0 | 0.00855 | 0.991 | 22.1 | 16.7 |
| TPU gyroid 15% | 1170 | 29.0 | 0.0124 | 0.988 | 22.0 | 16.6 |
| TPU gyroid 25% | 3250 | 10.0 | 0.00154 | 0.998 | 22.1 | 16.7 |
| TPU gyroid 25% | 3250 | 20.0 | 0.00308 | 0.997 | 22.1 | 16.7 |
| TPU gyroid 25% | 3250 | 29.0 | 0.00446 | 0.996 | 22.1 | 16.7 |
| espuma de PU 30 kg/m3 | 28.1 | 10.0 | 0.178 | 0.822 | 19.7 | 15.0 |
| espuma de PU 30 kg/m3 | 28.1 | 20.0 | 0.356 | 0.644 | 16.1 | 12.7 |
| espuma de PU 30 kg/m3 | 28.1 | 29.0 | 0.516 | 0.484 | 11.2 | 9.65 |
| espuma de PU 50 kg/m3 | 78.1 | 10.0 | 0.0640 | 0.936 | 21.4 | 16.2 |
| espuma de PU 50 kg/m3 | 78.1 | 20.0 | 0.128 | 0.872 | 20.5 | 15.5 |
| espuma de PU 50 kg/m3 | 78.1 | 29.0 | 0.186 | 0.814 | 19.6 | 14.9 |
| espuma de PU 80 kg/m3 | 200 | 10.0 | 0.0250 | 0.975 | 21.9 | 16.5 |
| espuma de PU 80 kg/m3 | 200 | 20.0 | 0.0500 | 0.950 | 21.5 | 16.3 |
| espuma de PU 80 kg/m3 | 200 | 29.0 | 0.0725 | 0.928 | 21.3 | 16.1 |


Fechar a irregularidade de 1 mm até a fresta de 0.02 mm com o material mais macio (espuma de PU 30 kg/m3, a almofada mais alta de 29 mm) exige p = (a − h_mín)·E/H = 0.950 kPa, 1.90 × os 0.5 kPa que a pré-carga pode ceder — por isso o Final é aberto (a almofada de vedação continua uma opção para usuários que aceitam a pressão).
![vedação](fig/seal_sweep.png)

Amortecimento: disco de feltro (resistividade ao fluxo σ, espessura t) no fundo da concha, R = σ t / A; ele fica no antinó de pressão do modo axial da concha e em série com a grade, acrescentando resistência atrás do diafragma (Q menor em Fs) e absorvendo os modos da concha acima.

![varreduras acústicas](fig/acoustic_sweeps.png)
![impedância](fig/impedance.png)
![abertura](fig/aperture_helmholtz.png)

Aberta vs semiaberta vs fechada (50 mm, 23 mm da abertura até a entrada do canal auditivo: afastamento 29 + rebaixo do módulo 2 − (projeção média do pavilhão 20 − profundidade da concha 12) mm [CAD, A/LIT]; SPL a 100 Hz com o mesmo sinal: aberta 95.3 dB, com respiros 93.0 dB, fechada 65.2 dB): a aberta (grade + feltro) mantém Fs baixa e a resposta suave, mas, sendo aberta fora da orelha, perde graves por cancelamento frente/trás; com respiros é um meio-termo; fechada é inutilizável com estes volumes de concha. Distância da abertura à orelha de 13 → 33 mm custa 6.16 dB a 100 Hz e 5.59 dB a 1 kHz (termo de campo próximo e^{−jkz} − e^{−jk√(z²+a²)}) — mantenha o módulo perto; o afastamento é definido pelo pavilhão p95.

## 17. Acúmulo de tolerâncias


Acúmulo de tolerâncias: pior caso, RSS e Monte Carlo (100 000 amostras, cada
tolerância uma distribuição normal com +-tol = 3 sigma [A]).

Tolerâncias FDM [A, impressora típica bem ajustada com bico de 0.4 mm, PETG]:
  detalhe em XY +-0.15 mm, Z (quantizado pela camada) +-0.1 mm; diâmetros de furos
  impressos entram nas cadeias com a tolerância XY (um furo sistematicamente menor
  é um item de calibração da impressora: impressão de teste);
  contração linear: as duas peças são do mesmo material, então só a DIFERENÇA
  entre duas impressões importa para um ajuste, +-0.2 % [A].
Peças de TPU: +-0.15 mm de espessura.
Driver: diâmetro externo e espessura do aro como em design.DRIVERS (tol_d, tol_depth) [A].
Aceitação: os valores de Monte Carlo de 0.135 % / 99.865 % (+-3 sigma) têm de ficar
na janela [mín., máx.]; o pior caso (todos os termos no seu limite ao mesmo tempo) é
informado como referência.


Driver 40 mm:

| cadeia | nominal mm | pior caso | RSS | MC ±3σ | mín. | máx. | componente limitante | MC ok | PC ok |
|---|---|---|---|---|---|---|---|---|---|
| compressão da espuma da UMI (tira anti-ruído) | 0.560 | 0.177 … 0.943 | 0.352 … 0.768 | 0.353 … 0.767 | 0.160 | 0.960 | espessura da folha de espuma (corte em faca) | PASSA | PASS |
| folga radial da UMI (diametral) | 0.400 | -0.0540 … 0.854 | 0.138 … 0.662 | 0.136 … 0.659 | 0 | 0.800 | diferença de contração entre impressões | PASSA | **FALHA** |
| sobreposição radial da lingueta com o lábio | 2.30 | 1.95 … 2.65 | 2.07 … 2.53 | 2.08 … 2.52 | 1.20 | – | flutuação radial (meia folga, pior lado) | PASSA | PASS |
| aro do driver no alojamento (diametral) | 0.440 | -0.01 … 0.890 | 0.105 … 0.775 | 0.107 … 0.774 | 0 | 0.800 | diâmetro externo do aro do driver | PASSA | **FALHA** |
| compressão da junta do driver | 0.300 | -0.150 … 0.750 | 0.0709 … 0.529 | 0.0674 … 0.530 | 0.0500 | 0.600 | espessura da junta do driver | PASSA | **FALHA** |
| folga do pavilhão ao módulo (orelha p95) | 4.40 | 1.70 … 7.10 | 2.35 … 6.45 | 2.35 … 6.46 | 1.00 | – | projeção do pavilhão p95 | PASSA | PASS |
| furo do feltro no ressalto do olhal (interferência) | 0.500 | 0.150 … 0.850 | 0.250 … 0.750 | 0.249 … 0.753 | 0 | – | furo do feltro (corte em faca) | PASSA | PASS |


Driver 50 mm:

| cadeia | nominal mm | pior caso | RSS | MC ±3σ | mín. | máx. | componente limitante | MC ok | PC ok |
|---|---|---|---|---|---|---|---|---|---|
| compressão da espuma da UMI (tira anti-ruído) | 0.560 | 0.177 … 0.943 | 0.352 … 0.768 | 0.353 … 0.767 | 0.160 | 0.960 | espessura da folha de espuma (corte em faca) | PASSA | PASS |
| folga radial da UMI (diametral) | 0.400 | -0.0540 … 0.854 | 0.138 … 0.662 | 0.136 … 0.659 | 0 | 0.800 | diferença de contração entre impressões | PASSA | **FALHA** |
| sobreposição radial da lingueta com o lábio | 2.30 | 1.95 … 2.65 | 2.07 … 2.53 | 2.08 … 2.52 | 1.20 | – | flutuação radial (meia folga, pior lado) | PASSA | PASS |
| aro do driver no alojamento (diametral) | 0.440 | -0.01 … 0.890 | 0.105 … 0.775 | 0.107 … 0.774 | 0 | 0.800 | diâmetro externo do aro do driver | PASSA | **FALHA** |
| compressão da junta do driver | 0.300 | -0.150 … 0.750 | 0.0709 … 0.529 | 0.0674 … 0.530 | 0.0500 | 0.600 | espessura da junta do driver | PASSA | **FALHA** |
| folga do pavilhão ao módulo (orelha p95) | 4.40 | 1.70 … 7.10 | 2.35 … 6.45 | 2.35 … 6.46 | 1.00 | – | projeção do pavilhão p95 | PASSA | PASS |
| furo do feltro no ressalto do olhal (interferência) | 0.500 | 0.150 … 0.850 | 0.250 … 0.750 | 0.249 … 0.753 | 0 | – | furo do feltro (corte em faca) | PASSA | PASS |


Driver 60 mm:

| cadeia | nominal mm | pior caso | RSS | MC ±3σ | mín. | máx. | componente limitante | MC ok | PC ok |
|---|---|---|---|---|---|---|---|---|---|
| compressão da espuma da UMI (tira anti-ruído) | 0.560 | 0.177 … 0.943 | 0.352 … 0.768 | 0.353 … 0.767 | 0.160 | 0.960 | espessura da folha de espuma (corte em faca) | PASSA | PASS |
| folga radial da UMI (diametral) | 0.400 | -0.0540 … 0.854 | 0.138 … 0.662 | 0.136 … 0.659 | 0 | 0.800 | diferença de contração entre impressões | PASSA | **FALHA** |
| sobreposição radial da lingueta com o lábio | 2.30 | 1.95 … 2.65 | 2.07 … 2.53 | 2.08 … 2.52 | 1.20 | – | flutuação radial (meia folga, pior lado) | PASSA | PASS |
| aro do driver no alojamento (diametral) | 0.440 | -0.01 … 0.890 | 0.105 … 0.775 | 0.107 … 0.774 | 0 | 0.800 | diâmetro externo do aro do driver | PASSA | **FALHA** |
| compressão da junta do driver | 0.300 | -0.150 … 0.750 | 0.0709 … 0.529 | 0.0674 … 0.530 | 0.0500 | 0.600 | espessura da junta do driver | PASSA | **FALHA** |
| folga do pavilhão ao módulo (orelha p95) | 4.40 | 1.70 … 7.10 | 2.35 … 6.45 | 2.35 … 6.46 | 1.00 | – | projeção do pavilhão p95 | PASSA | PASS |
| furo do feltro no ressalto do olhal (interferência) | 0.500 | 0.150 … 0.850 | 0.250 … 0.750 | 0.249 … 0.753 | 0 | – | furo do feltro (corte em faca) | PASSA | PASS |


Toda cadeia atende a janela de ±3σ em todos os tamanhos verificados (40 mm, 50 mm, 60 mm). No pior caso, folga radial da UMI (diametral) sai da janela em até 0.0540 mm; aro do driver no alojamento (diametral) sai da janela em até 0.0900 mm; compressão da junta do driver sai da janela em até 0.200 mm: cada um exige todos os termos no seu limite de 3σ ao mesmo tempo, o que o critério estatístico aceita; o raro par de peças que cair ali é encontrado na montagem (verificação de ajuste).

## 18. Varreduras de parâmetros estruturais e do suporte (50 mm)

Espessura dos braços (estrutura) — barra, perna e pé escalados juntos:

| escala | barra/perna/pé mm | 5 g FS vM | em | 5 g FS entre camadas | manuseio FS vM | em | manuseio FS entre camadas | k_braço mastoide N/m | 5 g início λ mín. |
|---|---|---|---|---|---|---|---|---|---|
| 0.600 | 3.30/3.30/2.70 | 0.831 | mastoide: barra na borda da fixação (fim do rasgo) | 1.41 | 0.656 | sela: barra na borda da fixação (fim do rasgo) | 0.769 | 15721 | 0.0312 |
| 0.800 | 4.40/4.40/3.60 | 1.23 | temporal: barra na borda da fixação (fim do rasgo) | 3.36 | 1.13 | sela: barra na borda da fixação (fim do rasgo) | 1.28 | 42103 | 0.0312 |
| 0.900 | 4.95/4.95/4.05 | 1.55 | temporal: barra na borda da fixação (fim do rasgo) | 3.25 | 1.41 | sela: barra na borda da fixação (fim do rasgo) | 1.57 | 63737 | 0.0312 |
| 1.00 | 5.50/5.50/4.50 | 1.91 | temporal: barra na borda da fixação (fim do rasgo) | 3.92 | 1.72 | sela: barra na borda da fixação (fim do rasgo) | 1.89 | 92963 | 0.0312 |
| 1.20 | 6.60/6.60/5.40 | 2.58 | mastoide: barra na borda da fixação (fim do rasgo) | 5.42 | 2.40 | sela: barra na borda da fixação (fim do rasgo) | 2.58 | 181578 | 0.0312 |
| 1.40 | 7.70/7.70/6.30 | 3.29 | mastoide: barra na borda da fixação (fim do rasgo) | 6.83 | 3.13 | sela: barra na borda da fixação (fim do rasgo) | 3.22 | 325600 | 0.0625 |


Tamanho e torque dos parafusos dos braços (junta serrilhada sob o envelope de 5 g e a carga de manuseio):

| parafuso | T N·m | FS mín. | governa | F_i N | F_i envelhecida N | D_parafuso N | FS engate | FS arrancamento | FS giro | FS rasgo | massa do par g |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | 0.0600 | 0.491 | sela (manuseio 10 N) | 107 | 61.6 | 105 | 0.588 | 0.491 | 5.83 | 487 | 0.940 |
| M2 | 0.100 | 0.352 | sela (manuseio 10 N) | 179 | 71.8 | 105 | 0.686 | 0.352 | 3.50 | 487 | 0.940 |
| M2 | 0.150 | 0.261 | sela (manuseio 10 N) | 268 | 71.8 | 105 | 0.686 | 0.261 | 2.33 | 487 | 0.940 |
| M2 | 0.250 | 0.171 | sela (manuseio 10 N) | 446 | 73.2 | 105 | 0.699 | 0.171 | 1.40 | 487 | 0.940 |
| M2 | 0.400 | 0.113 | sela (manuseio 10 N) | 714 | 117 | 105 | 1.12 | 0.113 | 0.875 | 487 | 0.940 |
| M2.5 | 0.0600 | 0.519 | sela (manuseio 10 N) | 85.7 | 54.4 | 105 | 0.519 | 0.845 | 10.0 | 608 | 1.50 |
| M2.5 | 0.100 | 0.623 | sela (manuseio 10 N) | 143 | 79.3 | 105 | 0.757 | 0.623 | 6.00 | 608 | 1.50 |
| M2.5 | 0.150 | 0.469 | sela (manuseio 10 N) | 214 | 79.3 | 105 | 0.757 | 0.469 | 4.00 | 608 | 1.50 |
| M2.5 | 0.250 | 0.314 | sela (manuseio 10 N) | 357 | 79.3 | 105 | 0.757 | 0.314 | 2.40 | 608 | 1.50 |
| M2.5 | 0.400 | 0.210 | sela (manuseio 10 N) | 571 | 93.7 | 105 | 0.895 | 0.210 | 1.50 | 608 | 1.50 |
| M3 | 0.0600 | 0.480 | sela (manuseio 10 N) | 71.4 | 49.7 | 103 | 0.480 | 1.35 | 16.7 | 736 | 2.56 |
| M3 | 0.100 | 0.800 | sela (manuseio 10 N) | 119 | 82.8 | 103 | 0.800 | 1.02 | 10.0 | 736 | 2.56 |
| M3 | 0.150 | 0.778 | sela (manuseio 10 N) | 179 | 86.9 | 103 | 0.840 | 0.778 | 6.67 | 736 | 2.56 |
| M3 | 0.250 | 0.529 | sela (manuseio 10 N) | 298 | 86.9 | 103 | 0.840 | 0.529 | 4.00 | 736 | 2.56 |
| M3 | 0.400 | 0.357 | sela (manuseio 10 N) | 476 | 86.9 | 103 | 0.840 | 0.357 | 2.50 | 736 | 2.56 |
| M4 | 0.0600 | 0.438 | sela (manuseio 10 N) | 53.6 | 39.3 | 89.7 | 0.438 | 2.73 | 30.0 | 1087 | 5.00 |
| M4 | 0.100 | 0.731 | sela (manuseio 10 N) | 89.3 | 65.5 | 89.7 | 0.731 | 2.10 | 18.0 | 1087 | 5.00 |
| M4 | 0.150 | 1.02 | sela (manuseio 10 N) | 134 | 91.8 | 89.7 | 1.02 | 1.62 | 12.0 | 1087 | 5.00 |
| M4 | 0.250 | 1.02 | sela (manuseio 10 N) | 223 | 91.8 | 89.7 | 1.02 | 1.12 | 7.20 | 1087 | 5.00 |
| M4 | 0.400 | 0.763 | sela (manuseio 10 N) | 357 | 91.8 | 89.7 | 1.02 | 0.763 | 4.50 | 1087 | 5.00 |


| almofada (TPU) h mm | p estático mastoide kPa | inclinação estática graus | demanda de μ estática | 1 g % | 1 g inclinação | 2 g % |
|---|---|---|---|---|---|---|
| 3.00 | 2.33 | 0.0888 | 0.802 | 0 | 0.380 | 3.05 |
| 4.50 | 2.33 | 0.0898 | 0.801 | 0 | 0.385 | 3.05 |
| 6.00 | 2.33 | 0.0909 | 0.799 | 0 | 0.390 | 3.05 |
| 8.00 | 2.33 | 0.0924 | 0.795 | 0 | 0.396 | 3.05 |
| 10.0 | 2.33 | 0.0939 | 0.791 | 0 | 0.402 | 3.05 |


| escala do raio das almofadas (espaçamento dos apoios) | estático | 1 g % | 1 g inclinação | 2 g % |
|---|---|---|---|---|
| 0.900 | sim | 0 | 1.15 | 4.05 |
| 0.950 | sim | 0 | 0.466 | 3.45 |
| 1.00 | sim | 0 | 0.390 | 3.05 |
| 1.05 | sim | 0 | 0.344 | 2.73 |
| 1.10 | sim | 0 | 0.309 | 2.43 |


| Δ ângulo temporal | Δ ângulo póstero-sup. | estático | 1 g % | 1 g inclinação | 2 g % |
|---|---|---|---|---|---|
| -15.0 | 0 | sim | 0 | 1.80 | 2.77 |
| -10.0 | 10.0 | sim | 0 | 3.86 | 5.92 |
| 0 | -15.0 | sim | 0 | 0.393 | 0.825 |
| 0 | 0 | sim | 0 | 0.390 | 3.05 |
| 0 | 15.0 | sim | 0.0713 | 4.93 | 8.12 |
| 10.0 | -10.0 | sim | 0 | 0.323 | 1.77 |
| 15.0 | 0 | sim | 0 | 0.357 | 3.90 |


| arco ('gancho') R mm | meio ângulo ° | p na raiz kPa (estático) | 1 g % | 2 g % |
|---|---|---|---|---|
| 16.0 | 25.0 | 3.44 | 0 | 3.77 |
| 16.0 | 35.0 | 3.23 | 0 | 3.05 |
| 16.0 | 45.0 | 2.90 | 0 | 2.85 |
| 22.0 | 25.0 | 3.48 | 0 | 3.70 |
| 22.0 | 35.0 | 3.27 | 0 | 3.05 |
| 22.0 | 45.0 | 2.94 | 0 | 2.88 |
| 30.0 | 25.0 | 3.52 | 0 | 3.80 |
| 30.0 | 35.0 | 3.31 | 0 | 3.12 |
| 30.0 | 45.0 | 2.98 | 0 | 2.88 |


Espessura do revestimento da sela (módulo de 60 mm, com o seu próprio olhal):

| revestimento mm | p na raiz kPa (estático) | demanda de μ estática | 1 g % | 1 g inclinação graus | 2 g % |
|---|---|---|---|---|---|
| 0 | 4.63 | 0.800 | 0 | 0.405 | 3.80 |
| 1.00 | 4.51 | 0.809 | 0 | 0.405 | 3.40 |
| 1.50 | 4.27 | 0.826 | 0 | 0.405 | 3.43 |
| 2.00 | 3.96 | 0.849 | 0 | 0.405 | 3.43 |
| 2.50 | 3.61 | 0.874 | 0 | 0.405 | 3.52 |
| 3.00 | 3.28 | 0.899 | 0 | 0.405 | 3.60 |


| material do revestimento (60 mm) | p na raiz kPa (estático) | demanda de μ estática | 1 g % | 2 g % |
|---|---|---|---|---|
| módulo do gel x0.5 | 2.96 | 0.922 | 0 | 3.92 |
| módulo do gel x2 (ou confinamento mais rígido) | 4.06 | 0.842 | 0 | 3.43 |
| nominal | 3.61 | 0.874 | 0 | 3.52 |


Razão de rigidez de contato tangencial/normal k_t/k_n [A] (ela decide quanto peso as almofadas levam por atrito):

| k_t/k_n (60 mm) | p na raiz kPa (estático) | demanda de μ estática | 1 g % | 1 g inclinação graus | 2 g % |
|---|---|---|---|---|---|
| 0.330 | 4.59 | 0.787 | 0 | 0.405 | 3.75 |
| 0.500 | 3.61 | 0.874 | 0 | 0.405 | 3.52 |
| 0.670 | 3.05 | 0.936 | 0 | 0.405 | 3.48 |


![varreduras](fig/structure_support_sweeps.png)
![ângulos](fig/support_angle_arch.png)

## 19. Resumo do pior caso e componentes limitantes

Ordenado pela utilização (demanda / permitido; 1 = no limite). A retenção em 2 g não é uma utilização: é a fração solta do conjunto de 2 g de combinações de carga (§8):

| verificação | onde | valor | requisito | utilização |
|---|---|---|---|---|
| pressão na raiz da orelha em uso, após a acomodação por movimento da cabeça (60 mm) | zonas do arco | 21.4 | ≤ 4.00 kPa sustentado; NÃO atendido (§6) | 5.35 |
| pressão na raiz da orelha em uso, após a acomodação por movimento da cabeça (55 mm) | zonas do arco | 20.5 | ≤ 4.00 kPa sustentado; NÃO atendido (§6) | 5.12 |
| pressão na raiz da orelha em uso, após a acomodação por movimento da cabeça (50 mm) | zonas do arco | 19.4 | ≤ 4.00 kPa sustentado; NÃO atendido (§6) | 4.86 |
| pressão na raiz se pendurado na orelha antes de prender (colocação B, 60 mm) | zonas do arco | 18.6 | ≤ 4.00 kPa sustentado (logo após colocar); não atendido → prender primeiro (colocação A) é a instrução | 4.65 |
| pressão na raiz da orelha em uso, após a acomodação por movimento da cabeça (45 mm) | zonas do arco | 18.4 | ≤ 4.00 kPa sustentado; NÃO atendido (§6) | 4.59 |
| pressão na raiz da orelha em uso, após a acomodação por movimento da cabeça (40 mm) | zonas do arco | 18.0 | ≤ 4.00 kPa sustentado; NÃO atendido (§6) | 4.50 |
| seção do braço, envelope de início em 5 g, 40 °C | 55 mm, mastoide: barra na borda da fixação (fim do rasgo) (vM) | 1.40 | FS ≥ γM 1.60 | 1.14 |
| seção do braço, fadiga 1e7 ciclos (envelope de 2 g mantido, de zero ao pico) | 60 mm, mastoide: barra na borda da fixação (fim do rasgo) | 1.71 | FS ≥ γM 1.60 | 0.938 |
| seção do braço, manuseio 10 N, 40 °C | 40 mm, sela: barra na borda da fixação (fim do rasgo) (vM) | 1.72 | FS ≥ γM 1.60 | 0.931 |
| pressão na raiz da orelha, colocação A (60 mm) | zonas do arco | 3.61 | ≤ 4.00 kPa sustentado (logo após colocar; em uso veja as linhas de acomodação) | 0.902 |
| engate da junta do braço (50 mm) | sela, manuseio 10 N | 1.14 | FS ≥ 1 com pré-carga envelhecida | 0.874 |
| engate da junta do braço (60 mm) | sela, manuseio 10 N | 1.14 | FS ≥ 1 com pré-carga envelhecida | 0.874 |
| demanda de atrito estático (60 mm) | almofada póstero-superior | 0.874 | μ_exig/μ_projeto ≤ 1 | 0.874 |
| arrancamento do inserto da junta do braço (50 mm) | sela, manuseio 10 N | 1.15 | FS ≥ 1 sobre o valor de projeto (γ = 2 incluído) | 0.869 |
| arrancamento do inserto da junta do braço (60 mm) | sela, manuseio 10 N | 1.15 | FS ≥ 1 sobre o valor de projeto (γ = 2 incluído) | 0.869 |
| arrancamento do inserto da âncora do cabo | clipe + plugue em série (superior) | 1.16 | FS ≥ 1 (γ = 2 incluído) | 0.864 |
| pressão na raiz da orelha, colocação A (55 mm) | zonas do arco | 3.44 | ≤ 4.00 kPa sustentado (logo após colocar; em uso veja as linhas de acomodação) | 0.860 |
| demanda de atrito estático (55 mm) | almofada póstero-superior | 0.848 | μ_exig/μ_projeto ≤ 1 | 0.848 |
| demanda de atrito estático (40 mm) | almofada póstero-superior | 0.846 | μ_exig/μ_projeto ≤ 1 | 0.846 |
| pressão na raiz da orelha, colocação A (50 mm) | zonas do arco | 3.27 | ≤ 4.00 kPa sustentado (logo após colocar; em uso veja as linhas de acomodação) | 0.817 |
| demanda de atrito estático (50 mm) | almofada póstero-superior | 0.799 | μ_exig/μ_projeto ≤ 1 | 0.799 |
| demanda de atrito estático (45 mm) | almofada póstero-superior | 0.785 | μ_exig/μ_projeto ≤ 1 | 0.785 |
| pressão estática na pele (50 mm) | almofada máx. | 3.11 | ≤ 4.00 kPa | 0.776 |
| pressão estática na pele (60 mm) | almofada máx. | 3.10 | ≤ 4.00 kPa | 0.775 |
| pressão na raiz da orelha, colocação A (45 mm) | zonas do arco | 3.07 | ≤ 4.00 kPa sustentado (logo após colocar; em uso veja as linhas de acomodação) | 0.768 |
| pressão estática na pele (55 mm) | almofada máx. | 3.06 | ≤ 4.00 kPa | 0.765 |
| pressão estática na pele (45 mm) | almofada máx. | 2.99 | ≤ 4.00 kPa | 0.746 |
| pressão na raiz da orelha, colocação A (40 mm) | zonas do arco | 2.96 | ≤ 4.00 kPa sustentado (logo após colocar; em uso veja as linhas de acomodação) | 0.740 |
| pressão estática na pele (40 mm) | almofada máx. | 2.67 | ≤ 4.00 kPa | 0.666 |
| seção do braço, 1 g sustentado | 60 mm, mastoide: barra na borda da fixação (fim do rasgo) (vM) | 4.12 | FS ≥ γM 1.60 | 0.388 |
| retenção, conjunto de 2 g (60 mm) | atrito nas almofadas + arco | 2.52 % das combinações soltas | 0 % (estrito) — não atendido | – |
| cadeia de tolerância com menor margem (60 mm) | compressão da junta do driver | MC inferior 0.0674 vs mín. 0.0500 | espessura da junta do driver | – |


## 20. Orientação de impressão (por peça) e por quê

| peça | material | orientação | motivo (anisotropia / suportes / precisão) |
|---|---|---|---|
| anel | PETG | face da cabeça para baixo | fundo da ranhura = superfície plana de topo, a parte de baixo do lábio é um cone de 45° (autossustentado); ranhuras da serrilha das abas na face da mesa; a tensão de contato das linguetas é compressão na camada; as abas terminam num arredondado completo em volta do inserto externo (parede ≥ 3.2 mm) |
| braços (4) | PETG | de lado (perfil na mesa) | toda a tensão de flexão corre ao longo do braço no plano da camada; só o cisalhamento transversal/de torção atravessa camadas (coluna entre camadas, §12); o perfil dos dentes da serrilha fica no plano de impressão (preciso) |
| defletor | PETG | face da cabeça para baixo | linguetas na mesa (face de apoio plana); o fundo do alojamento do driver é uma superfície de topo; chanfro da abertura de 45° |
| concha | PETG | fundo externo para baixo | grade/respiros e o furo do inserto do ressalto do olhal na mesa; o ressalto do olhal sobe dentro da concha como uma coluna simples; ressaltos dos parafusos em altura total; parede de 1.2 mm = 3 perímetros de linhas de 0.42 mm com camadas de 0.2 mm |
| feltro traseiro | feltro + borda de PSA | cortado em faca (não impresso) | empurrado sobre o ressalto do olhal, colado no lado de dentro do fundo da concha |
| âncora do cabo | PETG | de lado (face tangencial na mesa; o STL é exportado assim) | flexão do pino do clipe na camada (§14: menor FS 5.01 impresso de lado, 4.59 se impresso em pé) |
| almofadas (3) | TPU 95A giroide 15 % | base plana para baixo | a cúpula não precisa de suporte; alojamento da porca cativa na base |
| faces das almofadas (2) | silicone Shore 10–30A | moldadas (não impressas) | camada de 0.8 mm pincelada ou moldada nas cúpulas temporal e mastoide; STLs de referência do molde em stl/common/cast_reference |
| tampa da sela | TPU 95A | plana, face da pele para baixo | barra arqueada no plano da mesa (sem balanço); luva aberta em cima (sem ponte); furo do pino horizontal; face de apoio rebaixada para o revestimento |
| revestimento da sela | silicone Shore 00-30 | moldado na tampa (não impresso) | STL de referência do molde em stl/common/cast_reference; aplicar primer no TPU (o silicone não adere a ele sem primer) ou criar travamento mecânico; trocado junto com a tampa |
| junta do driver, clipe, almofada de vedação | TPU 95A | plano | anéis finos |
| tiras de espuma da UMI | espuma de PU, PSA | cortadas em faca | STL de gabarito |


## 21. Onde FEA, simulação acústica ou testes são necessários

Nenhuma FEA ou BEM foi rodada para este relatório; nada aqui é apresentado como simulado.
* **Raiz da aba do anel e raiz da lingueta** (concentração de tensão 3-D onde a aba se une ao anel; linguetas sob impacto de queda): a teoria de vigas dá valores nominais → FEA de sólidos com propriedades ortotrópicas de peça impressa, e um teste de queda (1.5 m sobre piso duro [A]).
* **Barra do braço na borda da fixação** (governa a carga de manuseio): uma placa entalhada sob flexão e torção combinadas; um modelo de EF com a geometria da serrilha e do rasgo substituiria o fator de furo Kt = 2.
* **Ressaltos dos insertos a quente**: a estimativa de tensão tangencial supõe um flanco de recartilhado de 30° → FEA ou, melhor, testes de arrancamento em corpos de prova impressos (§22). O inserto do olhal da ligação fica numa coluna que sobe do fundo da concha e é carregado lateralmente pela ligação: EF do ressalto ou um teste de puxão lateral.
* **Flexibilidade dos braços** (define quanto peso a raiz da orelha carrega, §6, §12): vigas de Timoshenko ao longo da linha média do braço; os cantos (pé–perna, perna–barra) são mais rígidos do que a teoria de vigas supõe, então o modelo erra para braços mais macios → EF de um braço, ou um teste de carga–deflexão de um braço impresso na sua almofada.
* **Tampa da sela na raiz da orelha** e as almofadas na pele: a pressão de contato em tecido mole curvo e em camadas não é hertziana → modelo de contato por EF ou medição com filme de pressão. O módulo de compressão do revestimento vem da fórmula de camada colada e do módulo da ficha técnica: um teste de carga–deflexão da tampa revestida sobre um simulador de pele o calibra (as linhas de módulo do gel do §18 mostram o que um fator de 2 faz).
* **Acústica acima de ~3 kHz** (pavilhão, modos da concha, grade, feltro como camada porosa): BEM/FEM ou medição num simulador de cabeça e tronco; o modelo concentrado não é afirmado ali.
* **Retenção sob movimento real da cabeça**: cinemática da cabeça gravada por IMU reproduzida numa cabeça artificial, ou testes de uso.
* **Migração do peso para a raiz da orelha em uso** (acomodação do §6): o atrito do modelo é elástico–Coulomb sem fluência da pele nem
  re-aderência; a pressão na raiz em uso que ele prevê é a primeira grandeza a medir (filme de pressão na raiz após uso com movimento da cabeça).

## 22. Limitações e as medições que substituem as suposições

| suposição | por que importa | medir |
|---|---|---|
| massa/geometria/T-S do driver | massa, CG, acústica | balança, paquímetro, varredura de impedância + Vas por massa adicionada |
| módulos e espessuras dos tecidos | rigidez de contato → divisão de carga | não é preciso exatamente: a varredura do §9 mostra a sensibilidade; testes de conforto |
| atrito μ (TPU e silicone na pele) | retenção | teste de plano inclinado de uma almofada na pele do antebraço (seca/suada) |
| módulo efetivo da almofada de TPU | rigidez de contato, pressão | carga–deflexão de uma almofada impressa |
| resistência/fluência do PETG | perda de pré-carga da junta | teste de retenção de torque numa aba impressa por 1 semana a 40 °C |
| rigidez e carga plana da arruela ondulada | pré-carga envelhecida da junta | ficha técnica da arruela; verificação de carga–deflexão |
| torque de aperto → pré-carga (fator de porca 0.20–0.35) | arrancamento do inserto na maior pré-carga, engate da serrilha na menor | teste de torque–tração do parafuso M3 num corpo de prova impresso com inserto |
| rigidez do braço impresso (E, G a 40 °C) | divisão de carga entre as almofadas e a raiz da orelha | carga–deflexão de um braço impresso na sua almofada |
| resistência ao descolamento do PSA em PETG impresso | colagem do feltro traseiro | descolamento a 90° da fita escolhida num corpo de prova impresso |
| arrancamento do inserto a quente | juntas dos braços e da âncora | arrancamento de insertos colocados em corpos de prova impressos |
| acelerações angulares da cabeça | retenção em 2 g/3 g | IMU de celular numa faixa de cabeça durante caminhada/corrida |
| atrito da pele sob carga cíclica (elástico–Coulomb, sem fluência nem re-aderência) | quão rápido e quão longe o peso migra para a raiz da orelha em uso (acomodação do §6) | filme de pressão na raiz da orelha após 30 min de uso caminhando, acenando com a cabeça e olhando para baixo |
| raio do arco da raiz da orelha | encaixe da sela | foto com escala; o R do arco é um parâmetro do CAD |
| módulo de compressão do revestimento da sela (módulo a 100 % da ficha técnica, confinamento de Gent–Lindley) | pressão na raiz da orelha vs atrito na mastoide | carga–deflexão da tampa revestida; filme de pressão na raiz em testes de uso |
| k_t/k_n = 0.5 para os contatos na pele | quanto peso as almofadas levam por atrito | varredura do §18; carga–deflexão ao cisalhamento de uma almofada no antebraço |
| CFD25 da espuma | sensação da trava de giro, folga | ficha técnica da espuma; comprimir uma tira com um peso conhecido |
| resposta acima de ~3 kHz: ressonância da minicavidade frontal (abertura), ressonância do driver na junta, modos da concha | equilíbrio de agudos | resposta em frequência num simulador de orelha / simulador de cabeça e tronco |
| modo livre do braço da sela (Rayleigh, sem contato com a pele) | possível zumbido na faixa de graves | varredura senoidal de 20–500 Hz em nível máximo numa cabeça artificial; acelerômetro ou escuta no braço da sela |


O modelo de contato é elástico-linear com rotações pequenas (válido até ~5°); quando um caso solta, ele é classificado, não acompanhado. A captura pelo pavilhão que segura o suporte depois do escorregamento não é modelada.

## 23. Arquivos

* `cad/umeh2.scad` + `cad/generated_params.scad` (padrão 50 mm) + `cad/params_<D>.scad` — CAD paramétrico e os parâmetros gerados.
* `stl/common/` — peças do suporte (iguais para todos os drivers); `stl/common/cast_reference/` — geometria das faces de silicone; `stl/module_<D>mm/` — peças do módulo por tamanho de driver (conchas com lado: posição do olhal).
* `calc/umeh2/*.py` — os modelos (materials, design, massprops, support, layout, linkspring, structure, cable, dynamics, acoustics, tolerance, extras, analysis).
* `calc/legs_liner.py`, `calc/tune_eye.py`, `calc/run_all.py`, `calc/shakedown.py`, `calc/sweeps.py`, `calc/figures.py`, `calc/build_stl.py`, `calc/bom.py`, `calc/make_report.py`.
* `results/*.json` — todos os números calculados; `report/fig/*.png`.
* `BOM.csv`, `docs/bom_table.md`.
