import mysql.connector
import time
import sys

# Configuración DB
DB_CONFIG = {
    'user': 'plasise',
    'password': 'plasise.',
    'host': '72.61.111.50',
    'database': 'plasise',
    'port': 9966
}

def create_order():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 1. Get SKU & User
        cursor.execute("SELECT id, sku, nombre, precio_base FROM productos WHERE sku IS NOT NULL AND sku != '' LIMIT 1")
        product = cursor.fetchone()
        
        if not product:
            print("ERROR: No products found with SKU")
            return

        print(f"Producto seleccionado: {product['sku']} - {product['nombre']}")
        
        # Get Validate User
        cursor.execute("SELECT id FROM usuarios LIMIT 1")
        user = cursor.fetchone()
        user_id = user['id'] if user else 1 # Fallback to 1, unlikely to fail if db has seed data
        print(f"Usuario seleccionado ID: {user_id}")
        
        # 2. Create Order
        order_num = f"AUTO-TEST-{int(time.time())}"
        total = product['precio_base']
        
        cursor.execute("""
            INSERT INTO pedidos (numero_pedido, usuario_id, estado, total, subtotal, impuestos, direccion_envio, metodo_pago, fecha)
            VALUES (%s, %s, 'pendiente', %s, %s, 0, 'Direccion Automatica', 'transferencia', NOW())
        """, (order_num, user_id, total, total))
        
        order_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO pedidos_items (pedido_id, producto_id, sku, cantidad, precio)
            VALUES (%s, %s, %s, 1, %s)
        """, (order_id, product['id'], product['sku'], total))
        
        conn.commit()
        print(f"PEDIDO CREADO EXITOSAMENTE: ID {order_id} ({order_num})")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR DB: {e}")

if __name__ == "__main__":
    create_order()
