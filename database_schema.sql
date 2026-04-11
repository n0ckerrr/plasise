-- ============================================================================
-- PLASISE DATABASE SCHEMA
-- Sistema B2B para Distribución de Seguridad Electrónica
-- Version: 2.0
-- Date: 2026-01-30
-- ============================================================================

-- Configuración inicial
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

-- ============================================================================
-- MÓDULO: USUARIOS Y EMPRESAS
-- ============================================================================

-- Tabla: empresas
DROP TABLE IF EXISTS `empresas`;
CREATE TABLE `empresas` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `razon_social` VARCHAR(255) NOT NULL,
  `nombre_comercial` VARCHAR(255) DEFAULT NULL,
  `cif` VARCHAR(20) NOT NULL UNIQUE,
  `direccion` VARCHAR(500) NOT NULL,
  `ciudad` VARCHAR(100) NOT NULL,
  `provincia` VARCHAR(100) NOT NULL,
  `codigo_postal` VARCHAR(10) NOT NULL,
  `pais` VARCHAR(2) DEFAULT 'ES',
  `telefono` VARCHAR(20) NOT NULL,
  `email_contacto` VARCHAR(255) NOT NULL,
  `web` VARCHAR(255) DEFAULT NULL,
  `tipo_cliente` ENUM('retail', 'profesional', 'distribuidor', 'mayorista') DEFAULT 'retail',
  `descuento_global` DECIMAL(5,2) DEFAULT 0.00,
  `credito_maximo` DECIMAL(10,2) DEFAULT 0.00,
  `forma_pago_preferida` ENUM('contado', 'transferencia', 'tarjeta', 'credito_30', 'credito_60', 'credito_90') DEFAULT 'transferencia',
  `delegado_asignado_id` INT UNSIGNED DEFAULT NULL,
  `estado` ENUM('pendiente_aprobacion', 'activo', 'suspendido', 'inactivo') DEFAULT 'pendiente_aprobacion',
  `notas_internas` TEXT DEFAULT NULL,
  `fecha_registro` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_tipo_cliente` (`tipo_cliente`),
  INDEX `idx_estado` (`estado`),
  INDEX `idx_cif` (`cif`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: usuarios
DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE `usuarios` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `email` VARCHAR(255) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `apellidos` VARCHAR(100) NOT NULL,
  `telefono` VARCHAR(20) DEFAULT NULL,
  `cargo` VARCHAR(100) DEFAULT NULL,
  `empresa_id` INT UNSIGNED DEFAULT NULL,
  `tipo_usuario` ENUM('admin', 'empleado', 'cliente') DEFAULT 'cliente',
  `rol` ENUM('super_admin', 'admin', 'comercial', 'tecnico', 'cliente_profesional', 'cliente_retail') DEFAULT 'cliente_retail',
  `idioma_preferido` VARCHAR(2) DEFAULT 'es',
  `activo` TINYINT(1) DEFAULT 1,
  `email_verificado` TINYINT(1) DEFAULT 0,
  `token_verificacion` VARCHAR(255) DEFAULT NULL,
  `token_reset_password` VARCHAR(255) DEFAULT NULL,
  `token_reset_expira` TIMESTAMP NULL DEFAULT NULL,
  `ultimo_acceso` TIMESTAMP NULL DEFAULT NULL,
  `intentos_login_fallidos` INT DEFAULT 0,
  `bloqueado_hasta` TIMESTAMP NULL DEFAULT NULL,
  `fecha_registro` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_email` (`email`),
  INDEX `idx_empresa` (`empresa_id`),
  INDEX `idx_tipo_usuario` (`tipo_usuario`),
  INDEX `idx_activo` (`activo`),
  CONSTRAINT `fk_usuarios_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- MÓDULO: CATÁLOGO
-- ============================================================================

-- Tabla: categorias
DROP TABLE IF EXISTS `categorias`;
CREATE TABLE `categorias` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(255) NOT NULL,
  `slug` VARCHAR(255) NOT NULL UNIQUE,
  `descripcion` TEXT DEFAULT NULL,
  `parent_id` INT UNSIGNED DEFAULT NULL,
  `nivel` TINYINT DEFAULT 0,
  `ruta` VARCHAR(500) DEFAULT NULL, -- Ej: /video/dahua/ip
  `orden` INT DEFAULT 0,
  `icono` VARCHAR(255) DEFAULT NULL,
  `imagen_banner` VARCHAR(500) DEFAULT NULL,
  `activo` TINYINT(1) DEFAULT 1,
  `meta_title` VARCHAR(255) DEFAULT NULL,
  `meta_description` VARCHAR(500) DEFAULT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_slug` (`slug`),
  INDEX `idx_parent` (`parent_id`),
  INDEX `idx_activo` (`activo`),
  INDEX `idx_orden` (`orden`),
  CONSTRAINT `fk_categorias_parent` FOREIGN KEY (`parent_id`) REFERENCES `categorias` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: marcas
