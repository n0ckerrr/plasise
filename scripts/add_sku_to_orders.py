"""
Database Migration Script - Add SKU field to pedidos_items
Adds 'sku' column to pedidos_items table to support IBD automation.
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(backend_dir, 'backend', '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "72.61.111.50")
DB_USER = os.getenv("DB_USER", "plasise")
DB_PASS = os.getenv("DB_PASSWORD", "plasise.")
DB_NAME = os.getenv("DB_NAME", "plasise")
DB_PORT = int(os.getenv("DB_PORT", 9966))


def main():
    """Add SKU column to pedidos_items table if it doesn't exist."""
    print("=" * 60)
    print("DATABASE MIGRATION: Add SKU to pedidos_items")
    print("=" * 60)
    
    try:
        # Connect to database
        print(f"\nConnecting to {DB_HOST}:{DB_PORT}/{DB_NAME}...")
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT
        )
        cursor = conn.cursor()
        
        # Check if column already exists
        print("Checking if 'sku' column exists in pedidos_items...")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'pedidos_items' 
            AND COLUMN_NAME = 'sku'
        """, (DB_NAME,))
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("OK - Column 'sku' already exists in pedidos_items. No migration needed.")
        else:
            print("Adding 'sku' column to pedidos_items...")
            cursor.execute("""
                ALTER TABLE pedidos_items 
                ADD COLUMN sku VARCHAR(100) AFTER producto_id
            """)
            conn.commit()
            print("OK - Column 'sku' added successfully!")
        
        # Show table structure
        print("\nCurrent pedidos_items table structure:")
        cursor.execute("DESCRIBE pedidos_items")
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} {row[1]:<15} {row[2]:<5}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        return True
        
    except mysql.connector.Error as err:
        print(f"\nERROR - Database error: {err}")
        return False
    except Exception as e:
        print(f"\nERROR - Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
