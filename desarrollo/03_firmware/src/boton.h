// boton.h - Botón BOOT (GPIO9, activo en bajo) con antirrebote.
// Pulsación corta: cambia de pantalla. Pulsación larga (>= 0.8 s): silenciar / reactivar buzzer.
// Nota: mantener BOOT presionado al ENCENDER entra al modo de descarga (es su función original).
#pragma once
#include <Arduino.h>

enum class EventoBoton : uint8_t { NINGUNO, CORTO, LARGO };

void boton_iniciar();
EventoBoton boton_leer(uint32_t ahora_ms);  // llamar seguido desde loop()
