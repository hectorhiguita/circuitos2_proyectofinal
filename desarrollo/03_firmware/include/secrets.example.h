// secrets.example.h - PLANTILLA. Copie a include/secrets.h y edite:
//   cp include/secrets.example.h include/secrets.h
// include/secrets.h está en .gitignore (no se sube al repositorio).
// Con WIFI_SSID vacío el equipo funciona solo sin red (OLED + BPM + buzzer).
#pragma once

#define WIFI_SSID  "MiRedWiFi"
#define WIFI_PASS  "MiClaveWiFi"

#define MQTT_HOST  "192.168.1.100"   // IP del PC con mosquitto (04_iot)
#define MQTT_PORT  1883
#define MQTT_USER  ""                // vacío = sin autenticación
#define MQTT_PASS  ""

#define DEVICE_ID  "medidor01"       // tópicos: pulso/<DEVICE_ID>/...
