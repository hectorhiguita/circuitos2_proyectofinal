#!/bin/sh
# Escribe las credenciales (MQTT y SMTP) desde el entorno y luego arranca Node-RED normalmente.
node /usr/src/node-red/generar-credenciales.js || echo "[arranque] aviso: no se pudo generar flows_cred.json"
exec /usr/src/node-red/entrypoint.sh "$@"
