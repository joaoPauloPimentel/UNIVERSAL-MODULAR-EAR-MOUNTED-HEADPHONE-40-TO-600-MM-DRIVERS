# UMEH-3: documentação

Fone circumaural de fundo fechado, uma concha impressa para drivers de 40 a 60 mm, preso por gancho atrás da orelha e
faixa na nuca. Modelo A, versão oval (almofada 110 × 90 mm, assento universal; 7/10/2026).

| Documento | Para quê |
|---|---|
| [01_impressao.md](01_impressao.md) | Arquivos STL, material e configuração de cada peça, logo em bronze |
| [02_lista_de_compras.md](02_lista_de_compras.md) | Peças compradas e onde achar no Brasil |
| [03_montagem.md](03_montagem.md) | Montagem passo a passo, com imagens |
| [04_testes.md](04_testes.md) | Testes com as peças reais (pesagem, bucha, queda, esteira, som) |
| [assento/molde_assento.pdf](assento/molde_assento.pdf) | Molde 1:1 dos discos de EVA do assento universal e das tiras de bronze |
| [07_embalagem.md](07_embalagem.md) | Caixa pronta, berço de EVA e adesivo do logo para enviar o fone |
| [../report/RELATORIO_UMEH3_modelo_A.md](../report/RELATORIO_UMEH3_modelo_A.md) | Relatório técnico: cálculos e resultados |

Modelo 3D interativo (oval): https://claude.ai/artifact/URyddQ9yXXfGch5ddgCAYa · versão redonda antiga: https://claude.ai/artifact/Sx1FKkQEhf4qXN1DecbGXC

Arquivos-fonte: `cad/umeh3.scad` com `cad/params3.scad` gerado por `calc/umeh3/geom.py` (`geom.apply("AO")`, a oval; `"AF"` é a redonda), imagens em `docs/img` (`cad/doc_views.scad`).
