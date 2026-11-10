#!/usr/bin/env python3
"""Genera medidor_ppg.kicad_sch (KiCad 10) desde componentes.py.

Conexión por etiquetas de red: cada pin lleva un tramo corto + etiqueta (o símbolo de potencia).
Componentes agrupados por etapa, con título por sección. Soporta símbolos multi-unidad (LM324).
Basado en el generador del proyecto citófono (validado con ERC).
"""
import math
import re
import uuid
from collections import Counter, OrderedDict
from datetime import date
from pathlib import Path

from componentes import COMPONENTES, POTENCIA
from lib_pins import _extract_block, get_pins, lib_symbol_def, parent_of, pin_xy, pin_outward

NOMBRE = "medidor_ppg"
ROOT_UUID = "00000000-0000-0000-0000-0000000000a1"
GRID = 1.27
STUB = 2.54
_NS = uuid.UUID("5e1a0000-0000-4000-8000-00000000a1a1")


def snap(v):
    return round(v / GRID) * GRID


def f(v):
    return f"{float(v):.4f}"


def uid():
    return str(uuid.uuid4())


def suid(k):
    return str(uuid.uuid5(_NS, k))


_PIN_RE = re.compile(r'\(pin\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)\s*'
                     r'\(length\s+[-\d.]+\).*?\(name\s+"([^"]*)".*?\(number\s+"([^"]*)"', re.S)


def unidades(lib, name):
    """{unidad: {pin: (nombre, x, y, ang)}} (unidad 0 = común)."""
    base = parent_of(lib, name) or name
    blk = _extract_block(lib, base)
    out = {}
    for m in re.finditer(rf'\(symbol "{re.escape(base)}_(\d+)_\d+"', blk):
        u = int(m.group(1))
        # bloque balanceado
        i, d = m.start(), 0
        for j in range(i, len(blk)):
            if blk[j] == "(":
                d += 1
            elif blk[j] == ")":
                d -= 1
                if d == 0:
                    break
        sub = blk[i:j + 1]
        for pm in _PIN_RE.finditer(sub):
            x, y, a, pn, num = pm.groups()
            out.setdefault(u, {})[num] = (pn, float(x), float(y), float(a))
    return out


def def_plana(lib, name):
    """Definición para lib_symbols sin 'extends' (el esquema exige símbolos aplanados)."""
    par = parent_of(lib, name)
    if not par:
        return lib_symbol_def(lib, name)
    b = _extract_block(lib, par)
    b = b.replace(f'(symbol "{par}"', f'(symbol "{lib}:{name}"', 1).replace(f'(symbol "{par}_', f'(symbol "{name}_')
    b = re.sub(r'\(property "Value" "[^"]*"', f'(property "Value" "{name}"', b, count=1)
    return "\n".join("    " + l if l else "" for l in b.split("\n")) + "\n"


def inst(ref, unit=1):
    return (f'    (instances (project "{NOMBRE}" (path "/{ROOT_UUID}" (reference "{ref}") (unit {unit}))))\n')


def simbolo(c, x, y, unit=1, rot=0):
    lib_id = f'{c["lib"]}:{c["name"]}'
    return (f'  (symbol (lib_id "{lib_id}") (at {f(x)} {f(y)} {rot}) (unit {unit})\n'
            f'    (exclude_from_sim no) (in_bom {"yes" if c["bom"] else "no"}) (on_board yes) (dnp no)\n'
            f'    (uuid "{suid(c["ref"] + "/" + str(unit))}")\n'
            f'    (property "Reference" "{c["ref"]}" (at {f(x)} {f(y - 7.62)} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Value" "{c["val"]}" (at {f(x)} {f(y + 7.62)} 0) (effects (font (size 1.27 1.27))))\n'
            f'    (property "Footprint" "{c["fp"]}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Datasheet" "~" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            + inst(c["ref"], unit) + '  )\n')


def wire(x1, y1, x2, y2):
    return f'  (wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})) (stroke (width 0) (type default)) (uuid "{uid()}"))\n'


def label(n, x, y, ox):
    rot, just = (0, "left") if ox >= 0 else (180, "right")
    if abs(ox) < 0.5:
        rot, just = (90, "left")
    return (f'  (label "{n}" (at {f(x)} {f(y)} {rot}) (effects (font (size 1.27 1.27)) (justify {just} bottom))'
            f' (uuid "{uid()}"))\n')


_pc = [0]


