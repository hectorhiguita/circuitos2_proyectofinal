#!/usr/bin/env python3
"""Genera medidor_ppg.kicad_sch (KiCad 10) con DIBUJO POR BLOQUES.

Cada etapa se coloca A MANO (posiciones fijas, no ruteo automatico) y se conecta
con CABLES RECTOS reales entre pines. La senal fluye de izquierda a derecha:

  J1 sensor -> C1 acople -> U1A buffer -> U1B preamp -> U1C Sallen-Key
            -> U1D salida -> R10/diodos proteccion -> ADC (J2 ESP32-C3)

Buses de alimentacion y referencia (+5V, +3V3, GND, VREF1, VREF2) van por simbolo
de potencia / etiqueta local, como en cualquier esquema de libro. Redes que cruzan
toda la hoja (ADC, BUZ, TFT_*, VBAT_S, ...) van por etiqueta.

El NETLIST es identico a componentes.py -> PCB, ERC y simulacion NO cambian.
Solo cambia como se VE el esquema.
"""
import math
import uuid
from collections import OrderedDict
from datetime import date
from pathlib import Path

from componentes import COMPONENTES, POTENCIA
from lib_pins import get_pins, pin_xy
import generar_esquema as base   # inst(), def_plana(), unidades()

NOMBRE = "medidor_ppg"
ROOT_UUID = "00000000-0000-0000-0000-0000000000a1"
GRID = 1.27
_NS = uuid.UUID("5e1a0000-0000-4000-8000-00000000a1a1")
BYREF = {c["ref"]: c for c in COMPONENTES}


def snap(v):
    return round(v / GRID) * GRID


def f(v):
    return f"{float(v):.4f}"


def uid():
    return str(uuid.uuid4())


def suid(k):
    return str(uuid.uuid5(_NS, k))


# ---------------- primitivas ----------------

def wire(x1, y1, x2, y2):
    if (snap(x1), snap(y1)) == (snap(x2), snap(y2)):
        return ""
    return (f'  (wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)}))'
            f' (stroke (width 0) (type default)) (uuid "{uid()}"))\n')


def junction(x, y):
    return f'  (junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0) (uuid "{uid()}"))\n'


def label(n, x, y, rot=0, just="left"):
    return (f'  (label "{n}" (at {f(x)} {f(y)} {rot}) (effects (font (size 1.27 1.27))'
            f' (justify {just} bottom)) (uuid "{uid()}"))\n')


def no_connect(x, y):
    return f'  (no_connect (at {f(x)} {f(y)}) (uuid "{uid()}"))\n'


def texto(t, x, y, sz=1.8, bold=True, just="left"):
    b = " bold" if bold else ""
    return (f'  (text "{t}" (at {f(x)} {f(y)} 0) (effects (font (size {sz} {sz}){b})'
            f' (justify {just})) (uuid "{uid()}"))\n')


def rect(x1, y1, x2, y2):
    return (f'  (rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)})'
            f' (stroke (width 0.2) (type dash)) (fill (type none)) (uuid "{uid()}"))\n')


_pc = [0]


def potencia(net, x, y, rot=None):
    _pc[0] += 1
    ref = f"#PWR{_pc[0]:03d}"
    if rot is None:
        rot = 0 if net == "GND" else 180
    voff = 3 if net == "GND" else -3
    return (f'  (symbol (lib_id "power:{net}") (at {f(x)} {f(y)} {rot}) (unit 1)\n'
            f'    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Value" "{net}" (at {f(x)} {f(y + voff)} 0) (effects (font (size 1 1))))\n'
            f'    (property "Footprint" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Datasheet" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            + base.inst(ref) + '  )\n')


def flag(net, x, y):
    x, y = snap(x), snap(y)
    _pc[0] += 1
    ref = f"#FLG{_pc[0]:03d}"
    s = (f'  (symbol (lib_id "power:PWR_FLAG") (at {f(x)} {f(y)} 0) (unit 1)\n'
         f'    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")\n'
         f'    (property "Reference" "{ref}" (at {f(x)} {f(y - 3)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
         f'    (property "Value" "PWR_FLAG" (at {f(x)} {f(y - 4)} 0) (effects (font (size 1 1))))\n'
         f'    (property "Footprint" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
         f'    (property "Datasheet" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
         + base.inst(ref) + '  )\n')
    return s + wire(x, y, x, y + 2.54) + potencia(net, x, y + 2.54)


def simbolo(ref, x, y, unit=1, rot=0, mirror=None):
    c = BYREF[ref]
    lib_id = f'{c["lib"]}:{c["name"]}'
    m = f' (mirror {mirror})' if mirror else ""
    return (f'  (symbol (lib_id "{lib_id}") (at {f(x)} {f(y)} {rot}){m} (unit {unit})\n'
            f'    (exclude_from_sim no) (in_bom {"yes" if c["bom"] else "no"}) (on_board yes) (dnp no)\n'
            f'    (uuid "{suid(ref + "/" + str(unit))}")\n'
            f'    (property "Reference" "{ref}" (at {f(x + 2.6)} {f(y - 1.0)} 0) (effects (font (size 1.1 1.1)) (justify left)))\n'
            f'    (property "Value" "{c["val"]}" (at {f(x + 2.6)} {f(y + 1.4)} 0) (effects (font (size 1.1 1.1)) (justify left)))\n'
            f'    (property "Footprint" "{c["fp"]}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Datasheet" "~" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            + base.inst(ref, unit) + '  )\n')


