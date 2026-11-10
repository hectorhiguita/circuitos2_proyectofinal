// red.cpp - ver red.h
#include "red.h"

#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>

#include "ajustes.h"
#include "alertas.h"
#include "config.h"
#include "muestreo.h"

#define T(x) MQTT_PREFIJO DEVICE_ID "/" x
static const char* TOP_ESTADO = T("estado");
static const char* TOP_ONDA = T("onda");
static const char* TOP_LATIDO = T("latido");
static const char* TOP_ALERTA = T("alerta");
static const char* TOP_CONFIG = T("config");
static const char* TOP_ONLINE = T("online");

static WiFiClient wcli;
static PubSubClient mqtt(wcli);
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
static EstadoRed est = {false, false, 0, "", 0};
static char client_id[40];

static void on_mensaje(char* topic, uint8_t* payload, unsigned int len) {
  if (strcmp(topic, TOP_CONFIG) != 0) return;
  if (ajustes_aplicar_json((const char*)payload, len)) {
    const Ajustes a = ajustes_leer();
    Serial.printf("# config MQTT aplicada: bpm_min=%d bpm_max=%d buzzer=%d (guardada en NVS)\n", a.bpm_min,
                  a.bpm_max, a.buzzer);
  }
}

static bool publicar_json(const char* topic, JsonDocument& doc, bool retained = false) {
  char buf[512];
  const size_t n = serializeJson(doc, buf, sizeof(buf));
  return mqtt.publish(topic, (const uint8_t*)buf, n, retained);
}

static bool conectar_mqtt() {
  const bool auth = strlen(MQTT_USER) > 0;
  // LWT: si el equipo se cae, el broker publica online="0" retenido.
  const bool ok = mqtt.connect(client_id, auth ? MQTT_USER : nullptr, auth ? MQTT_PASS : nullptr, TOP_ONLINE, 1,
                               true, "0");
  if (!ok) {
    Serial.printf("# MQTT fallo rc=%d (%s:%d)\n", mqtt.state(), MQTT_HOST, MQTT_PORT);
    return false;
  }
  mqtt.publish(TOP_ONLINE, "1", true);
  mqtt.subscribe(TOP_CONFIG, 1);
  Serial.printf("# MQTT conectado como %s\n", client_id);
  return true;
}

static void publicar_estado() {
  const EstadoPulso e = muestreo_estado();
  JsonDocument d;
  d["bpm"] = e.bpm;
  d["dedo"] = e.dedo;
  d["senal_ok"] = e.senal_ok;
  d["bat_v"] = roundf(e.bat_v * 100.0f) / 100.0f;
  d["bat_pct"] = bateria_pct(e.bat_v);
  d["rssi"] = WiFi.RSSI();
  d["uptime"] = millis() / 1000;
  publicar_json(TOP_ESTADO, d);
}