def potencia(net, x, y):
    _pc[0] += 1
    ref = f"#PWR{_pc[0]:03d}"
    rot = 0 if net == "GND" else 180
    return (f'  (symbol (lib_id "power:{net}") (at {f(x)} {f(y)} {rot}) (unit 1)\n'
            f'    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")\n'
            f'    (property "Reference" "{ref}" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Value" "{net}" (at {f(x)} {f(y + (3 if net == "GND" else -3))} 0) (effects (font (size 1 1))))\n'
            f'    (property "Footprint" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            f'    (property "Datasheet" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
            + inst(ref) + '  )\n')


def flag(net, x, y):
    """PWR_FLAG con su propio símbolo de potencia (marca rieles que llegan por conector)."""
    _pc[0] += 1
    ref = f"#FLG{_pc[0]:03d}"
    s = (f'  (symbol (lib_id "power:PWR_FLAG") (at {f(x)} {f(y)} 0) (unit 1)\n'
         f'    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid "{uid()}")\n'
         f'    (property "Reference" "{ref}" (at {f(x)} {f(y - 3)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
         f'    (property "Value" "PWR_FLAG" (at {f(x)} {f(y - 4)} 0) (effects (font (size 1 1))))\n'
         f'    (property "Footprint" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
         f'    (property "Datasheet" "" (at {f(x)} {f(y)} 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
         + inst(ref) + '  )\n')
    if net in POTENCIA:
        return s + wire(x, y, x, y + 2.54) + potencia(net, x, y + 2.54 if net != "GND" else y + 2.54)
    return s + wire(x, y, x + 2.54, y) + label(net, x + 2.54, y, 1)


def texto(t, x, y, sz=2.0, bold=True):
    b = " bold" if bold else ""
    return f'  (text "{t}" (at {f(x)} {f(y)} 0) (effects (font (size {sz} {sz}){b}) (justify left)) (uuid "{uid()}"))\n'


def pines_de(c, unit):
    if unit is None:
        return get_pins(c["lib"], c["name"])
    u = unidades(c["lib"], c["name"])
    return u.get(unit, {})


def construir():
    partes = []
    defs = OrderedDict()
    for c in COMPONENTES:
        defs[(c["lib"], c["name"])] = 1
    for p in POTENCIA | {"PWR_FLAG"}:
        defs[("power", p)] = 1
    hoy = date.today().isoformat()
    partes += ['(kicad_sch\n  (version 20231120)\n  (generator "medidor_ppg_gen")\n  (generator_version "1.0")\n',
               f'  (uuid "{ROOT_UUID}")\n  (paper "A2")\n',
               f'  (title_block (title "Medidor de ritmo cardiaco PPG - LM324 + ESP32-C3") (date "{hoy}") (rev "1")\n'
               '    (company "ITM - Circuitos Electricos II") (comment 1 "Conexiones por etiqueta de red. Valores: 01_analogico/ppg.cir"))\n',
               '  (lib_symbols\n', "".join(def_plana(l, n) for l, n in defs), '  )\n']

    secciones = OrderedDict()
    for c in COMPONENTES:
        secciones.setdefault(c["sec"], []).append(c)

    y = 30.0
    extremos = []
    for sec, comps in secciones.items():
        partes.append(texto(sec, 20, y - 8))
        x = 30.0
        alto = 22.0
        for c in comps:
            es_multi = c["name"] == "LM324"
            units = [1, 2, 3, 4, 5] if es_multi else [None]
            for u in units:
                px, py = snap(x), snap(y + 6)
                partes.append(simbolo(c, px, py, unit=u or 1))
                pins = pines_de(c, u)
                for num, (pn, lx, ly, ang) in pins.items():
                    cx, cy = pin_xy(lx, ly, px, py, 0)
                    ox, oy = pin_outward(ang, 0)
                    ex, ey = snap(cx + ox * STUB), snap(cy + oy * STUB)
                    net = c["nets"].get(num)
                    if net is None:
                        partes.append(f'  (no_connect (at {f(cx)} {f(cy)}) (uuid "{uid()}"))\n')
                        continue
                    partes.append(wire(cx, cy, ex, ey))
                    if net in POTENCIA:
                        partes.append(potencia(net, ex, ey))
                    else:
                        partes.append(label(net, ex, ey, ox))
                    extremos.append(net)
                ancho = 40 if es_multi or c["name"].startswith("Conn_01x08") else 28
                x += ancho
                if x > 560:
                    x = 30.0
                    y += alto + 12
        y += alto + 26

    # PWR_FLAG: rieles que entran por conector (+5V del MT3608 vía D1, +3V3 del SuperMini, GND)
    for i, net in enumerate(["+5V", "+3V3", "GND", "BAT", "VSW", "+5V_B"]):
        partes.append(flag(net, snap(30 + i * 20), snap(y)))
    partes.append(texto("PWR_FLAG: rieles alimentados desde módulos externos (TP4056, MT3608, LDO del SuperMini)",
                        20, y - 8, 1.5, False))
    partes.append('  (sheet_instances (path "/" (page "1")))\n)\n')
    return "".join(partes), extremos


def proyecto():
    import json
    return json.dumps({
        "meta": {"filename": f"{NOMBRE}.kicad_pro", "version": 1},
        "board": {"design_settings": {"defaults": {"board_outline_line_width": 0.1}}},
        "net_settings": {"classes": [
            {"name": "Default", "clearance": 0.25, "track_width": 0.4, "via_drill": 0.4, "via_diameter": 0.8},
            {"name": "Potencia", "clearance": 0.25, "track_width": 0.8, "via_drill": 0.5, "via_diameter": 1.0}],
            "meta": {"version": 3},
            "netclass_patterns": [{"netclass": "Potencia", "pattern": n} for n in ["+5V", "/+5V_B", "GND", "/BAT", "/VSW"]]},
        "schematic": {"drawing": {"default_line_thickness": 6, "default_text_size": 50}},
        "sheets": [[ROOT_UUID, "Root"]], "text_variables": {}}, indent=2)


if __name__ == "__main__":
    aqui = Path(__file__).parent
    sch, ext = construir()
    (aqui / f"{NOMBRE}.kicad_sch").write_text(sch, encoding="utf-8")
    pro = aqui / f"{NOMBRE}.kicad_pro"
    if not pro.exists():
        pro.write_text(proyecto(), encoding="utf-8")
    n = Counter(ext)
    print(f"{len(COMPONENTES)} componentes, {len(ext)} conexiones, {len(n)} redes -> {NOMBRE}.kicad_sch")
