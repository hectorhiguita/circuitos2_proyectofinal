# Medidor de ritmo cardiaco PPG — Especificación común (fuente de verdad)

Proyecto final Circuitos Eléctricos II (ITM). Guía: `../Filtros_proyecto_Final.pdf`, referencia del curso: `../Tablas.pdf`.
El usuario suelda y arma. Todo lo demás (diseño, PCB, firmware, IoT, carcasa, informe) se genera aquí.

## Hardware elegido
- MCU: **ESP32-C3 SuperMini** (USB-C, 4 MB flash, 3.3 V lógica, pin 5V = VBUS).
- Pantalla **TFT IPS 1.3" ST7789 240x240 SPI** (GMT130-V1.0, 7 pines GND VCC SCK SDA RES DC BLK, sin CS). Alternativa: OLED 0.96" SSD1306 I2C (entorno `c3_oled`).
- **LM324N** (DIP-14), alimentado a 5 V.
- LED **IR 940 nm 5 mm** + **fotodiodo** (BPW34 o fotodiodo IR 5 mm). Obligatorio LED+fotodiodo (si no, nota 0).
- Buzzer activo 5 V con NPN 2N3904.
- Energía (CAMBIO: recargable): batería **LiPo 1S 3.7 V** (3.0–4.2 V) BL-3.7V-1000-25C, 1000 mAh, 68x34x6 mm (sin protección propia: la da el DW01 del TP4056)
  -> módulo cargador **TP4056 USB-C con protección DW01** (≈28x17 mm; B+/B- a batería, OUT+/OUT- a carga; LED rojo cargando/azul lleno)
  -> interruptor SS12D00 -> módulo elevador **MT3608** ajustado a 5.0 V -> diodo 1N5819 -> riel +5V.
  Dos puertos USB-C en la carcasa: el del TP4056 (cargar) y el del SuperMini (programar).
  USB-C del SuperMini también alimenta el riel +5V (por su pin 5V); el 1N5819 evita retroalimentar el MT3608.
  Consumo ≈ 150 mA de batería con WiFi -> ≈ 6–7 h con 1000 mAh.
- Medición batería: divisor 100k/100k desde OUT+ del TP4056 -> GPIO0 (máx 2.1 V). 4.2 V = 100 %, 3.3 V = 0 %; aviso batería baja < 3.4 V.

## Mapa de pines ESP32-C3 SuperMini
| GPIO | Uso |
|---|---|
| GPIO1 (ADC1_CH1) | Punto 6: señal PPG acondicionada |
| GPIO0 (ADC1_CH0) | Voltaje de batería, divisor 100k/100k (Vbat/2) |
| GPIO4 | TFT SCK |
| GPIO6 | TFT SDA (MOSI) — o I2C SDA con OLED (`c3_oled`) |
| GPIO7 | TFT DC — o I2C SCL con OLED |
| GPIO5 | TFT RES |
| GPIO3 | TFT BLK (brillo PWM) |
| GPIO10 | Buzzer (base NPN vía 1k) |
| GPIO9 | Botón BOOT de la placa (uso: cambiar pantalla / silenciar) |
| GPIO8 | LED azul de la placa (activo en bajo), indicador de latido |
| 3V3 | Referencia Vref y clamp |
| 5V, GND | Riel |

No usar GPIO2/8/9 como entradas externas (pines de arranque).

## Cadena analógica (5 V, una sola fuente, todo centrado en Vref)
**Dos referencias** de 1.32 V = 3V3 · 2.2k/(3.3k+2.2k), cada una con 100 µF + 100 nF:
VREF1 (R3 y R4: entrada y preamp) y VREF2 (R11 y R8: etapa final). Si fueran una sola, la corriente
del Rg final vuelve a la entrada y baja ~4 dB la banda del pulso (verificado en simulación, v1).
Rango ADC C3 con 12 dB: 0–2.5 V. Señal útil: 1.32 V ± 1 V. Simulación y gráficas: `01_analogico/`.
Netlist fuente de verdad: `01_analogico/ppg.cir`.

