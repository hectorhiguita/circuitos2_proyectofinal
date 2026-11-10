// pantalla_tft.cpp - TFT IPS 1.3" 240x240 ST7789 por SPI (módulo GMT130-V1.0, 7 pines, sin CS).
// Misma interfaz que pantalla.h. Se compila con -DPANTALLA_TFT=1 (entornos c3 y c3_demo).
// Pines: SCK=GPIO4, SDA(MOSI)=GPIO6, DC=GPIO7, RES=GPIO5, BLK=GPIO3 (brillo PWM).
// Dibuja en un lienzo de 240x240 en RAM (115 kB) y lo envía completo: sin parpadeo.
#include "config.h"
#if PANTALLA_TFT
#include <Adafruit_GFX.h>
#include <Adafruit_ST7789.h>
#include <SPI.h>

#include "ajustes.h"
#include "alertas.h"
#include "muestreo.h"
#include "pantalla.h"
#include "red.h"

static constexpr int W = 240, H = 240;
static Adafruit_ST7789 tft(&SPI, -1, TFT_DC, TFT_RST);
static GFXcanvas16* lienzo = nullptr;
static bool presente = false;
static uint8_t pagina = 0;
static constexpr uint8_t N_PAGINAS = 3;
static PuntoOnda buf[W];
static uint32_t ultimo_envio = 0;

// Colores RGB565
static constexpr uint16_t NEGRO = 0x0000, BLANCO = 0xFFFF, GRIS = 0x4208, GRIS_C = 0x8410,
                          ROJO = 0xF800, VERDE = 0x07E0, AMARILLO = 0xFFE0, CIAN = 0x07FF,
                          AZUL_O = 0x10A2, NARANJA = 0xFD20, VERDE_O = 0x0320;

#define G (*lienzo)

bool pantalla_iniciar() {
  pinMode(TFT_BLK, OUTPUT);
  analogWrite(TFT_BLK, TFT_BRILLO);
  SPI.begin(TFT_SCK, -1, TFT_MOSI, -1);
  tft.init(W, H, SPI_MODE3);   // módulos sin CS necesitan modo 3
  tft.setSPISpeed(40000000);
  tft.setRotation(TFT_ROTACION);
  tft.fillScreen(NEGRO);
  lienzo = new GFXcanvas16(W, H);
  presente = lienzo && lienzo->getBuffer();
  if (presente) G.cp437(true);
  return presente;
}

void pantalla_siguiente() { pagina = (pagina + 1) % N_PAGINAS; }

static void enviar() { tft.drawRGBBitmap(0, 0, G.getBuffer(), W, H); }

void pantalla_mensaje(const char* l1, const char* l2) {
  if (!presente) return;
  G.fillScreen(NEGRO);
  G.setTextColor(ROJO);
  G.setTextSize(3);
  G.setCursor(12, 80);
  G.print(l1);
  G.setTextColor(BLANCO);
  G.setTextSize(2);
  G.setCursor(12, 130);
  G.print(l2);
  enviar();
}

// ------------------------------------------------------------------ iconos
static void corazon(int cx, int cy, int r, uint16_t c) {
  G.fillCircle(cx - r, cy - r / 2, r, c);
  G.fillCircle(cx + r, cy - r / 2, r, c);
  G.fillTriangle(cx - 2 * r, cy - r / 4 + 1, cx + 2 * r, cy - r / 4 + 1, cx, cy + 2 * r, c);
}

static void icono_wifi(int x, int y, const EstadoRed& r) {
  if (!r.wifi) {
    G.drawLine(x, y, x + 14, y + 14, ROJO);
    G.drawLine(x, y + 14, x + 14, y, ROJO);
    return;
  }
  const int barras = r.rssi > -60 ? 4 : r.rssi > -70 ? 3 : r.rssi > -80 ? 2 : 1;
  for (int i = 0; i < 4; i++) {
    const int h = 4 + 3 * i;
    G.fillRect(x + i * 4, y + 15 - h, 3, h, i < barras ? BLANCO : GRIS);
  }
}

static void icono_bateria(int x, int y, float v) {
  const int pct = bateria_pct(v);
  const bool baja = v < BAT_V_BAJA;
  if (baja && (millis() / 500) % 2) return;  // parpadea
  const uint16_t c = baja ? ROJO : pct < 30 ? NARANJA : VERDE;
  G.drawRect(x, y, 28, 14, BLANCO);
  G.fillRect(x + 28, y + 4, 3, 6, BLANCO);
  G.fillRect(x + 2, y + 2, (int)(24 * pct / 100.0f + 0.5f), 10, c);
}

static void barra_estado(const EstadoPulso& e, const EstadoRed& r, const Ajustes& a) {
  G.fillRect(0, 0, W, 22, AZUL_O);
  icono_wifi(4, 3, r);
  G.setTextSize(2);
  G.setCursor(26, 3);
  G.setTextColor(r.mqtt ? VERDE : GRIS_C);
  G.print("MQTT");
  if (a.silencio || !a.buzzer) {
    G.setTextColor(NARANJA);
    G.setCursor(80, 3);
    G.print("MUDO");
  }
#if DEMO_SENSOR
  G.setTextColor(CIAN);
  G.setCursor(80, 3);
  G.print("DEMO");
#endif
  G.setTextColor(BLANCO);
  G.setCursor(150, 3);
  G.printf("%3d%%", bateria_pct(e.bat_v));
  icono_bateria(204, 4, e.bat_v);
}