def place_pins(ref, px, py, unit=None, rot=0, mirror=None):
    """{pin: (x_snap, y_snap)} del componente colocado. mirror: None|'x'|'y'."""
    c = BYREF[ref]
    pins = (get_pins(c["lib"], c["name"]) if unit is None
            else base.unidades(c["lib"], c["name"]).get(unit, {}))
    out = {}
    t = math.radians(rot)
    for num, (pn, lx, ly, ang) in pins.items():
        if mirror == 'y':
            lx = -lx
        elif mirror == 'x':
            ly = -ly
        x = lx * math.cos(t) + ly * math.sin(t)
        y = lx * math.sin(t) - ly * math.cos(t)
        out[num] = (snap(px + x), snap(py + y))
    return out


# =====================================================================
#  layout: lista de instrucciones de dibujo acumuladas
# =====================================================================
class Sheet:
    def __init__(self):
        self.P = []

    def add(self, s):
        if s:
            self.P.append(s)

    def comp(self, ref, x, y, unit=None, rot=0, mirror=None):
        self.add(simbolo(ref, snap(x), snap(y), unit=unit or 1, rot=rot, mirror=mirror))
        return place_pins(ref, snap(x), snap(y), unit=unit, rot=rot, mirror=mirror)

    def w(self, x1, y1, x2, y2):
        self.add(wire(x1, y1, x2, y2))

    def wires(self, *pts):
        for (a, b) in zip(pts, pts[1:]):
            self.w(a[0], a[1], b[0], b[1])

    def j(self, x, y):
        self.add(junction(x, y))

    def gnd(self, x, y, drop=2.54):
        self.w(x, y, x, y - drop); self.add(potencia("GND", x, y - drop))

    def rail(self, net, x, y, up=2.54):
        self.w(x, y, x, y + up); self.add(potencia(net, x, y + up))

    def lab(self, net, x, y, rot=0, just="left"):
        self.add(label(net, x, y, rot, just))

    def nc(self, x, y):
        self.add(no_connect(x, y))

    def txt(self, *a, **k):
        self.add(texto(*a, **k))

    def box(self, x1, y1, x2, y2, title=None):
        self.add(rect(x1, y1, x2, y2))
        if title:
            self.txt(title, x1 + 1, y1 - 1.5, 1.8)

    # --- terminacion uniforme de un pin en su red ---
    # direccion del stub segun hacia donde "mira" el pin; usamos la posicion
    # relativa al cuerpo para elegir un sentido de salida corto y limpio.
    def term(self, net, x, y, dir="auto", body=None, stub=5.08):
        """Lleva el pin en (x,y) a su red 'net' con un stub que SALE del cuerpo
        + etiqueta/potencia. El sentido se calcula desde body=(bx,by) para que
        el stub siempre se aleje del cuerpo (nunca hacia adentro)."""
        bx, by = body if body else (x, y)
        dx, dy = x - bx, y - by
        if dir == "auto":
            if abs(dx) >= abs(dy):
                dir = "R" if dx > 0 else "L"
            else:
                dir = "D" if dy > 0 else "U"   # D = +y (abajo en pantalla), U = -y (arriba)
        # El stub SIEMPRE sale alejandose del cuerpo segun el eje dominante del pin
        ex, ey = x, y
        if dir == "L":
            ex = x - stub
        elif dir == "R":
            ex = x + stub
        elif dir == "U":
            ey = y - stub    # arriba en pantalla
        elif dir == "D":
            ey = y + stub    # abajo en pantalla
        self.w(x, y, ex, ey)
        if net in POTENCIA:
            self.add(potencia(net, ex, ey))
        else:
            rot = {"L": 180, "R": 0, "U": 90, "D": 270}[dir]
            just = "right" if dir in ("L",) else "left"
            self.add(label(net, ex, ey, rot, just))
        return (ex, ey)


def header(P):
    defs = OrderedDict()
    for c in COMPONENTES:
        defs[(c["lib"], c["name"])] = 1
    for p in POTENCIA | {"PWR_FLAG"}:
        defs[("power", p)] = 1
    hoy = date.today().isoformat()
    P += ['(kicad_sch\n  (version 20231120)\n  (generator "medidor_ppg_gen")\n  (generator_version "1.0")\n',
          f'  (uuid "{ROOT_UUID}")\n  (paper "A1")\n',
          f'  (title_block (title "Medidor de ritmo cardiaco PPG - LM324 + ESP32-C3") (date "{hoy}") (rev "1")\n'
          '    (company "ITM - Circuitos Electricos II") (comment 1 "Dibujo por bloques, cables reales. Valores: 01_analogico/ppg.cir"))\n',
          '  (lib_symbols\n', "".join(base.def_plana(l, n) for l, n in defs), '  )\n']


def footer(P):
    P.append('  (sheet_instances (path "/" (page "1")))\n)\n')


if __name__ == "__main__":
    print("modulo base; usar construir.py")
