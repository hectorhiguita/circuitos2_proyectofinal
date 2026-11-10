#!/usr/bin/env python3
"""Genera nodered/data/flows.json (Node-RED 4 + Dashboard 2.0) para el Medidor PPG.

Uso:  python3 nodered/generar_flujo.py      (desde 04_iot/)
Contrato MQTT: ../SPEC.md  (prefijo pulso/<DEVICE_ID>/)
"""
import json
import pathlib

SALIDA = pathlib.Path(__file__).parent / "data" / "flows.json"
TAB = "tab_pulso"
nodos = []


def n(**kw):
    kw.setdefault("z", TAB)
    nodos.append(kw)
    return kw["id"]


# ------------------------------------------------------------------ configuración
nodos.append({"id": TAB, "type": "tab", "label": "Medidor PPG", "disabled": False,
              "info": "Flujo del Medidor de ritmo cardiaco PPG. Ver 04_iot/README.md"})

nodos.append({"id": "mqtt_broker", "type": "mqtt-broker", "name": "Mosquitto local",
              "broker": "${MQTT_HOST}", "port": "${MQTT_PORT}", "clientid": "nodered-pulso",
              "autoConnect": True, "usetls": False, "protocolVersion": "4", "keepalive": "60",
              "cleansession": True, "autoUnsubscribe": True,
              "birthTopic": "", "birthQos": "0", "birthPayload": "", "birthMsg": {},
              "closeTopic": "", "closeQos": "0", "closePayload": "", "closeMsg": {},
              "willTopic": "", "willQos": "0", "willPayload": "", "willMsg": {},
              "userProps": "", "sessionExpiry": ""})

nodos.append({"id": "email_alertas", "type": "e-mail", "z": TAB, "name": "Correo de alerta",
              "server": "${SMTP_HOST}", "port": "${SMTP_PORT}", "secure": True, "tls": True,
              "authtype": "BASIC", "dname": "", "to": "", "x": 1250, "y": 520, "wires": []})

nodos.append({"id": "ui_base", "type": "ui-base", "name": "Medidor PPG", "path": "/dashboard",
              "appIcon": "", "includeClientData": True,
              "acceptsClientConfig": ["ui-notification", "ui-control"],
              "showPathInSidebar": False, "headerContent": "page", "navigationStyle": "default",
              "titleBarStyle": "default", "showReconnectNotification": True,
              "notificationDisplayTime": 1, "showDisconnectNotification": True, "allowInstall": False})

nodos.append({"id": "ui_tema", "type": "ui-theme", "name": "Tema PPG",
              "colors": {"surface": "#b71c1c", "primary": "#d32f2f", "bgPage": "#f6f6f8",
                         "groupBg": "#ffffff", "groupOutline": "#e0e0e6"},
              "sizes": {"density": "default", "pagePadding": "12px", "groupGap": "12px",
                        "groupBorderRadius": "8px", "widgetGap": "12px"}})

nodos.append({"id": "ui_pagina", "type": "ui-page", "name": "Monitor de pulso", "ui": "ui_base",
              "path": "/", "icon": "heart-pulse", "layout": "grid", "theme": "ui_tema",
              "breakpoints": [{"name": "Default", "px": "0", "cols": "3"},
                              {"name": "Tablet", "px": "576", "cols": "6"},
                              {"name": "Small Desktop", "px": "768", "cols": "9"},
                              {"name": "Desktop", "px": "1024", "cols": "12"}],
              "order": 1, "className": "", "visible": "true", "disabled": "false"})


def grupo(gid, nombre, ancho, orden):
    nodos.append({"id": gid, "type": "ui-group", "name": nombre, "page": "ui_pagina",
                  "width": str(ancho), "height": "1", "order": orden, "showTitle": True,
                  "className": "", "visible": "true", "disabled": "false", "groupType": "default"})


