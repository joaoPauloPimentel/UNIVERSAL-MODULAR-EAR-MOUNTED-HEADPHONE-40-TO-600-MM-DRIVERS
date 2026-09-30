# UMEH-2: concluído (2026-09-30)

A cadeia completa rodou no projeto final (pré-carga da ligação 5.0 N; olhais por módulo em `calc/final_layout.json`;
pernas 5.5 mm, revestimento da sela 2.5 mm): run_all → shakedown → sweeps → figures → build_stl → bom → eye_record →
make_report. O relatório é `report/ENGINEERING_REPORT.md` (tradução em `report/RELATORIO_ENGENHARIA.md`); `README.md`
o resume; `BOM.csv` é a lista de materiais. Os arquivos STL (na orientação de impressão) estão em `stl/`, gerados por
`calc/build_stl.py`.

Nota: o arquivo de saída do próprio ajuste dos olhais se perdeu com a máquina que o rodou; `results/eye_tuning.json` é
um registro escrito por `calc/eye_record.py`, e a verificação densa de 1 g do run_all é a prova de aprovação (relatório §7, §8).
