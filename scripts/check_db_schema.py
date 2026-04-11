import mysql.connector
import os
from dotenv import load_dotenv

env_path = "/code/backend/.env"
load_dotenv(env_path)

try:
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        port=int(os.getenv('DB_PORT', 3306))
    )
    cursor = conn.cursor()
    cursor.execute("DESCRIBE orders")
    columns = cursor.fetchall()
    print("Columns in 'orders' table:")
    for col in columns:
        print(col)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
