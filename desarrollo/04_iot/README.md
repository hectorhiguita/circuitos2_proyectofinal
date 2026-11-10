# Servidor IoT — MQTT + Node-RED (tablero, alertas por correo y WhatsApp)

```
ESP32-C3 --MQTT 1883--> Mosquitto --> Node-RED --> Tablero web (gráficas)
                                          |------> Motor de alertas --> Correo (Gmail)
                                          |                        \--> WhatsApp (CallMeBot)
                                          \------> Registro CSV (/nodered/data/registros)
```

Contrato de tópicos: `../SPEC.md` (prefijo `pulso/<DEVICE_ID>/`).

## 1. Arrancar (Linux, macOS o Windows con Docker Desktop)
```bash
cd 04_iot
./scripts/generar_passwd.sh          # crea .env y las claves MQTT
docker compose up -d --build
```
- Tablero: <http://localhost:1880/dashboard>
- Editor Node-RED: <http://localhost:1880>
- Clave del ESP32: `MQTT_DEVICE_PASS` dentro de `04_iot/.env` (usuario `medidor`)

Apagar: `docker compose down`. Los datos se conservan.

## 2. Probar sin el equipo (simulador)
```bash
python3 -m venv .venv && .venv/bin/pip install paho-mqtt
.venv/bin/python simulador.py --password <MQTT_DEVICE_PASS> --escenario normal
```
Escenarios: `normal`, `taquicardia`, `bradicardia`, `sin_dedo`, `bateria_baja`.

## 3. Alertas
| Tipo | Regla | Espera entre avisos |
|---|---|---|
| Pulso alto | BPM > máximo por 10 s | 5 min |
| Pulso bajo | BPM < mínimo por 10 s | 5 min |
| Subida rápida | +25 lpm en 30 s (alerta temprana) | 5 min |
| Bajada rápida | −25 lpm en 30 s (alerta temprana) | 5 min |
| Sin señal | 60 s sin señal válida en plena medición | 5 min |
| Desconectado | Sin datos 60 s, o LWT `online=0` | 5 min |
| Batería baja | < 3.4 V | 30 min |

Los umbrales se cambian en el tablero ("Umbrales de alerta"). Se guardan retenidos en `pulso/<id>/config` y el ESP32 los recibe.

Sin claves configuradas, el registro de Node-RED muestra `no configurado, se enviaría: …`. No falla.

### Correo (Gmail)
1. Activar verificación en 2 pasos en la cuenta Google.
2. Crear una contraseña de aplicación: <https://myaccount.google.com/apppasswords>.
3. En `.env`: `SMTP_USER=tucorreo@gmail.com`, `SMTP_PASS=<16 letras>`, `EMAIL_TO=destino1@x.com,destino2@y.com`.

### WhatsApp (CallMeBot, gratis)
1. Guardar el contacto **+34 644 66 32 62** (ver número actual en <https://www.callmebot.com/blog/free-api-whatsapp-messages/>).
2. Enviarle por WhatsApp: `I allow callmebot to send me messages`.
3. Llega un mensaje con tu `apikey`.
4. En `.env`: `CALLMEBOT_PHONE=+57300xxxxxxx`, `CALLMEBOT_APIKEY=123456`. Varios números: separados por coma, en el mismo orden.

Después de editar `.env`: `docker compose up -d` (reinicia Node-RED).

## 4. Conectar el ESP32
1. IP del PC: `ip -4 addr` (Linux) o `ipconfig` (Windows). Ejemplo: `192.168.1.50`.
2. En `03_firmware/include/secrets.h`: `MQTT_HOST "192.168.1.50"`, `MQTT_USER "medidor"`, `MQTT_PASS "<MQTT_DEVICE_PASS>"`.
3. Abrir el puerto 1883 en el firewall:
   - Linux (ufw): `sudo ufw allow 1883/tcp`
   - Linux (firewalld): `sudo firewall-cmd --add-port=1883/tcp --permanent && sudo firewall-cmd --reload`
   - Windows: `netsh advfirewall firewall add rule name="MQTT" dir=in action=allow protocol=TCP localport=1883`
4. En la universidad: comparte internet desde el celular. Conecta el PC y el ESP32 a esa red.

## 5. Ver el tablero desde el celular
En `.env`: `NODERED_BIND=0.0.0.0`, y define `DASHBOARD_USER` y `DASHBOARD_HASH`:
`docker compose exec nodered node-red admin hash-pw`. Luego abre `http://<IP_PC>:1880/dashboard`.

**Riesgo:** sin usuario y clave, cualquiera en la misma red ve y cambia el tablero.

## 6. Raspberry Pi (opcional)
Igual que en el PC: instalar Docker (`curl -fsSL https://get.docker.com | sh`), copiar `04_iot/` y seguir el paso 1. Las imágenes sirven en ARM64.

## 7. Datos para el informe
`nodered/data/registros/estado_AAAA-MM-DD.csv` (1 fila/s) y `alertas_AAAA-MM-DD.csv`.
Con `LOG_ONDA=true` en `.env` también se guarda `onda_*.csv` (50 muestras/s).

## Archivos
| Archivo | Qué es |
|---|---|
| `docker-compose.yml` | Mosquitto + Node-RED |
| `nodered/generar_flujo.py` | Genera `nodered/data/flows.json`. Editar aquí y volver a correrlo |
| `simulador.py` | Datos falsos con el mismo contrato MQTT |
| `scripts/generar_passwd.sh` | Claves MQTT y ACL |

## Prueba hecha (2026-11-06)
Servidor en Docker + simulador. Se dispararon `subida_rapida`, `alto`, `desconectado`, `bajada_rapida`, `bajo` y `bateria_baja`. Se escribieron los CSV. El tablero respondió HTTP 200. Los 46 nodos se desplegaron sin errores. Falta verlo en un navegador y probarlo con el ESP32 real.
