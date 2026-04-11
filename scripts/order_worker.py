"""
Order Worker - Monitors PLASISE orders and triggers IBD Global cart automation.

Flow:
  1. Polls the `pedidos` table for new orders (estado != 'carrito').
  2. For each new order, fetches order items with SKUs from `pedidos_items` + `productos`.
  3. Calls `ibd_automator.login_and_add_to_cart()` with the product list.
"""
import time
import os
import sys
import json
import mysql.connector
from dotenv import load_dotenv

# Flush verify
print("Order Worker Initializing...", flush=True)

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', 'security-web', '.env')
if not os.path.exists(env_path):
    env_path = "/code/backend/.env"

print(f"Loading .env from {env_path}", flush=True)
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "plasise_db")
DB_PORT = int(os.getenv("DB_PORT", 3306))

PROCESSED_FILE = "/code/processed_orders.json"
CHECK_INTERVAL = 30  # seconds between checks


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT
    )


def load_processed_orders():
    if os.path.exists(PROCESSED_FILE):
        try:
            with open(PROCESSED_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_processed_orders(processed):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(processed, f)


import re

def parse_shipping_address(direccion_texto, notas, order_id):
    """
    Parses the combined address string from the DB into structured fields.
    Format is typically: "Direccion, CP Ciudad, Provincia - Tel: 666555"
    """
    address = {
        'name': f'Cliente Pedido #{order_id}',
        'phone': '',
        'street': '',
        'city': '',
        'zip': '',
        'country_id': "67" # Spain
    }
    
    if not direccion_texto:
        return address
        
    # Extract phone
    if " - Tel: " in direccion_texto:
        parts = direccion_texto.split(" - Tel: ")
        main_addr = parts[0]
        address['phone'] = parts[1].strip()
    else:
        main_addr = direccion_texto
        
    # Split main address by comma
    addr_parts = [p.strip() for p in main_addr.split(',')]
    
    if len(addr_parts) >= 1:
        address['street'] = addr_parts[0]
        
    if len(addr_parts) >= 2:
        # Second part is usually "CP Ciudad"
        cp_ciudad = addr_parts[1].strip()
        # Extract CP if it starts with numbers
        match = re.search(r'^(\d{4,5})\s+(.*)', cp_ciudad)
        if match:
            address['zip'] = match.group(1)
            address['city'] = match.group(2)
        else:
            address['city'] = cp_ciudad
            
    # Include notes in street address
    if notas and str(notas).strip() != "None" and str(notas).strip() != "":
        address['street'] += f" [Notas: {notas}]"
        
    return address


def get_order_products(order_id, cursor):
    """
    Fetch products for an order from pedidos_items + productos tables.
    Returns list of dicts: [{'sku': 'ABC-123', 'quantity': 2}, ...]
    
    NOTE: SKU is stored in the productos table, not in pedidos_items.
    We JOIN to get it.
    """
    query = """
        SELECT p.sku, pi.cantidad as quantity
        FROM pedidos_items pi
        JOIN productos p ON pi.producto_id = p.id
        WHERE pi.pedido_id = %s AND p.sku IS NOT NULL AND p.sku != ''
    """
    cursor.execute(query, (order_id,))
    rows = cursor.fetchall()

    products = []
    for row in rows:
        sku = row['sku']
        qty = row['quantity']
        if sku:
            products.append({'sku': sku, 'quantity': qty})
        else:
            print(f"  WARNING: pedidos_items for pedido {order_id} has no SKU.", flush=True)

    return products


def process_order(order_id, cursor, order_data):
    """Process a single order: fetch items and trigger IBD automation."""
    print(f"\n{'='*50}", flush=True)
    print(f"Processing order #{order_id}...", flush=True)

    products = get_order_products(order_id, cursor)

    if not products:
        print(f"  No products with SKU found for order #{order_id}. Skipping.", flush=True)
        return True  # Mark as processed to avoid retrying

    print(f"  Products to order from IBD:", flush=True)
    for p in products:
        print(f"    - SKU: {p['sku']}, Qty: {p['quantity']}", flush=True)

    # Import and call the automator directly (same Python process)
    try:
        # Add scripts dir to path if not there (now located in webb/plasise-vps/scripts)
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webb', 'plasise-vps', 'scripts'))
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)

        from ibd_automator import login_and_add_to_cart
        
        # Parse shipping address
        direccion_envio = order_data.get('direccion_envio')
        notas_cliente = order_data.get('notas_cliente')
        address = parse_shipping_address(direccion_envio, notas_cliente, order_id)
        
        success = login_and_add_to_cart(products, address=address)

        if success:
            print(f"  ORDER #{order_id}: All products added to IBD cart.", flush=True)
        else:
            print(f"  ORDER #{order_id}: Some products may have failed.", flush=True)

        return True  # Mark as processed regardless (logged above)

    except Exception as e:
        print(f"  ERROR running IBD automator for order #{order_id}: {e}", flush=True)
        return False


def check_new_orders():
    """Check for new unprocessed orders and process them."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    processed_orders = load_processed_orders()

    # Query recent pedidos (last 10, excluding carritos)
    query = "SELECT id, total, estado, direccion_envio, notas_cliente FROM pedidos WHERE estado != 'carrito' ORDER BY fecha DESC LIMIT 10"
    cursor.execute(query)
    orders = cursor.fetchall()

    new_count = 0
    for order in orders:
        order_id = order['id']
        if order_id not in processed_orders:
            new_count += 1
            total_str = order.get('total', 'N/A')
            estado = order.get('estado', 'N/A')
            print(f"\nNew order detected: #{order_id} (Total: {total_str}€, Estado: {estado})", flush=True)

            success = process_order(order_id, cursor, order)
            if success:
                processed_orders.append(order_id)

    if new_count == 0:
        pass  # Silently continue polling

    save_processed_orders(processed_orders)

    cursor.close()
    conn.close()


def main():
    try:
        print(f"Order Worker started. Checking every {CHECK_INTERVAL}s for new orders...", flush=True)
        print(f"DB: {DB_HOST}:{DB_PORT}/{DB_NAME}", flush=True)

        import traceback
        while True:
            try:
                check_new_orders()
            except Exception as e:
                print(f"Error checking orders:\n{traceback.format_exc()}", flush=True)

            time.sleep(CHECK_INTERVAL)
    except Exception as e:
        import traceback
        print(f"CRITICAL FATAL ERROR IN WORKER INITIALIZATION:\n{traceback.format_exc()}", flush=True)
        time.sleep(60) # Prevent rapid restart loops

if __name__ == "__main__":
    main()
