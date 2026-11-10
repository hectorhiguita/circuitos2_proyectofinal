// config.h - Pines y constantes del firmware (ver ../SPEC.md).
#pragma once

#if __has_include("secrets.h")
#include "secrets.h"
#else
#warning "include/secrets.h no existe: usando secrets.example.h (copie y edite el archivo)"
#include "secrets.example.h"
#endif

#define FW_VERSION "1.0.0"

// -DDEMO_SENSOR=1 (entorno c3_demo): señal PPG sintética, sin tarjeta analógica.
#ifndef DEMO_SENSOR
#define DEMO_SENSOR 0
#endif

// ------------------------------------------------------------ pines ESP32-C3 SuperMini
#define PIN_PPG      1   // ADC1_CH1, punto 6 (señal acondicionada)
#define PIN_BAT      0   // ADC1_CH0, divisor 100k/100k (Vbat/2)
#define PIN_SDA      6   // solo OLED (c3_oled)
#define PIN_SCL      7
#define PIN_BUZZER   10  // base del 2N3904 vía 1k, activo en alto
#define PIN_BOTON    9   // BOOT, activo en bajo
#define PIN_LED      8   // LED azul de la placa, activo en bajo

// Pantalla: TFT 1.3" ST7789 240x240 SPI (por defecto) u OLED 0.96" SSD1306 I2C (-DPANTALLA_TFT=0)
#ifndef PANTALLA_TFT
#define PANTALLA_TFT 1
#endif
#define TFT_SCK      4
#define TFT_MOSI     6   // "SDA" en la serigrafía del módulo
#define TFT_DC       7
#define TFT_RST      5
#define TFT_BLK      3   // luz de fondo (PWM)
#define TFT_BRILLO   200 // 0..255
#define TFT_ROTACION 0   // 0..3 según cómo quede montada
#define TFT_PERIODO_MS 80

#define OLED_ADDR    0x3C
#define OLED_W       128
#define OLED_H       64

// ------------------------------------------------------------ muestreo
#define FS_HZ             200   // frecuencia de muestreo
#define ADC_PROMEDIO      8     // lecturas promediadas por muestra
#define BAT_DIVISOR       2.0f  // 100k/100k
#define BAT_V_BAJA        3.40f // LiPo 1S: aviso de batería baja
#define DECIMACION_ONDA   4     // 200 Hz / 4 = 50 Hz (MQTT "onda" y pantalla)

// Polaridad: en transmisión la sístole BAJA la tensión del fotodiodo -> invertir.
#ifndef INVERTIR_SENAL
#define INVERTIR_SENAL    1
#endif

// ------------------------------------------------------------ indicadores
#define BEEP_MS           30
#define LED_MS            60
#define BOTON_LARGO_MS    800

// ------------------------------------------------------------ alertas / config por defecto
#define BPM_MIN_DEF       50
#define BPM_MAX_DEF       120
#define BUZZER_DEF        true

// ------------------------------------------------------------ red
#define MQTT_PREFIJO      "pulso/"
#define WIFI_REINTENTO_MS 15000
#define MQTT_REINTENTO_MS 5000

// ------------------------------------------------------------ batería LiPo 1S (TP4056)
// Curva de descarga típica LiPo a carga baja: 4.20 V = 100 %, 3.30 V = 0 %.
static inline int bateria_pct(float v) {
  static const float tv[] = {3.30f, 3.50f, 3.60f, 3.70f, 3.75f, 3.80f, 3.85f, 3.95f, 4.05f, 4.20f};
  static const int   tp[] = {0,     5,     10,    20,    30,    40,    50,    70,    85,    100};
  const int n = sizeof(tv) / sizeof(tv[0]);
  if (v <= tv[0]) return 0;
  if (v >= tv[n - 1]) return 100;
  for (int i = 1; i < n; i++) {
    if (v < tv[i]) return tp[i - 1] + (int)((v - tv[i - 1]) / (tv[i] - tv[i - 1]) * (tp[i] - tp[i - 1]) + 0.5f);
  }
  return 100;
}

// ------------------------------------------------------------ depuración serie
// 0 = registro legible 1 Hz, 1 = CSV para el graficador serie (tecla 'p' alterna)
#ifndef SERIAL_PLOT_DEF
#define SERIAL_PLOT_DEF   0
#endif
