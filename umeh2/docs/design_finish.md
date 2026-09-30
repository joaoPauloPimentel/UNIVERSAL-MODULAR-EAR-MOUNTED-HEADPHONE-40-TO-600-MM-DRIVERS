# UMEH-2 commercial finish / acabamento comercial

Interactive viewer: https://claude.ai/artifact/NYE6Sr5QZXdr25Mjt27k6M (private to the owner until shared).

**Scope.** Cosmetic only. No load-bearing part changed (ring, arms, pads, saddle, baffle, cup, link). The
calculations in `results/` were NOT re-run with the finish parts.

**Cup cap** (`cad/umeh2_styled.scad`, STL `stl/module_<D>mm/cup_cap_<D>_R|L.stl`, handed by the eye position):
0.6 mm PETG shell bonded with PSA on the cup outer end; rounded tri-lobe outline that hides the three cup-screw
bosses; 1.6 mm top-edge round-over; 5 mm skirt down the cup side; the cup grille repeated hole for hole (same open
pattern); clearance around the link eye and a 3.5 mm channel along the wire's path, so the link keeps the calculated
geometry (wire 1 mm above the cup end face, `support.EYE_Z_CUP`) and never touches the cap. Print top face down.

| module | cap g per side | normal-use driver-mass margin g (report §10: max − nominal) |
|---|---|---|
| 40 mm | 2.03 | 12.7 |
| 45 mm | 2.14 | 15.4 |
| 50 mm | 2.28 | 5.8 |
| 55 mm | 2.40 | 8.2 |
| 60 mm | 2.55 | 5.2 |

The cap sits farther from the head than the driver, so the margin comparison is indicative only; re-run the chain
with the cap mass before relying on it. Mass from the exported mesh at 1.27 g/cm³.

**Colour, material, finish**

| surface | finish | colour |
|---|---|---|
| ring, baffle, cup (PETG) | matte graphite | #2C2F34 |
| arms (PETG) | satin gunmetal | #4A4F57 |
| cup cap (PETG, metallic fill) | brushed bronze | #A27449 |
| pads, saddle cap, cable clip/anchor (TPU 95A) | soft charcoal | #1D1F22 |
| pad facings, saddle liner (silicone) | slate | #6D737A |

Português: acabamento só cosmético; a tampa da concha (0,6 mm de PETG, colada) esconde os parafusos, repete a grade furo
a furo e deixa um canal para o fio da ligação. Acrescenta 2,0–2,6 g por lado; os cálculos não foram refeitos com ela.