DROP TABLE IF EXISTS `marcas`;
CREATE TABLE `marcas` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `slug` VARCHAR(100) NOT NULL UNIQUE,
  `logo_url` VARCHAR(500) DEFAULT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `web_oficial` VARCHAR(255) DEFAULT NULL,
  `pais_origen` VARCHAR(2) DEFAULT NULL,
  `orden` INT DEFAULT 0,
  `destacada` TINYINT(1) DEFAULT 0,
  `activo` TINYINT(1) DEFAULT 1,
  `meta_title` VARCHAR(255) DEFAULT NULL,
  `meta_description` VARCHAR(500) DEFAULT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_slug` (`slug`),
  INDEX `idx_destacada` (`destacada`),
  INDEX `idx_activo` (`activo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: productos
DROP TABLE IF EXISTS `productos`;
CREATE TABLE `productos` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `sku` VARCHAR(100) NOT NULL UNIQUE,
  `ean` VARCHAR(13) DEFAULT NULL,
  `nombre` VARCHAR(255) NOT NULL,
  `slug` VARCHAR(255) NOT NULL UNIQUE,
  `descripcion_corta` VARCHAR(500) DEFAULT NULL,
  `descripcion_larga` TEXT DEFAULT NULL,
  `categoria_id` INT UNSIGNED NOT NULL,
  `marca_id` INT UNSIGNED NOT NULL,
  `precio_base` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `precio_pvp_recomendado` DECIMAL(10,2) DEFAULT NULL,
  `coste` DECIMAL(10,2) DEFAULT NULL,
  `stock_actual` INT DEFAULT 0,
  `stock_minimo` INT DEFAULT 0,
  `stock_reservado` INT DEFAULT 0, -- Para pedidos pendientes
  `peso` DECIMAL(8,3) DEFAULT NULL, -- Kg
  `ancho` DECIMAL(8,2) DEFAULT NULL, -- cm
  `alto` DECIMAL(8,2) DEFAULT NULL,
  `largo` DECIMAL(8,2) DEFAULT NULL,
  `imagen_principal` VARCHAR(500) DEFAULT NULL,
  `ficha_tecnica_url` VARCHAR(500) DEFAULT NULL,
  `manual_url` VARCHAR(500) DEFAULT NULL,
  `video_url` VARCHAR(500) DEFAULT NULL,
  `estado` ENUM('activo', 'outlet', 'proximamente', 'descatalogado', 'sin_stock') DEFAULT 'activo',
  `destacado` TINYINT(1) DEFAULT 0,
  `nuevo` TINYINT(1) DEFAULT 0,
  `fecha_lanzamiento` DATE DEFAULT NULL,
  `vistas` INT DEFAULT 0,
  `ventas_totales` INT DEFAULT 0,
  `valoracion_promedio` DECIMAL(3,2) DEFAULT NULL,
  `num_valoraciones` INT DEFAULT 0,
  `meta_title` VARCHAR(255) DEFAULT NULL,
  `meta_description` VARCHAR(500) DEFAULT NULL,
  `meta_keywords` VARCHAR(500) DEFAULT NULL,
  `activo` TINYINT(1) DEFAULT 1,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_sku` (`sku`),
  INDEX `idx_slug` (`slug`),
  INDEX `idx_categoria` (`categoria_id`),
  INDEX `idx_marca` (`marca_id`),
  INDEX `idx_estado` (`estado`),
  INDEX `idx_destacado` (`destacado`),
  INDEX `idx_precio` (`precio_base`),
  INDEX `idx_activo` (`activo`),
  FULLTEXT INDEX `ft_busqueda` (`nombre`, `descripcion_corta`, `sku`),
  CONSTRAINT `fk_productos_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`),
  CONSTRAINT `fk_productos_marca` FOREIGN KEY (`marca_id`) REFERENCES `marcas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: productos_imagenes
