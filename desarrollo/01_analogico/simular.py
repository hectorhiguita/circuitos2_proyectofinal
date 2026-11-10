#!/usr/bin/env python3
"""Simula ppg.cir con ngspice y genera gráficas + resumen para el informe.

  python3 simular.py
Salidas en ./resultados/: bode.png, transitorio.png, arranque.png, resumen.md
"""
import math
import pathlib
import re
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

AQUI = pathlib.Path(__file__).resolve().parent
OUT = AQUI / "resultados"
OUT.mkdir(exist_ok=True)
BASE = (AQUI / "ppg.cir").read_text()


def correr(rv="200k", vos="0", senal=None, control=""):
    net = re.sub(r"^\.param RV=\S+", f".param RV={rv}", BASE, flags=re.M)
    # offset de entrada en cada operacional (peor caso del LM324: 7 mV)
    net = net.replace("G1 0 n1 inp inn 1m", f"Vos inp inp2 {vos}\nG1 0 n1 inp2 inn 1m")
    if senal:
        net = net.replace("Vsig sraw 0 DC 0.5 AC {ACM}", f"Bsig sraw 0 V = {senal}")
    net = net.replace(".end", control + "\n.end")
    with tempfile.TemporaryDirectory() as d:
        cir = pathlib.Path(d) / "c.cir"
        cir.write_text(net)
        r = subprocess.run(["ngspice", "-b", str(cir)], capture_output=True, text=True, cwd=d)
        datos = {}
        for f in pathlib.Path(d).glob("*.txt"):
            datos[f.stem] = np.loadtxt(f)
        if r.returncode != 0 and not datos:
            raise RuntimeError(r.stdout[-2000:] + r.stderr[-2000:])
        return datos, r.stdout


# ---------------------------------------------------------------- 1) respuesta en frecuencia
ctl_ac = """
.control
ac dec 200 0.02 1k
let gp = vdb(p)-vdb(sraw)
let gs = vdb(sk)-vdb(sraw)
let gf = vdb(adc)-vdb(sraw)
wrdata ac.txt gp gs gf
.endc"""
curvas = {}
for rv in ["10k", "100k", "200k"]:
    d, _ = correr(rv=rv, control=ctl_ac)
    curvas[rv] = d["ac"]

def corte(f, g):
    gmax = g.max()
    i0 = int(np.argmax(g))
    lo = f[:i0][g[:i0] <= gmax - 3]
    hi = f[i0:][g[i0:] <= gmax - 3]
    return gmax, f[i0], (lo[-1] if len(lo) else float("nan")), (hi[0] if len(hi) else float("nan"))

fig, ax = plt.subplots(figsize=(8, 4.5))
res_ac = {}
for rv, a in curvas.items():
    f, gf = a[:, 0], a[:, 5]
    gmax, fpk, flo, fhi = corte(f, gf)
    res_ac[rv] = (gmax, fpk, flo, fhi)
    ax.semilogx(f, gf, label=f"Punto 6, RV1={rv} (máx {gmax:.1f} dB)")
a = curvas["100k"]
ax.semilogx(a[:, 0], a[:, 1], "--", label="Salida preamp (etapa 4)")
ax.semilogx(a[:, 0], a[:, 3], ":", label="Salida Sallen-Key (etapa 5)")
for x, t in [(0.5, "30 lpm"), (5, "300 lpm"), (60, "60 Hz red")]:
    ax.axvline(x, color="gray", lw=0.6)
    ax.text(x, -38, t, rotation=90, fontsize=8, va="bottom")
ax.set_xlabel("Frecuencia (Hz)")
ax.set_ylabel("Ganancia desde el sensor (dB)")
ax.set_ylim(-40, 70)
ax.grid(True, which="both", alpha=0.3)
ax.legend(fontsize=8)
ax.set_title("Respuesta en frecuencia del acondicionador")
fig.tight_layout()
fig.savefig(OUT / "bode.png", dpi=150)

# atenuación a 60 Hz respecto al máximo (RV 200k)
a = curvas["100k"]
g60 = np.interp(60, a[:, 0], a[:, 5])
g1 = np.interp(1.2, a[:, 0], a[:, 5])

# ---------------------------------------------------------------- 2) transitorio con pulso + 60 Hz
fp = 1.2  # 72 lpm
ppg = (f"0.5 + 1m*(sin(2*pi*{fp}*time) + 0.5*sin(4*pi*{fp}*time+1) + 0.25*sin(6*pi*{fp}*time+2))"
       f" + 1m*sin(2*pi*60*time)")