grupo("g_vivo", "Pulso en vivo", 3, 1)
grupo("g_onda", "Onda PPG (Punto 6)", 9, 2)
grupo("g_hist", "Historial de BPM (30 min)", 6, 3)
grupo("g_equipo", "Estado del equipo", 3, 4)
grupo("g_ajustes", "Umbrales de alerta", 3, 5)
grupo("g_alertas", "Registro de alertas", 12, 6)


def texto(nid, g, orden, etiqueta, tam=16, x=0, y=0, layout="row-spread"):
    return n(id=nid, type="ui-text", group=g, order=orden, width="0", height="0", name=etiqueta,
             label=etiqueta, format="{{msg.payload}}", layout=layout, style=tam != 16,
             font="Helvetica", fontSize=tam, color="#222222", wrapText=False, className="",
             value="payload", valueType="msg", x=x, y=y, wires=[])


# ------------------------------------------------------------------ funciones
F_FILTRO = r"""
// Filtra por DEVICE_ID y guarda el último estado
const id = msg.topic.split('/')[1];
if (id !== (env.get('DEVICE_ID') || 'medidor01')) return null;
const e = msg.payload;
if (typeof e !== 'object' || e === null) return null;
const ahora = Date.now();
flow.set('ultimo_estado', ahora);
flow.set('estado', e);
const bpmTxt = (e.dedo && e.bpm > 0) ? String(e.bpm) : '--';
const zona = !e.dedo ? 'Sin dedo' : !e.senal_ok ? 'Señal débil' : 'Midiendo';
return [
  { payload: bpmTxt },
  (e.dedo && e.bpm > 0) ? { payload: e.bpm } : null,
  (e.dedo && e.bpm > 0) ? { topic: 'BPM', payload: e.bpm, timestamp: ahora } : null,
  [
    { payload: zona },
    { payload: (e.bat_pct !== undefined ? e.bat_pct + ' %  ' : '') + (e.bat_v !== undefined ? e.bat_v.toFixed(2) + ' V' : '') },
    { payload: (e.rssi !== undefined ? e.rssi + ' dBm' : '--') },
    { payload: new Date(ahora).toLocaleTimeString('es-CO', { timeZone: env.get('TZ') || 'America/Bogota' }) }
  ],
  { topic: 'estado', payload: e },
  { payload: e }
];
"""

F_ONDA = r"""
const id = msg.topic.split('/')[1];
if (id !== (env.get('DEVICE_ID') || 'medidor01')) return null;
const p = msg.payload;
if (!p || !Array.isArray(p.v)) return null;
// Hora local del servidor; el t0 del equipo es millis() desde el arranque.
const fs = p.fs || 50, dt = 1000 / fs;
let t = context.get('t') || 0;
const ahora = Date.now();
if (ahora - t > 1500 || t > ahora + 1500) t = ahora - p.v.length * dt;
const puntos = p.v.map((mv) => { t += dt; return { x: Math.round(t), y: mv / 1000 }; });
context.set('t', t);
const salida = [{ payload: puntos }];
if (String(env.get('LOG_ONDA')) === 'true') salida.push({ onda: puntos });
else salida.push(null);
return salida;
"""

F_ONLINE = r"""
const id = msg.topic.split('/')[1];
if (id !== (env.get('DEVICE_ID') || 'medidor01')) return null;
const on = String(msg.payload) === '1';
flow.set('online', on);
if (on) flow.set('ultimo_estado', Date.now());
return [{ payload: on ? 'En línea' : 'Desconectado' }, { topic: 'online', payload: on }];
"""

F_ALERTA_EQUIPO = r"""
const id = msg.topic.split('/')[1];
if (id !== (env.get('DEVICE_ID') || 'medidor01')) return null;
msg.topic = 'alerta_equipo';
return msg;
"""

