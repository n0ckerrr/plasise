"""
email_service.py – Servicio centralizado de emails transaccionales PLASISE
Usa smtplib (stdlib) + SMTP Gmail con App Password del .env
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── Configuración SMTP ────────────────────────────────────────────────────────
SMTP_SERVER   = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT     = int(os.getenv('SMTP_PORT', 587))
SMTP_USER     = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
ADMIN_EMAIL   = os.getenv('ADMIN_EMAIL', '')
SENDER_NAME   = 'PLASISE'
SENDER        = f'{SENDER_NAME} <{SMTP_USER}>'
BASE_URL      = 'https://plasise.es'


# ─── Utilidad de envío ─────────────────────────────────────────────────────────
def send_email(to: str | list, subject: str, html_body: str) -> bool:
    """
    Envía un email HTML. Nunca propaga excepción al código llamante.
    Retorna True si se envió correctamente, False si hubo error.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print('[EMAIL] Credenciales SMTP no configuradas. Email no enviado.')
        return False

    recipients = [to] if isinstance(to, str) else to

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = SENDER
        msg['To']      = ', '.join(recipients)
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipients, msg.as_string())

        print(f'[EMAIL] ✓ Enviado a {recipients} | {subject}')
        return True

    except Exception as e:
        print(f'[EMAIL] ✗ Error enviando email a {recipients}: {e}')
        return False


# ─── Layout base ──────────────────────────────────────────────────────────────
def _base_layout(content: str, title: str = 'PLASISE') -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#0F1117;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0F1117;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

          <!-- HEADER -->
          <tr>
            <td style="background:linear-gradient(135deg,#1E293B 0%,#0F172A 100%);
                       border-radius:12px 12px 0 0;padding:32px 40px;text-align:center;
                       border-bottom:2px solid #3B82F6;">
              <div style="font-size:28px;font-weight:800;color:#fff;letter-spacing:-0.5px;">
                PLA<span style="color:#3B82F6;">SISE</span>
              </div>
              <div style="font-size:12px;color:#64748B;margin-top:4px;letter-spacing:2px;text-transform:uppercase;">
                Seguridad &amp; Automatización
              </div>
            </td>
          </tr>

          <!-- BODY -->
          <tr>
            <td style="background:#1E293B;padding:40px;">
              {content}
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background:#0F172A;border-radius:0 0 12px 12px;padding:24px 40px;
                       text-align:center;border-top:1px solid #1E293B;">
              <p style="color:#475569;font-size:13px;margin:0 0 8px;">
                PLASISE · Soluciones de Seguridad Electrónica
              </p>
              <p style="color:#334155;font-size:12px;margin:0;">
                <a href="{BASE_URL}" style="color:#3B82F6;text-decoration:none;">{BASE_URL}</a>
                &nbsp;·&nbsp;
                <a href="mailto:{ADMIN_EMAIL}" style="color:#3B82F6;text-decoration:none;">{ADMIN_EMAIL}</a>
              </p>
              <p style="color:#1E293B;font-size:11px;margin:12px 0 0;">
                © {datetime.now().year} PLASISE. Todos los derechos reservados.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _btn(text: str, url: str) -> str:
    return f"""<div style="text-align:center;margin:28px 0;">
      <a href="{url}" style="background:#3B82F6;color:#fff;text-decoration:none;
                              padding:14px 32px;border-radius:8px;font-weight:700;
                              font-size:15px;display:inline-block;letter-spacing:0.3px;">
        {text}
      </a>
    </div>"""


def _h1(text: str) -> str:
    return f'<h1 style="color:#F1F5F9;font-size:22px;font-weight:700;margin:0 0 20px;">{text}</h1>'


def _p(text: str) -> str:
    return f'<p style="color:#94A3B8;font-size:15px;line-height:1.7;margin:0 0 16px;">{text}</p>'


def _divider() -> str:
    return '<hr style="border:none;border-top:1px solid #334155;margin:24px 0;">'


def _badge(text: str, color: str = '#3B82F6') -> str:
    return f'<span style="background:{color}22;color:{color};padding:4px 12px;border-radius:20px;font-size:13px;font-weight:600;">{text}</span>'


# ─── Templates de emails ───────────────────────────────────────────────────────

def _tpl_bienvenida(nombre: str) -> str:
    content = f"""
      {_h1(f'¡Bienvenido a PLASISE, {nombre}! 🎉')}
      {_p('Tu cuenta ha sido creada correctamente. Ya puedes acceder al catálogo profesional de productos de seguridad electrónica con precios adaptados a tu perfil.')}
      {_p('Como nuevo usuario tendrás acceso a:')}
      <ul style="color:#94A3B8;font-size:15px;line-height:2;padding-left:20px;margin:0 0 20px;">
        <li>Catálogo completo con más de 800 referencias</li>
        <li>Precios diferenciados por volumen</li>
        <li>Historial y seguimiento de pedidos</li>
        <li>Fichas técnicas y documentación descargable</li>
      </ul>
      {_btn('Acceder a mi cuenta', f'{BASE_URL}/pages/login.html')}
      {_divider()}
      {_p('Si tienes alguna duda, contáctanos directamente por WhatsApp o email.')}
    """
    return _base_layout(content, 'Bienvenido a PLASISE')


