# Medidor de ritmo cardiaco PPG — Proyecto final Circuitos Eléctricos II (ITM)

LED IR + fotodiodo → LM324 (6 etapas) → ESP32-C3 SuperMini → OLED + buzzer → MQTT → tablero + alertas por correo y WhatsApp.

| Carpeta | Contenido | Estado |
|---|---|---|
| `SPEC.md` | Especificación: pines, valores, contrato MQTT | ✅ |
| `01_analogico/` | Netlist ngspice, simulación, gráficas | ✅ simulado |
| `02_pcb/` | KiCad 10: esquema, PCB, Gerbers JLCPCB, BOM | ✅ DRC 0 errores |
| `03_firmware/` | PlatformIO (ESP32-C3) | ✅ compila, 13 pruebas OK |
| `04_iot/` | Mosquitto + Node-RED (tablero, alertas) + simulador | ✅ probado con simulador |
| `05_carcasa/` | OpenSCAD + STL | ✅ STL listos |
| `06_informe/` | Informe escrito | ✅ borrador (faltan fotos y medidas reales) |

## Lista de compras
| # | Pieza | Cant | Nota |
|---|---|---|---|
| 1 | ESP32-C3 SuperMini | 1 | USB-C |
| 2 | OLED 0.96" I2C SSD1306 (4 pines) | 1 | dirección 0x3C |
| 3 | LM324N (DIP-14) + zócalo DIP-14 | 1 | |
| 4 | LED IR 940 nm 5 mm | 1 | |
| 5 | Fotodiodo IR 5 mm (o BPW34) | 1 | **no** fototransistor |
| 6 | Batería LiPo BL-3.7V-1000-25C (68×34×6 mm) | 1 | cortar el conector rojo y soldar al TP4056 |
| 7 | Módulo TP4056 USB-C con protección (DW01) | 1 | |
| 8 | Módulo elevador MT3608 | 1 | ajustar a 5.0 V |
| 9 | Interruptor deslizante SS12D00 | 1 | |
| 10 | Buzzer activo 5 V, 12 mm | 1 | |
| 11 | Trimmer multivuelta 3296W 200 kΩ | 1 | |
| 12 | Condensador film (MKT) 1 µF 63 V | 3 | paso 5 mm |
| 13 | Condensador film 470 nF 63 V | 1 | paso 5 mm |
| 14 | Electrolítico 100 µF 16 V (6.3 mm) | 3 | |
| 15 | Cerámico 100 nF | 6 | |
| 16 | Cerámico 47 nF | 1 | |
| 17 | Cerámico 10 nF | 1 | |
| 18 | Resistencias 1/4 W: 220, 1k ×3, 1.5k ×2, 4.7k, 10k ×3, 47k ×3, 100k ×2, 330k, 470k ×2 | 19 | |
| 19 | Diodo BAT85 | 2 | Schottky |
| 20 | Diodo 1N5819 | 1 | |
| 21 | Diodo 1N4148 | 1 | |
| 22 | Transistor 2N3904 | 1 | |
| 23 | Conector JST-XH 4 pines (macho PCB + hembra con cable) | 1 | sensor |
| 24 | Regleta hembra 1×8 (2.54) | 2 | zócalo SuperMini |
| 25 | Regleta macho 1×8 y 1×4 | 1+1 | J5, J4 |
| 26 | Tornillos M3 + insertos, M2, liga | — | ver `05_carcasa/README.md` |
| 27 | PCB JLCPCB 80×52 mm | 5 | `02_pcb/fab/medidor_ppg_gerbers_JLCPCB.zip` |

## Orden sugerido
1. Pedir la PCB e imprimir la carcasa (tardan más).
2. Probar firmware y tablero **sin** hardware: `03_firmware` entorno `c3_demo` + `04_iot` con simulador.
3. Soldar y validar por etapas con el osciloscopio (`02_pcb/README.md`).
4. Ajustar RV1. Probar alertas. Tomar fotos y capturas para el informe.

## Riesgos
- **Punto 6** nunca debe pasar de 2.5 V ni bajar de 0 V. Mídelo antes de poner el SuperMini.
- Ajusta el **MT3608 a 5.0 V** antes de conectar la placa.
- La LiPo debe tener protección. No la cargues sin vigilar.
- El `.env` de `04_iot` tiene claves. No lo subas a internet.
