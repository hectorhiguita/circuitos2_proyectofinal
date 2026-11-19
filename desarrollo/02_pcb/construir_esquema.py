#!/usr/bin/env python3
"""Construye el esquema por bloques (opcion B).

Todos los pasivos van VERTICALES (rot=0): asi sus dos pines caen EXACTO en la
rejilla (como el generador original validado con ERC) y la etiqueta de cada pin
cae sobre el pin correcto -> el netlist sale identico a componentes.py.
El flujo de senal (izquierda->derecha) lo da la POSICION de los bloques, no la
orientacion de cada componente. Cada pin se termina con S.term(net,...)
(etiqueta de red o simbolo de potencia). Op-amps y conectores con dirs explicitos.

Fuente de verdad: componentes.py.
"""
from pathlib import Path
import esq_bloques_lib as L
from esq_bloques_lib import Sheet, header, footer, NOMBRE
from componentes import COMPONENTES

BYREF = {c["ref"]: c for c in COMPONENTES}
S = Sheet(); P = S.P; header(P)

def net_of(ref, pin): return BYREF[ref]["nets"].get(pin)

def place(ref, x, y, unit=None, rot=0, mirror=None, dirs=None, stub=3.81):
    pins = S.comp(ref, x, y, unit=unit, rot=rot, mirror=mirror)
    for pin, (px, py) in pins.items():
        net = net_of(ref, pin)
        if net is None:
            S.nc(px, py); continue
        d = (dirs or {}).get(pin, "auto")
        S.term(net, px, py, dir=d, body=(x, y), stub=stub)
    return pins


# ===================== titulo =====================
S.txt("MEDIDOR DE RITMO CARDIACO PPG   (LM324 + ESP32-C3)", 25, 18, 3.0)
S.txt("Cadena:  J1 sensor -> C1 acople -> U1A buffer -> U1B preamp -> U1C Sallen-Key -> U1D salida -> R10/D2/D3 proteccion -> ADC (GPIO1)", 25, 24, 1.8, False)
S.txt("Buses +5V/+3V3/GND por simbolo de potencia; senales entre etapas y VREF1/VREF2 por etiqueta. Mismo netlist que la PCB (ERC y simulacion sin cambios).", 25, 28, 1.5, False)
S.txt("Rieles externos:", 25, 37, 1.6, False)
for i, net in enumerate(["+5V", "+3V3", "GND"]):
    S.add(L.flag(net, 66 + i*18, 36))

# Todas las columnas separadas >=20mm; pasivos verticales.
# ---------- 1  Sensor ----------
S.box(22, 54, 150, 132, "1  Sensor optico (pinza)")
place("J1", 70, 86, dirs={"1":"L","2":"L","3":"L","4":"R"}, stub=7.62)
place("R1", 44, 72)          # 1=+5V(arriba) 2=LED_A(abajo)
place("R2", 110, 104)        # 1=SENS(arriba) 2=GND(abajo)
place("TP1", 128, 80, dirs={"1":"D"})

# ---------- 2  Acople + referencias ----------
S.box(154, 54, 268, 170, "2  Acople AC (C1,R3) + referencias VREF1/VREF2 = 1.32 V")
place("C1", 176, 86)         # 1=SENS 2=N1
place("R3", 200, 108)        # 1=N1 2=VREF1
place("R15", 232, 72)        # +3V3 - VREF1
place("R16", 232, 92)        # VREF1 - GND
place("R17", 232, 120)       # +3V3 - VREF2
place("R18", 232, 140)       # VREF2 - GND

# ---------- 3  Buffer U1A ----------
S.box(272, 54, 352, 124, "3  Buffer U1A (x1)")
place("U1", 312, 92, unit=1, dirs={"3":"L","2":"U","1":"R"})
place("TP2", 338, 78, dirs={"1":"D"})

# ---------- 4  Preamp U1B ----------
S.box(356, 54, 452, 140, "4  Preamp U1B (R4,R5,C5)  A=31")
place("U1", 410, 92, unit=2, dirs={"5":"L","6":"U","7":"R"})
place("R4", 376, 118)        # INV1 - VREF1
place("R5", 392, 72)         # PRE - INV1
place("C5", 376, 72)         # PRE - INV1
place("TP3", 440, 78, dirs={"1":"D"})

