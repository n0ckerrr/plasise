"""
Integration Test Script

Run this on the VPS to verify:
1. Database connection
2. Schema migration (presence of 'sku' column)
3. Worker functionality (by creating a test order)
"""
import mysql.connector
import os
import sys
import time
import random
import string
from dotenv import load_dotenv

# Load environment variables
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, 'backend', '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')

load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "72.61.111.50")
DB_USER = os.getenv("DB_USER", "plasise")
DB_PASS = os.getenv("DB_PASSWORD", "plasise.")
DB_NAME = os.getenv("DB_NAME", "plasise")
DB_PORT = int(os.getenv("DB_PORT", 9966))

# Test Data
TEST_SKU = "TEST-SKU-123"  # A fake SKU, or use a real one if known
TEST_USER_ID = 1  # Assuming user ID 1 exists, otherwise update this

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        port=DB_PORT
    )

def test_db_connection():
    print("1. Testing Database Connection...", end=" ")
    try:
        conn = get_db_connection()
        conn.close()
        print("OK")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_schema_migration():
    print("2. Verifying 'sku' column in 'pedidos_items'...", end=" ")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'pedidos_items' 
            AND COLUMN_NAME = 'sku'
        """, (DB_NAME,))
        exists = cursor.fetchone()[0] > 0
        conn.close()
        
        if exists:
            print("OK (Column exists)")
            return True
        else:
            print("FAILED (Column 'sku' missing! Run add_sku_to_orders.py first)")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def create_test_order():
    print("3. Creating Test Order to trigger Worker...", end=" ")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Create Order
        order_num = 'TEST-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        total = 10.00
        
        cursor.execute("""
            INSERT INTO pedidos (numero_pedido, usuario_id, estado, total, subtotal, impuestos, direccion_envio, metodo_pago, fecha)
            VALUES (%s, %s, 'pendiente', %s, %s, 0, 'Direccion de Test', 'transferencia', NOW())
        """, (order_num, TEST_USER_ID, total, total))
        
        order_id = cursor.lastrowid
        
        # 2. Create Order Item with SKU
        cursor.execute("""
            INSERT INTO pedidos_items (pedido_id, producto_id, sku, cantidad, precio)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, 0, TEST_SKU, 1, total)) # product_id 0 for test
        
        conn.commit()
        conn.close()
        
        print(f"OK (Created Order #{order_num} with ID {order_id})")
        print(f"\n[INFO] Check your 'order_worker' logs now.")
        print(f"[INFO] It should detect Order #{order_num} and try to process SKU '{TEST_SKU}'.")
        print(f"[INFO] (The IBD login/search might fail if credentials aren't set or SKU is invalid, but the WORKER detection is what we are testing here)")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def main():
    print("--- INTEGRATION TEST START ---")
    if not test_db_connection(): return
    if not test_schema_migration(): return
    create_test_order()
    print("--- INTEGRATION TEST END ---")

if __name__ == "__main__":
    main()