| Etapa | Componentes | Valor | Resultado |
|---|---|---|---|
| 1 Sensor | LED IR: R1 220 Ω desde +5V (≈17 mA). Fotodiodo en inversa: cátodo a +5V, ánodo a R2 47 kΩ a GND (nodo = salida) | | DC 0.05–1 V, AC ≈ 0.5–5 mV |
| 2 Acoplamiento | C1 1 µF (cerámico 105 o film) serie; R3 470 kΩ a **VREF1** | fHP = 0.31 Hz (con R2) | Señal centrada en VREF1 |
| 3 Buffer U1A | seguidor | A = 1 | |
| 4 Preamp U1B | no inversor; Rf R5 300k ∥ C5 47 nF; Rg R4 10k a VREF1 | A = 31; fLP 11.3 Hz | DC = VREF1 + 31·Vos |
| 5 Sallen-Key U1C | R6 = R7 = 47 kΩ; C3 1 µF (realimentación, a salida); C2 470 nF a GND; seguidor | f0 = 4.94 Hz, Q = 0.73 (≈Butterworth) | 300 lpm = 5 Hz |
| Acople 2 | C8 1 µF film; R11 470 kΩ a **VREF2** | fHP = 0.34 Hz | borra el offset del preamp |
| 6 Final U1D | no inversor; Rf = R9 10k + RV1 200k trimmer, C9 10 nF; Rg R8 10k a VREF2 | A = 2…22 (empezar en RV1 ≈ 100k → 12) | DC = VREF2 + A·Vos |
| Protección | R10 4.7 kΩ serie; D2/D3 BAT85 a 3V3 y GND; C7 100 nF a GND | fc 340 Hz | Punto 6 -> GPIO1 |

Resultado simulado (ngspice): banda −3 dB **0.46–5.05 Hz**, ganancia 83–600 V/V (38–56 dB), 60 Hz atenuado 58 dB
frente al pulso, Punto 6 entre 0.23 y 1.83 V en el peor caso (Vos 7 mV, ganancia máxima). Asentamiento ≈ 5 s.
Sin electrolíticos en la ruta de señal: arranque rápido y sin polaridad que cuidar (C1, C8 son film MKT).
Desacople: 100 nF en VCC del LM324, 100 µF en +5V, 100 nF en 3V3.

## Señales digitales / firmware
- Muestreo 200 Hz (timer), cada muestra = promedio de 8 lecturas `analogReadMilliVolts`.
- DSP: quitar DC (EMA), pasabajas digital, detección de picos con umbral adaptativo + histéresis, periodo refractario 200 ms (300 lpm).
- BPM = mediana de los últimos 5 intervalos; válido 30–220 lpm. Detección de dedo ausente (amplitud o DC fuera de rango).
- OLED: onda desplazándose + BPM grande + corazón que late + estado WiFi/MQTT + batería.
- Buzzer: pitido de 30 ms por latido (silenciable con BOOT, pulsación larga).

## MQTT (contrato entre firmware y servidor)
Prefijo `pulso/<device_id>/` (device_id por defecto `medidor01`). JSON UTF-8.
| Tópico | Frecuencia | Payload |
|---|---|---|
| `estado` | 1 Hz | `{"bpm":72,"dedo":true,"senal_ok":true,"bat_v":2.9,"rssi":-60,"uptime":123}` |
| `onda` | 4 Hz | `{"t0":<ms>,"fs":50,"v":[mV,…25 valores]}` (onda decimada a 50 Hz) |
| `latido` | por latido | `{"t":<ms>,"ibi":830,"bpm":72}` |
| `alerta` | evento | `{"tipo":"alto"|"bajo"|"subida_rapida"|"bajada_rapida"|"sin_senal","bpm":130,"umbral":120}` |
| `config` (suscrito) | retained | `{"bpm_min":50,"bpm_max":120,"buzzer":true}` |
| `online` | LWT retained | `"1"` / `"0"` |

Alertas tempranas: BPM fuera de [bpm_min,bpm_max] sostenido 10 s; o cambio > 25 lpm en 30 s (tendencia). Enfriamiento 5 min por tipo.
El servidor (Node-RED) recalcula y envía las alertas por **correo y WhatsApp** (CallMeBot); el firmware también publica `alerta`.

## Estructura
```
desarrollo/
  SPEC.md            esta especificación
  01_analogico/      cálculos, simulación ngspice, gráficas
  02_pcb/            KiCad 10 (esquema + PCB), gerbers, BOM
  03_firmware/       PlatformIO (Arduino, esp32-c3 SuperMini)
  04_iot/            docker compose: mosquitto + node-red (dashboard, correo, WhatsApp) + simulador
  05_carcasa/        OpenSCAD + STL (carcasa y pinza)
  06_informe/        informe escrito
```
