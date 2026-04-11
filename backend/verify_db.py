import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', '72.61.111.50'),
        port=int(os.getenv('DB_PORT', 9966)),
        user=os.getenv('DB_USER', 'plasise'),
        password=os.getenv('DB_PASSWORD', 'plasise.'),
        database=os.getenv('DB_NAME', 'plasise')
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    cursor.fetchone()
    cursor.close()
    conn.close()
    print("✅ Conexión a base de datos exitosa!")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
