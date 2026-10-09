// Relógio de palavras em português (jeito digital: "SÃO DUAS E QUARENTA E CINCO")
// 12 x 10 letras, uma LED WS2812B (fita 60 LED/m) atrás de cada letra.
// Peças: part = "frente" | "grade" | "placa_leds" | "caixa" | "montagem"
part = "none";

// ---- grade de letras (mesma ordem do firmware) ----
ROWS = [
  "ÉRSÃOUMADUAS",
  "TRÊSKQUATROB",
  "CINCOTSEISPV",
  "SETEOITONOVE",
  "DEZONZEJDOZE",
  "HORASEQUINZE",
  "VINTETRINTAX",
  "DEZQUARENTAZ",
  "CINQUENTAEXY",
  "CINCOMHL····"     // os 4 pontos = minutos 1 a 4
];
NC = 12; NR = 10;
P   = 1000/60;        // passo da fita 60 LED/m = 16,67 mm (colunas e linhas)
AW  = NC*P;           // 200 mm
AH  = NR*P;           // 166,7 mm
M   = 9;              // margem da frente
OW  = AW + 2*M;       // 218 mm (cabe em mesa 220)
OH  = AH + 2*M;       // 184,7 mm
R   = 4;              // raio dos cantos
WALL = 3;             // parede da caixa
CL  = 0.25;           // folga de encaixe

// frente: 0,6 mm de PETG/PLA branco (difusor) + 1,6 mm preto com as letras vazadas
T_SKIN = 0.6;
T_LET  = 1.6;
FONT = "DejaVu Sans:style=Bold";
LETTER_H = 9;      // altura da maiúscula (mm)
LIP_H = 3; LIP_T = 1.2;

// grade (colmeia) entre frente e LEDs
GRID_H = 12;  GRID_W = 1.2;
NOTCH_W = 11; NOTCH_H = 0.9;   // passagem da fita por baixo das paredes verticais

// caixa
T_PLATE = 2;        // placa das LEDs
ELEC_D  = 16;       // espaço da eletrônica atrás da placa
T_BACK  = 2;
BOX_D   = T_BACK + ELEC_D + T_PLATE + GRID_H;   // 32 mm
LEDGE   = 2;        // degrau que segura a placa das LEDs

$fn = 48;

module rrect(w, h, r) {
  translate([r, r]) offset(r = r) square([w - 2*r, h - 2*r]);
}
// centro da célula (c, r); linha 0 em cima
function cx(c) = M + (c + 0.5)*P;
function cy(r) = M + (NR - r - 0.5)*P;

module glyphs() {
  for (r = [0:NR-1]) for (c = [0:NC-1]) {
    ch = ROWS[r][c];
    translate([cx(c), cy(r)])
      if (ch == "·") circle(d = 4.5);
      else text(ch, size = LETTER_H/0.73, font = FONT, halign = "center", valign = "center");
  }
}

// impressa de face para baixo: a pele branca sai primeiro, troca o filamento em 0,6 mm
module frente() {
  // espelhada para ler certo vista de frente (a face de baixo na mesa é a face da frente)
  mirror([1, 0, 0]) translate([-OW, 0, 0]) {
    linear_extrude(T_SKIN) rrect(OW, OH, R);
    translate([0, 0, T_SKIN]) linear_extrude(T_LET) difference() {
      rrect(OW, OH, R);
      glyphs();
    }
    // aba que entra na caixa
    translate([0, 0, T_SKIN + T_LET]) linear_extrude(LIP_H) difference() {
      translate([WALL + CL, WALL + CL]) rrect(OW - 2*(WALL + CL), OH - 2*(WALL + CL), 1);
      translate([WALL + CL + LIP_T, WALL + CL + LIP_T])
        square([OW - 2*(WALL + CL + LIP_T), OH - 2*(WALL + CL + LIP_T)]);
    }
  }
}