static void tarea_red(void*) {
  const bool con_wifi = strlen(WIFI_SSID) > 0;
  uint8_t mac[6];
  WiFi.macAddress(mac);
  snprintf(client_id, sizeof(client_id), "%s-%02x%02x", DEVICE_ID, mac[4], mac[5]);

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(on_mensaje);
  mqtt.setBufferSize(768);
  mqtt.setKeepAlive(15);
  mqtt.setSocketTimeout(3);
  wcli.setTimeout(3);

  if (con_wifi) {
    WiFi.mode(WIFI_STA);
    WiFi.setAutoReconnect(true);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    // Muchas SuperMini C3 tienen antena deficiente: bajar potencia mejora la conexión.
    WiFi.setTxPower(WIFI_POWER_8_5dBm);
  } else {
    WiFi.mode(WIFI_OFF);
    Serial.println("# WIFI_SSID vacío: modo sin red");
  }

  uint32_t t_wifi = millis(), t_mqtt = 0, t_estado = 0, t_onda = 0, t_info = 0;
  uint32_t cursor = muestreo_onda_total();
  bool mqtt_antes = false;
  PuntoOnda pts[25];

  for (;;) {
    const uint32_t ahora = millis();
    const bool wifi_ok = con_wifi && WiFi.status() == WL_CONNECTED;

    // ---- supervisión WiFi (no bloqueante)
    if (con_wifi && !wifi_ok && ahora - t_wifi > WIFI_REINTENTO_MS) {
      t_wifi = ahora;
      Serial.println("# WiFi: reintentando...");
      WiFi.disconnect();
      WiFi.begin(WIFI_SSID, WIFI_PASS);
    }
    if (wifi_ok) t_wifi = ahora;

    // ---- MQTT
    if (wifi_ok && !mqtt.connected() && (t_mqtt == 0 || ahora - t_mqtt > MQTT_REINTENTO_MS)) {
      t_mqtt = ahora;
      if (conectar_mqtt()) {
        portENTER_CRITICAL(&mux);
        est.reconexiones++;
        portEXIT_CRITICAL(&mux);
        cursor = muestreo_onda_total();
      }
    }
    const bool mq = wifi_ok && mqtt.connected();
    if (mq) mqtt.loop();
    if (mq != mqtt_antes && !mq) Serial.println("# MQTT desconectado");
    mqtt_antes = mq;

    // ---- publicaciones
    Latido l;
    while (muestreo_sacar_latido(l)) {  // se vacía siempre (sin red se descartan)
      if (!mq) continue;
      JsonDocument d;
      d["t"] = l.t;
      d["ibi"] = l.ibi;
      d["bpm"] = l.bpm;
      publicar_json(TOP_LATIDO, d);
    }
    ppg::AlertEvent a;
    while (alertas_sacar(a)) {
      if (!mq) continue;
      JsonDocument d;
      d["tipo"] = ppg::alertName(a.type);
      d["bpm"] = a.bpm;
      d["umbral"] = a.umbral;
      publicar_json(TOP_ALERTA, d);
    }
    if (mq && ahora - t_estado >= 1000) {
      t_estado = ahora;
      publicar_estado();
    }
    if (!mq) {
      cursor = muestreo_onda_total();
    } else if (ahora - t_onda >= 250) {
      t_onda = ahora;
      // Si hubo un atasco, salta al final para no acumular retraso.
      if (muestreo_onda_total() - cursor > 100) cursor = muestreo_onda_total() - 25;
      while (muestreo_onda_total() - cursor >= 25) {
        const size_t n = muestreo_leer_onda(cursor, pts, 25);
        JsonDocument d;
        d["t0"] = pts[0].t;
        d["fs"] = 1000 / (1000 / FS_HZ * DECIMACION_ONDA);
        JsonArray v = d["v"].to<JsonArray>();
        for (size_t i = 0; i < n; i++) v.add(pts[i].filt);
        publicar_json(TOP_ONDA, d);
      }
    }

    // ---- estado para la pantalla (llamadas a WiFi fuera de la sección crítica)
    if (ahora - t_info >= 1000 || wifi_ok != est.wifi || mq != est.mqtt) {
      t_info = ahora;
      const int rssi = wifi_ok ? WiFi.RSSI() : 0;
      char ip[16] = "";
      if (wifi_ok) WiFi.localIP().toString().toCharArray(ip, sizeof(ip));
      portENTER_CRITICAL(&mux);
      est.wifi = wifi_ok;
      est.mqtt = mq;
      est.rssi = rssi;
      memcpy(est.ip, ip, sizeof(ip));
      portEXIT_CRITICAL(&mux);
    }

    vTaskDelay(pdMS_TO_TICKS(10));
  }
}

void red_iniciar() { xTaskCreate(tarea_red, "red", 8192, nullptr, 2, nullptr); }

EstadoRed red_estado() {
  portENTER_CRITICAL(&mux);
  EstadoRed e = est;
  portEXIT_CRITICAL(&mux);
  return e;
}