def _tpl_confirmacion_pedido(numero_pedido: str, nombre: str, items: list, subtotal: float, iva: float, total: float, metodo_pago: str) -> str:
    rows = ''
    for item in items:
        precio = float(item.get('precio', 0))
        cantidad = item.get('cantidad', 1)
        rows += f"""<tr>
          <td style="color:#94A3B8;padding:10px 0;border-bottom:1px solid #334155;font-size:14px;">
            {item.get('nombre','Producto')}
            <span style="color:#64748B;font-size:12px;"> × {cantidad}</span>
          </td>
          <td style="color:#F1F5F9;padding:10px 0;border-bottom:1px solid #334155;
                     text-align:right;font-size:14px;font-weight:600;">
            {precio * cantidad:.2f} €
          </td>
        </tr>"""

    pago_label = {'transferencia': 'Transferencia bancaria', 'tarjeta': 'Tarjeta de crédito'}.get(metodo_pago, metodo_pago.capitalize())

    content = f"""
      {_h1('✅ Pedido confirmado')}
      {_p(f'Gracias, <strong style="color:#F1F5F9;">{nombre}</strong>. Hemos recibido tu pedido correctamente.')}

      <div style="background:#0F172A;border-radius:8px;padding:20px;margin:20px 0;">
        <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
          <span style="color:#64748B;font-size:13px;text-transform:uppercase;letter-spacing:1px;">Nº Pedido</span>
          <span style="color:#3B82F6;font-size:15px;font-weight:700;">{numero_pedido}</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
          <span style="color:#64748B;font-size:13px;text-transform:uppercase;letter-spacing:1px;">Método de pago</span>
          <span style="color:#94A3B8;font-size:14px;">{pago_label}</span>
        </div>
      </div>

      <table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;">
        {rows}
        <tr>
          <td style="color:#64748B;padding:10px 0;font-size:13px;">Subtotal</td>
          <td style="color:#94A3B8;text-align:right;padding:10px 0;font-size:13px;">{subtotal:.2f} €</td>
        </tr>
        <tr>
          <td style="color:#64748B;padding:6px 0;font-size:13px;">IVA (21%)</td>
          <td style="color:#94A3B8;text-align:right;padding:6px 0;font-size:13px;">{iva:.2f} €</td>
        </tr>
        <tr>
          <td style="color:#F1F5F9;padding:12px 0 0;font-size:16px;font-weight:700;border-top:1px solid #3B82F6;">TOTAL</td>
          <td style="color:#3B82F6;text-align:right;padding:12px 0 0;font-size:18px;font-weight:800;border-top:1px solid #3B82F6;">{total:.2f} €</td>
        </tr>
      </table>

      {_btn('Ver mi pedido', f'{BASE_URL}/pages/pedidos.html')}
      {_divider()}
      {_p('Procesaremos tu pedido en las próximas 24–48 horas laborables. Te avisaremos cuando sea enviado.')}
    """
    return _base_layout(content, f'Pedido {numero_pedido} confirmado')


def _tpl_pedido_enviado(numero_pedido: str, nombre: str, tracking: str = '', transportista: str = '') -> str:
    tracking_html = ''
    if tracking:
        tracking_html = f"""
        <div style="background:#0F172A;border-radius:8px;padding:20px;margin:20px 0;">
          <p style="color:#64748B;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">Seguimiento del envío</p>
          <p style="color:#3B82F6;font-size:18px;font-weight:700;margin:0;">{tracking}</p>
          {'<p style="color:#94A3B8;font-size:13px;margin:8px 0 0;">Transportista: ' + transportista + '</p>' if transportista else ''}
        </div>"""

    content = f"""
      {_h1('🚚 Tu pedido está en camino')}
      {_p(f'Buenas noticias, <strong style="color:#F1F5F9;">{nombre}</strong>. Tu pedido <strong style="color:#3B82F6;">{numero_pedido}</strong> ha sido enviado.')}
      {tracking_html}
      {_p('En breve recibirás el paquete en la dirección indicada. Normalmente el envío tarda entre 24 y 72 horas.')}
      {_btn('Ver mi pedido', f'{BASE_URL}/pages/pedidos.html')}
    """
    return _base_layout(content, f'Pedido {numero_pedido} enviado')


def _tpl_pedido_entregado(numero_pedido: str, nombre: str) -> str:
    content = f"""
      {_h1('📦 Pedido entregado')}
      {_p(f'Hola <strong style="color:#F1F5F9;">{nombre}</strong>, tu pedido <strong style="color:#3B82F6;">{numero_pedido}</strong> ha sido marcado como entregado.')}
      {_p('Esperamos que todo sea de tu agrado. Si tienes cualquier incidencia, contacta con nosotros y lo resolveremos.')}
      {_divider()}
      {_p('¿Quieres volver a pedir? Explora el catálogo actualizado.')}
      {_btn('Ver catálogo', f'{BASE_URL}/pages/productos.html')}
    """
    return _base_layout(content, f'Pedido {numero_pedido} entregado')