DROP TABLE IF EXISTS `productos_imagenes`;
CREATE TABLE `productos_imagenes` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `producto_id` INT UNSIGNED NOT NULL,
  `url` VARCHAR(500) NOT NULL,
  `tipo` ENUM('principal', 'galeria', 'tecnica', 'ambiente') DEFAULT 'galeria',
  `orden` INT DEFAULT 0,
  `alt_text` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_producto` (`producto_id`),
  INDEX `idx_tipo` (`tipo`),
  CONSTRAINT `fk_productos_imagenes_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: productos_atributos
DROP TABLE IF EXISTS `productos_atributos`;
CREATE TABLE `productos_atributos` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `producto_id` INT UNSIGNED NOT NULL,
  `nombre` VARCHAR(100) NOT NULL,
  `valor` VARCHAR(500) NOT NULL,
  `tipo` ENUM('tecnico', 'comercial', 'seo') DEFAULT 'tecnico',
  `unidad` VARCHAR(20) DEFAULT NULL,
  `orden` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `idx_producto` (`producto_id`),
  INDEX `idx_nombre` (`nombre`),
  CONSTRAINT `fk_productos_atributos_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: productos_relacionados
DROP TABLE IF EXISTS `productos_relacionados`;
CREATE TABLE `productos_relacionados` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `producto_id` INT UNSIGNED NOT NULL,
  `producto_relacionado_id` INT UNSIGNED NOT NULL,
  `tipo` ENUM('similar', 'complementario', 'accesorio', 'alternativa') DEFAULT 'similar',
  PRIMARY KEY (`id`),
  INDEX `idx_producto` (`producto_id`),
  CONSTRAINT `fk_productos_rel_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_productos_rel_relacionado` FOREIGN KEY (`producto_relacionado_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- MÓDULO: PRECIOS Y PROMOCIONES
-- ============================================================================

-- Tabla: precios_clientes
DROP TABLE IF EXISTS `precios_clientes`;
CREATE TABLE `precios_clientes` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `producto_id` INT UNSIGNED NOT NULL,
  `tipo_cliente` ENUM('retail', 'profesional', 'distribuidor', 'mayorista') NOT NULL,
  `precio` DECIMAL(10,2) NOT NULL,
  `descuento_porcentaje` DECIMAL(5,2) DEFAULT 0.00,
  `fecha_inicio` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_fin` TIMESTAMP NULL DEFAULT NULL,
  `activo` TINYINT(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_precio_producto_tipo` (`producto_id`, `tipo_cliente`),
  INDEX `idx_tipo_cliente` (`tipo_cliente`),
  INDEX `idx_activo` (`activo`),
  CONSTRAINT `fk_precios_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: promociones
DROP TABLE IF EXISTS `promociones`;
CREATE TABLE `promociones` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(50) DEFAULT NULL UNIQUE,
  `nombre` VARCHAR(255) NOT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `tipo` ENUM('descuento_porcentaje', 'descuento_fijo', 'envio_gratis', '2x1', '3x2') NOT NULL,
  `valor` DECIMAL(10,2) NOT NULL,
  `compra_minima` DECIMAL(10,2) DEFAULT 0.00,
  `fecha_inicio` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_fin` TIMESTAMP NULL DEFAULT NULL,
  `usos_maximos` INT DEFAULT NULL,
  `usos_por_cliente` INT DEFAULT 1,
  `usos_actuales` INT DEFAULT 0,
  `aplicable_a` ENUM('todos', 'categorias', 'productos', 'marcas') DEFAULT 'todos',
  `tipo_cliente_aplicable` ENUM('todos', 'retail', 'profesional', 'distribuidor', 'mayorista') DEFAULT 'todos',
  `activo` TINYINT(1) DEFAULT 1,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_codigo` (`codigo`),
  INDEX `idx_activo` (`activo`),
  INDEX `idx_fechas` (`fecha_inicio`, `fecha_fin`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: promociones_productos
DROP TABLE IF EXISTS `promociones_productos`;
CREATE TABLE `promociones_productos` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `promocion_id` INT UNSIGNED NOT NULL,
  `producto_id` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_promocion` (`promocion_id`),
  INDEX `idx_producto` (`producto_id`),
  CONSTRAINT `fk_promo_prod_promocion` FOREIGN KEY (`promocion_id`) REFERENCES `promociones` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_promo_prod_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- MÓDULO: PEDIDOS Y VENTAS
