// muestreo.cpp - ver muestreo.h
#include "muestreo.h"

#include "config.h"
#include "indicadores.h"
#include "ppg_dsp.h"
#if DEMO_SENSOR
#include "ppg_synth.h"
#endif

#if configTICK_RATE_HZ != 1000
#error "Se requiere configTICK_RATE_HZ = 1000 (5 ms exactos por muestra)"
#endif

static ppg::PpgProcessor proc;
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

static PuntoOnda onda[ONDA_LEN];
static volatile uint32_t onda_n = 0;  // nº total de puntos escritos
static QueueHandle_t cola_latidos;
static EstadoPulso estado = {};

#if DEMO_SENSOR
// ---------------------------------------------------------------- señal sintética
static ppg::PpgSynth synth(0xC0FFEE);
// Perfil de 240 s que recorre las alertas: normal, taquicardia sostenida,
// bajada rápida, bradicardia y retiro del dedo.
struct Tramo { float t_s, bpm; };
static const Tramo perfil[] = {{0, 72},   {50, 72},  {70, 135}, {110, 135}, {120, 85},
                               {150, 85}, {165, 45}, {195, 45}, {205, 72},  {240, 72}};
static float demo_bpm(float t) {
  const int n = sizeof(perfil) / sizeof(perfil[0]);
  for (int i = 0; i < n - 1; i++)
    if (t < perfil[i + 1].t_s)
      return perfil[i].bpm + (perfil[i + 1].bpm - perfil[i].bpm) * (t - perfil[i].t_s) / (perfil[i + 1].t_s - perfil[i].t_s);
  return perfil[n - 1].bpm;
}
static float leer_ppg_mv(uint32_t t_ms) {
  const float ts = (float)(t_ms % 240000u) / 1000.0f;
  const bool dedo = !(ts >= 215.0f && ts < 228.0f);  // 13 s sin dedo -> alerta "sin_senal"
  synth.setBpm(demo_bpm(ts));
  return synth.next(dedo);
}
static float leer_bat_v() { return 3.92f; }
#else
// ---------------------------------------------------------------- ADC real
static float leer_ppg_mv(uint32_t) {
  uint32_t acc = 0;
  for (int i = 0; i < ADC_PROMEDIO; i++) acc += analogReadMilliVolts(PIN_PPG);
  return (float)acc / ADC_PROMEDIO;
}
static float leer_bat_v() {
  uint32_t acc = 0;
  for (int i = 0; i < ADC_PROMEDIO; i++) acc += analogReadMilliVolts(PIN_BAT);
  return (float)acc / ADC_PROMEDIO * BAT_DIVISOR / 1000.0f;
}
#endif

static void tarea_muestreo(void*) {
  const TickType_t periodo = pdMS_TO_TICKS(1000 / FS_HZ);
  TickType_t ultimo = xTaskGetTickCount();
  const uint32_t t0 = millis();
  uint32_t n = 0, dec = 0, retrasos = 0;
  float bat = leer_bat_v();
  uint8_t inicio_pend = 0;

  for (;;) {
    // vTaskDelayUntil devuelve pdFALSE si ya íbamos tarde (periodo perdido).
    if (xTaskDelayUntil(&ultimo, periodo) == pdFALSE) retrasos++;
    const uint32_t t = t0 + n * (1000 / FS_HZ);  // base de tiempo exacta del muestreo
    n++;

    const float mv = leer_ppg_mv(t);
    ppg::Output o = proc.process(mv, t);

    if (o.onset) {
      indicadores_latido(t);
      inicio_pend = 1;
    }
    indicadores_tick(t);

    if (o.beat && o.ibi) {
      Latido l{o.beat_t, o.ibi, (uint16_t)(proc.bpmValid() ? lroundf(proc.bpm()) : lroundf(60000.0f / o.ibi))};
      xQueueSend(cola_latidos, &l, 0);  // si la cola está llena se descarta
    }

    if (n % FS_HZ == 0) bat = 0.8f * bat + 0.2f * leer_bat_v();  // batería 1 Hz

    // Punto de onda decimado a 50 Hz.
    if (++dec >= DECIMACION_ONDA) {
      dec = 0;
      PuntoOnda p{t, (int16_t)lroundf(o.raw), (int16_t)lroundf(o.filt), (int16_t)lroundf(o.hi),
                  (int16_t)lroundf(o.lo), inicio_pend};
      inicio_pend = 0;
      portENTER_CRITICAL(&mux);
      onda[onda_n % ONDA_LEN] = p;
      onda_n = onda_n + 1;
      portEXIT_CRITICAL(&mux);
    }

    // Estado compartido (barato: copia de ~40 bytes).
    portENTER_CRITICAL(&mux);
    estado.bpm_valido = proc.bpmValid();
    estado.bpm = estado.bpm_valido ? (int)lroundf(proc.bpm()) : 0;
    estado.dedo = proc.finger();
    estado.senal_ok = proc.signalOk();
    estado.recorte = proc.clipping();
    estado.amp_mv = proc.amplitude();
    estado.dc_mv = proc.dc();
    if (o.ibi) estado.ibi = o.ibi;
    if (o.onset) estado.ultimo_inicio_ms = t;
    estado.bat_v = bat;
    estado.muestras = n;
    estado.retrasos = retrasos;
    portEXIT_CRITICAL(&mux);
  }
}

void muestreo_iniciar() {
#if !DEMO_SENSOR
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);  // rango ~0-2.5 V en el C3
  pinMode(PIN_PPG, INPUT);
  pinMode(PIN_BAT, INPUT);
#endif
  ppg::Config c;
  c.fs = FS_HZ;
  c.invert = INVERTIR_SENAL;
#if DEMO_SENSOR
  c.invert = true;  // el sintetizador imita la polaridad real
#endif
  proc.init(c);
  indicadores_iniciar();
  cola_latidos = xQueueCreate(16, sizeof(Latido));
  // Prioridad alta (loop() corre en 1); pila holgada para float + ADC.
  xTaskCreate(tarea_muestreo, "muestreo", 4096, nullptr, configMAX_PRIORITIES - 3, nullptr);
}

EstadoPulso muestreo_estado() {
  portENTER_CRITICAL(&mux);
  EstadoPulso e = estado;
  portEXIT_CRITICAL(&mux);
  return e;
}

uint32_t muestreo_onda_total() { return onda_n; }

size_t muestreo_leer_onda(uint32_t& cursor, PuntoOnda* out, size_t max) {
  portENTER_CRITICAL(&mux);
  const uint32_t total = onda_n;
  if (total - cursor > ONDA_LEN) cursor = total - ONDA_LEN;  // el lector se quedó atrás
  size_t k = 0;
  while (cursor != total && k < max) out[k++] = onda[cursor++ % ONDA_LEN];
  portEXIT_CRITICAL(&mux);
  return k;
}

size_t muestreo_ultimos(PuntoOnda* out, size_t n) {
  portENTER_CRITICAL(&mux);
  const uint32_t total = onda_n;
  if (n > total) n = total;
  if (n > ONDA_LEN) n = ONDA_LEN;
  for (size_t i = 0; i < n; i++) out[i] = onda[(total - n + i) % ONDA_LEN];
  portEXIT_CRITICAL(&mux);
  return n;
}

bool muestreo_sacar_latido(Latido& l) { return xQueueReceive(cola_latidos, &l, 0) == pdTRUE; }
