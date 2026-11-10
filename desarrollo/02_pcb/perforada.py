#!/usr/bin/env python3
"""Versión en baquela perforada (paso 2.54 mm) a partir de la PCB ubicada.

  python3 perforada.py
Salidas en perforada/: vista_componentes.pdf/png (lado componentes, escala 1:1),
vista_soldadura.pdf/png (lado cobre, espejada, con los cables), conexiones.md (lista por red).
Cada pin se ajusta al agujero más cercano. Las conexiones de cada red se trazan como el
árbol mínimo (Manhattan) entre sus pines: cada segmento = un cable o puente de estaño.
"""
import itertools
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pcbnew

AQUI = Path(__file__).resolve().parent
OUT = AQUI / "perforada"
OUT.mkdir(exist_ok=True)
P = 2.54
OX, OY = 100.0, 100.0
COLS, FILAS = 35, 27            # baquela universal 9 x 7 cm
board = pcbnew.LoadBoard(str(AQUI / "medidor_ppg.ubicado.kicad_pcb"))
fps = list(board.GetFootprints())


def pxy(p):
    q = p.GetPosition()
    return pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY


def mover(fp, dx, dy):
    q = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(q.x + pcbnew.FromMM(dx), q.y + pcbnew.FromMM(dy)))


def caja(fp):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    b = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (pcbnew.ToMM(b.GetLeft()) - OX, pcbnew.ToMM(b.GetTop()) - OY,
            pcbnew.ToMM(b.GetRight()) - OX, pcbnew.ToMM(b.GetBottom()) - OY)


def choca(a, b):
    return not (a[2] <= b[0] or a[0] >= b[2] or a[3] <= b[1] or a[1] >= b[3])


# 1) ajustar cada footprint para que su pin 1 caiga en un agujero
puestos = []
for fp in sorted(fps, key=lambda f: -len(f.Pads())):
    if fp.GetReference().startswith("H"):
        continue
    pad1 = [p for p in fp.Pads() if p.GetNumber() in ("1", "A", "")][0]
    x, y = pxy(pad1)
    mover(fp, round(x / P) * P - x, round(y / P) * P - y)
    # si choca con uno ya puesto, buscar el agujero libre más cercano
    for r in range(0, 8):
        ok = False
        for dx, dy in sorted(itertools.product(range(-r, r + 1), repeat=2), key=lambda d: abs(d[0]) + abs(d[1])):
            if max(abs(dx), abs(dy)) != r:
                continue
            mover(fp, dx * P, dy * P)
            if not any(choca(caja(fp), caja(o)) for o in puestos):
                ok = True
                break
            mover(fp, -dx * P, -dy * P)
        if ok:
            break
    puestos.append(fp)

# 2) agujeros de cada pin + desvío respecto a la rejilla
pins, desv = defaultdict(list), []
for fp in puestos:
    for p in fp.Pads():
        x, y = pxy(p)
        i, j = round(x / P), round(y / P)
        desv.append(math.hypot(x - i * P, y - j * P))
        n = p.GetNetname()
        if n:
            pins[n].append((i, j, f"{fp.GetReference()}.{p.GetNumber()}"))
i_min = min(i for v in pins.values() for i, _, _ in v)
j_min = min(j for v in pins.values() for _, j, _ in v)
ancho = max(i for v in pins.values() for i, _, _ in v) - i_min + 1
alto = max(j for v in pins.values() for _, j, _ in v) - j_min + 1
assert ancho <= COLS and alto <= FILAS, (ancho, alto)


def col(i):
    i -= i_min
    return chr(ord("A") + i) if i < 26 else "A" + chr(ord("A") + i - 26)


def nombre(i, j):
    return f"{col(i)}{j - j_min + 1}"


# 3) árbol mínimo por red (Prim, distancia Manhattan)
def mst(nodos):
    if len(nodos) < 2:
        return []
    dentro, aristas = {0}, []
    while len(dentro) < len(nodos):
        best = min(((a, b) for a in dentro for b in range(len(nodos)) if b not in dentro),
                   key=lambda e: abs(nodos[e[0]][0] - nodos[e[1]][0]) + abs(nodos[e[0]][1] - nodos[e[1]][1]))
        aristas.append(best)
        dentro.add(best[1])
    return aristas


COLOR = {"GND": "#222222", "+5V": "#d32f2f", "+3V3": "#f57c00"}
paleta = ["#1e88e5", "#43a047", "#8e24aa", "#00897b", "#6d4c41", "#3949ab", "#c2185b", "#7cb342", "#5e35b1",
          "#00acc1", "#fb8c00", "#546e7a"]
redes = sorted(pins, key=lambda n: (n not in COLOR, n))
color = {n: COLOR.get(n, paleta[k % len(paleta)]) for k, n in enumerate(redes)}


