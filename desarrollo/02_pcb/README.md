# PCB — Medidor PPG (KiCad 10)

Placa 80 × 52 mm, 2 capas, todo THT. Plano GND en las dos caras. DRC: 0 errores, 0 pendientes, esquema = placa.

## Archivos
| Archivo | Qué es |
|---|---|
| `medidor_ppg.kicad_pro` | Abrir en KiCad |
| `fab/medidor_ppg_gerbers_JLCPCB.zip` | Subir a JLCPCB tal cual |
| `fab/medidor_ppg_BOM.csv` | Lista de piezas de la placa |
| `fab/medidor_ppg_esquema.pdf` | Esquema para el informe |
| `fab/medidor_ppg_montaje_superior.pdf` | Guía de montaje (cara superior) |
| `img/*.png` | Vistas 3D |
| `componentes.py` | Netlist (fuente única) |
| `generar_esquema.py`, `generar_pcb.py`, `fabricar.sh` | Regeneran todo |

Regenerar: `python3 generar_esquema.py && python3 generar_pcb.py && ./fabricar.sh`.
**Riesgo:** `generar_pcb.py` sobrescribe la placa. Si la editas a mano en KiCad, no lo vuelvas a correr.

## Opción sin PCB: baquela perforada 9 × 7 cm
Todas las huellas usan paso de 2.54 mm. Por eso la misma ubicación sirve en baquela universal (35 × 27 agujeros). Ocupa 32 × 19 agujeros.

| Archivo | Uso |
|---|---|
| `perforada/vista_componentes.pdf` | Imprimir al **100 %**, pegar sobre la baquela y pinchar las piezas |
| `perforada/vista_soldadura.pdf` | Vista desde abajo (espejada). Cada línea = un cable |
| `perforada/conexiones.md` | 99 conexiones con casilla para marcar. Ej.: `R15.1 (R5) → C12.1 (P19)` |

Columnas = letras, filas = números (como un tablero de ajedrez). Usa cable de wire-wrap o hilos de UTP. GND, +5V y +3V3 con cable más grueso.
Regenerar: `python3 perforada.py`.

## Pedido en JLCPCB
2 capas, 80×52 mm, 1.6 mm, HASL, cualquier color. 5 placas cuestan ~2 USD más el envío.

## Antes de soldar: verifica con el calibrador
1. **SuperMini:** filas a **15.24 mm**. Pon la placa sobre la serigrafía. El pin `5V` debe quedar del lado del USB, en la fila de arriba.
   Si los pines quedan al revés, se puede montar el SuperMini boca abajo: así se cruzan las filas y el orden se mantiene.
2. **Buzzer:** la pata `+` va en el pad cuadrado.

## Orden de soldadura (de bajo a alto)
1. Resistencias (paradas) y diodos. `K` en la serigrafía = cátodo (raya).
2. Zócalo DIP-14 (muesca hacia arriba en la serigrafía). El LM324 va al final.
3. Condensadores cerámicos, puntos de prueba TP1–TP7.
4. Transistor 2N3904 (cara plana como la serigrafía), trimmer RV1.
5. Condensadores de film, electrolíticos (pata larga `+`), conectores, zócalos del SuperMini y buzzer.

## Conector de energía J5 (cables al piso de la caja)
| Pin | Va a |
|---|---|
| 1 B+ | TP4056 OUT+ |
| 2 SWa | Interruptor, pata 1 |
| 3 SWb | Interruptor, pata común |
| 4 MT+ | MT3608 IN+ |
| 5 B− | TP4056 OUT− |
| 6 MT− | MT3608 IN− |
| 7 5V | MT3608 OUT+ |
| 8 G | MT3608 OUT− |

La batería va a B+ / B− del **TP4056**, no a la placa.

## Sensor J1 (JST-XH 4, hacia la pinza)
| Pin | Va a |
|---|---|
| 1 LED+ | Ánodo del LED IR (pata larga) |
| 2 LED− | Cátodo del LED IR |
| 3 PD-K | Cátodo del fotodiodo (pata corta / lado plano) |
| 4 PD-A | Ánodo del fotodiodo |

Usa cable apantallado o trenzado. La malla va a GND.

## Prueba por etapas (lo pide la guía)
1. **Sin LM324 ni SuperMini:** conecta la LiPo y ajusta el MT3608 a **5.00 V** en el pin 7 de J5.
2. Pon el SuperMini sin el LM324. Mide **3.3 V** en el pin 3V3 y **1.32 V** en TP6.
3. Pon el LM324, con el dedo en la pinza. Mira cada punto con el osciloscopio:

| TP | Etapa | Esperado |
|---|---|---|
| TP1 | Sensor | DC 0.1–1 V, pulso de pocos mV |
| TP2 | Buffer | ≈1.32 V con el pulso encima |
| TP3 | Preamp ×34 | ≈1.32 V, pulso ≈0.1 Vpp |
| TP4 | Sallen-Key | Igual, más suave |
| TP5 | **Punto 6** | 1.32 V ± 0.5 V. Nunca < 0 V ni > 2.5 V |
| TP7 | GND | Tierra del osciloscopio |

4. Ajusta RV1 hasta ver **0.8–1.6 Vpp** en TP5.
