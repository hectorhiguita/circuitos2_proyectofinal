// main.cpp - Medidor de ritmo cardiaco PPG (ESP32-C3 SuperMini)
// Proyecto final Circuitos Eléctricos II - ITM. Ver ../SPEC.md y README.md.
//
// Tareas:
//   muestreo (prioridad alta): ADC 200 Hz x8, DSP, detector, buzzer/LED  -> muestreo.cpp
//   red      (prioridad 2)   : WiFi + MQTT no bloqueante                 -> red.cpp
//   loop()   (prioridad 1)   : OLED 20 fps, botón, alertas 1 Hz, consola serie
#include <Arduino.h>

#include "ajustes.h"
#include "alertas.h"
#include "boton.h"
#include "config.h"
#include "indicadores.h"
#include "muestreo.h"
#include "pantalla.h"
#include "red.h"

static bool modo_plot = SERIAL_PLOT_DEF;
static uint32_t cursor_plot = 0;

static void ayuda() {
  Serial.println(F("# Comandos: p = alternar CSV graficador | s = estado | h = ayuda"));
}

static void imprimir_estado() {
  const EstadoPulso e = muestreo_estado();
  const EstadoRed r = red_estado();
  const Ajustes a = ajustes_leer();
  Serial.printf("# bpm=%d valido=%d dedo=%d ok=%d recorte=%d amp=%.0fmV dc=%.0fmV ibi=%u bat=%.2fV | wifi=%d mqtt=%d "
                "rssi=%d | lim=%d-%d buzzer=%d silencio=%d | retrasos=%lu\n",
                e.bpm, e.bpm_valido, e.dedo, e.senal_ok, e.recorte, e.amp_mv, e.dc_mv, e.ibi, e.bat_v, r.wifi, r.mqtt,
                r.rssi, a.bpm_min, a.bpm_max, a.buzzer, a.silencio, (unsigned long)e.retrasos);
}

static void consola() {
  while (Serial.available()) {
    const int c = Serial.read();
    if (c == 'p') {
      modo_plot = !modo_plot;
      cursor_plot = muestreo_onda_total();
      if (modo_plot) Serial.println("raw_mV,filt_mV,umbral_alto,umbral_bajo,latido_x100");
    } else if (c == 's') {
      imprimir_estado();
    } else if (c == 'h' || c == '?') {
      ayuda();
    }
  }
}

static void plot() {
  // CSV a 50 Hz (Arduino IDE Serial Plotter, `pio device monitor`, o guardar a archivo).
  PuntoOnda p[16];
  size_t n;
  while ((n = muestreo_leer_onda(cursor_plot, p, 16)) > 0) {
    for (size_t i = 0; i < n; i++)
      Serial.printf("%d,%d,%d,%d,%d\n", p[i].raw, p[i].filt, p[i].hi, p[i].lo, p[i].latido ? 100 : 0);
  }
}

void setup() {
  Serial.begin(115200);
  const uint32_t t = millis();
  while (!Serial && millis() - t < 1500) delay(10);  // USB CDC: espera breve al monitor
  Serial.printf("\n# Medidor PPG v%s  id=%s%s\n", FW_VERSION, DEVICE_ID, DEMO_SENSOR ? "  [DEMO_SENSOR]" : "");
  ayuda();

  ajustes_iniciar();
  boton_iniciar();
  if (!pantalla_iniciar()) Serial.println(PANTALLA_TFT ? "# TFT: sin memoria para el lienzo" : "# OLED no detectada en 0x3C (SDA=6, SCL=7)");
  pantalla_mensaje("Pulso PPG", DEMO_SENSOR ? "modo DEMO" : "ponga el dedo");
  alertas_iniciar();
  muestreo_iniciar();
  red_iniciar();
  cursor_plot = muestreo_onda_total();
  if (modo_plot) Serial.println("raw_mV,filt_mV,umbral_alto,umbral_bajo,latido_x100");
}

void loop() {
  static uint32_t t_pant = 0, t_alerta = 0, t_log = 0;
  const uint32_t ahora = millis();

  switch (boton_leer(ahora)) {
    case EventoBoton::CORTO:
      pantalla_siguiente();
      t_pant = 0;
      break;
    case EventoBoton::LARGO: {
      const bool s = !ajustes_leer().silencio;
      ajustes_set_silencio(s);
      indicadores_confirmacion(s ? 1 : 2);  // 1 pitido = silenciado, 2 = reactivado
      Serial.printf("# buzzer %s\n", s ? "silenciado" : "activo");
      break;
    }
    default: break;
  }

  if (ahora - t_alerta >= 1000) {
    t_alerta = ahora;
    alertas_actualizar(ahora);
  }
  if (ahora - t_pant >= 50) {
    t_pant = ahora;
    pantalla_dibujar(ahora);
  }

  consola();
  if (modo_plot) {
    plot();
  } else if (ahora - t_log >= 1000) {
    t_log = ahora;
    imprimir_estado();
  }
  delay(5);
}
