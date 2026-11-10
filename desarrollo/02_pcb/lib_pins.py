#!/usr/bin/env python3
"""
lib_pins.py — Extractor de símbolos y pines de las librerías KiCad instaladas.
Maneja herencia (extends): resuelve el símbolo padre para pines y gráficos.
Usado por generar_kicad.py
"""
import re, math
from pathlib import Path
from functools import lru_cache

SYM_DIR = Path("/usr/share/kicad/symbols")

@lru_cache(maxsize=None)
def _libtext(lib: str) -> str:
    return (SYM_DIR / f"{lib}.kicad_sym").read_text(encoding="utf-8")

def _extract_block(lib: str, name: str) -> str:
    """Devuelve el bloque (symbol ...) balanceado en paréntesis."""
    content = _libtext(lib)
    marker = f'\t(symbol "{name}"'
    pos = content.find(marker)
    if pos == -1:
        pos = content.find(f'(symbol "{name}"')
    if pos == -1:
        return ""
    depth = 0
    for i, c in enumerate(content[pos:], pos):
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return content[pos:i+1]
    return ""

def parent_of(lib: str, name: str) -> str | None:
    m = re.search(r'\(extends "([^"]+)"', _extract_block(lib, name))
    return m.group(1) if m else None

_PIN_RE = re.compile(
    r'\(pin\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\)\s*'
    r'\(length\s+[-\d.]+\).*?\(name\s+"([^"]*)".*?\(number\s+"([^"]*)"',
    re.S)

def get_pins(lib: str, name: str) -> dict:
    """
    {numero_pin: (nombre, x, y, angulo)} en coords de librería (Y-arriba).
    Resuelve extends al padre si el símbolo no tiene pines propios.
    """
    block = _extract_block(lib, name)
    if "(pin " not in block:
        par = parent_of(lib, name)
        if par:
            block = _extract_block(lib, par)
    out = {}
    for m in _PIN_RE.finditer(block):
        x, y, a, pname, num = m.groups()
        if num not in out:    # primer pin con ese número (evita GND duplicados)
            out[num] = (pname, float(x), float(y), float(a))
    return out

def all_pin_numbers(lib: str, name: str) -> list:
    return list(get_pins(lib, name).keys())

# ─── Transformación validada empíricamente contra ERC de KiCad ──────────────
def pin_xy(lx: float, ly: float, px: float, py: float, theta: float):
    """Coordenada del pin en el esquema (Y-abajo) tras colocar y rotar."""
    t = math.radians(theta)
    x = lx * math.cos(t) + ly * math.sin(t)
    y = lx * math.sin(t) - ly * math.cos(t)
    return (px + x, py + y)

def pin_outward(angle: float, theta: float):
    """Vector unitario hacia AFUERA del cuerpo (para dibujar el stub)."""
    # En librería, 'angle' apunta hacia el cuerpo; afuera = angle+180
    a = math.radians(angle + 180)
    dx, dy = math.cos(a), math.sin(a)
    t = math.radians(theta)
    Dx = dx * math.cos(t) + dy * math.sin(t)
    Dy = dx * math.sin(t) - dy * math.cos(t)
    # Normalizar a paso de rejilla
    n = math.hypot(Dx, Dy) or 1.0
    return (Dx / n, Dy / n)

def lib_symbol_def(lib: str, name: str) -> str:
    """
    Bloque de definición para lib_symbols, indentado 4 espacios.
    Incluye el padre si hay extends (KiCad lo necesita).
    Devuelve cadena (puede contener 2 símbolos: padre + derivado).
    """
    blocks = []
    par = parent_of(lib, name)
    if par:
        pb = _extract_block(lib, par)
        pb = pb.replace(f'(symbol "{par}"', f'(symbol "{lib}:{par}"', 1)
        blocks.append(pb)
    b = _extract_block(lib, name)
    b = b.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    blocks.append(b)
    indented = []
    for blk in blocks:
        indented.append("\n".join("    " + l if l else "" for l in blk.split("\n")))
    return "\n".join(indented) + "\n"