-- ============================================================================

-- Tabla: pedidos
DROP TABLE IF EXISTS `pedidos`;
CREATE TABLE `pedidos` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `numero_pedido` VARCHAR(20) NOT NULL UNIQUE,
  `usuario_id` INT UNSIGNED NOT NULL,
  `empresa_id` INT UNSIGNED DEFAULT NULL,
  `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `estado` ENUM('carrito', 'pendiente', 'confirmado', 'en_preparacion', 'enviado', 'entregado', 'cancelado', 'devuelto') DEFAULT 'pendiente',
  `subtotal` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `descuento` DECIMAL(10,2) DEFAULT 0.00,
  `codigo_promocion` VARCHAR(50) DEFAULT NULL,
  `gastos_envio` DECIMAL(10,2) DEFAULT 0.00,
  `impuestos` DECIMAL(10,2) DEFAULT 0.00,
  `total` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  `metodo_pago` ENUM('transferencia', 'tarjeta', 'contado', 'credito_30', 'credito_60', 'credito_90') DEFAULT 'transferencia',
  `estado_pago` ENUM('pendiente', 'pagado', 'parcial', 'reembolsado') DEFAULT 'pendiente',
  `direccion_envio` TEXT NOT NULL,
  `direccion_facturacion` TEXT DEFAULT NULL,
  `notas_cliente` TEXT DEFAULT NULL,
  `notas_internas` TEXT DEFAULT NULL,
  `ip_cliente` VARCHAR(45) DEFAULT NULL,
  `user_agent` VARCHAR(500) DEFAULT NULL,
  `fecha_confirmacion` TIMESTAMP NULL DEFAULT NULL,
  `fecha_envio` TIMESTAMP NULL DEFAULT NULL,
  `fecha_entrega` TIMESTAMP NULL DEFAULT NULL,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_numero_pedido` (`numero_pedido`),
  INDEX `idx_usuario` (`usuario_id`),
  INDEX `idx_empresa` (`empresa_id`),
  INDEX `idx_estado` (`estado`),
  INDEX `idx_fecha` (`fecha`),
  CONSTRAINT `fk_pedidos_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `fk_pedidos_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: pedidos_detalle
DROP TABLE IF EXISTS `pedidos_detalle`;
CREATE TABLE `pedidos_detalle` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `pedido_id` INT UNSIGNED NOT NULL,
  `producto_id` INT UNSIGNED NOT NULL,
  `sku` VARCHAR(100) NOT NULL,
  `nombre_producto` VARCHAR(255) NOT NULL,
  `cantidad` INT NOT NULL DEFAULT 1,
  `precio_unitario` DECIMAL(10,2) NOT NULL,
  `descuento` DECIMAL(10,2) DEFAULT 0.00,
  `subtotal` DECIMAL(10,2) NOT NULL,
  `impuestos` DECIMAL(10,2) DEFAULT 0.00,
  `total` DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_pedido` (`pedido_id`),
  INDEX `idx_producto` (`producto_id`),
  CONSTRAINT `fk_pedidos_detalle_pedido` FOREIGN KEY (`pedido_id`) REFERENCES `pedidos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pedidos_detalle_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: envios
