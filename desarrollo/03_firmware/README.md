# Firmware — Medidor de ritmo cardiaco (ESP32-C3 SuperMini)

PlatformIO + Arduino. Especificación: `../SPEC.md`.

## Entornos
| Entorno | Uso |
|---|---|
| `c3` | Firmware real con TFT 1.3". Lee el Punto 6 en GPIO1 |
| `c3_oled` | Igual, pero con OLED 0.96" I2C |
| `c3_demo` | Señal PPG sintética. Sirve para probar OLED, buzzer y MQTT sin la tarjeta analógica |
| `native` | Pruebas del DSP en el PC |

## Instalar PlatformIO (sin sudo)
```bash
python3 -m venv ~/.platformio-venv
~/.platformio-venv/bin/pip install platformio
alias pio=~/.platformio-venv/bin/pio
```

## Configurar
```bash
cp include/secrets.example.h include/secrets.h
# editar WIFI_SSID, WIFI_PASS, MQTT_HOST (IP del PC con el servidor), MQTT_USER, MQTT_PASS, DEVICE_ID
```
Sin WiFi el equipo funciona igual: OLED, BPM y buzzer.

## Compilar, probar y grabar
```bash
pio test -e native          # pruebas DSP (13 casos)
pio run -e c3               # compilar
pio run -e c3 -t upload     # grabar
pio device monitor          # ver el registro (115200)
```
Si no graba: mantener **BOOT**, pulsar **RST**, soltar BOOT. Luego `upload` otra vez.

## Pines
| GPIO | Función |
|---|---|
| 1 | Punto 6 (ADC) |
| 0 | Batería LiPo (divisor 100k/100k) |
| 4 / 6 / 7 / 5 / 3 | TFT SCK / SDA / DC / RES / BLK |
| 6 / 7 | OLED SDA / SCL (solo `c3_oled`) |
| 10 | Buzzer (NPN) |
| 9 | Botón BOOT: corto = cambiar pantalla, largo = silencio |
| 8 | LED azul, parpadea en cada latido |

## Calibrar el trimmer RV1
1. Grabar `c3` y abrir el monitor serie. Pulsar `p` para modo CSV.
2. Abrir el graficador serie (VS Code "Serial Plotter" o Arduino IDE).
3. Dedo en la pinza. Girar RV1 hasta que la onda mida **0.8–1.6 Vpp**, sin tocar 0 V ni 2.5 V.
4. Si sale `recorte=1` en el registro, bajar la ganancia.

## Batería
LiPo 1S: 4.20 V = 100 %, 3.30 V = 0 % (curva de descarga). Por debajo de 3.40 V el icono parpadea. El valor `bat_pct` sale en el tópico `estado`.

## Uso medido
RAM 14 % (45.8 kB), Flash 58.5 % (1.15 MB de 1.97 MB).
