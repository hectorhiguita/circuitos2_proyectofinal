#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Crea/actualiza las credenciales del broker Mosquitto a partir del .env
#   - Si no existe .env, lo copia de .env.example y fija HOST_UID/HOST_GID.
#   - Si MQTT_DEVICE_PASS / MQTT_NODERED_PASS están vacías, genera claves aleatorias.
#   - Genera mosquitto/config/passwd (hash PBKDF2-SHA512) con mosquitto_passwd
#     usando la propia imagen eclipse-mosquitto:2 (no hace falta instalar nada).
#   - Reescribe mosquitto/config/acl con los nombres de usuario del .env.
# Uso:  ./scripts/generar_passwd.sh        (desde 04_iot/, Linux/macOS/WSL/Git Bash)
# ---------------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE=.env
if [[ ! -f $ENV_FILE ]]; then
  cp .env.example "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  if command -v id >/dev/null; then
    sed -i.bak "s/^HOST_UID=.*/HOST_UID=$(id -u)/; s/^HOST_GID=.*/HOST_GID=$(id -g)/" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  fi
  echo "[ok] Creado $ENV_FILE a partir de .env.example"
fi

leer() { grep -E "^$1=" "$ENV_FILE" | tail -n1 | cut -d= -f2- | tr -d '\r' ; }
fijar() { # fijar CLAVE VALOR  (reemplaza la línea en .env)
  local k=$1 v=$2
  if grep -qE "^$k=" "$ENV_FILE"; then
    sed -i.bak "s|^$k=.*|$k=$v|" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  else
    echo "$k=$v" >> "$ENV_FILE"
  fi
}
# Entrada finita: evita SIGPIPE de `tr </dev/urandom | head` con pipefail
aleatoria() { head -c 96 /dev/urandom | base64 | LC_ALL=C tr -dc 'A-Za-z0-9' | cut -c1-20; }

DEV_USER=$(leer MQTT_DEVICE_USER);   DEV_USER=${DEV_USER:-medidor}
DEV_PASS=$(leer MQTT_DEVICE_PASS)
NR_USER=$(leer MQTT_NODERED_USER);   NR_USER=${NR_USER:-nodered}
NR_PASS=$(leer MQTT_NODERED_PASS)

if [[ -z $DEV_PASS ]]; then DEV_PASS=$(aleatoria); fijar MQTT_DEVICE_PASS "$DEV_PASS"; echo "[ok] Clave aleatoria para '$DEV_USER'"; fi
if [[ -z $NR_PASS  ]]; then NR_PASS=$(aleatoria);  fijar MQTT_NODERED_PASS "$NR_PASS";  echo "[ok] Clave aleatoria para '$NR_USER'"; fi

CONF_DIR="$PWD/mosquitto/config"
mkdir -p "$CONF_DIR" mosquitto/data nodered/data/registros
# Si Docker creó mosquitto/data como root (arranque antes de este script), devolverlo al usuario
if [[ ! -w mosquitto/data ]]; then
  docker run --rm -v "$PWD/mosquitto/data:/d" eclipse-mosquitto:2 chown -R "$(id -u):$(id -g)" /d
fi

UIDGID="$(leer HOST_UID):$(leer HOST_GID)"
[[ $UIDGID == ":" ]] && UIDGID="$(id -u):$(id -g)"

# mosquitto_passwd dentro del contenedor oficial; el archivo queda del usuario del host
docker run --rm --user "$UIDGID" -v "$CONF_DIR:/work" eclipse-mosquitto:2 sh -c "
  rm -f /work/passwd &&
  touch /work/passwd && chmod 0600 /work/passwd &&
  mosquitto_passwd -b /work/passwd '$DEV_USER' '$DEV_PASS' &&
  mosquitto_passwd -b /work/passwd '$NR_USER' '$NR_PASS'"
chmod 0600 "$CONF_DIR/passwd"

cat > "$CONF_DIR/acl" <<EOF
# ACL generada por scripts/generar_passwd.sh - cada usuario solo usa el árbol pulso/#
user $NR_USER
topic readwrite pulso/#
topic read \$SYS/#

user $DEV_USER
topic readwrite pulso/#
EOF
chmod 0600 "$CONF_DIR/acl"

echo "[ok] mosquitto/config/passwd y acl generados (usuarios: $DEV_USER, $NR_USER)"
echo
echo "  Credenciales para el ESP32 (03_firmware) y el simulador:"
echo "     MQTT_USER = $DEV_USER"
echo "     MQTT_PASS = (ver MQTT_DEVICE_PASS en 04_iot/.env)"
echo
echo "  Siguiente paso:  docker compose up -d --build"
