# Integración Push Notifications en Dashboard Admin - SOP

## Objetivo
Integrar el sistema de notificaciones push (`n0cker-push`) dentro del panel de administración de PLASISE, accesible desde el sidebar del dashboard.

## Arquitectura
- El sistema push es un servicio Node.js **independiente** que corre en el **puerto 3100**.
- El puerto 3000 está reservado para EasyPanel.
- La integración se hace mediante un `<iframe>` en `frontend/pages/admin/notificaciones.html`.

## Entradas
- Servidor push en `n0cker-push/` (Express + web-push).
- Dashboard admin en `frontend/pages/admin/`.

## Salidas
- Nueva página `notificaciones.html` con iframe embebido.
- Enlace "Notificaciones" visible en el sidebar de TODAS las páginas de admin.

## Lógica / Pasos
1. El iframe en `notificaciones.html` detecta si estamos en local (`localhost:3100`) o producción (`https://n0cker-push.v6hb8q.easypanel.host`).
2. El sidebar de cada página de admin incluye un enlace `<a href="notificaciones.html">` con icono `fa-bell`.
3. La autenticación del dashboard se verifica antes de cargar el iframe.

## Restricciones / Casos Borde

> **NOTA CRÍTICA**: No usar puerto 3000 para el push. EasyPanel lo ocupa. Usar siempre 3100.

> **NOTA**: Al añadir un enlace al sidebar, cada página de admin tiene un formato DIFERENTE de sidebar:
> - `index.html`, `categorias.html`, `marcas.html`, `productos.html`, `usuarios.html`, `eventos.html`: Usan `<nav class="sidebar-nav">` con `<a class="nav-item">`.
> - `pedidos.html`: Usa formato similar pero con ligeras diferencias de indentación.
> - `configuracion.html`: Usa `<ul class="sidebar-nav">` con `<li><a>`.
> Hay que respetar el formato de cada archivo al añadir el enlace.

> **NOTA**: El iframe requiere que el servidor push permita ser embebido. Se resolvió añadiendo un middleware en `server.js` que:
> 1. Elimina `X-Frame-Options` (que por defecto bloquea iframes).
> 2. Añade `Content-Security-Policy: frame-ancestors 'self' https://n0cker-plasise.v6hb8q.easypanel.host http://localhost:* http://127.0.0.1:*`.
> 3. Configura CORS permitiendo orígenes específicos del dashboard de Plasise.
> Si se cambia el dominio del dashboard, hay que actualizar la lista `allowedOrigins` y `frame-ancestors` en `server.js`.

## Archivos Modificados
- `n0cker-push/.env` → Puerto 3100
- `n0cker-push/docker-compose.yml` → Puerto 3100
- `n0cker-push/server.js` → Fallback puerto 3100
- `n0cker-push/README.md` → Referencias puerto 3100
- `frontend/pages/admin/notificaciones.html` → NUEVO
- `frontend/pages/admin/*.html` (8 archivos) → Sidebar actualizado
