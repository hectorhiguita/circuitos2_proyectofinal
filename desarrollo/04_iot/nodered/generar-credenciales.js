// Crea /data/flows_cred.json (texto plano; settings.js usa credentialSecret:false) con las
// credenciales tomadas de las variables de entorno. Los IDs coinciden con los nodos de flows.json.
// Node-RED NO sustituye ${VAR} dentro de credenciales, por eso se generan aquí en cada arranque.
const fs = require('fs')
const path = require('path')
const dir = process.env.NODE_RED_USER_DIR || '/data'
const e = (k) => (process.env[k] || '').trim()

const cred = {
  mqtt_broker: { user: e('MQTT_NODERED_USER'), password: e('MQTT_NODERED_PASS') },
  // Se escriben siempre (aunque vacíos) para que el nodo de correo no marque error al desplegar.
  email_alertas: { userid: e('SMTP_USER'), password: e('SMTP_PASS') }
}
fs.writeFileSync(path.join(dir, 'flows_cred.json'), JSON.stringify(cred, null, 2), { mode: 0o600 })
console.log('[arranque] flows_cred.json generado. MQTT usuario=' + (cred.mqtt_broker.user || '(vacío)') +
  ' | SMTP ' + (cred.email_alertas.userid ? 'configurado' : 'NO configurado (modo simulación)'))