module grade() {
  difference() {
    linear_extrude(GRID_H) difference() {
      translate([M - GRID_W/2, M - GRID_W/2]) square([AW + GRID_W, AH + GRID_W]);
      for (r = [0:NR-1]) for (c = [0:NC-1])
        translate([M + c*P + GRID_W/2, M + (NR - r - 1)*P + GRID_W/2])
          square([P - GRID_W, P - GRID_W]);
    }
    // canal da fita ao longo de cada linha (por baixo das paredes verticais)
    for (r = [0:NR-1])
      translate([M - 2, cy(r) - NOTCH_W/2, -0.01]) cube([AW + 4, NOTCH_W, NOTCH_H]);
  }
}

// placa onde se colam as 10 tiras de 12 LEDs (fita adesiva da própria fita)
module placa_leds() {
  difference() {
    linear_extrude(T_PLATE)
      translate([WALL + CL, WALL + CL]) rrect(OW - 2*(WALL + CL), OH - 2*(WALL + CL), 1);
    // furos nas pontas das linhas para os fios do zigue-zague e da alimentação
    for (r = [0:NR-1]) for (side = [0, 1])
      translate([side == 0 ? M - 1.8 : M + AW + 1.8, cy(r), -1]) cylinder(d = 3.5, h = T_PLATE + 2);
    // marcas de alinhamento das tiras (0,4 mm)
    for (r = [0:NR-1])
      translate([M, cy(r) - 5, T_PLATE - 0.4]) cube([AW, 10, 1]);
  }
}

module caixa() {
  usb_z = T_BACK + ELEC_D/2;
  difference() {
    linear_extrude(BOX_D) rrect(OW, OH, R);
    // espaço da eletrônica (mais estreito: deixa o degrau que segura a placa)
    translate([0, 0, T_BACK]) linear_extrude(ELEC_D + 0.01)
      translate([WALL + LEDGE, WALL + LEDGE]) rrect(OW - 2*(WALL + LEDGE), OH - 2*(WALL + LEDGE), 1);
    // placa + grade
    translate([0, 0, T_BACK + ELEC_D]) linear_extrude(T_PLATE + GRID_H + 1)
      translate([WALL, WALL]) rrect(OW - 2*WALL, OH - 2*WALL, 1);
    // USB-C (parede de baixo, centro)
    translate([OW/2 - 6, -1, usb_z - 3.5]) cube([12, WALL + 2, 7]);
    // 2 botões de 12 mm (acertar hora / minuto), parede de baixo
    for (x = [OW/2 - 40, OW/2 + 40])
      translate([x, -1, usb_z]) rotate([-90, 0, 0]) cylinder(d = 7.5, h = WALL + 2);
    // LDR (sensor de luz) no alto
    translate([OW/2, OH - WALL - 1, T_BACK + ELEC_D - 4]) rotate([-90, 0, 0]) cylinder(d = 5.2, h = WALL + 2);
    // 2 furos tipo fechadura para pendurar
    for (x = [OW/2 - 50, OW/2 + 50]) translate([x, OH - 35, -1]) {
      cylinder(d = 9, h = T_BACK + 2);
      translate([-2.25, 0, 0]) cube([4.5, 12, T_BACK + 2]);
    }
  }
}

module montagem() {
  color("dimgray") caixa();
  color("darkgreen") translate([0, 0, T_BACK + ELEC_D]) placa_leds();
  color("black") translate([0, 0, T_BACK + ELEC_D + T_PLATE]) grade();
  translate([0, 0, BOX_D + T_SKIN + T_LET]) mirror([0, 0, 1]) frente_vista();
}
module frente_vista() {   // frente como fica montada (face para cima)
  translate([OW, 0, 0]) mirror([1, 0, 0]) frente();
}

if (part == "frente") frente();
if (part == "grade") grade();
if (part == "placa_leds") placa_leds();
if (part == "caixa") caixa();
if (part == "montagem") montagem();
if (part == "frente_2d") glyphs();
if (part == "frente_vista") frente_vista();
// vista explodida para documentação
if (part == "explodida") {
  color("dimgray") caixa();
  color("seagreen") translate([0, 0, T_BACK + ELEC_D + 40]) placa_leds();
  color("black") translate([0, 0, T_BACK + ELEC_D + T_PLATE + 80]) grade();
  color("white") translate([0, 0, BOX_D + 150]) frente();   // como sai da impressora: letras para cima
}
