#!/usr/bin/env python3
"""Simulador del Medidor PPG: publica datos falsos con el mismo contrato MQTT del firmware.

  pip install paho-mqtt
  python3 simulador.py --host localhost --user medidor --password <MQTT_DEVICE_PASS> --escenario normal

Escenarios: normal (72), taquicardia (sube a 140), bradicardia (45), sin_dedo, bateria_baja.
"""
import argparse
import json
import math
import random
import time

import paho.mqtt.client as mqtt


def bpm_objetivo(esc, t):
    if esc == "taquicardia":
        return min(72 + t * 2.0, 140)          # sube ~2 lpm/s -> dispara tendencia y "alto"
    if esc == "bradicardia":
        return max(72 - t * 1.5, 45)
    return 72


def ppg(fase):
    """Forma de onda PPG: pico sistólico + muesca dicrótica, en 0..1."""
    s = math.exp(-((fase - 0.15) / 0.07) ** 2)
    d = 0.35 * math.exp(-((fase - 0.45) / 0.10) ** 2)
    return s + d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--user", default="medidor")
    ap.add_argument("--password", default="")
    ap.add_argument("--id", default="medidor01", help="DEVICE_ID")
    ap.add_argument("--escenario", default="normal",
                    choices=["normal", "taquicardia", "bradicardia", "sin_dedo", "bateria_baja"])
    ap.add_argument("--duracion", type=float, default=0, help="segundos (0 = sin fin)")
    a = ap.parse_args()

    pre = f"pulso/{a.id}/"
    cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"sim-{a.id}-{random.randint(0, 9999)}")
    if a.user:
        cli.username_pw_set(a.user, a.password)
    cli.will_set(pre + "online", "0", retain=True)
    cli.connect(a.host, a.port, 30)
    cli.loop_start()
    cli.publish(pre + "online", "1", retain=True)
    print(f"Conectado a {a.host}:{a.port} como {a.user}. Escenario: {a.escenario}. Ctrl+C para salir.")

    fs = 50
    t0 = time.time()
    fase, ultimo_lat, bpm_med = 0.0, 0.0, 72.0
    onda, prox_estado = [], 0.0
    try:
        while True:
            ahora = time.time()
            t = ahora - t0
            if a.duracion and t > a.duracion:
                break
            dedo = a.escenario != "sin_dedo"
            bpm = bpm_objetivo(a.escenario, t) + random.uniform(-1.5, 1.5)
            fase += bpm / 60 / fs
            if fase >= 1:
                fase -= 1
                ibi = int((t - ultimo_lat) * 1000) if ultimo_lat else int(60000 / bpm)
                ultimo_lat = t
                bpm_med = 0.7 * bpm_med + 0.3 * (60000 / max(ibi, 1))
                if dedo:
                    cli.publish(pre + "latido", json.dumps({"t": int(t * 1000), "ibi": ibi, "bpm": round(bpm_med)}))
            if dedo:
                mv = 1320 + 600 * (ppg(fase) - 0.4) + random.gauss(0, 15)
            else:
                mv = 1320 + random.gauss(0, 5)
            onda.append(int(mv))
            if len(onda) >= 25:                      # 4 Hz x 25 muestras = 50 Hz
                cli.publish(pre + "onda", json.dumps({"t0": int(t * 1000), "fs": fs, "v": onda}))
                onda = []
            if t >= prox_estado:                     # 1 Hz
                prox_estado = t + 1
                bat_v = 3.35 if a.escenario == "bateria_baja" else 3.92
                bat_pct = 3 if a.escenario == "bateria_baja" else 72
                est = {"bpm": round(bpm_med) if dedo else 0, "dedo": dedo, "senal_ok": dedo,
                       "bat_v": bat_v, "bat_pct": bat_pct, "rssi": random.randint(-68, -55),
                       "uptime": int(t)}
                cli.publish(pre + "estado", json.dumps(est))
                print(f"t={t:5.0f}s  {est}")
            time.sleep(max(0, 1 / fs - (time.time() - ahora)))
    except KeyboardInterrupt:
        pass
    finally:
        cli.publish(pre + "online", "0", retain=True).wait_for_publish(2)
        cli.loop_stop()
        cli.disconnect()


if __name__ == "__main__":
    main()
