/**
 * Configuración de Node-RED para el Medidor PPG.
 * Los nodos (Dashboard 2.0, correo) vienen instalados en la imagen Docker.
 * Secretos: SOLO en 04_iot/.env (ver .env.example). flows_cred.json se regenera al arrancar.
 */
const fs = require('fs')
const path = require('path')

const settings = {
    flowFile: 'flows.json',
    flowFilePretty: true,
    // flows_cred.json en texto plano: lo genera generar-credenciales.js desde el .env
    credentialSecret: false,

    uiPort: process.env.PORT || 1880,
    httpAdminRoot: '/',
    httpNodeRoot: '/',

    diagnostics: { enabled: false, ui: false },
    runtimeState: { enabled: false, ui: false },
    telemetry: { enabled: false },

    logging: {
        console: { level: process.env.NODE_RED_LOG_LEVEL || 'info', metrics: false, audit: false }
    },

    // Contexto persistente en disco (/data/context): registro de alertas, enfriamientos, etc.
    contextStorage: {
        default: { module: 'localfilesystem', config: { flushInterval: 10 } },
        memory: { module: 'memory' }
    },
    exportGlobalContextKeys: false,

    // Módulos de Node.js disponibles para los nodos function (global.get('fs'))
    functionGlobalContext: { fs, path },
    functionExternalModules: false,

    externalModules: {
        autoInstall: false,
        palette: { allowInstall: true },
        modules: { allowInstall: false }
    },

    mqttReconnectTime: 5000,
    debugMaxLength: 1000,

    editorTheme: {
        page: { title: 'Medidor PPG · Node-RED' },
        header: { title: 'Medidor PPG · Node-RED' },
        projects: { enabled: false },
        tours: false
    }
}

// Protección opcional del editor/API (recomendado si se abre el puerto 1880 a la LAN).
// Genere el hash con:  docker compose exec nodered node-red admin hash-pw
if (process.env.NODERED_ADMIN_USER && process.env.NODERED_ADMIN_HASH) {
    settings.adminAuth = {
        type: 'credentials',
        users: [{ username: process.env.NODERED_ADMIN_USER, password: process.env.NODERED_ADMIN_HASH, permissions: '*' }]
    }
}
// Protección opcional del dashboard y de /registros (autenticación básica HTTP).
if (process.env.DASHBOARD_USER && process.env.DASHBOARD_HASH) {
    settings.httpNodeAuth = { user: process.env.DASHBOARD_USER, pass: process.env.DASHBOARD_HASH }
}

module.exports = settings
