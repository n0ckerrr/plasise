# SOP – Reorganización y Limpieza del Frontend PLASISE

## Diagnóstico

### CSS en uso real
- **Bootstrap 5.3** (CDN) → todas las páginas
- **Font Awesome 6.4** (CDN) → todas las páginas  
- **`assets/css/cookies.css`** → la mayoría de páginas (banner cookies)
- **`assets/css/style.css`** → solo carrito.html y servicios.html
- **`assets/css/luxe.css`** → login.html, registro.html, sobre-nosotros.html, logina.html
- **`assets/css/premium.css`** → NADIE lo usa actualmente
- `@n8n/chat/dist/style.css` (CDN) → checkout.html, login.html, productos.html

### JS en uso real
- **Bootstrap JS** (CDN) → la mayoría
- **`assets/js/cookies-v1.js`** → TODAS las páginas (es la versión activa del banner)
- **`assets/js/cookies.js`** → solo productos.html (redundante)
- **`assets/js/config.js`** → solo logina.html y registro.html (debería estar en TODAS)
- **`assets/js/luxe.js`** → solo sobre-nosotros.html
- `../assets/js/chatbot.js` → producto-detalle.html (ruta relativa diferente)

### Rutas inconsistentes detectadas
- Páginas en `/pages/` usan `assets/css/` (sin `../`) → funciona si Nginx sirve desde `/pages/`
- `producto-detalle.html` y `productos.html` usan `../assets/` → rutas distintas a sus vecinas
- Las páginas admin usan `.../assets/js/` con `../` correcto

### Archivos a eliminar (duplicados/obsoletos)
- `/frontend/` raíz: todos los .html excepto `index.html` (que hace redirect)
- `/frontend/pages/logina.html` (copia de login.html)
- `/frontend/pages/productos_CON_BUSCADOR.html` (experimental, el buscador ya está en productos.html)
- `/frontend/pages/index_live.html` (si existe en pages/)
- `assets/css/premium.css` (no se usa)
- `assets/js/cookies.js` (usar solo cookies-v1.js)
- `assets/js/luxe.js` (mover estilos inline a luxe.css o style.css)

### Qué se unifica
- Renombrar `cookies-v1.js` → `cookies.js` (la versión definitiva)
- `config.js` se añade a TODAS las páginas que aún no lo tienen
- Las rutas `../assets/` se normalizan a `../assets/` consistentemente desde /pages/

## Restricciones Conocidas
- **No borrar `luxe.css`** – lo usan 4 paginas activamente
- **No borrar `style.css`** – lo usan carrito.html y servicios.html
- El CSS final sera: Bootstrap (CDN) + FA (CDN) + `luxe.css` o `style.css` segun pagina + `cookies.css`
- **No modificar el contenido HTML interno** – solo imports de CSS/JS en `<head>` y al final del `<body>`
- Los archivos en la raiz de `/frontend/` son versiones antiguas: no estan en produccion
- **CRITICO – Windows cp1252:** Los scripts Python que se ejecuten en PowerShell de Windows NO deben usar emojis (!, ->, *) ni simbolos Unicode en `print()` o `log()`. Causa UnicodeEncodeError. Usar solo ASCII. Patron correcto: `msg.encode('ascii', errors='replace').decode('ascii')`

## Plan de Ejecución (script Python)
1. Hacer backup de todo antes de tocar nada
2. Normalizar todas las rutas a `../assets/css/` y `../assets/js/` desde `/pages/`
3. Añadir `config.js` a todas las páginas que no lo tengan
4. Estandarizar: `cookies-v1.js` → `cookies.js` (renombrar referencias)
5. Eliminar archivos obsoletos
6. Verificar que la estructura es consistente
