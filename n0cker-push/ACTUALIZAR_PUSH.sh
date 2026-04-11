#!/bin/bash
echo "🚀 Actualizando sistema de notificaciones push PLASISE..."

# Ruta del proyecto en el VPS
PROJECT_PATH="/etc/easypanel/projects/n0cker/plasise/code/n0cker-push"

# Asegurar que el directorio existe
mkdir -p "$PROJECT_PATH/public"
mkdir -p "$PROJECT_PATH/data"

cd "$PROJECT_PATH"

# Copiar server.js con soporte para puerto 3100, CORS/Iframe y rutas de datos corregidas
cat > server.js << 'EOF'
const express = require('express');
const webpush = require('web-push');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3100;

// Middleware
app.use(bodyParser.json());

// CORS y headers para permitir iframe desde el dashboard de Plasise
app.use((req, res, next) => {
  const allowedOrigins = [
    'https://n0cker-plasise.v6hb8q.easypanel.host',
    'http://localhost:5000',
    'http://localhost:8080',
    'http://127.0.0.1:5000',
    'http://127.0.0.1:8080'
  ];
  const origin = req.headers.origin;
  if (allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
  }
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  // Permitir iframe desde los dominios de Plasise
  res.removeHeader('X-Frame-Options');
  res.setHeader('Content-Security-Policy', "frame-ancestors 'self' https://n0cker-plasise.v6hb8q.easypanel.host http://localhost:* http://127.0.0.1:*");
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

app.use(express.static('public'));

// Archivo para almacenar suscripciones (en producción usar /data)
const SUBSCRIPTIONS_FILE = process.env.NODE_ENV === 'production' ? '/data/subscriptions.json' : path.join(__dirname, 'data', 'subscriptions.json');
const DATA_DIR = path.dirname(SUBSCRIPTIONS_FILE);

// Asegurar que existe el directorio de datos
if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Inicializar archivo de suscripciones si no existe
if (!fs.existsSync(SUBSCRIPTIONS_FILE)) {
  fs.writeFileSync(SUBSCRIPTIONS_FILE, JSON.stringify([]));
}

// Generar VAPID keys
const vapidKeys = webpush.generateVAPIDKeys();

// En producción, usar variables de entorno
const publicVapidKey = process.env.PUBLIC_VAPID_KEY || vapidKeys.publicKey;
const privateVapidKey = process.env.PRIVATE_VAPID_KEY || vapidKeys.privateKey;

webpush.setVapidDetails(
  'mailto:info@plasise.com',
  publicVapidKey,
  privateVapidKey
);

console.log('=================================');
console.log('VAPID Keys (guarda estas keys):');
console.log('PUBLIC_VAPID_KEY:', publicVapidKey);
console.log('PRIVATE_VAPID_KEY:', privateVapidKey);
console.log('=================================');

// Función para leer suscripciones
function getSubscriptions() {
  try {
    const data = fs.readFileSync(SUBSCRIPTIONS_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return [];
  }
}

// Función para guardar suscripciones
function saveSubscriptions(subscriptions) {
  fs.writeFileSync(SUBSCRIPTIONS_FILE, JSON.stringify(subscriptions, null, 2));
}

// API: Obtener la clave pública VAPID
app.get('/api/vapidPublicKey', (req, res) => {
  res.json({ publicKey: publicVapidKey });
});

// API: Suscribirse a notificaciones
app.post('/api/subscribe', (req, res) => {
  const subscription = req.body;
  let subscriptions = getSubscriptions();
  const exists = subscriptions.some(sub => sub.endpoint === subscription.endpoint);
  if (!exists) {
    subscriptions.push({ ...subscription, subscribedAt: new Date().toISOString() });
    saveSubscriptions(subscriptions);
  }
  res.status(201).json({ message: 'Suscripción exitosa' });
});

// API: Desuscribirse
app.post('/api/unsubscribe', (req, res) => {
  const { endpoint } = req.body;
  let subscriptions = getSubscriptions();
  subscriptions = subscriptions.filter(sub => sub.endpoint !== endpoint);
  saveSubscriptions(subscriptions);
  res.json({ message: 'Desuscripción exitosa' });
});

// API: Enviar notificación
app.post('/api/notify', async (req, res) => {
  const { title, body, icon, url } = req.body;
  const subscriptions = getSubscriptions();
  if (subscriptions.length === 0) return res.status(400).json({ error: 'No hay suscriptores' });
  const payload = JSON.stringify({
    title: title || 'PLASISE Notification',
    body: body || 'Nueva notificación',
    icon: icon || '/icon-192.png',
    url: url || '/'
  });
  const results = await Promise.allSettled(subscriptions.map(subscription =>
    webpush.sendNotification(subscription, payload).catch(error => {
      if (error.statusCode === 410) {
        let subs = getSubscriptions();
        subs = subs.filter(sub => sub.endpoint !== subscription.endpoint);
        saveSubscriptions(subs);
      }
      throw error;
    })
  ));
  const successful = results.filter(r => r.status === 'fulfilled').length;
  const failed = results.filter(r => r.status === 'rejected').length;
  res.json({ message: 'Notificaciones enviadas', successful, failed, total: subscriptions.length });
});

// API: Estadísticas
app.get('/api/stats', (req, res) => {
  const subscriptions = getSubscriptions();
  res.json({
    totalSubscribers: subscriptions.length,
    subscriptions: subscriptions.map(sub => ({ endpoint: sub.endpoint.substring(0, 50) + '...', subscribedAt: sub.subscribedAt }))
  });
});

app.get('/', (req, res) => { res.sendFile(path.join(__dirname, 'public', 'index.html')); });
app.get('/admin', (req, res) => { res.sendFile(path.join(__dirname, 'public', 'admin.html')); });

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
EOF

# Copiar Dockerfile actualizado
cat > Dockerfile << 'EOF'
FROM node:18-alpine
RUN apk add --no-cache tini
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force
COPY server.js ./
COPY public ./public
RUN mkdir -p /data && chown -R node:node /data
USER node
EXPOSE 3100
ENV NODE_ENV=production \
    PORT=3100
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3100/api/stats', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "server.js"]
EOF

# Copiar .env actualizado al puerto 3100
cat > .env << 'EOF'
PORT=3100
PUBLIC_VAPID_KEY=BFPL_c0ylav-Jfii49CkXlwZI4PITS22AL62pKbI3VNgI7wl9cWjoDoYujIA4XGnuR6CUihEDJ24DleohoMxwmU
PRIVATE_VAPID_KEY=LWbLj7FQPskHWLnHyjQO1Eaf-v2-cKE7p1Ikul7cZ68
COMPANY_NAME=PLASISE
ADMIN_EMAIL=info@plasise.com
NODE_ENV=production
EOF

echo "✅ Archivos actualizados en $PROJECT_PATH"
echo "⚙️ Reiniciando contenedores..."

# Limpiar y reconstruir para asegurar cambios en Dockerfile
if command -v easypanel &> /dev/null; then
    easypanel restart n0cker-push
else
    docker compose down
    docker compose up -d --build
fi

echo "✨ Proceso completado exitosamente."
