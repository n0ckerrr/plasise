"""
PLASISE — Automatización de pedidos al proveedor
Se ejecuta cuando llega un pedido nuevo (llamado desde Flask) o vía cron:
    */15 * * * * /usr/local/bin/python3 /code/scripts/procesar_pedidos.py >> /code/logs/pedidos.log 2>&1
"""

import os
import sys
import json
import logging
import requests
import mysql.connector
from datetime import datetime

# ─────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.environ.get('DB_HOST', 'n0cker_web'),
    'port':     int(os.environ.get('DB_PORT', 3306)),
    'user':     os.environ.get('DB_USER', 'plasise'),
    'password': os.environ.get('DB_PASSWORD', 'plasise.'),
    'database': os.environ.get('DB_NAME', 'plasise'),
    'charset':  'utf8mb4',
}

PROVEEDOR_PEDIDOS_URL = os.environ.get('PROVEEDOR_PEDIDOS_URL', '')
PROVEEDOR_API_KEY     = os.environ.get('PROVEEDOR_API_KEY', '')
NOTIF_EMAIL           = os.environ.get('NOTIF_EMAIL', '')

LOG_FILE = '/code/logs/pedidos.log'

# ─────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


# ─────────────────────────────────────────────────────
# OBTENER PEDIDOS PENDIENTES DE PROCESAR
# ─────────────────────────────────────────────────────
def get_pedidos_pendientes(pedido_id: int = None) -> list[dict]:
    """
    Obtiene pedidos en estado 'pendiente' que aún no se han enviado al proveedor.
    Si se pasa pedido_id, solo procesa ese pedido.
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        if pedido_id:
            cursor.execute("""
                SELECT p.id, p.numero_pedido, p.usuario_id, p.total,
                       p.metodo_pago, p.notas, p.fecha_pedido,
                       u.nombre, u.apellidos, u.email, u.telefono,
                       d.calle, d.numero, d.piso, d.ciudad, d.provincia,
                       d.codigo_postal, d.pais
                FROM pedidos p
                LEFT JOIN usuarios u ON u.id = p.usuario_id
                LEFT JOIN direcciones_usuario d ON d.id = p.direccion_envio_id
                WHERE p.id = %s AND p.estado = 'pendiente'
            """, (pedido_id,))
        else:
            cursor.execute("""
                SELECT p.id, p.numero_pedido, p.usuario_id, p.total,
                       p.metodo_pago, p.notas, p.fecha_pedido,
                       u.nombre, u.apellidos, u.email, u.telefono,
                       d.calle, d.numero, d.piso, d.ciudad, d.provincia,
                       d.codigo_postal, d.pais
                FROM pedidos p
                LEFT JOIN usuarios u ON u.id = p.usuario_id
                LEFT JOIN direcciones_usuario d ON d.id = p.direccion_envio_id
                WHERE p.estado = 'pendiente'
                  AND p.enviado_proveedor IS NULL
                ORDER BY p.fecha_pedido ASC
                LIMIT 50
            """)
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


def get_items_pedido(pedido_id: int) -> list[dict]:
    """Obtiene las líneas de productos de un pedido"""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT pi.producto_id, pi.cantidad, pi.precio_unitario, pi.subtotal,
                   p.nombre, p.sku, p.referencia_proveedor
            FROM pedidos_items pi
            INNER JOIN productos p ON p.id = pi.producto_id
            WHERE pi.pedido_id = %s
        """, (pedido_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


# ─────────────────────────────────────────────────────
# ENVIAR PEDIDO AL PROVEEDOR
# ─────────────────────────────────────────────────────
def enviar_pedido_proveedor(pedido: dict, items: list[dict]) -> dict:
    """
    Envía el pedido al proveedor IBD Global usando el automator.
    Retorna {'ok': bool, 'referencia': str, 'error': str}
    """
    # ── Usar ibd_automator para añadir al carrito de IBD ──
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from ibd_automator import login_and_add_to_cart

        productos_ibd = [
            {'sku': item.get('sku') or item.get('referencia_proveedor', ''), 'quantity': item['cantidad']}
            for item in items
            if item.get('sku') or item.get('referencia_proveedor')
        ]

        if not productos_ibd:
            return {'ok': False, 'referencia': None, 'error': 'Ningún item tiene SKU de proveedor'}

        success = login_and_add_to_cart(productos_ibd)
        if success:
            return {
                'ok': True,
                'referencia': f"IBD-{pedido['numero_pedido']}",
                'error': None
            }
        else:
            return {'ok': False, 'referencia': None, 'error': 'Error añadiendo productos al carrito IBD'}

    except ImportError:
        log.warning("ibd_automator no disponible — usando envío por API REST")
    except Exception as e:
        log.error(f"Error en ibd_automator: {e}")
        return {'ok': False, 'referencia': None, 'error': str(e)}

    # ── Fallback: API REST del proveedor ──────────────────
    if not PROVEEDOR_PEDIDOS_URL:
        log.warning(f"PROVEEDOR_PEDIDOS_URL no configurada — simulando envío para pedido #{pedido['numero_pedido']}")
        return {
            'ok': True,
            'referencia': f"DEMO-{pedido['numero_pedido']}",
            'error': None
        }

    # Construir payload para el proveedor
    payload = {
        'referencia_cliente': pedido['numero_pedido'],
        'fecha': pedido['fecha_pedido'].isoformat() if isinstance(pedido['fecha_pedido'], datetime) else str(pedido['fecha_pedido']),
        'cliente': {
            'nombre':   f"{pedido.get('nombre', '')} {pedido.get('apellidos', '')}".strip(),
            'email':    pedido.get('email', ''),
            'telefono': pedido.get('telefono', ''),
        },
        'envio': {
            'direccion':     f"{pedido.get('calle', '')} {pedido.get('numero', '')} {pedido.get('piso', '')}".strip(),
            'ciudad':        pedido.get('ciudad', ''),
            'provincia':     pedido.get('provincia', ''),
            'codigo_postal': pedido.get('codigo_postal', ''),
            'pais':          pedido.get('pais', 'España'),
        },
        'lineas': [
            {
                'sku':        item.get('sku') or item.get('referencia_proveedor', ''),
                'cantidad':   item['cantidad'],
                'precio':     float(item['precio_unitario']),
            }
            for item in items
        ],
        'total': float(pedido['total']),
        'notas': pedido.get('notas', ''),
    }

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    if PROVEEDOR_API_KEY:
        headers['Authorization'] = f'Bearer {PROVEEDOR_API_KEY}'
        headers['X-API-Key'] = PROVEEDOR_API_KEY

    try:
        log.info(f"Enviando pedido {pedido['numero_pedido']} al proveedor...")
        r = requests.post(
            PROVEEDOR_PEDIDOS_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        r.raise_for_status()
        data = r.json()

        referencia = (
            data.get('referencia') or data.get('order_id') or
            data.get('id') or data.get('numero', 'OK')
        )
        return {'ok': True, 'referencia': str(referencia), 'error': None}

    except requests.HTTPError as e:
        error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
        log.error(f"Error HTTP enviando pedido: {error}")
        return {'ok': False, 'referencia': None, 'error': error}
    except Exception as e:
        log.error(f"Error enviando pedido al proveedor: {e}")
        return {'ok': False, 'referencia': None, 'error': str(e)}


# ─────────────────────────────────────────────────────
# ACTUALIZAR ESTADO DEL PEDIDO EN BD
# ─────────────────────────────────────────────────────
def marcar_pedido_enviado(pedido_id: int, referencia_proveedor: str):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE pedidos
            SET estado = 'confirmado',
                enviado_proveedor = NOW(),
                referencia_proveedor = %s
            WHERE id = %s
        """, (referencia_proveedor, pedido_id))
        db.commit()
        log.info(f"Pedido #{pedido_id} marcado como confirmado. Ref proveedor: {referencia_proveedor}")
    except Exception as e:
        db.rollback()
        log.error(f"Error actualizando estado pedido #{pedido_id}: {e}")
    finally:
        cursor.close()
        db.close()


def marcar_pedido_error(pedido_id: int, error: str):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE pedidos
            SET estado = 'error_proveedor',
                notas = CONCAT(COALESCE(notas, ''), '\n[ERROR PROVEEDOR]: ', %s)
            WHERE id = %s
        """, (error[:500], pedido_id))
        db.commit()
    except Exception as e:
        db.rollback()
        log.error(f"Error marcando error en pedido #{pedido_id}: {e}")
    finally:
        cursor.close()
        db.close()


# ─────────────────────────────────────────────────────
# PROCESAMIENTO PRINCIPAL
# ─────────────────────────────────────────────────────
def procesar_pedido(pedido: dict) -> bool:
    pedido_id = pedido['id']
    numero    = pedido.get('numero_pedido', f'#{pedido_id}')

    log.info(f"── Procesando pedido {numero} (ID: {pedido_id})")

    # Obtener líneas del pedido
    items = get_items_pedido(pedido_id)
    if not items:
        log.warning(f"Pedido {numero} sin items — saltando")
        return False

    log.info(f"  Items: {len(items)} productos")
    for item in items:
        log.info(f"  → SKU {item.get('sku', '?')} × {item['cantidad']} = {item['subtotal']}€")

    # Enviar al proveedor
    resultado = enviar_pedido_proveedor(pedido, items)

    if resultado['ok']:
        marcar_pedido_enviado(pedido_id, resultado['referencia'])
        log.info(f"✓ Pedido {numero} enviado correctamente. Ref: {resultado['referencia']}")
        return True
    else:
        marcar_pedido_error(pedido_id, resultado['error'])
        log.error(f"✗ Error en pedido {numero}: {resultado['error']}")
        return False


def main(pedido_id: int = None):
    log.info("=" * 60)
    log.info("PLASISE — Inicio procesamiento de pedidos")

    pedidos = get_pedidos_pendientes(pedido_id)
    log.info(f"Pedidos pendientes: {len(pedidos)}")

    if not pedidos:
        log.info("No hay pedidos pendientes — fin")
        return

    ok = 0
    errores = 0
    for pedido in pedidos:
        if procesar_pedido(pedido):
            ok += 1
        else:
            errores += 1

    log.info(f"Resultado: {ok} procesados OK, {errores} con error")
    log.info("PLASISE — Fin procesamiento de pedidos")
    log.info("=" * 60)


if __name__ == '__main__':
    # Permite pasar un ID de pedido específico como argumento
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(pid)
