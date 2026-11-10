# Resultados de simulación (ngspice)

Modelo LM324: GBW 1 MHz, salida 0.02 V a VCC−1.5 V. Entrada: pulso ≈3.5 mVpp a 72 lpm + 60 Hz 2 mVpp.

## Respuesta en frecuencia (desde el sensor hasta el Punto 6)

| RV1 | Ganancia máx | f pico | f −3 dB baja | f −3 dB alta |
|---|---|---|---|---|
| 10k | 37.6 dB (76 V/V) | 2.39 Hz | 0.54 Hz | 5.11 Hz |
| 100k | 49.6 dB (301 V/V) | 2.41 Hz | 0.57 Hz | 5.11 Hz |
| 200k | 54.8 dB (551 V/V) | 2.41 Hz | 0.57 Hz | 5.11 Hz |

Con RV1 = 100k: ganancia a 1.2 Hz = 48.7 dB; a 60 Hz = -8.1 dB (rechazo de 56.9 dB frente al pulso).

## Transitorio (Punto 6, después de 10 s)

| Caso | Mín (V) | Máx (V) | Vpp | Media | Asentamiento |
|---|---|---|---|---|---|
| tipico | 0.907 | 1.693 | 0.786 | 1.320 | 5.9 s |
| offset 7 mV | 0.781 | 1.567 | 0.786 | 1.194 | 5.9 s |
| ganancia max + offset | 0.335 | 1.773 | 1.438 | 1.090 | 5.9 s |

VREF en régimen: 1.318 V.

Criterio: Punto 6 siempre entre 0 y 2.5 V (rango útil del ADC del ESP32-C3 con 12 dB).