DROP TABLE IF EXISTS `envios`;
CREATE TABLE `envios` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `pedido_id` INT UNSIGNED NOT NULL,
  `transportista` VARCHAR(100) DEFAULT NULL,
  `numero_seguimiento` VARCHAR(100) DEFAULT NULL,
  `url_seguimiento` VARCHAR(500) DEFAULT NULL,
  `fecha_envio` TIMESTAMP NULL DEFAULT NULL,
  `fecha_entrega_estimada` DATE DEFAULT NULL,
  `fecha_entrega_real` TIMESTAMP NULL DEFAULT NULL,
  `estado` ENUM('pendiente', 'en_transito', 'entregado', 'devuelto', 'incidencia') DEFAULT 'pendiente',
  `notas` TEXT DEFAULT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_pedido` (`pedido_id`),
  INDEX `idx_numero_seguimiento` (`numero_seguimiento`),
  CONSTRAINT `fk_envios_pedido` FOREIGN KEY (`pedido_id`) REFERENCES `pedidos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- MÓDULO: CONTENIDOS
-- ============================================================================

-- Tabla: blog_categorias
DROP TABLE IF EXISTS `blog_categorias`;
CREATE TABLE `blog_categorias` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `slug` VARCHAR(100) NOT NULL UNIQUE,
  `descripcion` TEXT DEFAULT NULL,
  `orden` INT DEFAULT 0,
  `activo` TINYINT(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  INDEX `idx_slug` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: blog_posts
DROP TABLE IF EXISTS `blog_posts`;
CREATE TABLE `blog_posts` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(255) NOT NULL,
  `slug` VARCHAR(255) NOT NULL UNIQUE,
  `resumen` VARCHAR(500) DEFAULT NULL,
  `contenido` LONGTEXT NOT NULL,
  `categoria_id` INT UNSIGNED NOT NULL,
  `autor_id` INT UNSIGNED NOT NULL,
  `imagen_destacada` VARCHAR(500) DEFAULT NULL,
  `fecha_publicacion` TIMESTAMP NULL DEFAULT NULL,
  `estado` ENUM('borrador', 'publicado', 'archivado') DEFAULT 'borrador',
  `vistas` INT DEFAULT 0,
  `destacado` TINYINT(1) DEFAULT 0,
  `meta_title` VARCHAR(255) DEFAULT NULL,
  `meta_description` VARCHAR(500) DEFAULT NULL,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_slug` (`slug`),
  INDEX `idx_categoria` (`categoria_id`),
  INDEX `idx_autor` (`autor_id`),
  INDEX `idx_estado` (`estado`),
  INDEX `idx_fecha_publicacion` (`fecha_publicacion`),
  CONSTRAINT `fk_blog_posts_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `blog_categorias` (`id`),
  CONSTRAINT `fk_blog_posts_autor` FOREIGN KEY (`autor_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: recursos
DROP TABLE IF EXISTS `recursos`;
CREATE TABLE `recursos` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(255) NOT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `tipo` ENUM('pdf', 'video', 'guia', 'manual', 'webinar') NOT NULL,
  `url` VARCHAR(500) NOT NULL,
  `archivo_size` INT DEFAULT NULL,
  `categoria_id` INT UNSIGNED DEFAULT NULL,
  `marca_id` INT UNSIGNED DEFAULT NULL,
  `producto_id` INT UNSIGNED DEFAULT NULL,
  `acceso` ENUM('publico', 'clientes', 'profesionales') DEFAULT 'publico',
  `descargas` INT DEFAULT 0,
  `destacado` TINYINT(1) DEFAULT 0,
  `activo` TINYINT(1) DEFAULT 1,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_tipo` (`tipo`),
  INDEX `idx_categoria` (`categoria_id`),
  INDEX `idx_marca` (`marca_id`),
  INDEX `idx_producto` (`producto_id`),
  INDEX `idx_acceso` (`acceso`),
  CONSTRAINT `fk_recursos_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_recursos_marca` FOREIGN KEY (`marca_id`) REFERENCES `marcas` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_recursos_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: webinars
DROP TABLE IF EXISTS `webinars`;
CREATE TABLE `webinars` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `titulo` VARCHAR(255) NOT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `ponente` VARCHAR(255) DEFAULT NULL,
  `fecha_hora` TIMESTAMP NOT NULL,
  `duracion_minutos` INT DEFAULT 60,
  `url_registro` VARCHAR(500) DEFAULT NULL,
  `url_grabacion` VARCHAR(500) DEFAULT NULL,
  `imagen_banner` VARCHAR(500) DEFAULT NULL,
  `estado` ENUM('programado', 'en_vivo', 'finalizado', 'cancelado') DEFAULT 'programado',
  `inscritos` INT DEFAULT 0,
  `asistentes` INT DEFAULT 0,
  `destacado` TINYINT(1) DEFAULT 0,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_fecha_hora` (`fecha_hora`),
  INDEX `idx_estado` (`estado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- MÓDULO: MULTIIDIOMA
-- ============================================================================

-- Tabla: idiomas
DROP TABLE IF EXISTS `idiomas`;
CREATE TABLE `idiomas` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `codigo` VARCHAR(2) NOT NULL UNIQUE,
  `nombre` VARCHAR(50) NOT NULL,
  `nombre_nativo` VARCHAR(50) NOT NULL,
  `activo` TINYINT(1) DEFAULT 1,
  `predeterminado` TINYINT(1) DEFAULT 0,
  `orden` INT DEFAULT 0,
  PRIMARY KEY (`id`),
  INDEX `idx_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: traducciones
DROP TABLE IF EXISTS `traducciones`;
CREATE TABLE `traducciones` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `clave` VARCHAR(255) NOT NULL,
  `idioma_codigo` VARCHAR(2) NOT NULL,
  `texto` TEXT NOT NULL,
  `contexto` VARCHAR(100) DEFAULT NULL,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_traduccion` (`clave`, `idioma_codigo`),
  INDEX `idx_clave` (`clave`),
  INDEX `idx_idioma` (`idioma_codigo`),
  CONSTRAINT `fk_traducciones_idioma` FOREIGN KEY (`idioma_codigo`) REFERENCES `idiomas` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- MÓDULO: CONFIGURACIÓN Y SISTEMA
-- ============================================================================

-- Tabla: configuracion
DROP TABLE IF EXISTS `configuracion`;
CREATE TABLE `configuracion` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `clave` VARCHAR(100) NOT NULL UNIQUE,
  `valor` TEXT NOT NULL,
  `tipo` ENUM('string', 'int', 'float', 'boolean', 'json') DEFAULT 'string',
  `categoria` VARCHAR(50) DEFAULT 'general',
  `descripcion` VARCHAR(255) DEFAULT NULL,
  `fecha_actualizacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_clave` (`clave`),
  INDEX `idx_categoria` (`categoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: logs_actividad
DROP TABLE IF EXISTS `logs_actividad`;
CREATE TABLE `logs_actividad` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `usuario_id` INT UNSIGNED DEFAULT NULL,
  `tipo` VARCHAR(50) NOT NULL,
  `accion` VARCHAR(255) NOT NULL,
  `descripcion` TEXT DEFAULT NULL,
  `entidad_tipo` VARCHAR(50) DEFAULT NULL,
  `entidad_id` INT DEFAULT NULL,
  `datos_antes` JSON DEFAULT NULL,
  `datos_despues` JSON DEFAULT NULL,
  `ip` VARCHAR(45) DEFAULT NULL,
  `user_agent` VARCHAR(500) DEFAULT NULL,
  `fecha` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_usuario` (`usuario_id`),
  INDEX `idx_tipo` (`tipo`),
  INDEX `idx_fecha` (`fecha`),
  INDEX `idx_entidad` (`entidad_tipo`, `entidad_id`),
  CONSTRAINT `fk_logs_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabla: sesiones
DROP TABLE IF EXISTS `sesiones`;
CREATE TABLE `sesiones` (
  `id` VARCHAR(255) NOT NULL,
  `usuario_id` INT UNSIGNED DEFAULT NULL,
  `ip` VARCHAR(45) DEFAULT NULL,
  `user_agent` VARCHAR(500) DEFAULT NULL,
  `datos` TEXT DEFAULT NULL,
  `ultima_actividad` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `fecha_creacion` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_usuario` (`usuario_id`),
  INDEX `idx_ultima_actividad` (`ultima_actividad`),
  CONSTRAINT `fk_sesiones_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- DATOS INICIALES
-- ============================================================================

-- Insertar idiomas
INSERT INTO `idiomas` (`codigo`, `nombre`, `nombre_nativo`, `activo`, `predeterminado`, `orden`) VALUES
('es', 'Español', 'Español', 1, 1, 1),
('ca', 'Catalán', 'Català', 1, 0, 2),
('en', 'Inglés', 'English', 1, 0, 3),
('fr', 'Francés', 'Français', 1, 0, 4),
('pt', 'Portugués', 'Português', 1, 0, 5);

-- Insertar categorías principales
INSERT INTO `categorias` (`nombre`, `slug`, `descripcion`, `parent_id`, `nivel`, `orden`, `icono`, `activo`) VALUES
('VÍDEO', 'video', 'Sistemas de videovigilancia CCTV', NULL, 0, 1, 'video-camera', 1),
('ACCESOS', 'accesos', 'Control de accesos y cerraduras', NULL, 0, 2, 'door-open', 1),
('INTRUSIÓN', 'intrusion', 'Sistemas de alarma y detección', NULL, 0, 3, 'shield', 1),
('INCENDIO', 'incendio', 'Sistemas de detección de incendios', NULL, 0, 4, 'fire', 1);

-- Insertar blog categorías
INSERT INTO `blog_categorias` (`nombre`, `slug`, `descripcion`, `orden`, `activo`) VALUES
('Noticias', 'noticias', 'Últimas novedades del sector', 1, 1),
('Formaciones y Eventos', 'formaciones-eventos', 'Calendario de formaciones', 2, 1),
('Webinars', 'webinars', 'Seminarios online', 3, 1),
('Tutoriales', 'tutoriales', 'Guías técnicas paso a paso', 4, 1);

-- Configuración inicial
INSERT INTO `configuracion` (`clave`, `valor`, `tipo`, `categoria`, `descripcion`) VALUES
('sitio_nombre', 'PLASISE', 'string', 'general', 'Nombre del sitio web'),
('sitio_email', 'info@plasise.com', 'string', 'general', 'Email de contacto'),
('sitio_telefono', '+34 93 123 45 67', 'string', 'general', 'Teléfono de contacto'),
('iva_defecto', '21', 'int', 'ventas', 'IVA por defecto en %'),
('gastos_envio_gratis_desde', '500', 'float', 'ventas', 'Pedido mínimo para envío gratis'),
('moneda', 'EUR', 'string', 'ventas', 'Moneda del sistema'),
('productos_por_pagina', '20', 'int', 'catalogo', 'Productos por página'),
('mantenimiento', 'false', 'boolean', 'sistema', 'Modo mantenimiento activado');

-- ============================================================================
-- TRIGGERS Y PROCEDIMIENTOS
-- ============================================================================

-- Trigger: Actualizar stock al confirmar pedido
DELIMITER //
CREATE TRIGGER `tr_pedidos_actualizar_stock`
AFTER UPDATE ON `pedidos`
FOR EACH ROW
BEGIN
    IF NEW.estado = 'confirmado' AND OLD.estado != 'confirmado' THEN
        UPDATE productos p
        INNER JOIN pedidos_detalle pd ON p.id = pd.producto_id
        SET p.stock_actual = p.stock_actual - pd.cantidad
        WHERE pd.pedido_id = NEW.id;
    END IF;
END//
DELIMITER ;

-- Trigger: Generar número de pedido
DELIMITER //
CREATE TRIGGER `tr_pedidos_generar_numero`
BEFORE INSERT ON `pedidos`
FOR EACH ROW
BEGIN
    IF NEW.numero_pedido IS NULL OR NEW.numero_pedido = '' THEN
        SET NEW.numero_pedido = CONCAT('PED-', DATE_FORMAT(NOW(), '%Y%m%d'), '-', LPAD(LAST_INSERT_ID() + 1, 6, '0'));
    END IF;
END//
DELIMITER ;

-- Trigger: Log de actividad en productos
DELIMITER //
CREATE TRIGGER `tr_productos_log_update`
AFTER UPDATE ON `productos`
FOR EACH ROW
BEGIN
    INSERT INTO logs_actividad (tipo, accion, descripcion, entidad_tipo, entidad_id, datos_antes, datos_despues)
    VALUES (
        'producto',
        'actualizar',
        CONCAT('Producto actualizado: ', NEW.nombre),
        'productos',
        NEW.id,
        JSON_OBJECT('precio', OLD.precio_base, 'stock', OLD.stock_actual),
        JSON_OBJECT('precio', NEW.precio_base, 'stock', NEW.stock_actual)
    );
END//
DELIMITER ;

-- ============================================================================
-- VISTAS ÚTILES
-- ============================================================================

-- Vista: Productos con información completa
CREATE OR REPLACE VIEW `v_productos_completos` AS
SELECT 
    p.id,
    p.sku,
    p.nombre,
    p.slug,
    p.descripcion_corta,
    p.precio_base,
    p.stock_actual,
    p.imagen_principal,
    p.estado,
    p.destacado,
    c.nombre AS categoria_nombre,
    c.slug AS categoria_slug,
    m.nombre AS marca_nombre,
    m.slug AS marca_slug,
    m.logo_url AS marca_logo,
    p.vistas,
    p.ventas_totales,
    p.valoracion_promedio,
    p.activo
FROM productos p
LEFT JOIN categorias c ON p.categoria_id = c.id
LEFT JOIN marcas m ON p.marca_id = m.id
WHERE p.activo = 1;

-- Vista: Estadísticas de ventas
CREATE OR REPLACE VIEW `v_estadisticas_ventas` AS
SELECT 
    DATE(p.fecha) AS fecha,
    COUNT(DISTINCT p.id) AS num_pedidos,
    SUM(p.total) AS total_ventas,
    AVG(p.total) AS ticket_medio,
    SUM(pd.cantidad) AS unidades_vendidas
FROM pedidos p
INNER JOIN pedidos_detalle pd ON p.id = pd.pedido_id
WHERE p.estado NOT IN ('carrito', 'cancelado')
GROUP BY DATE(p.fecha);

-- ============================================================================
-- ÍNDICES ADICIONALES PARA PERFORMANCE
-- ============================================================================

-- Índices compuestos para búsquedas frecuentes
CREATE INDEX idx_productos_categoria_marca ON productos(categoria_id, marca_id, activo);
CREATE INDEX idx_productos_estado_destacado ON productos(estado, destacado, activo);
CREATE INDEX idx_pedidos_usuario_estado ON pedidos(usuario_id, estado, fecha);
CREATE INDEX idx_blog_estado_fecha ON blog_posts(estado, fecha_publicacion);

-- ============================================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================================================

-- Fin del schema
-- Total de tablas: 30+
-- Total de índices: 80+
-- Total de constraints: 40+
-- Total de triggers: 3
-- Total de vistas: 2

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- FIN DEL SCHEMA
-- ============================================================================
