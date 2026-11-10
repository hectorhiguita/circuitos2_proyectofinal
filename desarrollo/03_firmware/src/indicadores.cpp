// indicadores.cpp - ver indicadores.h
#include "indicadores.h"

#include "ajustes.h"
#include "config.h"

static uint32_t buzzer_hasta = 0, led_hasta = 0;
static bool buzzer_on = false, led_on = false;
// Patrón pendiente: nº de pitidos. Las alertas respetan el silencio; la confirmación
// del botón suena siempre (para saber que se silenció / reactivó).
static volatile uint8_t patron_pendiente = 0;
static uint8_t patron_restante = 0;
static uint32_t patron_t = 0;
static bool patron_fase_on = false;

static inline void buzzer(bool on) {
  buzzer_on = on;
  digitalWrite(PIN_BUZZER, on ? HIGH : LOW);
}
static inline void led(bool on) {
  led_on = on;
  digitalWrite(PIN_LED, on ? LOW : HIGH);  // activo en bajo
}

void indicadores_iniciar() {
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  buzzer(false);
  led(false);
}

void indicadores_latido(uint32_t t) {
  led(true);
  led_hasta = t + LED_MS;
  if (ajustes_pitido_activo() && patron_restante == 0) {
    buzzer(true);
    buzzer_hasta = t + BEEP_MS;
  }
}

void indicadores_alerta() {
  if (!ajustes_pitido_activo()) return;
  patron_pendiente = 3;
}

void indicadores_confirmacion(uint8_t n) {
  patron_pendiente = n;
}

void indicadores_tick(uint32_t t) {
  if (led_on && (int32_t)(t - led_hasta) >= 0) led(false);

  if (patron_pendiente && patron_restante == 0) {
    patron_restante = patron_pendiente;
    patron_pendiente = 0;
    patron_fase_on = false;
    patron_t = t;
  }
  if (patron_restante) {
    if ((int32_t)(t - patron_t) >= 0) {
      patron_fase_on = !patron_fase_on;
      buzzer(patron_fase_on);
      patron_t = t + 80;
      if (!patron_fase_on) patron_restante--;
    }
    return;
  }
  if (buzzer_on && (int32_t)(t - buzzer_hasta) >= 0) buzzer(false);
}
