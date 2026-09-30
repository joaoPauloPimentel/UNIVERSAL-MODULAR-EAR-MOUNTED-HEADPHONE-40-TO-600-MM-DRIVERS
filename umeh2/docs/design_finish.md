# UMEH-2 commercial finish / acabamento comercial

Interactive viewer: https://claude.ai/artifact/NYE6Sr5QZXdr25Mjt27k6M (private to the owner until shared).

**Scope.** Cosmetic only. No load-bearing part changed (ring, arms, pads, saddle, baffle, cup, link). The
calculations in `results/` were NOT re-run with the finish parts.

**Cup cap** (`cad/umeh2_styled.scad`, STL `stl/module_<D>mm/cup_cap_<D>_R|L.stl`, handed by the eye position):
0.6 mm PETG shell bonded with PSA on the cup outer end; rounded tri-lobe outline that hides the three cup-screw
bosses; 1.6 mm top-edge round-over; 5 mm skirt down the cup side; the cup grille repeated hole for hole (same open
pattern); clearance around the link eye and a 3.5 mm channel along the wire's path, so the link keeps the calculated
geometry (wire 1 mm above the cup end face, `support.EYE_Z_CUP`) and never touches the cap. Print top face down.

| module | cap g per side (+0.27 g front foam) | normal-use driver-mass margin g (report §10: max − nominal) |
|---|---|---|
| 40 mm | 2.03 | 12.7 |
| 45 mm | 2.14 | 15.4 |
| 50 mm | 2.28 | 5.8 |
| 55 mm | 2.40 | 8.2 |
| 60 mm | 2.55 | 5.2 |

The cap sits farther from the head than the driver, so the margin comparison is indicative only; re-run the chain
with the cap mass before relying on it. Mass from the exported mesh at 1.27 g/cm³.

**Front foam** (`front_foam` in `cad/umeh2_styled.scad`; die-cut template `stl/module_<D>mm/front_foam_<D>_template.stl`):
a 2.0 mm reticulated (open-cell) PU foam disc, 20–30 PPI [A], Ø = spigot − 1 mm (76 mm, all modules), on the module's
head face between the pinna and the driver, bonded by a PSA ring outside the aperture chamfer. It fills the module's
2 mm recess and ends flush with the ring's head face. Pinna clearance (report §17, chain 6) is measured to the module
head face: with the foam it drops by 2.0 mm, to 2.4 mm nominal and 0.35 mm at the Monte-Carlo −3σ end, so the p95 ear
does not reach it, but the low end is below the 1 mm hair/earring rule. Mass 0.27 g at 30 kg/m³ [A].
Acoustics: the lumped model (report §16) was not re-run with the foam; its flow resistance adds a small series
resistance at the aperture and should damp the front mini-cavity resonance (9–11 kHz); measure the response with and
without it (report §22).

**Colour, material, finish**

| surface | finish | colour |
|---|---|---|
| ring, baffle, cup (PETG) | matte graphite | #2C2F34 |
| arms (PETG) | satin gunmetal | #4A4F57 |
| cup cap (PETG, metallic fill) | brushed bronze | #A27449 |
| pads, saddle cap, cable clip/anchor (TPU 95A) | soft charcoal | #1D1F22 |
| pad facings, saddle liner (silicone) | slate | #6D737A |
| front foam (reticulated PU) | charcoal | #2A2D31 |

Português: a espuma frontal é um disco de PU reticulada de 2 mm entre a orelha e o driver; ocupa o rebaixo do módulo
e deixa 2,4 mm de folga nominal até a orelha p95. Acabamento só cosmético; a tampa da concha (0,6 mm de PETG, colada) esconde os parafusos, repete a grade furo
a furo e deixa um canal para o fio da ligação. Acrescenta 2,0–2,6 g por lado; os cálculos não foram refeitos com ela.
