// Painel de piloto automático universal para simulador de voo (MobiFlight)
// 2 displays MAX7219 de 8 dígitos, 4 encoders KY-040, 10 botões PBS-102 com LED 3 mm, Arduino Mega 2560.
// Peças: part = "painel" | "letras" | "caixa" | "montagem" | "frente_2d"
part = "none";

// ---- painel ----
PW = 210;  PH = 110;  PT = 3;   // largura, altura (ao longo da inclinação), espessura
TXT_H = 0.6;                    // letras em alto-relevo (troca de filamento em PT)
R  = 5;
FONT = "DejaVu Sans:style=Bold";
SCREW_IN = 6.5;                 // furos M3 a 6,5 mm das bordas

// ---- caixa ----
ANG = 15;                       // inclinação do painel
HF  = 35;                       // altura na frente
W   = 2.4;                      // parede e fundo
D   = PH*cos(ANG);              // 106,3 mm de profundidade
HB  = HF + PH*sin(ANG);         // 63,5 mm atrás

// ---- componentes (medidas típicas: confira as suas peças antes de imprimir) ----
DISP_WIN = [61, 14];            // janela dos dígitos (2 displays 0,36" de 4 dígitos)
DISP_PCB = [82, 15];
DIG = 7.55;                     // passo entre dígitos
ENC_D = 7.4;                    // bucha M7 do encoder
BTN_D = 7.2;                    // botão PBS-102 (rosca de 7 mm)
LED_D = 3.1;                    // LED 3 mm
MEGA = [101.6, 53.3];
MEGA_HOLES = [[14.0,2.5],[15.3,50.7],[66.1,7.6],[66.1,35.5],[90.2,50.7],[96.5,2.5]];
MEGA_POS = [12, 49.5];           // canto da placa dentro da caixa (USB na parede esquerda)
STAND_H = 5;

$fn = 40;

// posições no painel (u = da esquerda, t = da borda de trás/alta para baixo)
function P(u, t) = [u, PH - t];
DISP_C = [PW/2 - 46, PW/2 + 46];          // centros dos displays
T_DLAB = 13.5;  T_DISP = 26;  T_ENC = 52;  T_BLAB = 69;  T_LED = 76;  T_BTN = 86;
function dig_x(d, k) = DISP_C[d] - DISP_WIN[0]/2 + (k + 0.5)*DIG;   // dígito k (0 = esquerda)
// grupos dos displays: [display, primeiro dígito, nº de dígitos, nome]
GROUPS = [[0,0,3,"SPD"], [0,5,3,"HDG"], [1,0,5,"ALT"], [1,5,3,"V/S"]];
function grp_x(g) = (dig_x(g[0], g[1]) + dig_x(g[0], g[1] + g[2] - 1))/2;
BTNS = ["AP","FD","HDG","NAV","APR","REV","ALT","VS","FLC","YD"];
BTN_PITCH = 19;
function btn_x(i) = PW/2 + (i - 4.5)*BTN_PITCH;
SCREWS = [[SCREW_IN,SCREW_IN],[PW-SCREW_IN,SCREW_IN],[SCREW_IN,PH-SCREW_IN],[PW-SCREW_IN,PH-SCREW_IN]];

module rrect(w, h, r) { translate([r, r]) offset(r = r) square([w - 2*r, h - 2*r]); }
module lbl(s, u, t, h = 4) translate(P(u, t)) text(s, size = h/0.73, font = FONT, halign = "center", valign = "center");

module furos2d() {
  for (d = [0, 1]) translate(P(DISP_C[d], T_DISP)) square(DISP_WIN, center = true);
  for (g = GROUPS) translate(P(grp_x(g), T_ENC)) circle(d = ENC_D);
  for (i = [0:9]) { translate(P(btn_x(i), T_BTN)) circle(d = BTN_D);
                    translate(P(btn_x(i), T_LED)) circle(d = LED_D); }
  for (s = SCREWS) translate(s) circle(d = 3.4);
}

module letras2d() {
  for (g = GROUPS) lbl(g[3], grp_x(g), T_DLAB);
  for (i = [0:9]) lbl(BTNS[i], btn_x(i), T_BLAB, 3.6);
  // marcas sob os encoders (anel fino)
  for (g = GROUPS) translate(P(grp_x(g), T_ENC)) difference() { circle(d = 19); circle(d = 18); }
  lbl("AUTOPILOT", PW/2, PH - 4.5, 2.6);
  // fios finos ligando os rótulos aos dígitos
  for (g = GROUPS) translate(P(grp_x(g), T_DISP - DISP_WIN[1]/2 - 2.2))
    square([(g[2] - 0.3)*DIG, 0.6], center = true);
}

module painel() {   // preto, face para cima; escareado por cima para parafuso M3 cabeça chata
  difference() {
    linear_extrude(PT) difference() { rrect(PW, PH, R); furos2d(); }
    for (s = SCREWS) translate([s[0], s[1], PT - 1.7]) cylinder(d1 = 3.4, d2 = 6.6, h = 1.71);
  }
}
module letras() { translate([0, 0, PT]) linear_extrude(TXT_H) letras2d(); }   // branco/bronze a partir de PT