# Motor de alertas del servidor (independiente del equipo). Reglas: ../SPEC.md
F_MOTOR = r"""
const ahora = Date.now();
const cfg = flow.get('config') || { bpm_min: Number(env.get('BPM_MIN') || 50), bpm_max: Number(env.get('BPM_MAX') || 120) };
const enfr = Number(env.get('ALERT_COOLDOWN_S') || 300) * 1000;
const enfrBat = 30 * 60 * 1000;
let s = context.get('s') || { fuera: {}, hist: [], ult: {}, ultimaValida: 0, sinDedoDesde: 0, desconectado: false };

function disparar(tipo, bpm, umbral, detalle, origen) {
  const cd = tipo === 'bateria_baja' ? enfrBat : enfr;
  if (s.ult[tipo] && ahora - s.ult[tipo] < cd) return null;
  s.ult[tipo] = ahora;
  return { topic: 'alerta', payload: { tipo, bpm, umbral, detalle, origen: origen || 'servidor', t: ahora } };
}
const salida = [];

if (msg.topic === 'alerta_equipo') {
  const a = msg.payload || {};
  // El equipo también decide; se registra, pero el envío comparte enfriamiento con el servidor.
  const r = disparar(a.tipo || 'equipo', a.bpm || 0, a.umbral || null, 'Reportada por el equipo', 'equipo');
  if (r) salida.push(r);
}

if (msg.topic === 'estado') {
  const e = msg.payload;
  s.desconectado = false;
  const valido = e.dedo && e.senal_ok && e.bpm > 0;
  if (valido) {
    s.ultimaValida = ahora;
    s.sinDedoDesde = 0;
    // Hueco > 5 s (sin dedo, reconexión): la tendencia empieza de cero
    const ultH = s.hist[s.hist.length - 1];
    if (ultH && ahora - ultH.t > 5000) s.hist = [];
    s.hist.push({ t: ahora, bpm: e.bpm });
    s.hist = s.hist.filter((h) => ahora - h.t <= 35000);
    // Fuera de rango sostenido 10 s
    for (const [tipo, cond, umbral] of [['alto', e.bpm > cfg.bpm_max, cfg.bpm_max], ['bajo', e.bpm < cfg.bpm_min, cfg.bpm_min]]) {
      if (cond) {
        s.fuera[tipo] = s.fuera[tipo] || ahora;
        if (ahora - s.fuera[tipo] >= 10000) {
          const r = disparar(tipo, e.bpm, umbral, (tipo === 'alto' ? 'Pulso alto' : 'Pulso bajo') + ' por más de 10 s');
          if (r) salida.push(r);
        }
      } else s.fuera[tipo] = 0;
    }
    // Tendencia: cambio > 25 lpm en 30 s (alerta temprana)
    const viejo = s.hist.find((h) => ahora - h.t >= 28000);
    if (viejo) {
      const d = e.bpm - viejo.bpm;
      if (d > 25) { const r = disparar('subida_rapida', e.bpm, null, 'Subió ' + d + ' lpm en 30 s'); if (r) salida.push(r); }
      if (d < -25) { const r = disparar('bajada_rapida', e.bpm, null, 'Bajó ' + (-d) + ' lpm en 30 s'); if (r) salida.push(r); }
    }
  } else {
    s.fuera = {};
    if (!s.sinDedoDesde) s.sinDedoDesde = ahora;
    // Señal perdida a mitad de una medición (hubo lectura válida en los últimos 5 min)
    if (ahora - s.sinDedoDesde >= 60000 && ahora - s.ultimaValida < 5 * 60000) {
      const r = disparar('sin_senal', 0, null, 'Sin señal válida por 60 s'); if (r) salida.push(r);
    }
  }
  if (typeof e.bat_v === 'number' && e.bat_v > 0 && e.bat_v < 3.4) {
    const r = disparar('bateria_baja', e.bpm || 0, 3.4, 'Batería ' + e.bat_v.toFixed(2) + ' V (' + (e.bat_pct ?? '?') + ' %)');
    if (r) salida.push(r);
  }
}

if (msg.topic === 'online' && msg.payload === false) {
  s.hist = [];
  if (!s.desconectado) { s.desconectado = true; const r = disparar('desconectado', 0, null, 'El equipo se desconectó (LWT)'); if (r) salida.push(r); }
}

if (msg.topic === 'tick') {
  const ult = flow.get('ultimo_estado') || 0;
  if (ult && ahora - ult > 60000 && !s.desconectado) {
    s.desconectado = true;
    const r = disparar('desconectado', 0, null, 'Sin datos del equipo por 60 s');
    if (r) salida.push(r);
  }
}

context.set('s', s);
return [salida];
"""

