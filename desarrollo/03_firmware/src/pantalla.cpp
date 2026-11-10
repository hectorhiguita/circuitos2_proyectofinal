// pantalla.cpp - OLED SSD1306 (entorno c3_oled). La TFT está en pantalla_tft.cpp.
#include "config.h"
#if !PANTALLA_TFT
#include "pantalla.h"

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>

#include "ajustes.h"
#include "alertas.h"
#include "config.h"
#include "muestreo.h"
#include "red.h"

static Adafruit_SSD1306 oled(OLED_W, OLED_H, &Wire, -1);
static bool presente = false;
static uint8_t pagina = 0;
static constexpr uint8_t N_PAGINAS = 3;
static PuntoOnda buf[OLED_W];

bool pantalla_iniciar() {
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);
  presente = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  if (!presente) return false;
  oled.setTextColor(SSD1306_WHITE);
  oled.cp437(true);
  return true;
}

void pantalla_siguiente() { pagina = (pagina + 1) % N_PAGINAS; }

void pantalla_mensaje(const char* l1, const char* l2) {
  if (!presente) return;
  oled.clearDisplay();
  oled.setTextSize(2);
  oled.setCursor(0, 8);
  oled.print(l1);
  oled.setTextSize(1);
  oled.setCursor(0, 40);
  oled.print(l2);
  oled.display();
}

// ------------------------------------------------------------------ iconos
static void corazon(int cx, int cy, int r) {
  oled.fillCircle(cx - r, cy - r / 2, r, SSD1306_WHITE);
  oled.fillCircle(cx + r, cy - r / 2, r, SSD1306_WHITE);
  oled.fillTriangle(cx - 2 * r, cy - r / 4, cx + 2 * r, cy - r / 4, cx, cy + 2 * r, SSD1306_WHITE);
}

static void icono_wifi(int x, int y, const EstadoRed& r) {
  if (!r.wifi) {  // X
    oled.drawLine(x, y, x + 6, y + 6, SSD1306_WHITE);
    oled.drawLine(x, y + 6, x + 6, y, SSD1306_WHITE);
    return;
  }
  const int barras = r.rssi > -60 ? 3 : r.rssi > -72 ? 2 : 1;
  for (int i = 0; i < 3; i++) {
    const int h = 3 + 2 * i;
    if (i < barras) oled.fillRect(x + i * 3, y + 7 - h, 2, h, SSD1306_WHITE);
    else oled.drawPixel(x + i * 3, y + 6, SSD1306_WHITE);
  }
}

static void icono_mqtt(int x, int y, bool ok) {
  if (ok) {
    oled.fillRoundRect(x, y, 9, 8, 1, SSD1306_WHITE);
    oled.setTextColor(SSD1306_BLACK);
  } else {
    oled.drawRoundRect(x, y, 9, 8, 1, SSD1306_WHITE);
  }
  oled.setTextSize(1);
  oled.setCursor(x + 2, y);
  oled.print('M');
  oled.setTextColor(SSD1306_WHITE);
}

static void icono_silencio(int x, int y) {  // altavoz tachado
  oled.fillRect(x, y + 2, 2, 4, SSD1306_WHITE);
  oled.fillTriangle(x + 2, y + 4, x + 5, y, x + 5, y + 7, SSD1306_WHITE);
  oled.drawLine(x + 7, y + 1, x + 10, y + 6, SSD1306_WHITE);
  oled.drawLine(x + 10, y + 1, x + 7, y + 6, SSD1306_WHITE);
}

static void icono_bateria(int x, int y, float v) {
  // Batería baja: el icono parpadea (1 Hz).
  if (v < BAT_V_BAJA && (millis() / 500) % 2) return;
  const float f = bateria_pct(v) / 100.0f;
  oled.drawRect(x, y, 18, 8, SSD1306_WHITE);
  oled.fillRect(x + 18, y + 2, 2, 4, SSD1306_WHITE);
  oled.fillRect(x + 2, y + 2, (int)(14 * f + 0.5f), 4, SSD1306_WHITE);
}

static void barra_estado(const EstadoPulso& e, const EstadoRed& r, const Ajustes& a) {
  icono_wifi(0, 0, r);
  icono_mqtt(12, 0, r.mqtt);
  if (a.silencio || !a.buzzer) icono_silencio(25, 0);
#if DEMO_SENSOR
  oled.setTextSize(1);
  oled.setCursor(42, 0);
  oled.print("DEMO");
#endif
  oled.setTextSize(1);
  oled.setCursor(78, 0);
  oled.printf("%3d%%", bateria_pct(e.bat_v));
  icono_bateria(106, 0, e.bat_v);
}

