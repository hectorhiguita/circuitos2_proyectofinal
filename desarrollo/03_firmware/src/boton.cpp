// boton.cpp - ver boton.h
#include "boton.h"

#include "config.h"

static bool estable = false;  // true = presionado
static bool ultimo_crudo = false;
static uint32_t t_cambio = 0, t_presion = 0;
static bool largo_emitido = false;

void boton_iniciar() { pinMode(PIN_BOTON, INPUT_PULLUP); }

EventoBoton boton_leer(uint32_t t) {
  const bool crudo = digitalRead(PIN_BOTON) == LOW;
  if (crudo != ultimo_crudo) {
    ultimo_crudo = crudo;
    t_cambio = t;
  }
  EventoBoton ev = EventoBoton::NINGUNO;
  if (crudo != estable && (t - t_cambio) >= 30) {  // 30 ms antirrebote
    estable = crudo;
    if (estable) {
      t_presion = t;
      largo_emitido = false;
    } else if (!largo_emitido) {
      ev = EventoBoton::CORTO;
    }
  }
  if (estable && !largo_emitido && (t - t_presion) >= BOTON_LARGO_MS) {
    largo_emitido = true;  // se emite mientras se mantiene presionado
    ev = EventoBoton::LARGO;
  }
  return ev;
}