F_TABLA = r"""
const a = msg.payload;
const nombres = { alto: 'Pulso alto', bajo: 'Pulso bajo', subida_rapida: 'Subida rápida', bajada_rapida: 'Bajada rápida',
  sin_senal: 'Sin señal', desconectado: 'Equipo desconectado', bateria_baja: 'Batería baja' };
const hora = new Date(a.t).toLocaleString('es-CO', { timeZone: env.get('TZ') || 'America/Bogota' });
const fila = { Hora: hora, Tipo: nombres[a.tipo] || a.tipo, BPM: a.bpm || '--', Detalle: a.detalle, Origen: a.origen };
const notif = { payload: '⚠ ' + fila.Tipo + (a.bpm ? ' — ' + a.bpm + ' lpm' : '') + '. ' + a.detalle };
msg.texto = '⚠ ALERTA Medidor PPG (' + (env.get('DEVICE_ID') || 'medidor01') + ')\n' + fila.Tipo +
  (a.bpm ? ': ' + a.bpm + ' lpm' : '') + (a.umbral ? ' (umbral ' + a.umbral + ')' : '') + '\n' + a.detalle + '\n' + hora;
msg.fila = fila;
return [{ payload: [fila] }, notif, msg];
"""

F_CORREO = r"""
const user = (env.get('SMTP_USER') || '').trim();
const to = (env.get('EMAIL_TO') || '').trim();
if (!user || !to) { node.warn('[correo] no configurado, se enviaría: ' + msg.texto.replace(/\n/g, ' | ')); return null; }
return { to, from: user, topic: 'Alerta Medidor PPG: ' + msg.fila.Tipo, payload: msg.texto };
"""

F_WHATSAPP = r"""
const tels = (env.get('CALLMEBOT_PHONE') || '').split(',').map((x) => x.trim()).filter(Boolean);
const keys = (env.get('CALLMEBOT_APIKEY') || '').split(',').map((x) => x.trim()).filter(Boolean);
if (!tels.length || tels.length !== keys.length) {
  node.warn('[whatsapp] no configurado, se enviaría: ' + msg.texto.replace(/\n/g, ' | '));
  return null;
}
return [tels.map((tel, i) => ({
  url: 'https://api.callmebot.com/whatsapp.php?phone=' + encodeURIComponent(tel) +
       '&text=' + encodeURIComponent(msg.texto) + '&apikey=' + encodeURIComponent(keys[i]),
  method: 'GET', telefono: tel
}))];
"""

F_RESP_WA = r"""
if (msg.statusCode !== 200) node.warn('[whatsapp] ' + msg.telefono + ' respondió ' + msg.statusCode + ': ' + String(msg.payload).slice(0, 200));
else node.log('[whatsapp] enviado a ' + msg.telefono);
return null;
"""