def dibujar(espejo, archivo):
    w_mm, h_mm = COLS * P + 10, FILAS * P + 22
    fig = plt.figure(figsize=(w_mm / 25.4, h_mm / 25.4))
    ax = fig.add_axes([5 / w_mm, 5 / h_mm, (COLS * P) / w_mm, (FILAS * P) / h_mm])
    ax.set_xlim(-0.5 * P, (COLS - 0.5) * P)
    ax.set_ylim((FILAS - 0.5) * P, -0.5 * P)
    ax.axis("off")
    X = lambda i: ((COLS - 1 - (i - i_min)) if espejo else (i - i_min)) * P
    Y = lambda j: (j - j_min) * P
    for a in range(COLS):
        for b in range(FILAS):
            ax.add_patch(plt.Circle((a * P, b * P), 0.45, fc="none", ec="#bbbbbb", lw=0.3))
    for a in range(ancho):
        ax.text(X(i_min + a), -0.9 * P + 0.2, col(i_min + a), ha="center", fontsize=3.5, color="#888")
    for b in range(alto):
        ax.text(X(i_min) + (-0.8 * P if not espejo else 0.8 * P), Y(j_min + b) + 0.4, str(b + 1),
                ha="center", fontsize=3.5, color="#888")
    for fp in puestos:
        x0, y0, x1, y1 = caja(fp)
        ii = [x0 / P, x1 / P]
        xs = sorted(X(v) for v in ii) if not espejo else sorted(X(v) for v in ii)
        ax.add_patch(plt.Rectangle((xs[0], Y(y0 / P)), xs[1] - xs[0], (y1 - y0), fc="#fff8e1" if not espejo else "none",
                                   ec="#999" if not espejo else "#ddd", lw=0.4, ls="-" if not espejo else ":"))
        cx = (xs[0] + xs[1]) / 2
        ax.text(cx, Y(y0 / P) + (y1 - y0) / 2, fp.GetReference() + ("" if espejo else "\n" + fp.GetValue()),
                ha="center", va="center", fontsize=3.2 if not espejo else 2.8, color="#444" if not espejo else "#aaa")
    if not espejo:
        for fp in puestos:
            for p in fp.Pads():
                x, y = pxy(p)
                ax.add_patch(plt.Circle((X(round(x / P)), Y(round(y / P))), 0.55, fc="#888", ec="none"))
    for n, lista in pins.items():
        for i, j, _ in lista:
            ax.add_patch(plt.Circle((X(i), Y(j)), 0.55, fc=color[n] if espejo else "#888", ec="none"))
        if espejo:
            for a, b in mst([(i, j) for i, j, _ in lista]):
                (i1, j1, _), (i2, j2, _) = lista[a], lista[b]
                lw = 1.3 if n in COLOR else 0.8
                ax.plot([X(i1), X(i2)], [Y(j1), Y(j2)], color=color[n], lw=lw, alpha=0.85, solid_capstyle="round")
    titulo = ("LADO SOLDADURA (visto por debajo, espejado) - cables por red" if espejo
              else "LADO COMPONENTES - escala 1:1 (imprimir al 100 %)")
    fig.text(0.5, 1 - 4 / h_mm, f"Medidor PPG - baquela 9x7 cm - {titulo}", ha="center", fontsize=4.5, weight="bold")
    if espejo:
        txt = "  ".join(f"{n.lstrip('/')}" for n in redes)
        y = 2.5 / h_mm
        x = 0.02
        for n in redes:
            fig.text(x, y, "■ " + n.lstrip("/"), color=color[n], fontsize=3.5)
            x += 0.065
            if x > 0.95:
                x, y = 0.02, y + 2.2 / h_mm
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{archivo}.{ext}", dpi=300)
    plt.close(fig)


dibujar(False, "vista_componentes")
dibujar(True, "vista_soldadura")

# 4) lista de conexiones
lin = ["# Conexiones en baquela (lado soldadura)", "",
       f"Baquela universal 9 × 7 cm ({COLS} × {FILAS} agujeros). Ocupa {ancho} columnas × {alto} filas.",
       "Columnas = letras (izquierda a derecha visto desde los componentes), filas = números.",
       "Cada línea = un cable aislado (wire-wrap o UTP) entre dos agujeros. GND, +5V y +3V3: cable más grueso.", "",
       f"Desvío máximo pin-agujero: {max(desv):.2f} mm (JST de 2.50 mm de paso; entra sin problema).", ""]
total = 0
for n in redes:
    lista = pins[n]
    ar = mst([(i, j) for i, j, _ in lista])
    if not ar:
        continue
    lin.append(f"## {n.lstrip('/')}  ({len(lista)} pines)")
    for a, b in ar:
        (i1, j1, p1), (i2, j2, p2) = lista[a], lista[b]
        lin.append(f"- [ ] {p1} ({nombre(i1, j1)})  →  {p2} ({nombre(i2, j2)})")
        total += 1
    lin.append("")
lin.insert(5, f"Total: **{total} conexiones**. Marca cada casilla al soldarla.")
(OUT / "conexiones.md").write_text("\n".join(lin) + "\n")
print(f"{ancho}x{alto} agujeros, {total} conexiones, desvío máx {max(desv):.2f} mm -> {OUT}")
