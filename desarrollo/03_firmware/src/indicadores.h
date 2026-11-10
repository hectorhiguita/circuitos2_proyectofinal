// indicadores.h - Buzzer (GPIO10) y LED de la placa (GPIO8, activo en bajo).
// indicadores_tick() y indicadores_latido() se llaman desde la tarea de muestreo (cada 5 ms),
// así el pitido dura exactamente BEEP_MS aunque la red o la pantalla estén ocupadas.
#pragma once
#include <Arduino.h>

void indicadores_iniciar();
void indicadores_latido(uint32_t ahora_ms);   // pitido 30 ms + destello LED
void indicadores_tick(uint32_t ahora_ms);
void indicadores_alerta();                    // 3 pitidos (se ejecutan en la tarea de muestreo)
void indicadores_confirmacion(uint8_t n);     // n pitidos cortos (p. ej. al silenciar)