# ---------- 5  Sallen-Key U1C ----------
S.box(456, 54, 584, 148, "5  Sallen-Key U1C (R6,R7,C2,C3)  fc=4.9 Hz")
place("R6", 472, 76)         # PRE - SKA
place("R7", 496, 76)         # SKA - SKB
place("C2", 520, 112)        # SKB - GND
place("C3", 484, 110)        # SKA - SKO
place("U1", 556, 92, unit=3, dirs={"10":"L","9":"U","8":"R"})
place("TP4", 580, 78, dirs={"1":"D"})

# ---------- 6  Salida U1D ----------
S.box(588, 54, 744, 170, "6  Salida U1D (C8,R11->VREF2, R8/R9/RV1, C9)")
place("C8", 608, 92)         # SKO - N2
place("R11", 632, 116)       # N2 - VREF2
place("U1", 672, 92, unit=4, dirs={"12":"L","13":"U","14":"R"})
place("R9", 648, 70)         # P6 - X9
place("RV1", 700, 70, dirs={"1":"U","2":"R","3":"D"})  # 1=X9 2,3=INV2
place("R8", 648, 116)        # INV2 - VREF2
place("C9", 724, 70)         # P6 - INV2
place("TP5", 724, 110, dirs={"1":"D"})

# ---------- LM324 alim ----------
S.box(748, 54, 806, 124, "LM324 alim.")
place("U1", 769, 86, unit=5, dirs={"4":"U","11":"D"})
place("C10", 794, 86)        # +5V - GND

# ===================== FILA DIGITAL =====================
# ---------- 7  Proteccion ADC ----------
S.box(22, 178, 170, 252, "7  Proteccion ADC  P6 -> R10 -> ADC (GPIO1)")
place("R10", 52, 206)        # P6 - ADC
place("C7", 92, 220)         # ADC - GND
place("D2", 124, 202)        # +3V3(K) - ADC(A)
place("D3", 148, 220)        # ADC(K) - GND(A)

# ---------- 8  ESP32-C3 + TFT + buzzer ----------
S.box(174, 178, 430, 284, "8  ESP32-C3 SuperMini (J2,J3), TFT 1.3 (J4), buzzer")
place("J2", 210, 210, dirs={k:"L" for k in "12345678"}, stub=7.62)
place("J3", 262, 210, dirs={k:"L" for k in "12345678"}, stub=7.62)
place("J4", 336, 214, dirs={k:"L" for k in "1234567"}, stub=7.62)
place("R12", 244, 256)       # BUZ - QB
place("Q1", 284, 254, dirs={"1":"D","2":"L","3":"U"})
place("BZ1", 326, 250)       # +5V - BZK
place("D4", 360, 256)        # +5V(K) - BZK(A)
place("C12", 400, 256)       # +3V3 - GND

# ---------- 9  Energia J5 ----------
S.box(434, 178, 596, 284, "9  Energia: LiPo->TP4056->SW->MT3608 5V (J5)")
place("J5", 470, 210, dirs={k:"L" for k in "12345678"}, stub=7.62)
place("D1", 512, 206)        # +5V(K) - +5V_B(A)
place("C11", 540, 210)       # +5V - GND
place("R13", 566, 196)       # VSW - VBAT_S
place("R14", 566, 220)       # VBAT_S - GND
place("C17", 586, 210)       # VBAT_S - GND

# ---------- desacoplo VREF + TP + agujeros ----------
S.box(600, 178, 744, 268, "Desacoplo VREF, TP y agujeros M3")
place("C13", 616, 206)       # VREF1 - GND
place("C14", 636, 206)       # VREF1 - GND
place("C15", 664, 206)       # VREF2 - GND
place("C16", 684, 206)       # VREF2 - GND
place("TP6", 616, 234, dirs={"1":"D"})   # VREF1
place("TP7", 640, 234, dirs={"1":"D"})   # GND
for i, ref in enumerate(["H1", "H2", "H3", "H4"]):
    place(ref, 680 + i*14, 234, dirs={"1":"D"})

footer(P)
Path(NOMBRE + ".kicad_sch").write_text("".join(P), encoding="utf-8")
print("esquema por bloques escrito")
