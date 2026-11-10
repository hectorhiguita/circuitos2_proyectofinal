// alertas.cpp - ver alertas.h
#include "alertas.h"

#include "ajustes.h"
#include "indicadores.h"
#include "muestreo.h"

static ppg::AlertEngine motor;
static QueueHandle_t cola;
static ppg::AlertEvent ultima;
static uint32_t ultima_t = 0;
static bool hay_ultima = false;

void alertas_iniciar() { cola = xQueueCreate(8, sizeof(ppg::AlertEvent)); }

void alertas_actualizar(uint32_t ahora) {
  const Ajustes a = ajustes_leer();
  motor.setLimits(a.bpm_min, a.bpm_max);
  const EstadoPulso e = muestreo_estado();
  ppg::AlertEvent ev[4];
  const int n = motor.update(ahora, e.bpm_valido, e.bpm, ev, 4);
  for (int i = 0; i < n; i++) {
    Serial.printf("# ALERTA %s bpm=%d umbral=%d\n", ppg::alertName(ev[i].type), ev[i].bpm, ev[i].umbral);
    xQueueSend(cola, &ev[i], 0);
    ultima = ev[i];
    ultima_t = ahora;
    hay_ultima = true;
    indicadores_alerta();
  }
}

bool alertas_sacar(ppg::AlertEvent& ev) { return xQueueReceive(cola, &ev, 0) == pdTRUE; }

bool alertas_reciente(uint32_t ahora, uint32_t ventana, ppg::AlertEvent& ev) {
  if (!hay_ultima || (ahora - ultima_t) > ventana) return false;
  ev = ultima;
  return true;
}
