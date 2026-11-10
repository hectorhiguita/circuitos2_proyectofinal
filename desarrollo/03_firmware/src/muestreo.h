// muestreo.h - Adquisición a 200 Hz + DSP en una tarea FreeRTOS de alta prioridad.
//
// La tarea usa vTaskDelayUntil (periodo exacto de 5 ms, sin deriva) y NO lee el ADC
// dentro de una ISR: analogReadMilliVolts usa el driver del ADC con bloqueos,
// que no es seguro desde interrupción. En la misma tarea se procesa el DSP y se
// manejan buzzer/LED, de modo que WiFi/MQTT/OLED nunca retrasan la medición.
//
// Salidas hacia el resto del firmware:
//   - anillo de onda a 50 Hz (pantalla, MQTT "onda", graficador serie)
//   - cola de latidos (MQTT "latido")
//   - estado instantáneo (BPM, dedo, batería...)
#pragma once
#include <Arduino.h>

struct PuntoOnda {
  uint32_t t;       // ms
  int16_t raw;      // mV en GPIO1
  int16_t filt;     // mV, señal filtrada AC con picos hacia arriba
  int16_t hi, lo;   // umbrales del detector
  uint8_t latido;   // 1 si hubo inicio de latido en este punto
};

struct Latido {
  uint32_t t;    // ms (máximo del pulso)
  uint16_t ibi;  // ms
  uint16_t bpm;  // BPM actual (mediana) tras este latido
};

struct EstadoPulso {
  int bpm;            // 0 si no válido
  bool bpm_valido;
  bool dedo;
  bool senal_ok;
  bool recorte;       // ADC saturado (bajar ganancia con RV1)
  float amp_mv;       // p-p señal filtrada
  float dc_mv;        // nivel DC en GPIO1 (debe ser ~Vref = 1320 mV)
  uint16_t ibi;
  uint32_t ultimo_inicio_ms;  // último inicio de latido (para animar el corazón)
  float bat_v;
  uint32_t muestras;          // contador de muestras
  uint32_t retrasos;          // periodos perdidos (diagnóstico)
};

static constexpr int ONDA_LEN = 256;  // ~5 s a 50 Hz

void muestreo_iniciar();
EstadoPulso muestreo_estado();
// Copia hasta `max` puntos nuevos desde `cursor` (nº de punto absoluto) y lo avanza.
size_t muestreo_leer_onda(uint32_t& cursor, PuntoOnda* out, size_t max);
// Copia los últimos `n` puntos (para la pantalla).
size_t muestreo_ultimos(PuntoOnda* out, size_t n);
uint32_t muestreo_onda_total();
// Cola de latidos (consumida por la tarea de red).
bool muestreo_sacar_latido(Latido& l);
