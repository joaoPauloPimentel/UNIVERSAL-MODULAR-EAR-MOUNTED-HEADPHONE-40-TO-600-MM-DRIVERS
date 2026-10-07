# UMEH-3 oval: 1:1 cutting template for the universal driver seat (EVA layers F, M, S) + bronze strip guide, A4.
# Sizes from cad/params3.scad (DRV, POCKET_R, UNIV); run: python3 gen.py . && node ../embalagem/render.js . '<jobs>'
import sys, re, json, pathlib, math
OUT = pathlib.Path(sys.argv[1])
P = (pathlib.Path(__file__).resolve().parents[2] / "cad" / "params3.scad").read_text()
POCKET_R = float(re.search(r"POCKET_R = ([\d.]+)", P).group(1))
UNIV = [float(x) for x in re.search(r"UNIV = \[([^\]]+)\]", P).group(1).split(",")]
DRV = [[float(x) for x in r.split(",")] for r in re.findall(r"\[(\d+, [\d., ]+)\]", P.split("DRV = [")[1].split("];")[0])]
FONT = "DejaVu Sans, Arial, sans-serif"
RO = POCKET_R - 0.15
LAYERS = [("F", f"frente · EVA {UNIV[0]:g} mm", lambda d: d[5] / 2),          # aperture
          ("M", f"meio · EVA {UNIV[1]:g} mm", lambda d: d[1] / 2 - 0.15),     # rim OD (grips the rim)
          ("S", f"trás · EVA {UNIV[2]:g} mm", lambda d: d[3] / 2 + 0.6)]   # basket

def disc(cx, cy, key, name, hole):
    s = [f'<circle cx="{cx}" cy="{cy}" r="{RO}" fill="none" stroke="#000" stroke-width="0.35"/>',
         f'<line x1="{cx-2}" y1="{cy}" x2="{cx+2}" y2="{cy}" stroke="#000" stroke-width="0.2"/>',
         f'<line x1="{cx}" y1="{cy-2}" x2="{cx}" y2="{cy+2}" stroke="#000" stroke-width="0.2"/>']
    for k, d in enumerate(DRV):
        r = hole(d)
        if r >= RO - 0.5:
            continue                                   # no ring left at this size: layer not used
        col = ["#c0392b", "#d35400", "#27ae60", "#2471a3", "#7d3c98"][k]
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.2f}" fill="none" stroke="{col}" stroke-width="0.3" stroke-dasharray="1.6 0.8"/>')
        a = math.radians(-60 - 22 * k)
        s.append(f'<text x="{cx + (r - 1.6) * math.cos(a):.2f}" y="{cy + (r - 1.6) * math.sin(a) + 0.9:.2f}" text-anchor="middle" '
                 f'font-family="{FONT}" font-size="2.3" fill="{col}">{int(d[0])}</text>')
    if key == "S":   # where the two strips lie: straight, parallel, from the hole out to the edge
        w, g = UNIV[5], UNIV[6]
        for sgn in (-1, 1):
            y0 = cy + sgn * (g + w) / 2 - w / 2
            s.append(f'<rect x="{cx + hole(DRV[0]):.2f}" y="{y0:.2f}" width="{RO - hole(DRV[0]):.2f}" height="{w}" fill="#d4a017" fill-opacity="0.35" stroke="#8a6d0b" stroke-width="0.2"/>')
        s.append(f'<text x="{cx + RO + 1.5}" y="{cy + 1}" font-family="{FONT}" font-size="2.4">lâminas</text>')
    s.append(f'<text x="{cx}" y="{cy + RO + 5}" text-anchor="middle" font-family="{FONT}" font-size="3.4" font-weight="bold">{key} · {name}</text>')
    return s

W, H = 210, 297
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">', f'<rect width="{W}" height="{H}" fill="#fff"/>',
     f'<text x="14" y="16" font-family="{FONT}" font-size="4.6" font-weight="bold">UMEH-3 oval · molde do assento universal do driver (1:1)</text>',
     f'<text x="14" y="22" font-family="{FONT}" font-size="3">Imprima em escala 100% (a régua deve medir 100 mm). Corte o contorno preto e, por dentro,</text>',
     f'<text x="14" y="26.5" font-family="{FONT}" font-size="3">só o círculo do tamanho do seu driver. Uma coluna para cada lado (L e R). Se não houver</text>',
     f'<text x="14" y="31" font-family="{FONT}" font-size="3">círculo do seu tamanho, essa camada não vai (M no driver de 60 mm).</text>']
for row, (key, name, hole) in enumerate(LAYERS):
    for col, side in enumerate("LR"):
        cx, cy = 58 + col * 95, 75 + row * 72
        s += disc(cx, cy, key, name, hole)
        s.append(f'<text x="{cx - RO}" y="{cy - RO + 2}" font-family="{FONT}" font-size="3.4" font-weight="bold">{side}</text>')
# strip cutting guide + ruler
y = 270
s.append(f'<text x="14" y="{y - 4}" font-family="{FONT}" font-size="3">Lâmina de bronze fosforoso 0,2 mm: corte 4 tiras (2 por lado) deste tamanho, {UNIV[5]:g} × 30 mm:</text>')
for k in range(4):
    s.append(f'<rect x="{14 + k * 36}" y="{y}" width="30" height="{UNIV[5]}" fill="#d4a017" fill-opacity="0.35" stroke="#8a6d0b" stroke-width="0.25"/>')
s.append(f'<line x1="14" y1="{y + 12}" x2="114" y2="{y + 12}" stroke="#000" stroke-width="0.4"/>')
for k in range(11):
    s.append(f'<line x1="{14 + 10 * k}" y1="{y + 10.5}" x2="{14 + 10 * k}" y2="{y + 12}" stroke="#000" stroke-width="0.3"/>')
s.append(f'<text x="118" y="{y + 12.5}" font-family="{FONT}" font-size="3">100 mm</text>')
leg = " · ".join(f'<tspan fill="{c}">{int(d[0])} mm</tspan>' for d, c in zip(DRV, ["#c0392b", "#d35400", "#27ae60", "#2471a3", "#7d3c98"]))
s.append(f'<text x="14" y="{y + 20}" font-family="{FONT}" font-size="3">Cores dos círculos: {leg}</text>')
s.append('</svg>')
(OUT / "molde_assento.svg").write_text("\n".join(s))
print(json.dumps([["molde_assento", W, H]]))
