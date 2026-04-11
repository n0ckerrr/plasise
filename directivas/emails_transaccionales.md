# SOP – Emails Transaccionales PLASISE

## Objetivo
Enviar emails automáticos en los eventos clave del ciclo de vida del usuario y del pedido.

## Stack
- **SMTP:** Gmail via `smtp.gmail.com:587` con TLS
- **Credenciales:** `SMTP_USER` / `SMTP_PASSWORD` del `.env` (App Password, no contraseña real)
- **Módulo Python:** `smtplib` + `email.mime` (stdlib, sin dependencias extra)
- **Templates:** Strings HTML en el propio `email_service.py`

## Eventos y Triggers

| Evento | Función | Receptor |
|---|---|---|
| Usuario registrado | `send_welcome_email(user)` | Cliente |
| Pedido creado | `send_order_confirmation(order, user, items)` | Cliente + Admin |
| Admin cambia estado a "enviado" | `send_order_shipped(order, user)` | Cliente |
| Admin cambia estado a "entregado" | `send_order_delivered(order, user)` | Cliente |
| Solicitud de recuperación de contraseña | `send_password_reset(user, token)` | Cliente |

## Diseño de Emails
- Layout oscuro (#0F1117) con acento azul (#3B82F6) – coherente con la plataforma
- Logo PLASISE en texto en el header
- Footer con datos de contacto reales
- CSS inline (compatibilidad máxima con clientes de correo)

## Restricciones Conocidas
- **No usar la contraseña real de Gmail** – siempre usar App Password de `SMTP_PASSWORD`
- El envío es síncrono (no hay Celery). Si el SMTP tarda, el request tarda. Aceptable para fase 2.
- Los emails de Gmail pueden ir a spam si el dominio remitente no tiene SPF. En producción con dominio `plasise.es`, configurar SPF en el DNS.
- `send_email()` nunca debe lanzar excepción al código llamante – captura interna + log.

## Archivos
- `backend/email_service.py` – Servicio centralizado
- `backend/api_productos.py` – Llamadas al servicio en los endpoints correctos
