import os
import mysql.connector
from dotenv import load_dotenv
import unicodedata
import datetime
import sys

from typing import Any, cast

# --- SETTINGS ---
# Try multiple .env locations
possible_envs = [
    "genoves/.env",
    "code/backend/.env",
    ".env"
]
for env in possible_envs:
    if os.path.exists(env):
        load_dotenv(env)
        break

def format_an(text: Any, length: int) -> str:
    """Format string to alphanumeric, uppercase, no accents, padded with spaces."""
    if text is None: 
        text_val = ""
    else:
        text_val = str(text)
        
    # Remove accents
    text_str = unicodedata.normalize('NFD', text_val)
    text_clean = "".join([c for c in text_str if unicodedata.category(c) != 'Mn'])
    # Upper case and clean special characters
    text_upper = text_clean.upper().replace('Ñ', 'N')
    # Keep only A-Z, 0-9 and spaces
    clean_text = ""
    for char in text_upper:
        if char.isalnum() or char.isspace():
            clean_text += char
        else:
            clean_text += " "
    
    # Final length adjustment using f-string precision
    res = f"{clean_text:.{length}s}"
    return res.ljust(length)

def format_num(number: Any, length: int) -> str:
    """Format number to string, padded with leading zeros."""
    try:
        val = int(float(number))
    except (ValueError, TypeError):
        val = 0
    s_val = str(abs(val)).zfill(length)
    # Use f-string to ensure max length
    return f"{s_val:.{length}s}"

def format_importe(amount: Any) -> str:
    """Format amount to AEAT 17-byte format: Sign + 16 digits (2 decimals)."""
    try:
        val = float(amount)
    except (ValueError, TypeError):
        val = 0.0
    
    sign = " " if val >= 0 else "N"
    cents_val = abs(val) * 100
    cents_str = str(round(cents_val)).zfill(16)
    # Truncate to 16 if it exceeds
    cents_trunc = f"{cents_str:.16s}"
    return sign + cents_trunc

def get_db_connection():
    # Attempt to use 'genoves' if 'plasise' fails or defaults to it
    db_name = os.getenv('DB_NAME', 'genoves')
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=db_name,
            port=int(os.getenv('DB_PORT', 3306))
        )
    except Exception as e:
        print(f"Error connecting to DB '{db_name}': {e}")
        return None

def fetch_data(id_expediente, id_propiedad, id_contribuyente):
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Fetch Taxpayer data
        cursor.execute("SELECT * FROM contribuyentes WHERE id_contribuyente = %s", (id_contribuyente,))
        contribuyente = cursor.fetchone()
        
        # 2. Fetch Property data
        cursor.execute("SELECT * FROM propiedades WHERE id_propiedad = %s", (id_propiedad,))
        propiedad = cursor.fetchone()
        
        if not contribuyente or not propiedad:
            print(f"Warning: Record not found (Cont:{id_contribuyente}, Prop:{id_propiedad})")
            return None
            
        return {
            'contribuyente': contribuyente,
            'propiedad': propiedad
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
    finally:
        conn.close()

def generate_boe_file(data, output_filename="M210_GENERATED.210"):
    # If no data, use MOCK
    if not data:
        data = {
            'nif_presentador': '12345678Z',
            'nombre_presentador': 'FINCAS GENOVES SL',
            'ejercicio': 2025,
            'fecha_devengo': '31122025',
            'nif_contribuyente': 'Y1234567A',
            'nombre_contribuyente': 'MULLER, HANS',
            'base_imponible': 1500.50,
            'tipo_gravamen': 19.0,
            'cuota_tributaria': 285.10
        }
    
    # Block 1: Header/Presentador
    reg = "<T21002> " 
    reg += "I" 
    reg += format_an(data.get('nif_presentador', '12345678Z'), 9)
    reg += format_an(data.get('nombre_presentador', 'FINCAS GENOVES SL'), 125)
    reg += "X     " 
    reg += " " 
    reg += "0A" 
    reg += format_num(data.get('ejercicio', 2025), 4)
    reg += format_num(data.get('fecha_devengo', '31122025'), 8)
    reg += "02" 
    reg += "EUR" 
    
    # Block 2: Contribuyente
    reg += format_an(data.get('nif_contribuyente'), 9)
    reg += "F" 
    reg += format_an(data.get('nombre_contribuyente'), 125)
    
    # Financial Block (Mapping positions 1442, 1703, 1708, 1849)
    reg = reg.ljust(1441)
    reg += format_importe(data.get('base_imponible', 0))
    
    reg = reg.ljust(1702)
    tipo_grav = float(data.get('tipo_gravamen', 19.0)) * 100
    reg += format_num(tipo_grav, 5)
    reg += format_importe(data.get('cuota_tributaria', 0))
    
    reg = reg.ljust(1848)
    reg += format_importe(data.get('cuota_tributaria', 0))
    
    reg = reg.ljust(1879)
    reg += format_an('FINCAS GENOVES SL', 100)
    
    # Final padding to 2700
    reg = reg.ljust(2700)
    
    with open(output_filename, 'w', encoding='iso-8859-1', newline='\r\n') as f:
        f.write(reg)
    
    print(f"SUCCESS: File {output_filename} generated ({len(reg)} bytes).")
    return output_filename

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        id_exp = sys.argv[1]
        id_prop = sys.argv[2]
        id_cont = sys.argv[3]
        anio = sys.argv[4]
        
        print(f"Fetching REAL data (Exp:{id_exp}, Prop:{id_prop}, Cont:{id_cont}, Year:{anio})...")
        raw = fetch_data(id_exp, id_prop, id_cont)
        
        if raw:
            c = raw['contribuyente']
            payload = {
                'nif_presentador': '12345678Z',
                'nombre_presentador': 'FINCAS GENOVES SL',
                'ejercicio': anio,
                'fecha_devengo': f"3112{anio}",
                'nif_contribuyente': c['nie'],
                'nombre_contribuyente': c['apellido_nombre'],
                'base_imponible': 0.0,
                'tipo_gravamen': 19.0 if c.get('es_ue_eee') else 24.0,
                'cuota_tributaria': 0.0
            }
            
            # Subquery for math
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                sql = "SELECT base_imponible, cuota_tributaria FROM calculos_irnr " \
                      "WHERE id_expediente = %s AND id_propiedad = %s AND id_contribuyente = %s AND anio_fiscal = %s " \
                      "ORDER BY fecha_calculo DESC LIMIT 1"
                cursor.execute(sql, (id_exp, id_prop, id_cont, anio))
                row = cursor.fetchone()
                if row:
                    payload['base_imponible'] = row.get('base_imponible', 0)
                    payload['cuota_tributaria'] = row.get('cuota_tributaria', 0)
                conn.close()
            
            generate_boe_file(payload, f"M210_{c['nie']}_{anio}.210")
        else:
            print("No data found for these IDs.")
    else:
        print("Usage: python db_generar_m210_boe.py <id_expediente> <id_propiedad> <id_contribuyente> <anio_fiscal>")
        print("Running mock test...")
        generate_boe_file(None, "M210_TEST_MOCK.210")