ctl_tr = """
.control
tran 1m 30 0 1m uic
wrdata tr.txt v(s) v(p) v(sk) v(f) v(adc) v(vref2)
.endc"""
casos = {}
for nombre, rv, vos in [("tipico", "100k", "0"), ("offset 7 mV", "100k", "7m"), ("ganancia max + offset", "200k", "7m")]:
    d, _ = correr(rv=rv, vos=vos, senal=ppg, control=ctl_tr)
    casos[nombre] = d["tr"]

t = casos["tipico"][:, 0]
fig, axs = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
axs[0].plot(t, casos["tipico"][:, 1] * 1000, lw=0.6)
axs[0].set_ylabel("Sensor (mV)")
axs[0].set_title("Entrada: 0.5 V DC + pulso ~3.5 mVpp (72 lpm) + 60 Hz 2 mVpp")
axs[1].plot(t, casos["tipico"][:, 3], lw=0.8, label="Preamp (etapa 4)")
axs[1].plot(t, casos["tipico"][:, 5], lw=0.8, label="Sallen-Key (etapa 5)")
axs[1].set_ylabel("V")
axs[1].legend(fontsize=8)
for nombre, d in casos.items():
    axs[2].plot(d[:, 0], d[:, 9], lw=0.8, label=f"Punto 6 ({nombre})")
axs[2].axhline(2.5, color="r", lw=0.6, ls="--")
axs[2].axhline(0, color="r", lw=0.6, ls="--")
axs[2].text(0.2, 2.53, "límite útil ADC C3 (2.5 V)", fontsize=8, color="r")
axs[2].set_ylabel("V en el ADC")
axs[2].set_xlabel("Tiempo (s)")
axs[2].legend(fontsize=8)
for x in axs:
    x.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "transitorio.png", dpi=150)

fig, ax = plt.subplots(figsize=(9, 3.2))
m = (t >= 20) & (t <= 25)
ax.plot(t[m], casos["tipico"][m, 9], lw=1)
ax.set_title("Punto 6 en régimen (20–25 s), RV1 = 100k")
ax.set_xlabel("Tiempo (s)")
ax.set_ylabel("V")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "punto6_detalle.png", dpi=150)

# métricas
def metricas(d, t0=10):
    m = d[:, 0] >= t0
    v = d[m, 9]
    return v.min(), v.max(), v.max() - v.min(), v.mean()

def arranque(d, tol=0.05):
    v = d[:, 9]; tt = d[:, 0]
    fin = metricas(d)
    lo, hi = fin[0] - tol, fin[1] + tol
    fuera = np.where((v < lo) | (v > hi))[0]
    return tt[fuera[-1]] if len(fuera) else 0.0

lineas = ["# Resultados de simulación (ngspice)", "",
          "Modelo LM324: GBW 1 MHz, salida 0.02 V a VCC−1.5 V. Entrada: pulso ≈3.5 mVpp a 72 lpm + 60 Hz 2 mVpp.", "",
          "## Respuesta en frecuencia (desde el sensor hasta el Punto 6)", "",
          "| RV1 | Ganancia máx | f pico | f −3 dB baja | f −3 dB alta |", "|---|---|---|---|---|"]
for rv, (g, fpk, flo, fhi) in res_ac.items():
    lineas.append(f"| {rv} | {g:.1f} dB ({10**(g/20):.0f} V/V) | {fpk:.2f} Hz | {flo:.2f} Hz | {fhi:.2f} Hz |")
lineas += ["", f"Con RV1 = 100k: ganancia a 1.2 Hz = {g1:.1f} dB; a 60 Hz = {g60:.1f} dB "
           f"(rechazo de {g1-g60:.1f} dB frente al pulso).", "",
           "## Transitorio (Punto 6, después de 10 s)", "",
           "| Caso | Mín (V) | Máx (V) | Vpp | Media | Asentamiento |", "|---|---|---|---|---|---|"]
for nombre, d in casos.items():
    mn, mx, pp, me = metricas(d)
    lineas.append(f"| {nombre} | {mn:.3f} | {mx:.3f} | {pp:.3f} | {me:.3f} | {arranque(d):.1f} s |")
vr = casos["tipico"][-1, 11]
lineas += ["", f"VREF en régimen: {vr:.3f} V.", "",
           "Criterio: Punto 6 siempre entre 0 y 2.5 V (rango útil del ADC del ESP32-C3 con 12 dB)."]
(OUT / "resumen.md").write_text("\n".join(lineas) + "\n")
print("\n".join(lineas))
