# 🏗️ PLASISE - SISTEMA B2B PROFESIONAL

Sistema completo de eCommerce B2B para distribución de productos de seguridad electrónica, inspirado en IBD Global España.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.3+-red.svg)
![MySQL](https://img.shields.io/badge/mysql-8.0+-orange.svg)

---

## 📋 TABLA DE CONTENIDOS

1. [Características](#características)
2. [Tecnologías](#tecnologías)
3. [Arquitectura](#arquitectura)
4. [Instalación](#instalación)
5. [Configuración](#configuración)
6. [Uso](#uso)
7. [API Documentation](#api-documentation)
8. [Deployment](#deployment)
9. [Testing](#testing)
10. [Contributing](#contributing)

---

## ✨ CARACTERÍSTICAS

### 🛒 eCommerce B2B
- ✅ Catálogo de productos con categorías jerárquicas
- ✅ Precios diferenciados por tipo de cliente
- ✅ Sistema de carrito y checkout
- ✅ Gestión completa de pedidos
- ✅ Seguimiento de envíos
- ✅ Facturación automatizada

### 👥 Gestión de Usuarios
- ✅ Autenticación JWT + Sesiones
- ✅ Registro y verificación de email
- ✅ Recuperación de contraseña
- ✅ Roles y permisos (RBAC)
- ✅ Tipos de cliente: Retail, Profesional, Distribuidor, Mayorista

### 📦 Gestión de Catálogo
- ✅ Productos con atributos técnicos
- ✅ Múltiples imágenes por producto
- ✅ Ficha técnica y manuales
- ✅ Gestión de stock
- ✅ Productos relacionados
- ✅ Sistema de valoraciones

### 💰 Precios y Promociones
- ✅ Precios por tipo de cliente
- ✅ Descuentos y promociones
- ✅ Cupones de descuento
- ✅ Envío gratis condicional
- ✅ Precios de outlet

### 📝 Contenidos
- ✅ Blog multiidioma
- ✅ Recursos descargables
- ✅ Webinars y formaciones
- ✅ Página de marcas
- ✅ SEO optimizado

### 🌍 Multiidioma
- ✅ Español
- ✅ Catalán
- ✅ Inglés
- ✅ Francés
- ✅ Portugués

### 🔒 Seguridad
- ✅ Passwords hasheados (bcrypt)
- ✅ Tokens JWT
- ✅ CSRF protection
- ✅ Rate limiting
- ✅ SQL injection prevention
- ✅ XSS protection

---

## 🛠️ TECNOLOGÍAS

### Backend
- **Python 3.9+**
- **Flask 2.3** - Framework web
- **MySQL 8.0** - Base de datos
- **SQLAlchemy** - ORM
- **JWT** - Autenticación
- **Werkzeug** - Seguridad
- **Gunicorn** - Servidor WSGI

### Frontend
- **HTML5 + CSS3**
- **JavaScript (Vanilla)**
- **Tailwind CSS**
- **Alpine.js**

### DevOps
- **Docker** + Docker Compose
- **Nginx** - Reverse proxy
- **Redis** - Cache & Sessions
- **Celery** - Task queue

---

## 🏛️ ARQUITECTURA

```
plasise-upgrade/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Application factory
│   │   ├── models/              # Modelos de datos
│   │   │   ├── user.py
│   │   │   ├── product.py
│   │   │   ├── order.py
│   │   │   └── ...
│   │   ├── routes/              # Rutas de la API
│   │   │   ├── auth.py
│   │   │   ├── products.py
│   │   │   ├── orders.py
│   │   │   └── ...
│   │   ├── services/            # Lógica de negocio
│   │   ├── utils/               # Utilidades
│   │   │   ├── database.py
│   │   │   ├── validators.py
│   │   │   ├── decorators.py
│   │   │   └── logger.py
│   │   └── middleware/          # Middleware
│   │       ├── auth.py
│   │       └── error_handler.py
│   ├── config/
│   │   └── config.py            # Configuración
│   ├── migrations/              # Migraciones DB
│   ├── tests/                   # Tests
│   ├── logs/                    # Logs
│   ├── requirements.txt         # Dependencias Python
│   └── run.py                   # Entry point
├── frontend/
│   ├── public/
│   ├── assets/
│   └── ...
├── database_schema.sql          # Schema completo de DB
├── ARQUITECTURA.md              # Documentación de arquitectura
├── docker-compose.yml           # Docker compose
├── Dockerfile                   # Dockerfile
└── README.md                    # Este archivo
```

---

## 🚀 INSTALACIÓN

### Requisitos Previos
- Python 3.9 o superior
- MySQL 8.0
- Redis (opcional, para cache)
- Node.js 16+ (para frontend)

### Paso 1: Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/plasise.git
cd plasise/plasise-upgrade
```

### Paso 2: Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

### Paso 3: Instalar dependencias
```bash
cd backend
pip install -r requirements.txt
```

### Paso 4: Configurar base de datos
```bash
# Crear base de datos MySQL
mysql -u root -p

CREATE DATABASE plasise CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'plasise_user'@'localhost' IDENTIFIED BY 'tu_password_segura';
GRANT ALL PRIVILEGES ON plasise.* TO 'plasise_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Importar schema
mysql -u plasise_user -p plasise < ../database_schema.sql
```

### Paso 5: Configurar variables de entorno
```bash
cd backend
cp .env.example .env
nano .env
```

Editar `.env`:
```env
# Flask
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta-muy-segura-cambiar-en-produccion
JWT_SECRET_KEY=otra-clave-secreta-para-jwt

# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=plasise_user
MYSQL_PASSWORD=tu_password_segura
MYSQL_DATABASE=plasise

# Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-password-app

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

### Paso 6: Ejecutar la aplicación
```bash
cd backend
python app/__init__.py

# O con Gunicorn (producción):
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

La API estará disponible en `http://localhost:5000`

---

## ⚙️ CONFIGURACIÓN

### Entornos

La aplicación soporta 3 entornos:

1. **Development** (por defecto)
   - Debug activado
   - Logs detallados
   - CORS permisivo
   - Cache desactivado

2. **Testing**
   - Base de datos en memoria
   - Mock de servicios externos

3. **Production**
   - Debug desactivado
   - HTTPS obligatorio
   - Cache activado
   - Rate limiting estricto

Cambiar entorno:
```bash
export FLASK_ENV=production
```

### Configuración de Email

Para envío de emails (verificación, recuperación de contraseña):

1. Gmail:
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=password-de-aplicacion
```

2. SMTP Custom:
```env
MAIL_SERVER=smtp.tu-servidor.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=usuario
MAIL_PASSWORD=password
```

### Cache con Redis

Activar cache para mejorar performance:

```bash
# Instalar Redis
sudo apt-get install redis-server

# Verificar que esté corriendo
redis-cli ping  # Debe responder: PONG

# En .env
REDIS_URL=redis://localhost:6379/0
```

---

## 💻 USO

### Crear usuario administrador

```bash
cd backend
python manage.py create-admin

# O manualmente en MySQL:
INSERT INTO usuarios (email, password_hash, nombre, apellidos, tipo_usuario, rol, activo, email_verificado)
VALUES (
  'admin@plasise.com',
  'tu_password_hasheado',
  'Admin',
  'System',
  'admin',
  'super_admin',
  1,
  1
);
```

### Importar productos desde CSV

```bash
python manage.py import-products productos.csv
```

### Ejecutar migraciones

```bash
# Crear migración
python manage.py db init
python manage.py db migrate -m "Descripción del cambio"

# Aplicar migración
python manage.py db upgrade
```

---

## 📚 API DOCUMENTATION

### Autenticación

#### POST `/api/v1/auth/register`
Registrar nuevo usuario

**Request:**
```json
{
  "email": "user@example.com",
  "password": "Password123",
  "nombre": "Juan",
  "apellidos": "García"
}
```

**Response:** `201 Created`
```json
{
  "message": "Usuario registrado correctamente",
  "user": {...},
  "verification_required": true
}
```

#### POST `/api/v1/auth/login`
Iniciar sesión

**Request:**
```json
{
  "email": "user@example.com",
  "password": "Password123",
  "remember_me": true
}
```

**Response:** `200 OK`
```json
{
  "message": "Login exitoso",
  "user": {...},
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "session_id": "sess_123abc"
}
```

#### GET `/api/v1/auth/session`
Obtener sesión actual

**Response:** `200 OK`
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "nombre": "Juan",
    "tipo_usuario": "cliente"
  }
}
```

### Productos

#### GET `/api/v1/products`
Listar productos con filtros

**Query Parameters:**
- `page`: Número de página (default: 1)
- `per_page`: Items por página (default: 20)
- `category`: ID de categoría
- `brand`: ID de marca
- `search`: Búsqueda por texto
- `min_price`: Precio mínimo
- `max_price`: Precio máximo
- `sort`: Ordenar por (price_asc, price_desc, name, newest)

**Response:** `200 OK`
```json
{
  "products": [...],
  "total": 846,
  "pages": 43,
  "current_page": 1
}
```

#### GET `/api/v1/products/:id`
Detalle de producto

**Response:** `200 OK`
```json
{
  "id": 1,
  "sku": "CAM-IP-001",
  "nombre": "Cámara IP 4MP",
  "precio_base": 125.50,
  "precio_cliente": 98.40,
  "stock": 50,
  "categoria": {...},
  "marca": {...},
  "imagenes": [...],
  "atributos": {...}
}
```

### Carrito

#### GET `/api/v1/cart`
Obtener carrito actual

**Response:** `200 OK`
```json
{
  "items": [...],
  "subtotal": 450.00,
  "descuento": 45.00,
  "total": 405.00,
  "items_count": 3
}
```

#### POST `/api/v1/cart/add`
Agregar producto al carrito

**Request:**
```json
{
  "producto_id": 1,
  "cantidad": 2
}
```

### Pedidos

#### POST `/api/v1/orders`
Crear pedido

**Request:**
```json
{
  "direccion_envio": {...},
  "metodo_pago": "transferencia",
  "notas": "Entregar en horario de oficina"
}
```

**Response:** `201 Created`
```json
{
  "numero_pedido": "PED-20260130-000001",
  "total": 405.00,
  "estado": "pendiente",
  "fecha_estimada_entrega": "2026-02-05"
}
```

Para documentación completa de la API: `/api/docs` (Swagger/OpenAPI)

---

## 🐳 DEPLOYMENT

### Docker Compose

```bash
# Construir y levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

### Producción Manual

```bash
# 1. Actualizar código
git pull origin main

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar migraciones
python manage.py db upgrade

# 4. Reiniciar servidor
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## 🧪 TESTING

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app tests/

# Tests específicos
pytest tests/test_auth.py
pytest tests/test_products.py

# En modo watch
pytest-watch
```

---

## 📈 ROADMAP

### Fase 1 - Base (✅ COMPLETADA)
- [x] Estructura de base de datos
- [x] Modelos y API básica
- [x] Sistema de autenticación
- [x] CRUD de productos

### Fase 2 - eCommerce (🚧 EN DESARROLLO)
- [ ] Sistema de carrito completo
- [ ] Checkout y pagos
- [ ] Gestión de pedidos
- [ ] Panel de cliente

### Fase 3 - Contenidos
- [ ] Blog CMS
- [ ] Recursos y downloads
- [ ] Webinars
- [ ] Multiidioma

### Fase 4 - Admin
- [ ] Panel de administración
- [ ] Dashboard con métricas
- [ ] Gestión de usuarios
- [ ] Reportes y estadísticas

### Fase 5 - Optimización
- [ ] Cache con Redis
- [ ] PWA
- [ ] SEO avanzado
- [ ] Performance optimization

---

## 🤝 CONTRIBUTING

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crear una rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

---

## 📄 LICENCIA

Este proyecto es privado y confidencial.

---

## 👨‍💻 AUTOR

**PLASISE Development Team**

- 📧 Email: info@plasise.com
- 🌐 Web: https://plasise.com

---

## 🙏 AGRADECIMIENTOS

- Inspirado en IBD Global España
- Comunidad de Flask
- Todos los contribuidores

---

**¡Construido con ❤️ para profesionales de la seguridad!**
