// pantalla.h - OLED SSD1306 128x64 I2C (SDA=GPIO6, SCL=GPIO7, 0x3C).
// Pantallas (botón BOOT, pulsación corta):
//   0 Principal: barra de estado (WiFi, MQTT, silencio, batería), BPM grande,
//     corazón que late y onda desplazándose.
//   1 Detalles: IBI, amplitud, DC, límites de alerta, recorte.
//   2 Red: SSID, IP, RSSI, MQTT, id del equipo, tiempo encendido.
#pragma once
#include <Arduino.h>

bool pantalla_iniciar();          // false si no se detecta la OLED (el resto sigue funcionando)
void pantalla_siguiente();
void pantalla_dibujar(uint32_t ahora_ms);  // ~20 fps desde loop()
void pantalla_mensaje(const char* l1, const char* l2);