// sistema do painel: origem na borda da frente (baixa), y subindo a rampa
module no_painel() translate([0, 0, HF]) rotate([ANG, 0, 0]) children();

module prisma(off = 0) {   // perfil lateral em cunha extrudado ao longo de x
  translate([off, 0, 0]) rotate([90, 0, 90]) linear_extrude(PW - 2*off)
    polygon([[0,0],[D,0],[D,HB],[0,HF]]);
}

module caixa() {
  usb_y = MEGA_POS[1] + 38.1;  usb_z = W + STAND_H + 1.6 + 5.5;
  difference() {
    union() {
      difference() {
        prisma();
        translate([W, W, W]) cube([PW - 2*W, D - 2*W, 200]);
      }
      // colunas dos parafusos do painel (perpendiculares ao painel)
      intersection() {
        prisma();
        no_painel() for (s = SCREWS) translate([s[0], s[1], -80]) cylinder(d = 9, h = 80);
      }
      // apoios do Mega
      for (h = MEGA_HOLES) translate([MEGA_POS[0] + h[0], MEGA_POS[1] + h[1], 0]) cylinder(d = 6.5, h = W + STAND_H);
    }
    no_painel() for (s = SCREWS) translate([s[0], s[1], -14]) cylinder(d = 2.6, h = 15);   // M3 auto-atarraxante
    for (h = MEGA_HOLES) translate([MEGA_POS[0] + h[0], MEGA_POS[1] + h[1], W]) cylinder(d = 2.5, h = STAND_H + 1);
    // USB-B do Mega na parede esquerda
    translate([-1, usb_y - 6.5, usb_z - 6]) cube([W + 2, 13, 12]);
    // 4 rebaixos para pés de borracha adesivos (10 mm)
    for (x = [18, PW - 18]) for (y = [14, D - 14]) translate([x, y, -0.01]) cylinder(d = 10.5, h = 0.6);
    // nome no fundo
    translate([PW/2, D/2, -0.01]) mirror([1,0,0]) linear_extrude(0.5)
      text("UMEH · AP-1", size = 6, font = FONT, halign = "center", valign = "center");
  }
}

// ---- peças só para visualização ----
module mega_vis() { translate([MEGA_POS[0], MEGA_POS[1], W + STAND_H]) { color("#1b5fa8") cube([MEGA[0], MEGA[1], 1.6]);
  color("silver") translate([-6.2, 31.8, 1.6]) cube([16, 12, 11]); } }
module componentes_vis() {
  no_painel() {
    for (d = [0, 1]) translate([DISP_C[d], PH - T_DISP, 0]) {
      color("#2a2a2a") translate([-DISP_WIN[0]/2, -DISP_WIN[1]/2, -8]) cube([DISP_WIN[0], DISP_WIN[1], 8 + PT - 0.4]);
      color("#c0392b") translate([-DISP_PCB[0]/2, -DISP_PCB[1]/2, -9.6]) cube([DISP_PCB[0], DISP_PCB[1], 1.6]);
    }
    for (g = GROUPS) translate([grp_x(g), PH - T_ENC, PT]) color("#3a3a3a") cylinder(d = 15, h = 14, $fn = 24);
    for (i = [0:9]) translate([btn_x(i), PH - T_BTN, PT]) color("#1c1c1c") cylinder(d = 9, h = 6, $fn = 20);
    for (i = [0:9]) translate([btn_x(i), PH - T_LED, PT - 1]) color(i == 0 ? "#ffb000" : "#4a3a10") cylinder(d = 3, h = 2.5, $fn = 16);
  }
  mega_vis();
}

module montagem(expl = 0) {
  color("#2b2d31") caixa();
  translate([0, 0, expl]) no_painel() { color("#111111") painel(); color("#e9e4d8") letras(); }
  if (expl == 0) componentes_vis();
}

if (part == "painel") painel();
if (part == "letras") letras();
if (part == "caixa") caixa();
if (part == "montagem") montagem();
if (part == "explodida") montagem(60);
if (part == "frente_2d") { letras2d(); furos2d(); }
// para o visualizador
if (part == "vis_painel") no_painel() painel();
if (part == "vis_letras") no_painel() letras();
if (part == "vis_comp") componentes_vis();
if (part == "vis_disp") no_painel() for (d = [0, 1]) translate([DISP_C[d], PH - T_DISP, 0])
  translate([-DISP_WIN[0]/2, -DISP_WIN[1]/2, -8]) cube([DISP_WIN[0], DISP_WIN[1], 8 + PT - 0.4]);
if (part == "vis_knobs") no_painel() for (g = GROUPS) translate([grp_x(g), PH - T_ENC, PT]) cylinder(d = 15, h = 14, $fn = 32);
if (part == "vis_btns") no_painel() for (i = [0:9]) translate([btn_x(i), PH - T_BTN, PT]) cylinder(d = 9, h = 6, $fn = 24);
if (part == "vis_leds") no_painel() for (i = [0:9]) translate([btn_x(i), PH - T_LED, PT - 1]) cylinder(d = 3, h = 2.5, $fn = 16);
if (part == "vis_mega") mega_vis();
