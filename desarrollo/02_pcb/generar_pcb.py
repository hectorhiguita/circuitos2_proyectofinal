#!/usr/bin/env python3
"""Genera, ubica, rutea (Freerouting) y verifica medidor_ppg.kicad_pcb.

  python3 generar_pcb.py            (crea la placa desde cero: ¡sobrescribe!)
Placa 80 x 52 mm, 2 capas, THT. USB-C del SuperMini hacia el borde trasero (x = 80).
Las piezas de ubicación libre se empacan en orden de flujo de señal (izquierda -> derecha).
"""
import subprocess
import sys
import uuid
from pathlib import Path

import pcbnew

from componentes import COMPONENTES, red_pcb

AQUI = Path(__file__).resolve().parent
NOMBRE = "medidor_ppg"
FP = "/usr/share/kicad/footprints"
FR = Path.home() / "Tools/freerouting/linux-x64/freerouting-2.2.4-linux-x64/bin/freerouting"
OX, OY = 100.0, 100.0          # origen de la placa en la hoja
W, H = 66.0, 48.0
_NS = uuid.UUID("5e1a0000-0000-4000-8000-00000000a1a1")   # mismo que el esquema


def mm(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))


def bbox(fp, margen=0.0):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    b = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (pcbnew.ToMM(b.GetLeft()) - OX - margen, pcbnew.ToMM(b.GetTop()) - OY - margen,
            pcbnew.ToMM(b.GetRight()) - OX + margen, pcbnew.ToMM(b.GetBottom()) - OY + margen)


def mover_centro(fp, x, y):
    x0, y0, x1, y1 = bbox(fp)
    p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x + pcbnew.FromMM(x - (x0 + x1) / 2), p.y + pcbnew.FromMM(y - (y0 + y1) / 2)))


def pad_xy(fp, n):
    for p in fp.Pads():
        if p.GetNumber() == n:
            q = p.GetPosition()
            return pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY
    raise KeyError(n)


def orientar_fila(fp, sentido):
    """Gira un conector 1xN para que el pin N quede hacia 'sentido' (+x, -x, +y) respecto al pin 1."""
    for ang in (0, 90, 180, 270):
        fp.SetOrientationDegrees(ang)
        (x1, y1), (xn, yn) = pad_xy(fp, "1"), pad_xy(fp, str(len(fp.Pads())))
        if (sentido == "+x" and xn > x1 + 1) or (sentido == "-x" and xn < x1 - 1) or (sentido == "+y" and yn > y1 + 1):
            return
    raise RuntimeError("no se pudo orientar " + fp.GetReference())


def mover_pad1(fp, x, y):
    px, py = pad_xy(fp, "1")
    p = fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(p.x + pcbnew.FromMM(x - px), p.y + pcbnew.FromMM(y - py)))


def silk(board, txt, x, y, size=1.0, layer=pcbnew.F_SilkS, ang=0):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetPosition(mm(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
    t.SetTextThickness(pcbnew.FromMM(size * 0.15))
    t.SetTextAngleDegrees(ang)
    board.Add(t)


def rect(board, x0, y0, x1, y1, layer, ancho=0.12):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_RECT)
    s.SetStart(mm(x0, y0))
    s.SetEnd(mm(x1, y1))
    s.SetLayer(layer)
    s.SetWidth(pcbnew.FromMM(ancho))
    board.Add(s)


def zona(board, red, capa):
    z = pcbnew.ZONE(board)
    z.SetLayer(capa)
    z.SetNet(red)
    z.SetLocalClearance(pcbnew.FromMM(0.4))
    z.SetMinThickness(pcbnew.FromMM(0.3))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(pcbnew.FromMM(0.5))
    z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.6))
    o = z.Outline()
    o.NewOutline()
    for x, y in [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]:
        o.Append(mm(x, y))
    board.Add(z)