def _tpl_reset_password(nombre: str, reset_url: str) -> str:
    content = f"""
      {_h1('🔑 Recuperar contraseña')}
      {_p(f'Hola <strong style="color:#F1F5F9;">{nombre}</strong>, hemos recibido una solicitud para restablecer la contraseña de tu cuenta PLASISE.')}
      {_p('Haz clic en el botón de abajo para crear una nueva contraseña. El enlace es válido durante <strong style="color:#F1F5F9;">1 hora</strong>.')}
      {_btn('Restablecer contraseña', reset_url)}
      {_divider()}
      {_p('Si no solicitaste este cambio, puedes ignorar este email. Tu contraseña actual no ha cambiado.')}
    """
    return _base_layout(content, 'Recuperar contraseña PLASISE')


def _tpl_admin_nuevo_pedido(numero_pedido: str, cliente_nombre: str, cliente_email: str, total: float, items: list) -> str:
    rows = ''.join(
        f'<tr><td style="color:#94A3B8;padding:8px 0;font-size:13px;border-bottom:1px solid #1E293B;">'
        f'{i.get("nombre","?")} × {i.get("cantidad",1)}</td>'
        f'<td style="color:#F1F5F9;text-align:right;padding:8px 0;font-size:13px;border-bottom:1px solid #1E293B;">'
        f'{float(i.get("precio",0))*i.get("cantidad",1):.2f} €</td></tr>'
        for i in items
    )
    content = f"""
      {_h1('🛒 Nuevo pedido recibido')}
      <div style="background:#0F172A;border-radius:8px;padding:20px;margin:20px 0;">
        <p style="color:#64748B;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px;">Datos del pedido</p>
        <p style="margin:0 0 6px;"><span style="color:#64748B;">Nº Pedido:</span> <strong style="color:#3B82F6;">{numero_pedido}</strong></p>
        <p style="margin:0 0 6px;"><span style="color:#64748B;">Cliente:</span> <span style="color:#F1F5F9;">{cliente_nombre}</span></p>
        <p style="margin:0;"><span style="color:#64748B;">Email:</span> <a href="mailto:{cliente_email}" style="color:#3B82F6;text-decoration:none;">{cliente_email}</a></p>
      </div>
      <table width="100%" cellpadding="0" cellspacing="0">{rows}</table>
      <p style="color:#3B82F6;font-size:20px;font-weight:800;text-align:right;margin:16px 0 0;">Total: {total:.2f} €</p>
      {_btn('Ver pedido en Admin', f'{BASE_URL}/pages/admin/pedidos.html')}
    """
    return _base_layout(content, f'Nuevo pedido {numero_pedido}')


# ─── Funciones públicas ────────────────────────────────────────────────────────

def send_welcome_email(nombre: str, email: str) -> bool:
    """Email de bienvenida tras el registro."""
    return send_email(
        to=email,
        subject='¡Bienvenido a PLASISE! Tu cuenta está lista 🎉',
        html_body=_tpl_bienvenida(nombre)
    )


def send_order_confirmation(numero_pedido: str, nombre: str, email: str,
                             items: list, subtotal: float, iva: float,
                             total: float, metodo_pago: str = 'transferencia') -> bool:
    """Confirmación de pedido al cliente."""
    html = _tpl_confirmacion_pedido(numero_pedido, nombre, items, subtotal, iva, total, metodo_pago)
    cliente_ok = send_email(
        to=email,
        subject=f'✅ Pedido {numero_pedido} confirmado – PLASISE',
        html_body=html
    )
    # Notificación al admin
    if ADMIN_EMAIL:
        admin_html = _tpl_admin_nuevo_pedido(numero_pedido, nombre, email, total, items)
        send_email(
            to=ADMIN_EMAIL,
            subject=f'🛒 Nuevo pedido {numero_pedido} de {nombre}',
            html_body=admin_html
        )
    return cliente_ok


def send_order_shipped(numero_pedido: str, nombre: str, email: str,
                        tracking: str = '', transportista: str = '') -> bool:
    """Notificación de envío al cliente."""
    return send_email(
        to=email,
        subject=f'🚚 Tu pedido {numero_pedido} está en camino – PLASISE',
        html_body=_tpl_pedido_enviado(numero_pedido, nombre, tracking, transportista)
    )


def send_order_delivered(numero_pedido: str, nombre: str, email: str) -> bool:
    """Notificación de entrega al cliente."""
    return send_email(
        to=email,
        subject=f'📦 Pedido {numero_pedido} entregado – PLASISE',
        html_body=_tpl_pedido_entregado(numero_pedido, nombre)
    )


def send_password_reset(nombre: str, email: str, reset_token: str) -> bool:
    """Email de recuperación de contraseña."""
    reset_url = f'{BASE_URL}/pages/reset-password.html?token={reset_token}'
    return send_email(
        to=email,
        subject='🔑 Recuperar contraseña PLASISE',
        html_body=_tpl_reset_password(nombre, reset_url)
    )
