# PLASISE Push Notification System

Sistema completo de notificaciones push con Node.js, Express y Web Push API.

## 🚀 Características

- ✅ Push Notifications en tiempo real
- ✅ Funciona con el navegador cerrado
- ✅ Panel de administración para enviar notificaciones
- ✅ API REST completa
- ✅ Interfaz moderna con diseño cyber-brutalist
- ✅ Compatible con PWA (Progressive Web App)
- ✅ Almacenamiento persistente de suscripciones
- ✅ Service Worker integrado
- ✅ Dockerizado y listo para producción

## 📋 Requisitos

- Docker (para despliegue en contenedor)
- O Node.js 18+ (para desarrollo local)
- Navegador moderno con soporte para Push API

## 🔧 Instalación en Easypanel

### Paso 1: Crear el servicio

1. Accede a tu Easypanel
2. Crea un nuevo servicio de tipo "App"
3. Selecciona "GitHub" o sube los archivos manualmente

### Paso 2: Configuración del servicio

En Easypanel, configura:

- **Puerto interno**: 3100
- **Dominio**: Tu dominio (ej: https://PLASISE-xadipeda.qddap6.easypanel.host)
- **Variables de entorno** (opcional):
  ```
  PUBLIC_VAPID_KEY=<tu_clave_publica>
  PRIVATE_VAPID_KEY=<tu_clave_privada>
  ```

### Paso 3: Volumen para datos persistentes

Crea un volumen y móntalo en `/data` para guardar las suscripciones:

- **Path**: `/data`
- **Type**: Volume

### Paso 4: Deploy

1. Haz commit de todos los archivos a tu repositorio
2. Despliega desde Easypanel
3. Espera a que el contenedor se construya e inicie

## 🎯 Uso

### Frontend Principal

Accede a tu dominio: `https://tu-dominio.easypanel.host`

- Haz clic en "ACTIVAR Notificaciones"
- Acepta los permisos en tu navegador
- ¡Listo! Ahora recibirás notificaciones

### Panel de Administración

Accede a: `https://tu-dominio.easypanel.host/admin`

Desde aquí puedes:
- Enviar notificaciones a todos los suscriptores
- Ver estadísticas en tiempo real
- Consultar la lista de suscriptores activos

## 🔑 VAPID Keys

Las VAPID keys se generan automáticamente la primera vez que inicias el servidor. 

**⚠️ IMPORTANTE**: Debes guardar estas keys y configurarlas como variables de entorno en producción para mantener las suscripciones entre reinicios:

```bash
# Las verás en los logs del contenedor al iniciar
PUBLIC_VAPID_KEY=...
PRIVATE_VAPID_KEY=...
```

Para configurarlas en Easypanel:
1. Ve a tu servicio → Environment
2. Agrega las variables `PUBLIC_VAPID_KEY` y `PRIVATE_VAPID_KEY`
3. Redespliega el servicio

## 🛠️ Desarrollo Local

### Con Docker

```bash
# Construir y ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### Sin Docker

```bash
# Instalar dependencias
npm install

# Iniciar servidor
npm start

# Desarrollo con hot-reload
npm run dev
```

Accede a:
- Frontend: http://localhost:3100
- Admin: http://localhost:3100/admin

## 📡 API REST

### Obtener clave pública VAPID
```bash
GET /api/vapidPublicKey
```

### Suscribirse
```bash
POST /api/subscribe
Content-Type: application/json

{
  "endpoint": "...",
  "keys": {
    "p256dh": "...",
    "auth": "..."
  }
}
```

### Enviar notificación
```bash
POST /api/notify
Content-Type: application/json

{
  "title": "Título de la notificación",
  "body": "Mensaje de la notificación",
  "url": "https://ejemplo.com",
  "icon": "/icon-192.png"
}
```

### Obtener estadísticas
```bash
GET /api/stats
```

## 🎨 Personalización

### Colores y diseño

Edita las variables CSS en `public/index.html` y `public/admin.html`:

```css
:root {
  --neon-green: #c8a45e;
  --neon-cyan: #d4b76a;
  --neon-magenta: #a6894c;
  --dark-bg: #0a0a0a;
  --gray: #1a1a1a;
}
```

### Iconos

Reemplaza los archivos en `public/`:
- `icon-192.png` (192x192px)
- `icon-512.png` (512x512px)

## 🔒 Seguridad

- Las suscripciones se almacenan en `/data/subscriptions.json`
- En producción, considera usar una base de datos real
- Las VAPID keys deben mantenerse secretas
- HTTPS es obligatorio para push notifications

## 📝 Estructura de archivos

```
.
├── server.js              # Servidor Node.js/Express
├── package.json           # Dependencias
├── Dockerfile            # Imagen Docker
├── docker-compose.yml    # Configuración Docker Compose
├── public/
│   ├── index.html        # Frontend principal
│   ├── admin.html        # Panel de administración
│   ├── app.js           # Lógica del frontend
│   ├── sw.js            # Service Worker
│   ├── manifest.json    # PWA manifest
│   └── icon-*.png       # Iconos
└── README.md            # Este archivo
```

## 🐛 Troubleshooting

### Las notificaciones no llegan

1. Verifica que HTTPS esté habilitado (obligatorio)
2. Revisa los permisos del navegador
3. Comprueba que las VAPID keys sean las mismas
4. Mira los logs del servidor

### Error al suscribirse

1. Borra el caché del navegador
2. Desactiva y reactiva las notificaciones
3. Verifica la consola del navegador (F12)

### El contenedor no inicia

1. Verifica los logs: `docker logs <container-id>`
2. Comprueba que el puerto 3100 esté disponible
3. Verifica que el volumen `/data` esté montado

## 📄 Licencia

MIT

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 💡 Soporte

Si tienes problemas o preguntas, abre un issue en GitHub.

---

Hecho con ❤️ por PLASISE
