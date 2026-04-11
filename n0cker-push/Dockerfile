FROM node:18-alpine

# Instalar dependencias del sistema
RUN apk add --no-cache tini

# Crear directorio de la aplicación
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias de producción
RUN npm ci --only=production && \
    npm cache clean --force

# Copiar el código de la aplicación
COPY server.js ./
COPY public ./public

# Crear directorio para datos persistentes
RUN mkdir -p /data && \
    chown -R node:node /data

# Cambiar al usuario node por seguridad
USER node

# Exponer puerto
EXPOSE 3100

# Variables de entorno por defecto
ENV NODE_ENV=production \
    PORT=3100

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3100/api/stats', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Usar tini como init system
ENTRYPOINT ["/sbin/tini", "--"]

# Comando para iniciar la aplicación
CMD ["node", "server.js"]
