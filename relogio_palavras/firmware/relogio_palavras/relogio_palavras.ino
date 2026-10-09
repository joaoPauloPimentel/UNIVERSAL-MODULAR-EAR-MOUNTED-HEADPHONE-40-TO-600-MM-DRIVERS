// Relógio de palavras em português — jeito digital ("SÃO DUAS E QUARENTA E CINCO")
// Arduino Nano + DS3231 + 120 LEDs WS2812B (10 linhas x 12, fita 60 LED/m em zigue-zague)
// Bibliotecas (Gerenciador de Bibliotecas da IDE): FastLED, RTClib (Adafruit)
//
// Ligações:
//   D6  -> DIN da fita (resistor de 330 ohm em série)     5V/GND da USB direto na fita
//   A4  -> SDA do DS3231    A5 -> SCL do DS3231
//   D2  -> botão HORA  (outro lado no GND)
//   D3  -> botão MINUTO (outro lado no GND)
//   A0  -> LDR para 5V + resistor de 10k para GND (opcional; sem LDR, deixe USA_LDR = false)
//
// Grade (linha 0 em cima), igual a cad/relogio.scad:
//   0 É R S Ã O U M A D U A S
//   1 T R Ê S K Q U A T R O B
//   2 C I N C O T S E I S P V
//   3 S E T E O I T O N O V E
//   4 D E Z O N Z E J D O Z E
//   5 H O R A S E Q U I N Z E
//   6 V I N T E T R I N T A X
//   7 D E Z Q U A R E N T A Z
//   8 C I N Q U E N T A E X Y
//   9 C I N C O M H L . . . .   (os 4 pontos = minutos 1 a 4)

#include <FastLED.h>
#include <RTClib.h>

#define PINO_LED      6
#define PINO_HORA     2
#define PINO_MIN      3
#define PINO_LDR      A0
#define USA_LDR       true
#define COLUNAS       12
#define LINHAS        10
#define NUM_LEDS      (COLUNAS * LINHAS)
#define LIMITE_MA     1500      // limite de corrente: a USB não aguenta a fita toda acesa (até ~7 A)
#define COR           CRGB(255, 170, 90)   // branco quente

// Zigue-zague: a linha 0 começa na esquerda (vista de FRENTE), a linha 1 volta da direita, etc.
// Se a sua fita começar pela direita, troque para true.
#define COMECA_DIREITA false

CRGB leds[NUM_LEDS];
RTC_DS3231 rtc;

struct Palavra { uint8_t linha, col, tam; };

const Palavra E_VERBO   = {0, 0, 1};
const Palavra SAO       = {0, 2, 3};
const Palavra HORAS_N[13] = {
  {0, 0, 0},
  {0, 5, 3},   // UMA
  {0, 8, 4},   // DUAS
  {1, 0, 4},   // TRÊS
  {1, 5, 6},   // QUATRO
  {2, 0, 5},   // CINCO
  {2, 6, 4},   // SEIS
  {3, 0, 4},   // SETE
  {3, 4, 4},   // OITO
  {3, 8, 4},   // NOVE
  {4, 0, 3},   // DEZ
  {4, 3, 4},   // ONZE
  {4, 8, 4},   // DOZE
};
const Palavra HORA      = {5, 0, 4};
const Palavra S_HORAS   = {5, 4, 1};
const Palavra E1        = {5, 5, 1};
const Palavra QUINZE    = {5, 6, 6};
const Palavra VINTE     = {6, 0, 5};
const Palavra TRINTA    = {6, 5, 6};
const Palavra DEZ_M     = {7, 0, 3};
const Palavra QUARENTA  = {7, 3, 8};
const Palavra CINQUENTA = {8, 0, 9};
const Palavra E2        = {8, 9, 1};
const Palavra CINCO_M   = {9, 0, 5};
const uint8_t COL_PONTOS = 8;     // linha 9, colunas 8..11

uint16_t indice(uint8_t linha, uint8_t col) {
  bool invertida = (linha % 2 == 1) != COMECA_DIREITA;
  return linha * COLUNAS + (invertida ? (COLUNAS - 1 - col) : col);
}

void acende(const Palavra &p) {
  for (uint8_t i = 0; i < p.tam; i++) leds[indice(p.linha, p.col + i)] = COR;
}

void mostra(uint8_t h24, uint8_t m) {
  FastLED.clear();
  uint8_t h = h24 % 12;
  if (h == 0) h = 12;
  uint8_t m5 = m / 5 * 5;

  acende(h == 1 ? E_VERBO : SAO);            // "É UMA" / "SÃO DUAS"
  acende(HORAS_N[h]);

  if (m5 == 0) {                             // "É UMA HORA" / "SÃO DUAS HORAS"
    acende(HORA);
    if (h != 1) acende(S_HORAS);
  } else {
    acende(E1);
    switch (m5) {
      case 5:  acende(CINCO_M); break;
      case 10: acende(DEZ_M); break;
      case 15: acende(QUINZE); break;
      case 20: acende(VINTE); break;
      case 25: acende(VINTE); acende(E2); acende(CINCO_M); break;
      case 30: acende(TRINTA); break;
      case 35: acende(TRINTA); acende(E2); acende(CINCO_M); break;
      case 40: acende(QUARENTA); break;
      case 45: acende(QUARENTA); acende(E2); acende(CINCO_M); break;
      case 50: acende(CINQUENTA); break;
      case 55: acende(CINQUENTA); acende(E2); acende(CINCO_M); break;
    }
  }
  for (uint8_t i = 0; i < m % 5; i++) leds[indice(9, COL_PONTOS + i)] = COR;   // minutos 1 a 4
  FastLED.show();
}

uint8_t brilho() {
  if (!USA_LDR) return 120;
  int l = analogRead(PINO_LDR);              // 0 (escuro) .. 1023 (claro)
  return constrain(map(l, 0, 1023, 12, 200), 12, 200);
}

bool apertou(uint8_t pino) {
  if (digitalRead(pino) == LOW) {
    delay(30);
    if (digitalRead(pino) == LOW) return true;
  }
  return false;
}

void setup() {
  pinMode(PINO_HORA, INPUT_PULLUP);
  pinMode(PINO_MIN, INPUT_PULLUP);
  FastLED.addLeds<WS2812B, PINO_LED, GRB>(leds, NUM_LEDS);
  FastLED.setMaxPowerInVoltsAndMilliamps(5, LIMITE_MA);
  if (!rtc.begin()) {                        // DS3231 não encontrado: pisca o "É" em vermelho
    while (true) { leds[indice(0, 0)] = CRGB::Red; FastLED.show(); delay(300);
                   FastLED.clear(); FastLED.show(); delay(300); }
  }
  if (rtc.lostPower()) rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));   // bateria nova: pega a hora do computador
}

void loop() {
  DateTime t = rtc.now();

  if (apertou(PINO_HORA)) {                  // HORA: +1 hora
    rtc.adjust(DateTime(t.year(), t.month(), t.day(), (t.hour() + 1) % 24, t.minute(), 0));
    t = rtc.now(); mostra(t.hour(), t.minute()); delay(250); return;
  }
  if (apertou(PINO_MIN)) {                   // MINUTO: +1 minuto (segundos zerados)
    rtc.adjust(DateTime(t.year(), t.month(), t.day(), t.hour(), (t.minute() + 1) % 60, 0));
    t = rtc.now(); mostra(t.hour(), t.minute()); delay(150); return;
  }

  FastLED.setBrightness(brilho());
  mostra(t.hour(), t.minute());
  delay(200);
}
