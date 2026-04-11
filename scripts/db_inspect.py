"""Inspect DB schema for order-related tables."""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv("/code/backend/.env")

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT", 3306))
)
cur = conn.cursor()

# Show all tables
cur.execute("SHOW TABLES")
tables = [t[0] for t in cur.fetchall()]
print("=== ALL TABLES ===")
for t in tables:
    print(f"  {t}")

# Look for order-related tables
print("\n=== ORDER-RELATED TABLES ===")
for t in tables:
    if "order" in t.lower() or "item" in t.lower() or "line" in t.lower() or "product" in t.lower():
        print(f"\n--- {t} ---")
        cur.execute(f"DESCRIBE {t}")
        for col in cur.fetchall():
            print(f"  {col[0]:30s} {col[1]}")

# Show sample order
print("\n=== SAMPLE ORDER ===")
cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 1")
cols = [d[0] for d in cur.description]
row = cur.fetchone()
if row:
    for c, v in zip(cols, row):
        print(f"  {c:30s} = {v}")

conn.close()
