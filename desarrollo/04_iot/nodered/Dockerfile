# Node-RED 4 + Dashboard 2.0 (@flowfuse/node-red-dashboard) + correo (node-red-node-email).
# Los nodos se instalan DENTRO de la imagen (/usr/src/node-red/node_modules) para que el
# directorio /data montado desde el host (settings.js, flows.json, registros CSV) no los oculte.
ARG NODE_RED_VERSION=4.1
FROM nodered/node-red:${NODE_RED_VERSION}

RUN npm install --no-audit --no-fund --omit=dev \
      @flowfuse/node-red-dashboard@1.35.0 \
      node-red-node-email@3.1.0 \
    && npm cache clean --force

# Genera /data/flows_cred.json a partir de variables de entorno (.env) en cada arranque,
# así ningún secreto queda escrito en flows.json.
COPY generar-credenciales.js /usr/src/node-red/generar-credenciales.js
COPY arranque.sh /usr/src/node-red/arranque.sh
USER root
RUN chmod 0755 /usr/src/node-red/arranque.sh && chmod 0644 /usr/src/node-red/generar-credenciales.js
USER node-red

ENTRYPOINT ["/usr/src/node-red/arranque.sh"]
