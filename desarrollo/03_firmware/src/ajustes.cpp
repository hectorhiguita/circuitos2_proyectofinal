// ajustes.cpp - ver ajustes.h
#include "ajustes.h"

#include <ArduinoJson.h>
#include <Preferences.h>

#include "config.h"

static Preferences prefs;
static SemaphoreHandle_t mtx;
static Ajustes actual = {BPM_MIN_DEF, BPM_MAX_DEF, BUZZER_DEF, false};
static volatile bool pitido = BUZZER_DEF;

static void guardar() {
  prefs.putInt("bpm_min", actual.bpm_min);
  prefs.putInt("bpm_max", actual.bpm_max);
  prefs.putBool("buzzer", actual.buzzer);
  prefs.putBool("silencio", actual.silencio);
}

void ajustes_iniciar() {
  mtx = xSemaphoreCreateMutex();
  prefs.begin("pulso", false);
  actual.bpm_min = prefs.getInt("bpm_min", BPM_MIN_DEF);
  actual.bpm_max = prefs.getInt("bpm_max", BPM_MAX_DEF);
  actual.buzzer = prefs.getBool("buzzer", BUZZER_DEF);
  actual.silencio = prefs.getBool("silencio", false);
  if (actual.bpm_min < 30 || actual.bpm_max > 220 || actual.bpm_min >= actual.bpm_max) {
    actual.bpm_min = BPM_MIN_DEF;
    actual.bpm_max = BPM_MAX_DEF;
  }
  pitido = actual.buzzer && !actual.silencio;
}

Ajustes ajustes_leer() {
  xSemaphoreTake(mtx, portMAX_DELAY);
  Ajustes a = actual;
  xSemaphoreGive(mtx);
  return a;
}

bool ajustes_pitido_activo() { return pitido; }

bool ajustes_aplicar_json(const char* json, size_t len) {
  JsonDocument doc;
  if (deserializeJson(doc, json, len)) return false;
  xSemaphoreTake(mtx, portMAX_DELAY);
  Ajustes n = actual;
  if (doc["bpm_min"].is<int>()) n.bpm_min = doc["bpm_min"].as<int>();
  if (doc["bpm_max"].is<int>()) n.bpm_max = doc["bpm_max"].as<int>();
  if (doc["buzzer"].is<bool>()) n.buzzer = doc["buzzer"].as<bool>();
  bool ok = n.bpm_min >= 30 && n.bpm_max <= 220 && n.bpm_min < n.bpm_max;
  bool cambio = ok && (n.bpm_min != actual.bpm_min || n.bpm_max != actual.bpm_max || n.buzzer != actual.buzzer);
  if (cambio) {  // solo escribe NVS si cambió (desgaste de flash)
    actual = n;
    guardar();
    pitido = actual.buzzer && !actual.silencio;
  }
  xSemaphoreGive(mtx);
  return cambio;
}

void ajustes_set_silencio(bool s) {
  xSemaphoreTake(mtx, portMAX_DELAY);
  if (actual.silencio != s) {
    actual.silencio = s;
    guardar();
  }
  pitido = actual.buzzer && !actual.silencio;
  xSemaphoreGive(mtx);
}