// Onda autoescalada en la franja [y0, y0+h).
static void onda(int y0, int h) {
  const size_t n = muestreo_ultimos(buf, OLED_W);
  if (n < 2) return;
  int mn = buf[0].filt, mx = buf[0].filt;
  for (size_t i = 1; i < n; i++) {
    if (buf[i].filt < mn) mn = buf[i].filt;
    if (buf[i].filt > mx) mx = buf[i].filt;
  }
  int rango = mx - mn;
  if (rango < 40) {  // señal mínima: escala fija para no amplificar ruido
    const int c = (mx + mn) / 2;
    mn = c - 20;
    rango = 40;
  }
  const int x0 = OLED_W - (int)n;
  int py = 0;
  for (size_t i = 0; i < n; i++) {
    const int y = y0 + h - 1 - (int)((long)(buf[i].filt - mn) * (h - 1) / rango);
    if (i) oled.drawLine(x0 + i - 1, py, x0 + i, y, SSD1306_WHITE);
    if (buf[i].latido) oled.drawPixel(x0 + i, y0, SSD1306_WHITE);  // marca de latido
    py = y;
  }
}

static void pagina_principal(uint32_t ahora, const EstadoPulso& e) {
  oled.setTextSize(3);
  oled.setCursor(0, 12);
  if (e.bpm_valido) oled.printf("%3d", e.bpm);
  else oled.print(e.dedo ? " .." : " --");
  oled.setTextSize(1);
  oled.setCursor(56, 14);
  oled.print("lpm");
  oled.setCursor(56, 26);
  if (!e.dedo) oled.print("sin dedo");
  else if (e.recorte) oled.print("recorte");
  else if (!e.bpm_valido) oled.print("midiendo");

  // Corazón: grande durante 150 ms tras cada latido.
  const bool golpe = e.dedo && (ahora - e.ultimo_inicio_ms) < 150;
  corazon(112, 21, golpe ? 5 : 3);

  ppg::AlertEvent a;
  if (alertas_reciente(ahora, 5000, a)) {
    oled.fillRect(0, 37, OLED_W, 9, SSD1306_WHITE);
    oled.setTextColor(SSD1306_BLACK);
    oled.setCursor(2, 38);
    oled.printf("ALERTA %s", ppg::alertName(a.type));
    oled.setTextColor(SSD1306_WHITE);
    onda(47, 17);
  } else {
    onda(38, 26);
  }
}

static void pagina_detalles(const EstadoPulso& e, const Ajustes& a) {
  oled.setTextSize(1);
  oled.setCursor(0, 12);
  oled.printf("BPM %3d  IBI %4u ms\n", e.bpm, e.ibi);
  oled.printf("Amp %4.0f mV DC %4.0f\n", e.amp_mv, e.dc_mv);
  oled.printf("Dedo %s  Senal %s\n", e.dedo ? "si" : "no", e.senal_ok ? "ok" : "--");
  oled.printf("Recorte ADC: %s\n", e.recorte ? "SI (bajar RV1)" : "no");
  oled.printf("Alertas %d-%d lpm\n", a.bpm_min, a.bpm_max);
  oled.printf("Buzzer %s %s", a.buzzer ? "on" : "off", a.silencio ? "(silencio)" : "");
}

static void pagina_red(uint32_t ahora, const EstadoRed& r) {
  oled.setTextSize(1);
  oled.setCursor(0, 12);
  oled.printf("SSID %.16s\n", strlen(WIFI_SSID) ? WIFI_SSID : "(sin red)");
  oled.printf("IP   %s\n", r.wifi ? r.ip : "-");
  oled.printf("RSSI %d dBm\n", r.rssi);
  oled.printf("MQTT %s\n", r.mqtt ? "conectado" : "desconectado");
  oled.printf("ID   %s\n", DEVICE_ID);
  oled.printf("Up   %lus  v%s", (unsigned long)(ahora / 1000), FW_VERSION);
}

void pantalla_dibujar(uint32_t ahora) {
  if (!presente) return;
  const EstadoPulso e = muestreo_estado();
  const EstadoRed r = red_estado();
  const Ajustes a = ajustes_leer();
  oled.clearDisplay();
  barra_estado(e, r, a);
  switch (pagina) {
    case 0: pagina_principal(ahora, e); break;
    case 1: pagina_detalles(e, a); break;
    default: pagina_red(ahora, r); break;
  }
  oled.display();
}
#endif  // !PANTALLA_TFT