static uint16_t color_bpm(int bpm, const Ajustes& a) {
  if (bpm < a.bpm_min || bpm > a.bpm_max) return ROJO;
  if (bpm < a.bpm_min + 5 || bpm > a.bpm_max - 10) return AMARILLO;
  return VERDE;
}

// Onda autoescalada con cuadrícula, en la franja [y0, y0+h).
static void onda(int y0, int h) {
  G.fillRect(0, y0, W, h, NEGRO);
  for (int x = 0; x < W; x += 50) G.drawFastVLine(x, y0, h, VERDE_O);   // 1 s por división (50 Hz)
  for (int y = y0; y < y0 + h; y += h / 4) G.drawFastHLine(0, y, W, VERDE_O);
  const size_t n = muestreo_ultimos(buf, W);
  if (n < 2) return;
  int mn = buf[0].filt, mx = buf[0].filt;
  for (size_t i = 1; i < n; i++) {
    if (buf[i].filt < mn) mn = buf[i].filt;
    if (buf[i].filt > mx) mx = buf[i].filt;
  }
  int rango = mx - mn;
  if (rango < 40) {
    mn = (mx + mn) / 2 - 20;
    rango = 40;
  }
  const int x0 = W - (int)n;
  int py = 0;
  for (size_t i = 0; i < n; i++) {
    const int y = y0 + h - 3 - (int)((long)(buf[i].filt - mn) * (h - 6) / rango);
    if (i) {
      G.drawLine(x0 + i - 1, py, x0 + i, y, VERDE);
      G.drawLine(x0 + i - 1, py + 1, x0 + i, y + 1, VERDE);   // trazo de 2 px
    }
    if (buf[i].latido) G.fillCircle(x0 + i, y0 + 4, 3, ROJO);
    py = y;
  }
}

static void pagina_principal(uint32_t ahora, const EstadoPulso& e, const Ajustes& a) {
  G.setTextSize(8);  // 48 x 64 px por cifra
  G.setCursor(8, 34);
  if (e.bpm_valido) {
    G.setTextColor(color_bpm(e.bpm, a));
    G.printf("%3d", e.bpm);
  } else {
    G.setTextColor(GRIS_C);
    G.print(e.dedo ? " .." : " --");
  }
  G.setTextColor(BLANCO);
  G.setTextSize(2);
  G.setCursor(160, 82);
  G.print("lpm");
  G.setCursor(10, 110);
  G.setTextColor(e.recorte ? NARANJA : GRIS_C);
  if (!e.dedo) G.print("Ponga el dedo");
  else if (e.recorte) G.print("Recorte: baje RV1");
  else if (!e.bpm_valido) G.print("Midiendo...");
  else G.printf("IBI %u ms", e.ibi);

  const bool golpe = e.dedo && (ahora - e.ultimo_inicio_ms) < 150;
  corazon(198, 50, golpe ? 13 : 9, golpe ? ROJO : 0x8000);

  ppg::AlertEvent al;
  int y_onda = 136;
  if (alertas_reciente(ahora, 5000, al)) {
    G.fillRect(0, 134, W, 24, ROJO);
    G.setTextColor(BLANCO);
    G.setCursor(6, 138);
    G.printf("ALERTA %s", ppg::alertName(al.type));
    y_onda = 160;
  }
  onda(y_onda, H - y_onda);
}

static void lineas(const char* titulo) {
  G.setTextColor(CIAN);
  G.setTextSize(2);
  G.setCursor(6, 30);
  G.print(titulo);
  G.setTextColor(BLANCO);
  G.setCursor(0, 58);
}

static void pagina_detalles(const EstadoPulso& e, const Ajustes& a) {
  lineas("Senal");
  G.printf(" BPM   %d\n IBI   %u ms\n Amp   %.0f mV\n DC    %.0f mV\n", e.bpm, e.ibi, e.amp_mv, e.dc_mv);
  G.printf(" Dedo  %s\n Senal %s\n Recorte %s\n", e.dedo ? "si" : "no", e.senal_ok ? "ok" : "--",
           e.recorte ? "SI" : "no");
  G.printf(" Alertas %d-%d\n Buzzer %s", a.bpm_min, a.bpm_max, a.silencio ? "mudo" : a.buzzer ? "on" : "off");
}

static void pagina_red(uint32_t ahora, const EstadoRed& r) {
  lineas("Red");
  G.printf(" SSID %.12s\n", strlen(WIFI_SSID) ? WIFI_SSID : "(sin red)");
  G.printf(" IP   %s\n RSSI %d dBm\n MQTT %s\n", r.wifi ? r.ip : "-", r.rssi, r.mqtt ? "ok" : "no");
  G.printf(" ID   %s\n Up   %lu s\n FW   v%s", DEVICE_ID, (unsigned long)(ahora / 1000), FW_VERSION);
}

void pantalla_dibujar(uint32_t ahora) {
  if (!presente || ahora - ultimo_envio < TFT_PERIODO_MS) return;   // ~12 fps: el envío SPI tarda ~25 ms
  ultimo_envio = ahora;
  const EstadoPulso e = muestreo_estado();
  const EstadoRed r = red_estado();
  const Ajustes a = ajustes_leer();
  G.fillScreen(NEGRO);
  barra_estado(e, r, a);
  switch (pagina) {
    case 0: pagina_principal(ahora, e, a); break;
    case 1: pagina_detalles(e, a); break;
    default: pagina_red(ahora, r); break;
  }
  enviar();
}
#endif  // PANTALLA_TFT