F_CSV = r"""
const fs = global.get('fs'), path = global.get('path');
const dir = '/data/registros';
const d = new Date();
const dia = d.toLocaleDateString('sv-SE', { timeZone: env.get('TZ') || 'America/Bogota' });
const iso = d.toISOString();
try { fs.mkdirSync(dir, { recursive: true }); } catch (e) {}
function escribir(nombre, cab, linea) {
  const f = path.join(dir, nombre + '_' + dia + '.csv');
  if (!fs.existsSync(f)) fs.writeFileSync(f, cab + '\n');
  fs.appendFileSync(f, linea + '\n');
}
if (msg.topic === 'alerta') {
  const a = msg.payload;
  escribir('alertas', 'fecha_iso,tipo,bpm,umbral,origen,detalle', [iso, a.tipo, a.bpm, a.umbral ?? '', a.origen, '"' + a.detalle + '"'].join(','));
} else if (msg.onda) {
  escribir('onda', 'tiempo_ms,voltaje_v', msg.onda.map((p) => p.x + ',' + p.y.toFixed(4)).join('\n'));
} else {
  const e = msg.payload;
  escribir('estado', 'fecha_iso,bpm,dedo,senal_ok,bat_v,bat_pct,rssi', [iso, e.bpm, e.dedo, e.senal_ok, e.bat_v ?? '', e.bat_pct ?? '', e.rssi ?? ''].join(','));
}
return null;
"""

F_CONFIG_RX = r"""
const id = msg.topic.split('/')[1];
if (id !== (env.get('DEVICE_ID') || 'medidor01')) return null;
const c = msg.payload;
if (typeof c !== 'object' || c === null) return null;
flow.set('config', c);
return { payload: { bpm_min: c.bpm_min, bpm_max: c.bpm_max, buzzer: !!c.buzzer } };
"""

F_CONFIG_TX = r"""
const p = msg.payload || {};
let min = Math.round(Number(p.bpm_min)), max = Math.round(Number(p.bpm_max));
if (!(min >= 30 && max <= 220 && min < max)) {
  node.warn('Umbrales inválidos: ' + JSON.stringify(p));
  return [null, { payload: 'Umbrales inválidos: mínimo ≥ 30, máximo ≤ 220 y mínimo < máximo.' }];
}
const c = { bpm_min: min, bpm_max: max, buzzer: !!p.buzzer };
flow.set('config', c);
return [{ topic: 'pulso/' + (env.get('DEVICE_ID') || 'medidor01') + '/config', payload: c, retain: true, qos: 1 },
        { payload: 'Umbrales guardados: ' + min + '–' + max + ' lpm' }];
"""

F_CONFIG_DEF = r"""
// Al arrancar: si el broker no tenía config retenida, publica la de .env
if (flow.get('config')) return null;
const c = { bpm_min: Number(env.get('BPM_MIN') || 50), bpm_max: Number(env.get('BPM_MAX') || 120), buzzer: true };
flow.set('config', c);
return { topic: 'pulso/' + (env.get('DEVICE_ID') || 'medidor01') + '/config', payload: c, retain: true, qos: 1 };
"""


def fn(nid, nombre, codigo, salidas, wires, x, y):
    return n(id=nid, type="function", name=nombre, func=codigo.strip(), outputs=salidas,
             timeout=0, noerr=0, initialize="", finalize="", libs=[], x=x, y=y, wires=wires)


def mqtt_in(nid, topico, wires, x, y, tipo="json"):
    return n(id=nid, type="mqtt in", name=topico, topic=topico, qos="0", datatype=tipo,
             broker="mqtt_broker", nl=False, rap=True, rh=0, inputs=0, x=x, y=y, wires=wires)


# ------------------------------------------------------------------ entradas MQTT
mqtt_in("in_estado", "pulso/+/estado", [["f_estado"]], 130, 80)
mqtt_in("in_onda", "pulso/+/onda", [["f_onda"]], 130, 220)
mqtt_in("in_online", "pulso/+/online", [["f_online"]], 130, 300, tipo="utf8")
mqtt_in("in_alerta", "pulso/+/alerta", [["f_alerta_eq"]], 130, 380)
mqtt_in("in_config", "pulso/+/config", [["f_config_rx"]], 130, 640)

