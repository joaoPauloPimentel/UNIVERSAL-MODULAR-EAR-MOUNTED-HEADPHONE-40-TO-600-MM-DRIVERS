# Lista de materiais do UMEH-2 (um par)

> Tradução para o português de `docs/bom_table.md` (gerado por `calc/bom.py`, que escreve a versão em inglês). Os números são os mesmos.

Gerado por `calc/bom.py` a partir dos valores de projeto e das massas do CAD. Marcas: CAD massa da malha, C calculado, DS ficha técnica/típico, A suposição. Sem preços (locais).

| item | qtd_por_par | material | impresso | origem | massa_cada_g | especificação | marca |
|---|---|---|---|---|---|---|---|
| Anel do suporte (D e E) | 2 | PETG | sim | stl/common/ring_R.stl, ring_L.stl | 33.85 | anel Ø ext. 88.7 mm, ranhura da trava de giro UMI-2, 5 abas (raio das abas 63.20 mm); face da cabeça para baixo; 5 perímetros, giroide 30 % | CAD |
| Braço da sela (arco da raiz da orelha) | 2 | PETG | sim | stl/common/arm_saddle.stl | 8.47 | barra 5.5 / perna 5.5 / pé 4.5 mm, fixação serrilhada p 1.2 mm; impresso de lado; 5 perímetros, preenchimento 40 % | CAD |
| Braço temporal | 2 | PETG | sim | stl/common/arm_temporal.stl | 3.16 | barra 5.5 / perna 5.5 / pé 4.5 mm, fixação serrilhada p 1.2 mm; impresso de lado; 5 perímetros, preenchimento 40 % | CAD |
| Braço mastoide | 2 | PETG | sim | stl/common/arm_mastoid.stl | 3.36 | barra 5.5 / perna 5.5 / pé 6.0 mm, fixação serrilhada p 1.2 mm; impresso de lado; 5 perímetros, preenchimento 40 % | CAD |
| Braço póstero-superior | 2 | PETG | sim | stl/common/arm_post.stl | 3.08 | barra 5.5 / perna 5.5 / pé 4.5 mm, fixação serrilhada p 1.2 mm; impresso de lado; 5 perímetros, preenchimento 40 % | CAD |
| Tampa da sela | 2 | TPU 95A | sim | stl/common/saddle_cap.stl | 6.83 | tampa arqueada sobre a raiz da orelha; plana, face da pele para baixo; a face de apoio é rebaixada 2.5 mm para o revestimento moldado | CAD |
| Revestimento da sela (silicone macio, moldado na face de apoio da tampa) | 2 | silicone platina seguro para a pele Shore 00-30 (módulo a 100 % ~69 kPa) | não (moldado) | stl/common/cast_reference/saddle_liner.stl (referência do molde) | 0.92 | 2.5 mm, amacia o contato na raiz da orelha (pressão na raiz <= 4 kPa a 55-60 mm, relatório §6); aplicar primer no TPU ou travar mecanicamente; trocar junto com a tampa | C |
| Almofada, temporal | 2 | TPU 95A, 15 % gyroid | sim | stl/common/pad_temporal.stl | 2.40 | cúpula 33.8 x 39.0 mm, h 6.0 mm, porca M2.5 cativa | CAD |
| Almofada, mastoide | 2 | TPU 95A, 15 % gyroid | sim | stl/common/pad_mastoid.stl | 3.49 | cúpula 39.0 x 49.4 mm, h 6.0 mm, porca M2.5 cativa | CAD |
| Almofada, póstero-sup. | 2 | TPU 95A, 15 % gyroid | sim | stl/common/pad_post.stl | 2.75 | cúpula 33.8 x 39.0 mm, h 6.0 mm, porca M2.5 cativa | CAD |
| Âncora do cabo | 2 | PETG | sim | stl/common/cable_anchor.stl | 3.92 | segura o soquete de 2 pinos; pino do clipe; impresso DE LADO (flexão do pino na camada) | CAD |
| Clipe do cabo | 2 | TPU 95A | sim | stl/common/cable_clip.stl | 0.93 | guia de passagem para um cabo de 3.8 mm (interferência 0.05 mm) | CAD |
| Tiras de espuma anti-ruído da UMI (3 por lado) | 6 | espuma de PU, com PSA | não (corte em faca) | stl/common/gasket_umi.stl (gabarito de corte) | 0.03 | folha de 1.6 mm, CFD25 46 kPa (janela 43-50 kPa), no topo das linguetas | C |
| Face de silicone das almofadas, temporal + mastoide | 4 | silicone de cura por platina Shore 10-30A | não (moldado) | stl/common/cast_reference/pad_face_*.stl (referência do molde) | 0.95 | 0.8 mm layer on the cúpula (static friction demand, report §9) | C |
| Almofada de vedação (opção C de frente vedada, fora da montagem padrão) | 0 | TPU 95A, 15 % gyroid | opcional | stl/common/seal_pad.stl |  | anel 62.0/92.0 mm; veja o relatório §16 (precisa de ~1 kPa em espuma de <= 30 kg/m3 para vedar) | C |
| Defletor 40 mm | 2 | PETG | sim | stl/module_40mm/baffle_40.stl | 17.67 | abertura 35.2 mm, linguetas UMI-2; face da cabeça para baixo | CAD |
| Concha 40 mm (D e E: posição do olhal) | 2 | PETG | sim | stl/module_40mm/cup_40_R.stl, cup_40_L.stl | 16.54 | parede 1.2 mm, altura 18.2 mm, olhal da ligação em (-15.0, 7.0) mm | CAD |
| Junta do aro do driver 40 mm | 2 | TPU 95A | sim | stl/module_40mm/gasket_driver_40.stl | 0.36 | 1.0 mm, compressão 0.3 mm | CAD |
| Disco de feltro 40 mm | 2 | feltro de lã/poliéster | não | cortado em faca | 0.38 | Ø35.2 x 2.0 mm, furo Ø7.5 no olhal da ligação (empurrado sobre o ressalto), resistividade ao fluxo ~40 kPa s/m2 [A] | C |
| Borda de PSA do feltro 40 mm | 2 | fita de transferência PSA acrílica | não | anel cortado em faca |  | OD 35.2 / ID 31.2 mm; descolamento a 90° em PETG >= 3 N/cm [A], massa < 0.02 g | A |
| Parafusos da concha 40 mm | 6 | inox A2 | não | ISO 10642 escareado | 0.55 | M2.5x25 cortado em 22.5 mm (engajamento 4.3 mm no inserto do defletor) | C |
| Driver 40 mm | 2 | - | não | fornecido pelo usuário | 15.00 | aro Ø ext. 40.5 mm, profundidade 10.0 mm (valores provisórios [A]: medir e rodar de novo) | A |
| Defletor 45 mm | 2 | PETG | sim | stl/module_45mm/baffle_45.stl | 16.24 | abertura 39.6 mm, linguetas UMI-2; face da cabeça para baixo | CAD |
| Concha 45 mm (D e E: posição do olhal) | 2 | PETG | sim | stl/module_45mm/cup_45_R.stl, cup_45_L.stl | 19.79 | parede 1.2 mm, altura 19.2 mm, olhal da ligação em (-18.0, 7.0) mm | CAD |
| Junta do aro do driver 45 mm | 2 | TPU 95A | sim | stl/module_45mm/gasket_driver_45.stl | 0.45 | 1.0 mm, compressão 0.3 mm | CAD |
| Disco de feltro 45 mm | 2 | feltro de lã/poliéster | não | cortado em faca | 0.48 | Ø39.4 x 2.0 mm, furo Ø7.5 no olhal da ligação (empurrado sobre o ressalto), resistividade ao fluxo ~40 kPa s/m2 [A] | C |
| Borda de PSA do feltro 45 mm | 2 | fita de transferência PSA acrílica | não | anel cortado em faca |  | OD 39.4 / ID 35.4 mm; descolamento a 90° em PETG >= 3 N/cm [A], massa < 0.02 g | A |
| Parafusos da concha 45 mm | 6 | inox A2 | não | ISO 10642 escareado | 0.55 | M2.5x25 cortado em 23.5 mm (engajamento 4.3 mm no inserto do defletor) | C |
| Driver 45 mm | 2 | - | não | fornecido pelo usuário | 19.00 | aro Ø ext. 45.5 mm, profundidade 11.0 mm (valores provisórios [A]: medir e rodar de novo) | A |
| Defletor 50 mm | 2 | PETG | sim | stl/module_50mm/baffle_50.stl | 15.29 | abertura 44.0 mm, linguetas UMI-2; face da cabeça para baixo | CAD |
| Concha 50 mm (D e E: posição do olhal) | 2 | PETG | sim | stl/module_50mm/cup_50_R.stl, cup_50_L.stl | 23.54 | parede 1.2 mm, altura 20.0 mm, olhal da ligação em (-19.0, 7.0) mm | CAD |
| Junta do aro do driver 50 mm | 2 | TPU 95A | sim | stl/module_50mm/gasket_driver_50.stl | 0.56 | 1.0 mm, compressão 0.3 mm | CAD |
| Disco de feltro 50 mm | 2 | feltro de lã/poliéster | não | cortado em faca | 0.58 | Ø43.6 x 2.0 mm, furo Ø7.5 no olhal da ligação (empurrado sobre o ressalto), resistividade ao fluxo ~40 kPa s/m2 [A] | C |
| Borda de PSA do feltro 50 mm | 2 | fita de transferência PSA acrílica | não | anel cortado em faca |  | OD 43.6 / ID 39.6 mm; descolamento a 90° em PETG >= 3 N/cm [A], massa < 0.02 g | A |
| Parafusos da concha 50 mm | 6 | inox A2 | não | ISO 10642 escareado | 0.55 | M2.5x25 cortado em 24.5 mm (engajamento 4.5 mm no inserto do defletor) | C |
| Driver 50 mm | 2 | - | não | fornecido pelo usuário | 26.00 | aro Ø ext. 50.5 mm, profundidade 12.0 mm (valores provisórios [A]: medir e rodar de novo) | A |
| Defletor 55 mm | 2 | PETG | sim | stl/module_55mm/baffle_55.stl | 13.42 | abertura 48.4 mm, linguetas UMI-2; face da cabeça para baixo | CAD |
| Concha 55 mm (D e E: posição do olhal) | 2 | PETG | sim | stl/module_55mm/cup_55_R.stl, cup_55_L.stl | 26.74 | parede 1.2 mm, altura 21.0 mm, olhal da ligação em (-18.0, 7.0) mm | CAD |
| Junta do aro do driver 55 mm | 2 | TPU 95A | sim | stl/module_55mm/gasket_driver_55.stl | 0.67 | 1.0 mm, compressão 0.3 mm | CAD |
| Disco de feltro 55 mm | 2 | feltro de lã/poliéster | não | cortado em faca | 0.72 | Ø48.5 x 2.0 mm, furo Ø7.5 no olhal da ligação (empurrado sobre o ressalto), resistividade ao fluxo ~40 kPa s/m2 [A] | C |
| Borda de PSA do feltro 55 mm | 2 | fita de transferência PSA acrílica | não | anel cortado em faca |  | OD 48.5 / ID 44.5 mm; descolamento a 90° em PETG >= 3 N/cm [A], massa < 0.02 g | A |
| Parafusos da concha 55 mm | 6 | inox A2 | não | ISO 10642 escareado | 0.55 | M2.5x25 (engajamento 4.0 mm no inserto do defletor) | C |
| Driver 55 mm | 2 | - | não | fornecido pelo usuário | 33.00 | aro Ø ext. 55.5 mm, profundidade 13.0 mm (valores provisórios [A]: medir e rodar de novo) | A |
| Defletor 60 mm | 2 | PETG | sim | stl/module_60mm/baffle_60.stl | 11.38 | abertura 52.8 mm, linguetas UMI-2; face da cabeça para baixo | CAD |
| Concha 60 mm (D e E: posição do olhal) | 2 | PETG | sim | stl/module_60mm/cup_60_R.stl, cup_60_L.stl | 29.95 | parede 1.2 mm, altura 22.0 mm, olhal da ligação em (-18.0, 7.0) mm | CAD |
| Junta do aro do driver 60 mm | 2 | TPU 95A | sim | stl/module_60mm/gasket_driver_60.stl | 0.80 | 1.0 mm, compressão 0.3 mm | CAD |
| Disco de feltro 60 mm | 2 | feltro de lã/poliéster | não | cortado em faca | 0.88 | Ø53.5 x 2.0 mm, furo Ø7.5 no olhal da ligação (empurrado sobre o ressalto), resistividade ao fluxo ~40 kPa s/m2 [A] | C |
| Borda de PSA do feltro 60 mm | 2 | fita de transferência PSA acrílica | não | anel cortado em faca |  | OD 53.5 / ID 49.5 mm; descolamento a 90° em PETG >= 3 N/cm [A], massa < 0.02 g | A |
| Parafusos da concha 60 mm | 6 | inox A2 | não | ISO 10642 escareado | 0.55 | M2.5x25 (engajamento 3.0 mm no inserto do defletor) | C |
| Driver 60 mm | 2 | - | não | fornecido pelo usuário | 40.00 | aro Ø ext. 60.5 mm, profundidade 14.0 mm (valores provisórios [A]: medir e rodar de novo) | A |
| Parafusos dos braços | 16 | inox A2 | não | ISO 7380 / ISO 4762 | 0.95 | M3x10 (engajamento 4.2 mm), torque 0.1 N m (chave de torque); insertos a 11.0 mm um do outro | C |
| Arruelas onduladas dos braços | 16 | aço mola | não | arruela ondulada | 0.03 | M3: ID 3.2, OD <= 6.0 mm, >= 100 N carga plana, rigidez <= 200 N/mm | C |
| Insertos a quente, abas dos braços | 16 | latão | não | recartilhado a quente | 0.33 | M3, OD 4.6 x 5.0 mm | DS |
| Parafusos da âncora do cabo | 4 | inox A2 | não | ISO 4762 | 0.95 | M3x8 (engajamento 3.7 mm), torque 0.1 N m, com uma arruela ondulada (próxima linha) | C |
| Arruelas onduladas da âncora | 4 | aço mola | não | arruela ondulada | 0.04 | M3: ID 3.2, OD <= 6.0 mm, >= 100 N carga plana, rigidez <= 200 N/mm (mesmo requisito das juntas dos braços) | C |
| Insertos a quente, aba do cabo | 4 | latão | não | recartilhado a quente | 0.33 | M3, OD 4.6 x 5.0 mm | DS |
| Parafuso + porca do clipe | 2 | inox A2 | não | ISO 4762 + ISO 4032 | 1.23 | M3x16 | DS |
| Insertos a quente, defletor (parafusos da concha; por par de módulos) | 6 | latão | não | recartilhado a quente | 0.20 | M2.5, OD 4.0 x 4.0 mm | DS |
| Parafusos + porcas das almofadas | 6 | inox A2 | não | ISO 7380 + ISO 4032 | 0.72 | M2.5x10 (almofada ao pé do braço) | DS |
| Pino da tampa da sela | 2 | inox A2 | não | M2x12 + nut | 0.45 | pino da articulação da tampa da sela | DS |
| Parafuso + inserto + arruela do olhal da ligação | 2 | A2 / latão | não | M2.5x8 ISO 7380 + heat-set M2.5 | 0.85 | prende a bucha do olhal ao ressalto da concha | DS |
| Bucha do olhal da ligação | 2 | tubo de latão | não | cortado | 1.31 | OD 7.5 x ID 2.7 x 4 mm (mantém o raio interno do olhal >= 1.5 d) | C |
| Fio da ligação occipital | 1 | corda de piano ASTM A228 | não | conformado | 22.87 | Ø2.5 mm, 4 espiras no ápice (Ø médio de linkspring.DC_COIL), comprimento 443 mm + espiras, meia abertura livre 100.6 mm | C |
| Capa da ligação | 1 | tubo de silicone | não | tubo | 12.39 | ID 2.5 mm (= wire), parede de 2 mm, 398 mm (90 % do arco; as dobras do olhal e a espira do ápice ficam nuas): contato com pele e cabelo | A |
| Soquete de 2 pinos 0.78 mm + rabicho JST | 2 | - | não | catálogo | 2.00 | na âncora do cabo | A |
