# 🏛️ ARQUITECTURA PLASISE - SISTEMA B2B PROFESIONAL

## 📋 ÍNDICE
1. [Visión General](#visión-general)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Estructura de Base de Datos](#estructura-de-base-de-datos)
4. [API Endpoints](#api-endpoints)
5. [Módulos del Sistema](#módulos-del-sistema)
6. [Seguridad](#seguridad)
7. [Performance](#performance)

---

## 🎯 VISIÓN GENERAL

**Objetivo:** Crear una plataforma B2B profesional para distribución de productos de seguridad electrónica, con funcionalidades de:
- eCommerce mayorista con precios diferenciados
- Gestión de contenidos (blog, recursos, webinars)
- Sistema multiidioma (ES, CA, EN, FR, PT)
- Área de cliente personalizada
- Gestión de marcas y catálogo técnico

**Inspiración:** IBD Global España - líder en distribución CCTV

---

## 🔧 STACK TECNOLÓGICO

### Backend
- **Python 3.9+** con Flask 2.0+
- **MySQL 8.0** para datos relacionales
- **Redis** para cache y sesiones (opcional, mejora performance)
- **Celery** para tareas asíncronas (emails, reportes)

### Frontend
- **HTML5 + CSS3** (diseño responsive)
- **JavaScript Vanilla** + Alpine.js (reactivo ligero)
- **Tailwind CSS** para estilos profesionales
- **Chart.js** para dashboards

### Infraestructura
- **Docker** + Docker Compose
- **Nginx** como reverse proxy
- **Let's Encrypt** para SSL
- **Gunicorn** como servidor WSGI

---

## 🗄️ ESTRUCTURA DE BASE DE DATOS

### Módulo Usuarios y Permisos
```sql
-- Tipos de usuario: admin, profesional, distribuidor, retail
usuarios (
    id, email, password_hash, nombre, apellidos,
    tipo_usuario, empresa_id, fecha_registro, activo,
    email_verificado, ultimo_acceso
)

empresas (
    id, razon_social, cif, direccion, telefono,
    tipo_cliente, descuento_global, credito_maximo,
    forma_pago_preferida, delegado_asignado
)
```

### Módulo Catálogo
```sql
categorias (
    id, nombre, slug, parent_id, orden, icono, activo
)
-- Jerarquía: VIDEO > DAHUA > IP > Cámaras > Domos 4MP

productos (
    id, sku, nombre, descripcion_corta, descripcion_larga,
    categoria_id, marca_id, precio_base, stock, 
    peso, dimensiones, ficha_tecnica_url, imagen_principal,
    estado (activo, outlet, descatalogado), destacado
)

productos_imagenes (
    id, producto_id, url, orden, tipo (principal, galeria, tecnica)
)

productos_atributos (
    id, producto_id, nombre, valor
)
-- Ej: resolución=4MP, tipo_sensor=CMOS, visión_nocturna=30m
```

### Módulo Marcas
```sql
marcas (
    id, nombre, slug, logo_url, descripcion,
    web_oficial, orden, destacada
)
```

### Módulo Precios
```sql
precios_clientes (
    id, producto_id, tipo_cliente, precio, activo
)
-- Mismo producto, diferentes precios según tipo cliente

promociones (
    id, nombre, tipo (descuento_porcentaje, descuento_fijo, 2x1),
    valor, fecha_inicio, fecha_fin, categorias_aplicables,
    productos_aplicables, clientes_aplicables
)
```

### Módulo Pedidos
```sql
pedidos (
    id, usuario_id, numero_pedido, fecha, 
    estado (pendiente, confirmado, enviado, entregado, cancelado),
    subtotal, descuento, impuestos, total,
    direccion_envio, notas
)

pedidos_detalle (
    id, pedido_id, producto_id, cantidad, 
    precio_unitario, descuento, subtotal
)

envios (
    id, pedido_id, transportista, numero_seguimiento,
    fecha_envio, fecha_entrega_estimada, estado
)
```

### Módulo Contenidos
```sql
blog_posts (
    id, titulo, slug, contenido, resumen,
    categoria (noticias, formaciones, webinars),
    autor_id, imagen_destacada, fecha_publicacion,
    estado (borrador, publicado), vistas
)

recursos (
    id, titulo, descripcion, tipo (pdf, video, guia),
    url, categoria_id, marca_id, acceso (publico, clientes)
)

webinars (
    id, titulo, descripcion, fecha_hora, duracion,
    url_registro, url_grabacion, estado (programado, finalizado)
)
```

### Módulo Multiidioma
```sql
traducciones (
    id, clave, idioma (es, ca, en, fr, pt), texto
)
-- Ej: clave="header.cart", idioma="es", texto="Carrito"
```

---

## 🔌 API ENDPOINTS

### Autenticación
```
POST   /api/auth/login
POST   /api/auth/register
POST   /api/auth/logout
GET    /api/auth/session
POST   /api/auth/reset-password
```

### Catálogo
```
GET    /api/productos                    # Listado con filtros
GET    /api/productos/:id                # Detalle producto
GET    /api/productos/buscar             # Búsqueda
GET    /api/categorias                   # Árbol de categorías
GET    /api/marcas                       # Listado de marcas
```

### Carrito y Pedidos
```
GET    /api/carrito
POST   /api/carrito/agregar
PUT    /api/carrito/actualizar/:item_id
DELETE /api/carrito/eliminar/:item_id
POST   /api/pedidos/crear
GET    /api/pedidos                      # Historial
GET    /api/pedidos/:id                  # Detalle
```

### Contenidos
```
GET    /api/blog                         # Listado posts
GET    /api/blog/:slug                   # Post individual
GET    /api/recursos                     # Recursos descargables
GET    /api/webinars                     # Próximos webinars
```

### Admin
```
GET    /api/admin/dashboard              # Estadísticas
POST   /api/admin/productos              # CRUD productos
POST   /api/admin/usuarios               # Gestión usuarios
GET    /api/admin/pedidos                # Gestión pedidos
```

---

## 📦 MÓDULOS DEL SISTEMA

### 1. Core (Núcleo)
- Configuración
- Database connection pool
- Logging
- Error handling
- Middleware (auth, CORS, rate limiting)

### 2. Auth (Autenticación)
- Registro de usuarios
- Login/Logout
- Recuperación de contraseña
- Verificación de email
- Gestión de sesiones

### 3. Catalog (Catálogo)
- Gestión de productos
- Categorías jerárquicas
- Búsqueda y filtros
- Gestión de stock
- Importación masiva (CSV/Excel)

### 4. Pricing (Precios)
- Precios por tipo de cliente
- Promociones y descuentos
- Reglas de pricing
- Cupones

### 5. Orders (Pedidos)
- Carrito de compras
- Checkout
- Gestión de pedidos
- Facturación
- Histórico

### 6. Content (Contenidos)
- Blog
- Recursos descargables
- Webinars
- Páginas estáticas

### 7. Admin (Administración)
- Dashboard
- Gestión de productos
- Gestión de usuarios
- Gestión de pedidos
- Reportes

### 8. i18n (Internacionalización)
- Gestión de idiomas
- Traducciones
- Detección automática

---

## 🔒 SEGURIDAD

### Autenticación
- Passwords hasheados con **Werkzeug + bcrypt**
- Tokens JWT para API
- Sesiones server-side con timeout
- 2FA opcional para admins

### Protección de Datos
- Validación de inputs (SQL Injection)
- Sanitización de HTML (XSS)
- CSRF tokens
- Rate limiting
- HTTPS obligatorio

### Permisos
- RBAC (Role-Based Access Control)
- Niveles: Admin, Profesional, Distribuidor, Retail
- Permisos granulares por módulo

---

## ⚡ PERFORMANCE

### Cache
- Redis para:
  - Sesiones de usuario
  - Catálogo de productos
  - Precios calculados
  - Resultados de búsqueda

### Optimizaciones DB
- Índices en campos frecuentes
- Query optimization
- Connection pooling
- Prepared statements

### Frontend
- Lazy loading de imágenes
- Minificación CSS/JS
- CDN para assets estáticos
- Service Workers para PWA

---

## 📊 MÉTRICAS Y MONITOREO

- **Logs estructurados** (JSON)
- **Alertas** para errores críticos
- **Dashboard de métricas:**
  - Ventas diarias/mensuales
  - Productos más vendidos
  - Usuarios activos
  - Rendimiento de categorías
  - Tasa de conversión

---

## 🚀 ROADMAP DE IMPLEMENTACIÓN

### FASE 1 - Base (Semana 1-2)
✅ Estructura de DB completa
✅ Módulo Auth robusto
✅ API CRUD productos básico
✅ Frontend básico responsive

### FASE 2 - eCommerce (Semana 3-4)
- Carrito funcional
- Sistema de precios diferenciados
- Checkout completo
- Área de cliente

### FASE 3 - Contenidos (Semana 5)
- Blog
- Recursos
- Webinars
- Página de marcas

### FASE 4 - Admin (Semana 6)
- Panel de administración
- Gestión de productos
- Gestión de pedidos
- Reportes

### FASE 5 - Optimización (Semana 7-8)
- Multiidioma
- Cache con Redis
- PWA
- SEO

---

## 📝 NOTAS FINALES

Este documento es la biblia del proyecto. Cada decisión técnica debe estar alineada con esta arquitectura. Si necesitas modificar algo, actualiza este documento PRIMERO.

**Mantra del proyecto:**
> "Si no está en la arquitectura, no se implementa. Si se implementa, debe estar en la arquitectura."

---

Creado con ❤️ para PLASISE
Última actualización: 2026-01-30