fn("f_estado", "Estado del equipo", F_FILTRO, 6,
   [["t_bpm"], ["gauge_bpm"], ["chart_hist"],
    ["t_senal", "t_bat", "t_rssi", "t_hora"], ["f_motor"], ["f_csv"]], 360, 80)
fn("f_onda", "Onda -> puntos", F_ONDA, 2, [["chart_onda"], ["f_csv"]], 360, 220)
fn("f_online", "En línea", F_ONLINE, 2, [["t_online"], ["f_motor"]], 360, 300)
fn("f_alerta_eq", "Alerta del equipo", F_ALERTA_EQUIPO, 1, [["f_motor"]], 360, 380)

n(id="tick", type="inject", name="cada 5 s", props=[{"p": "topic", "vt": "str"}], repeat="5",
  crontab="", once=True, onceDelay="5", topic="tick", x=130, y=440, wires=[["f_motor"]])

fn("f_motor", "Motor de alertas", F_MOTOR, 1, [["f_tabla", "f_csv"]], 620, 380)
fn("f_tabla", "Formato alerta", F_TABLA, 3, [["tabla_alertas"], ["notif"], ["f_correo", "f_wa"]], 860, 380)
fn("f_correo", "Correo (si hay SMTP)", F_CORREO, 1, [["email_alertas"]], 1060, 520)
fn("f_wa", "WhatsApp CallMeBot", F_WHATSAPP, 1, [["http_wa"]], 1060, 580)
n(id="http_wa", type="http request", name="CallMeBot", method="use", ret="txt", paytoqs="ignore",
  url="", tls="", persist=False, proxy="", insecureHTTPParser=False, authType="", senderr=False,
  headers=[], x=1250, y=580, wires=[["f_resp_wa"]])
fn("f_resp_wa", "Resultado WhatsApp", F_RESP_WA, 1, [[]], 1430, 580)
fn("f_csv", "Registro CSV", F_CSV, 1, [[]], 860, 160)

# Ajustes
fn("f_config_rx", "Config retenida", F_CONFIG_RX, 1, [["form_cfg"]], 360, 640)
n(id="cfg_arranque", type="inject", name="al arrancar", props=[], repeat="", crontab="",
  once=True, onceDelay="4", topic="", x=130, y=700, wires=[["f_config_def"]])
fn("f_config_def", "Config por defecto", F_CONFIG_DEF, 1, [["out_config"]], 360, 700)
fn("f_config_tx", "Validar y publicar", F_CONFIG_TX, 2, [["out_config"], ["notif"]], 860, 660)
n(id="out_config", type="mqtt out", name="config (retenido)", topic="", qos="", retain="",
  respTopic="", contentType="", userProps="", correl="", expiry="", broker="mqtt_broker",
  x=1080, y=680, wires=[])

# ------------------------------------------------------------------ widgets
texto("t_bpm", "g_vivo", 1, "BPM", tam=56, x=620, y=40, layout="col-center")
n(id="gauge_bpm", type="ui-gauge", name="BPM", group="g_vivo", order=2, width="0", height="4",
  gtype="gauge-half", gstyle="rounded", title="Frecuencia cardiaca", alwaysShowTitle=False,
  floatingTitlePosition="top-left", units="lpm", icon="heart", prefix="", suffix="",
  segments=[{"from": "30", "color": "#1e88e5", "text": "", "textType": "label"},
            {"from": "50", "color": "#43a047", "text": "", "textType": "label"},
            {"from": "100", "color": "#fbc02d", "text": "", "textType": "label"},
            {"from": "120", "color": "#e53935", "text": "", "textType": "label"}],
  min="30", max="200", sizeThickness=16, sizeGap=4, sizeKeyThickness=8, styleRounded=True,
  styleGlow=False, className="", value="payload", valueType="msg", x=620, y=80, wires=[])