def main():
    pcb_path = AQUI / f"{NOMBRE}.kicad_pcb"
    board = pcbnew.NewBoard(str(pcb_path))
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetTrackWidth(pcbnew.FromMM(0.4))
    nc.SetClearance(pcbnew.FromMM(0.25))     # proveedor: >= 0.2 mm pista/pad
    nc.SetViaDiameter(pcbnew.FromMM(1.2))    # anillo via = (1.2-0.4)/2*2 = 0.8 mm
    nc.SetViaDrill(pcbnew.FromMM(0.4))

    # ---------------------------------------------------------------- redes
    redes = {}
    for c in COMPONENTES:
        for n in c["nets"].values():
            if n not in redes:
                ni = pcbnew.NETINFO_ITEM(board, red_pcb(n))
                board.Add(ni)
                redes[n] = ni

    # ---------------------------------------------------------------- footprints
    fps = {}
    for c in COMPONENTES:
        lib, name = c["fp"].split(":")
        fp = pcbnew.FootprintLoad(f"{FP}/{lib}.pretty", name)
        if fp is None:
            sys.exit(f"no encontré {c['fp']}")
        fp.SetReference(c["ref"])
        fp.SetValue(c["val"])
        fp.SetFPIDAsString(c["fp"])
        fp.SetPath(pcbnew.KIID_PATH("/" + str(uuid.uuid5(_NS, c["ref"] + "/1"))))
        for p in fp.Pads():
            n = c["nets"].get(p.GetNumber())
            if n:
                p.SetNet(redes[n])
            # Regla del proveedor: diametro del pad - agujero >= 0.8 mm (anillo para soldar).
            ds_ = p.GetDrillSize()
            drill = pcbnew.ToMM(ds_.x)
            if drill > 0:
                objetivo = pcbnew.FromMM(drill + 0.9)   # 0.9 > 0.8 exigido, margen de seguridad
                sz = p.GetSize()
                nx = max(sz.x, objetivo)
                ny = max(sz.y, objetivo)
                p.SetSize(pcbnew.VECTOR2I(nx, ny))
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        fp.Reference().SetTextThickness(pcbnew.FromMM(0.12))
        board.Add(fp)
        fps[c["ref"]] = fp

    # ---------------------------------------------------------------- ubicación fija
    # Agujeros M3 en zonas libres (lejos de conectores y del SuperMini del borde derecho).
    for i, (x, y) in enumerate([(4.0, 4.0), (4.0, H - 4.0), (W - 4.0, H - 4.0), (W - 4.0, 4.0)], 1):
        mover_centro(fps[f"H{i}"], x, y)
    # SuperMini: filas a 15.24 mm, USB hacia x = W (la placa sobresale 0.8 mm del borde)
    yc, x_pin1 = 28.0, W - 1.55
    for ref, y in (("J2", yc - 7.62), ("J3", yc + 7.62)):
        orientar_fila(fps[ref], "-x")
        mover_pad1(fps[ref], x_pin1, y)
    orientar_fila(fps["J5"], "+x")       # energía, borde superior
    mover_pad1(fps["J5"], 22.0, 3.0)
    orientar_fila(fps["J4"], "+x")       # TFT
    mover_pad1(fps["J4"], 22.0, 15.0)
    orientar_fila(fps["J1"], "+y")       # sensor MAX30102, borde frontal izquierdo
    mover_pad1(fps["J1"], 8.5, 11.0)
    mover_centro(fps["BZ1"], 50.0, 8.0)

    fijos = {"H1", "H2", "H3", "H4", "J1", "J2", "J3", "J4", "J5", "BZ1"}
    ocupado = [bbox(fps[r], 0.6) for r in fijos]
    # zona del SuperMini completa (cuerpo 22.5 x 18 sobre zócalos)
    ocupado.append((W - 24.0, yc - 9.6, W + 0.5, yc + 9.6))

    # ---------------------------------------------------------------- empaque en orden lógico
    orden = ["C1", "R1", "R2", "R3", "TP1", "TP2", "TP3", "C2", "R4", "Q1", "D1",
             "C3", "D2", "R5", "R6", "C4", "TP4"]
    faltan = set(fps) - fijos - set(orden)
    assert not faltan, faltan
    x_min, y_min, x_max, y_max = 1.0, 22.0, 58.0, 47.0
    paso = 0.635
    for ref in orden:
        fp = fps[ref]
        fp.SetOrientationDegrees(0)
        x0, y0, x1, y1 = bbox(fp, 0.35)
        w, h = x1 - x0, y1 - y0
        colocado = False
        y = y_min
        while y + h <= y_max and not colocado:
            x = x_min
            while x + w <= x_max:
                cand = (x, y, x + w, y + h)
                if all(cand[2] <= o[0] or cand[0] >= o[2] or cand[3] <= o[1] or cand[1] >= o[3] for o in ocupado):
                    mover_centro(fp, x + w / 2, y + h / 2)
                    ocupado.append(bbox(fp, 0.35))
                    colocado = True
                    break
                x += paso
            y += paso
        if not colocado:
            sys.exit(f"no cupo {ref}")

    # ---------------------------------------------------------------- contorno y serigrafía
    rect(board, 0, 0, W, H, pcbnew.Edge_Cuts, 0.1)
    silk(board, "MEDIDOR PPG v1 - ITM Circuitos II", 30, H - 1.2, 1.0, pcbnew.B_SilkS)
    silk(board, "ESP32-C3 SuperMini  USB ->", W - 11.5, yc, 0.9)
    for i, t in enumerate(["5V", "G", "3V3", "4", "3", "INT", "SCL", "SDA"]):
        silk(board, t, x_pin1 - i * 2.54, yc - 7.62 - 2.2, 0.8)
    for i, t in enumerate(["5", "6", "7", "8", "9", "10", "20", "21"]):
        silk(board, t, x_pin1 - i * 2.54, yc + 7.62 + 2.2, 0.8)
    for i, t in enumerate(["B+", "SWa", "SWb", "MT+", "B-", "MT-", "5V", "G"]):
        silk(board, t, 22.0 + i * 2.54, 5.4, 0.8)
    for i, t in enumerate(["G", "V", "SCK", "SDA", "RES", "DC", "BLK"]):
        silk(board, t, 22.0 + i * 2.54, 13.0, 0.8)
    for i, t in enumerate(["VIN", "SCL", "SDA", "INT", "IRD", "RD", "G"]):
        silk(board, t, 13.2, 11.0 + i * 2.5, 0.8)

    pcbnew.SaveBoard(str(pcb_path), board)
    print("ubicado:", pcb_path)

    # ---------------------------------------------------------------- ruteo Freerouting
    # Freerouting no es determinista: se reintenta hasta que no quede ninguna conexión pendiente.
    dsn, ses = AQUI / f"{NOMBRE}.dsn", AQUI / f"{NOMBRE}.ses"
    ubicado = AQUI / f"{NOMBRE}.ubicado.kicad_pcb"
    pcbnew.SaveBoard(str(ubicado), board)
    for intento in range(1, 6):
        board = pcbnew.LoadBoard(str(ubicado))
        ses.unlink(missing_ok=True)
        if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
            sys.exit("falló export DSN")
        r = subprocess.run([str(FR), "-de", str(dsn), "-do", str(ses), "-mp", str(60 + 40 * intento), "-mt", "8"],
                           capture_output=True, text=True, timeout=900)
        if not ses.exists() or not pcbnew.ImportSpecctraSES(board, str(ses)):
            print(r.stdout[-2000:], r.stderr[-2000:])
            continue
        gnd = board.FindNet(red_pcb("GND"))
        zona(board, gnd, pcbnew.B_Cu)
        zona(board, gnd, pcbnew.F_Cu)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.BuildConnectivity()
        pend = board.GetConnectivity().GetUnconnectedCount(False)
        print(f"intento {intento}: {pend} conexiones pendientes")
        if pend == 0:
            break
    else:
        print("AVISO: quedaron conexiones sin rutear; revisar en KiCad")
    pcbnew.SaveBoard(str(pcb_path), board)
    print("ruteado:", pcb_path)


if __name__ == "__main__":
    main()
