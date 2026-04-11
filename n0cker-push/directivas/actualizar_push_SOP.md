# SOP: Actualización de Sistema de Notificaciones Push

Este procedimiento describe cómo actualizar los metadatos, branding y configuración de VAPID del sistema de notificaciones push.

## Objetivos
- Actualizar el branding de "N0CKER" a "PLASISE".
- Configurar llaves VAPID persistentes.
- Ajustar la estética para que coincida con la plataforma principal.

## Entradas
- `n0cker-push/server.js`
- `n0cker-push/public/index.html`
- `n0cker-push/public/admin.html`
- `n0cker-push/public/app.js`
- `n0cker-push/public/sw.js`
- `n0cker-push/public/manifest.json`

## Pasos

### 1. Identificación de Datos Antiguos
- Buscar todas las ocurrencias de "N0CKER" (case insensitive).
- Identificar el email de contacto en `server.js`.
- Identificar colores neón en los archivos HTML/CSS.

### 2. Generación de Nuevas VAPID Keys
- Si el sistema no tiene llaves persistentes, se deben generar unas nuevas.
- Estas llaves deben guardarse en un archivo `.env`.

### 3. Actualización de Branding
- Reemplazar "N0CKER" por "PLASISE".
- Actualizar el email de `admin@n0cker.com` por el email oficial de Plasise.
- Actualizar los colores en el CSS de `index.html` y `admin.html`.
- Usar el color acento de Plasise: `#c8a45e`.

### 4. Actualización de Assets
- Los iconos `icon-192.png` y `icon-512.png` deben ser reemplazados si se dispone de los nuevos. Si no, se pueden usar placeholders o avisar al usuario.

### 5. Verificación
- Ejecutar el servidor.
- Comprobar que los logs muestran las nuevas llaves VAPID.
- Verificar que el frontend carga correctamente y permite la suscripción.

## Restricciones / Casos Borde
- **IMPORTANTE**: Cambiar las VAPID keys invalidará todas las suscripciones existentes. Los usuarios deberán volver a suscribirse.
- Asegurarse de que el Service Worker se actualice correctamente en el navegador.
- El archivo `/data/subscriptions.json` puede contener datos antiguos que ya no sirven si se cambian las llaves. Considerar limpiarlo.
