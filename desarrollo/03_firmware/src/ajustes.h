// ajustes.h - Configuración persistente en NVS (Preferences).
// bpm_min / bpm_max / buzzer llegan por MQTT (pulso/<id>/config, retained);
// "silencio" se cambia con pulsación larga del botón BOOT.
#pragma once
#include <Arduino.h>

struct Ajustes {
  int bpm_min;
  int bpm_max;
  bool buzzer;    // habilitado por configuración remota
  bool silencio;  // silenciado localmente con el botón
};

void ajustes_iniciar();
Ajustes ajustes_leer();
// Aplica un JSON de configuración; devuelve true si algo cambió (y lo guarda).
bool ajustes_aplicar_json(const char* json, size_t len);
void ajustes_set_silencio(bool s);
// Pitido efectivo = buzzer && !silencio (lectura rápida, sin bloqueo; usable en la tarea de muestreo).
bool ajustes_pitido_activo();
