# Packaging sheets for UMEH-3: EVA cradle (1:1, A4 landscape) and logo sticker sheet (A4), as SVG + PDF + PNG preview.
import sys, pathlib
OUT = pathlib.Path(sys.argv[1])
BOX = (260, 170)                       # inner box floor, mm
CUP_D = 108                            # hole height for the oval 110 x 90 pad (long side across the box), 1 mm squeeze per side
CUP_W = 88                             # hole width
GAP = 16
FONT = "DejaVu Sans, Arial, sans-serif"

def berco():
    W, H = 297, 210
    ox, oy = (W - BOX[0]) / 2, (H - BOX[1]) / 2 + 4
    cx = [ox + BOX[0] / 2 - (CUP_W + GAP) / 2, ox + BOX[0] / 2 + (CUP_W + GAP) / 2]
    cy = oy + BOX[1] / 2
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">',
         f'<rect width="{W}" height="{H}" fill="#fff"/>',
         f'<text x="{ox}" y="{oy-6}" font-family="{FONT}" font-size="4.2" font-weight="bold">UMEH-3 · berço de EVA 10 mm (corte 2 iguais) · imprimir em A4 deitado, escala 100%</text>',
         f'<rect x="{ox}" y="{oy}" width="{BOX[0]}" height="{BOX[1]}" fill="none" stroke="#000" stroke-width="0.4"/>']
    for i, x in enumerate(cx):
        s.append(f'<ellipse cx="{x}" cy="{cy}" rx="{CUP_W/2}" ry="{CUP_D/2}" fill="none" stroke="#000" stroke-width="0.4" stroke-dasharray="3 1.5"/>')
        s.append(f'<line x1="{x-3}" y1="{cy}" x2="{x+3}" y2="{cy}" stroke="#000" stroke-width="0.25"/><line x1="{x}" y1="{cy-3}" x2="{x}" y2="{cy+3}" stroke="#000" stroke-width="0.25"/>')
        s.append(f'<text x="{x}" y="{cy+12}" text-anchor="middle" font-family="{FONT}" font-size="3.5">furo oval {CUP_W} × {CUP_D} mm ({"R" if i else "L"})</text>')
        s.append(f'<text x="{x}" y="{cy+17}" text-anchor="middle" font-family="{FONT}" font-size="3">concha com a almofada para baixo</text>')
    # finger notches on the long edges so the cups lift out (at the ends of the ovals)
    for x in cx:
        y0 = cy - CUP_D / 2 + 0.6       # notch on the top of each hole, to get a finger under the cup
        s.append(f'<path d="M{x-12},{y0} a12,10 0 0 1 24,0" fill="none" stroke="#000" stroke-width="0.4" stroke-dasharray="3 1.5"/>')
    s.append(f'<text x="{ox+BOX[0]/2}" y="{oy+BOX[1]+7}" text-anchor="middle" font-family="{FONT}" font-size="3.4">contorno = fundo interno da caixa ({BOX[0]} × {BOX[1]} mm) · tracejado = cortar fora · confira: a régua abaixo deve medir 100 mm</text>')
    rx, ry = ox, oy + BOX[1] + 11
    s.append(f'<line x1="{rx}" y1="{ry}" x2="{rx+100}" y2="{ry}" stroke="#000" stroke-width="0.4"/>')
    for k in range(11):
        s.append(f'<line x1="{rx+10*k}" y1="{ry-1.5}" x2="{rx+10*k}" y2="{ry}" stroke="#000" stroke-width="0.3"/>')
    s.append('</svg>')
    return "\n".join(s), (W, H)

def adesivos():
    W, H, D = 210, 297, 50
    cols, rows = 3, 5
    mx, my = (W - cols * D - (cols - 1) * 12) / 2, (H - rows * D - (rows - 1) * 6) / 2
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">', f'<rect width="{W}" height="{H}" fill="#fff"/>']
    for r in range(rows):
        for c in range(cols):
            x, y = mx + c * (D + 12) + D / 2, my + r * (D + 6) + D / 2
            s.append(f'<circle cx="{x}" cy="{y}" r="{D/2}" fill="#141518"/>')
            s.append(f'<circle cx="{x}" cy="{y}" r="{D/2-2.6}" fill="none" stroke="#7a46c2" stroke-width="1.2"/>')
            s.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-family="{FONT}" font-weight="bold" font-size="10.5" letter-spacing="0.4" fill="#ffffff">UMEH</text>')
            s.append(f'<text x="{x}" y="{y+11}" text-anchor="middle" font-family="{FONT}" font-size="3.1" letter-spacing="0.5" fill="#b48cf0">FONE SEM TIARA</text>')
            s.append(f'<text x="{x}" y="{y-10}" text-anchor="middle" font-family="{FONT}" font-size="2.8" letter-spacing="0.5" fill="#b48cf0">FEITO NO BRASIL</text>')
            s.append(f'<circle cx="{x}" cy="{y}" r="{D/2+0.2}" fill="none" stroke="#bbb" stroke-width="0.15"/>')   # cut guide
    s.append('</svg>')
    return "\n".join(s), (W, H)

import json
jobs=[]
for name, (svg, (W, H)) in {"berco_eva": berco(), "adesivos_logo": adesivos()}.items():
    (OUT / f"{name}.svg").write_text(svg); jobs.append([name, W, H])
print(json.dumps(jobs))
