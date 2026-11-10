// red.h - WiFi + MQTT en su propia tarea FreeRTOS (no bloquea pantalla ni medición).
// Tópicos (prefijo pulso/<DEVICE_ID>/), ver SPEC.md:
//   estado 1 Hz, onda 4 Hz (25 valores a 50 Hz), latido, alerta, online (LWT retained),
//   config (suscrito, retained) -> bpm_min / bpm_max / buzzer en NVS.
#pragma once
#include <Arduino.h>

struct EstadoRed {
  bool wifi;
  bool mqtt;
  int rssi;
  char ip[16];
  uint32_t reconexiones;
};

void red_iniciar();
EstadoRed red_estado();
