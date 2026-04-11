# Directiva SOP: Corrección de Responsive Layout en Móvil

## 1. Objetivo
Arreglar los errores visuales reportados en la vista móvil de la página web principal y de la vista de administración del panel de notificaciones Push.

## 2. Entradas
- Archivos HTML del frontend involucrados (e.g. `frontend/index.html`, `frontend/pages/index.html`, `frontend/pages/admin/notificaciones.html`).

## 3. Problemas Detectados
1.  En la página principal, los elementos del carrusel (si existe en la versión actual) o la sección Hero se superponen de forma incorrecta entre sí y sobre todo en la zona del título bajo el header fijo (sticky).
2.  Los botones y elementos del header (`Acceder` y menú hamburguesa) están muy apretados y el tamaño del botón no se ajusta en móviles.
3.  El panel de Notificaciones dentro del área de administración (`notificaciones.html`) puede tener problemas de desbordamiento horizontal debido al iframe y topbar.
4.  Banner de cookies intrusivo.

## 4. Lógica de Modificación (Scripts)
El script de Python `fix_responsive.py` ejecutará `BeautifulSoup` y manipulará expresiones regulares para:
1. Buscar las etiquetas `<style>` dentro de `notificaciones.html` e `index.html` (revisando ambas variantes).
2. Insertar media queries `@media (max-width: 768px)` específicos que añadan un tamaño y padding adaptado.
3. Asegurar `padding-top` adicional en `.hero` si es necesario, y unificación segura de carrusel/slides.
4. Asegurar que las tarjetas `.cat-card` o las fuentes se reduzcan de tamaño.
5. Inyectar mejoras en la cabecera (header actions spacing).

## 5. Salidas Expectadas
- Los archivos `.html` editados guardados intactos pero con el parche en la sección de media query del móvil.

## 6. Restricciones y Casos Borde
- No machacar otras clases existentes. Usar métodos seguros de añadir CSS al final del bloque `<style>`.