def chart(nid, g, orden, etiqueta, alto, x, y, **extra):
    base = dict(id=nid, type="ui-chart", group=g, name=etiqueta, label=etiqueta, order=orden,
                chartType="line", category="topic", categoryType="msg", xAxisLabel="",
                xAxisProperty="", xAxisPropertyType="timestamp", xAxisType="time",
                xAxisFormat="", xAxisFormatType="auto", xmin="", xmax="", yAxisLabel="",
                yAxisProperty="payload", yAxisPropertyType="msg", ymin="", ymax="",
                bins=10, action="append", stackSeries=False, pointShape="false", pointRadius=0,
                showLegend=False, removeOlder="1", removeOlderUnit="3600", removeOlderPoints="",
                colors=["#d32f2f", "#1e88e5", "#43a047", "#fbc02d", "#8e24aa", "#00acc1",
                        "#f4511e", "#6d4c41", "#546e7a"],
                textColor=["#666666"], textColorDefault=True, gridColor=["#e5e5e5"],
                gridColorDefault=True, width="0", height=str(alto), className="",
                interpolation="linear", x=x, y=y, wires=[[]])
    base.update(extra)
    return n(**base)


chart("chart_onda", "g_onda", 1, "Voltaje (V)", 6, 620, 220, category="PPG", categoryType="str",
      xAxisProperty="x", xAxisPropertyType="property", yAxisProperty="y",
      yAxisPropertyType="property", ymin="0", ymax="2.5", removeOlderPoints="300",
      yAxisLabel="V", xAxisFormat="HH:mm:ss", xAxisFormatType="custom")
chart("chart_hist", "g_hist", 1, "BPM", 5, 620, 120, removeOlder="30", removeOlderUnit="60",
      ymin="30", ymax="200", pointShape="circle", pointRadius=2, yAxisLabel="lpm",
      xAxisFormat="HH:mm", xAxisFormatType="custom")

texto("t_online", "g_equipo", 1, "Conexión", x=620, y=300)
texto("t_senal", "g_equipo", 2, "Señal", x=620, y=160)
texto("t_bat", "g_equipo", 3, "Batería", x=620, y=180)
texto("t_rssi", "g_equipo", 4, "WiFi", x=620, y=200)
texto("t_hora", "g_equipo", 5, "Último dato", x=620, y=240)

n(id="tabla_alertas", type="ui-table", group="g_alertas", name="Alertas", label="", order=1,
  width="0", height="0", maxrows=10, passthru=False, autocols=True, showSearch=False,
  deselect=True, selectionType="none", columns=[], mobileBreakpoint="sm",
  mobileBreakpointType="defaults", action="append", className="", x=1060, y=340, wires=[[]])

n(id="notif", type="ui-notification", ui="ui_base", position="top right", colorDefault=False,
  color="#d32f2f", displayTime="8", showCountdown=True, outputs=0, allowDismiss=True,
  dismissText="Cerrar", allowConfirm=False, confirmText="", raw=False, className="",
  name="Aviso", x=1060, y=400, wires=[])

n(id="form_cfg", type="ui-form", group="g_ajustes", name="Umbrales", label="", order=1,
  width="0", height="0",
  options=[{"label": "BPM mínimo", "key": "bpm_min", "type": "number", "required": True, "rows": None},
           {"label": "BPM máximo", "key": "bpm_max", "type": "number", "required": True, "rows": None},
           {"label": "Pitido en cada latido", "key": "buzzer", "type": "checkbox", "required": False, "rows": None}],
  formValue={"bpm_min": "50", "bpm_max": "120", "buzzer": True},
  payload="", submit="Guardar", cancel="Restaurar", resetOnSubmit=False, topic="topic",
  topicType="msg", splitLayout="", className="", passthru=False, dropdownOptions=[],
  x=620, y=660, wires=[["f_config_tx"]])

SALIDA.write_text(json.dumps(nodos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{SALIDA} ({len(nodos)} nodos)")
