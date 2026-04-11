import requests
import re
import os
import sys
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'security-web', '.env'))
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if not os.path.exists(env_path):
    env_path = "/code/.env"
load_dotenv(env_path)

# Configuración
LOGIN_URL = "https://www.ibdglobal.com/web/login"
DOWNLOAD_URL = "https://www.ibdglobal.com/my/pricelist/download/simple"
USERNAME = os.getenv("IBD_USER")
PASSWORD = os.getenv("IBD_PASS")
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
DRIVE_FOLDER_ID = "1ywQhKAzZeLj54vy3NQgeoGRWUJMS_odZ"

# Database Configuration
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = int(os.getenv('DB_PORT', 9966))
DB_USER = os.getenv('DB_USER', 'plasise')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'plasise')

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
    except Exception as e:
        print(f"[!] Error connecting to database: {e}")
        return None

def log_event(event_type, message):
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO script_events (script_name, event_type, message) VALUES (%s, %s, %s)",
                ('ibd_downloader', event_type, str(message)[:1000])
            )
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        print(f"[!] Unable to log event: {e}")

if os.name == 'nt':
    OUTPUT_DIR = Path("c:/Users/plasi/Documents/PROYECTOS/PROYECTOS-ANTIGRAVITY/.tmp")
else:
    # Ruta para VPS (ajustar según la estructura de Easypanel si es necesario)
    OUTPUT_DIR = Path("/etc/easypanel/projects/n0cker/plasise/code/.tmp")

OUTPUT_FILE = OUTPUT_DIR / "ibd_productos.xlsx"
UPLOAD_TO_DRIVE = True  # Set to False to skip Google Drive upload

def upload_to_drive(file_path):
    """Sube el archivo a la carpeta especificada en Google Drive."""
    if not CREDENTIALS_FILE.exists():
        print(f"[!] Error: No se encontró el archivo de credenciales en {CREDENTIALS_FILE}")
        print("[!] Por favor, sigue las instrucciones de la directiva para configurar las credenciales de Google.")
        return False

    try:
        print(f"[*] Autenticando con Google Drive API...")
        scopes = ['https://www.googleapis.com/auth/drive.file']
        creds = service_account.Credentials.from_service_account_file(
            str(CREDENTIALS_FILE), scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': file_path.name,
            'parents': [DRIVE_FOLDER_ID]
        }
        media = MediaFileUpload(str(file_path),
                                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                resumable=True)
        
        print(f"[*] Subiendo '{file_path.name}' a Google Drive...")
        file = service.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id').execute()
        print(f"[+] Archivo subido con éxito. ID en Drive: {file.get('id')}")
        return True
    except Exception as e:
        print(f"[!] Error al subir a Google Drive: {e}")
        return False

def download_ibd_products():
    log_event('INFO', 'Iniciando descarga de catálogo completo de IBD Global')
    # Validar credenciales
    if not USERNAME or not PASSWORD:
        msg = "Error: IBD_USER o IBD_PASS no están definidos en el .env"
        print(f"[!] {msg}")
        log_event('ERROR', msg)
        return False
    
    # Crear directorio temporal si no existe
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
    })
    
    print(f"[*] Accediendo a la página de login: {LOGIN_URL}")
    try:
        response = session.get(LOGIN_URL, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"[!] Error de conexión: {e}")
        return False
    
    # Extraer CSRF Token
    csrf_token = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    if not csrf_token:
        print("[!] Error: No se pudo encontrar el csrf_token")
        return False
    
    token = csrf_token.group(1)
    print(f"[*] CSRF Token encontrado: {token[:10]}...")
    
    # Datos de Login
    login_data = {
        'login': USERNAME,
        'password': PASSWORD,
        'csrf_token': token,
        'redirect': ''
    }
    
    print("[*] Intentando login...")
    response = session.post(LOGIN_URL, data=login_data)
    
    print(f"[*] Post Login URL: {response.url}")
    print(f"[*] Post Login Status: {response.status_code}")
    
    # Extraer título de la página
    title = re.search(r'<title>(.*?)</title>', response.text, re.IGNORECASE)
    if title:
        print(f"[*] Título de la página: {title.group(1).strip()}")
    
    # Buscar mensajes de alerta de Odoo
    alert = re.search(r'<(div|p)[^>]+class="[^"]*alert[^"]*"[^>]*>(.*?)</\1>', response.text, re.DOTALL | re.IGNORECASE)
    if alert:
        clean_alert = re.sub(r'<[^>]+>', '', alert.group(2)).strip()
        print(f"[!] Alerta encontrada: {clean_alert}")
    
    if "error" in response.text.lower() and "invalid" in response.text.lower():
        print("[!] Error: Credenciales inválidas o error en el formulario detectado en la respuesta.")
    
    if response.status_code != 200:
        print(f"[!] Error en el login. Status code: {response.status_code}")
        return False
    
    # Verificar cookies
    print(f"[*] Cookies después de login: {session.cookies.get_dict()}")
    
    # Verificar si el login fue exitoso
    print(f"[*] Intentando descargar desde: {DOWNLOAD_URL}")
    try:
        response = session.get(DOWNLOAD_URL, stream=True, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"[!] Error de conexión al descargar: {e}")
        return False
    
    if response.status_code == 200:
        # Verificar content-type: debe ser un archivo, no HTML
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            print("[!] Error: La descarga devolvió HTML en lugar de un archivo. Posible sesión expirada.")
            return False
        
        # Verificar si no nos redirigió de nuevo al login
        if "web/login" in response.url:
            print("[!] Error: Login fallido o sesión expirada al intentar descargar.")
            return False
            
        print(f"[*] Descarga exitosa. Guardando en {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(OUTPUT_FILE)
        msg_success = f"Archivo guardado correctamente ({file_size} bytes)."
        print(f"[+] {msg_success}")
        
        if file_size < 1000:
            msg_warn = "Advertencia: El archivo es muy pequeño, puede estar vacío o corrupto."
            print(f"[!] {msg_warn}")
            log_event('WARNING', msg_warn)
            return False
        
        log_event('SUCCESS', msg_success)
        
        # Subir a Google Drive (opcional)
        if UPLOAD_TO_DRIVE:
            upload_to_drive(OUTPUT_FILE)
        
        return True
    else:
        msg_err = f"Error en la descarga. Status code: {response.status_code}"
        print(f"[!] {msg_err}")
        log_event('ERROR', msg_err)
        return False

if __name__ == "__main__":
    if download_ibd_products():
        print("\n[SUCCESS] Proceso completado con éxito.")
    else:
        print("\n[FAILED] El proceso falló.")
        sys.exit(1)
