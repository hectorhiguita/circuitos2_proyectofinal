// alertas.h - Alertas tempranas en el equipo (funcionan también sin red).
// Usa ppg::AlertEngine (lib/ppg_dsp, probado en el PC). Cada alerta: 3 pitidos,
// aviso en la OLED y publicación en pulso/<id>/alerta (si hay MQTT).
#pragma once
#include <Arduino.h>

#include "alert_logic.h"

void alertas_iniciar();
void alertas_actualizar(uint32_t ahora_ms);  // llamar ~1 Hz desde loop()
bool alertas_sacar(ppg::AlertEvent& ev);     // cola hacia la tarea de red
// Última alerta para la pantalla; devuelve false si no hay una reciente (< ms).
bool alertas_reciente(uint32_t ahora_ms, uint32_t ventana_ms, ppg::AlertEvent& ev);
