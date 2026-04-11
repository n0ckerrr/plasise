from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector
from werkzeug.security import check_password_hash, generate_password_hash
import os
from dotenv import load_dotenv
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load env variables from parent directory using absolute path
script_dir = os.path.dirname(os.path.abspath(__file__))
# Check if .env is in same folder, parent folder, or security-web/
possible_env_paths = [
    os.path.join(script_dir, '.env'),
    os.path.join(os.path.dirname(script_dir), '.env'),
    os.path.join(os.path.dirname(os.path.dirname(script_dir)), 'security-web', '.env')
]

env_path = None
for p in possible_env_paths:
    if os.path.exists(p):
        env_path = p
        break

if env_path:
    print(f"Loading .env from: {env_path}")
    load_dotenv(env_path)
else:
    print("Warning: .env file not found in any expected location.")

app = Flask(__name__, static_folder='../', static_url_path='', template_folder='../')
app.secret_key = os.getenv('SECRET_KEY', 'aegis_super_secret_default_key_fix_me')

# Session configuration for Production (HTTPS/Proxy)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=86400 # 24 hours
)

# Fix for being behind a proxy (Nginx)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Database connection
def get_db_connection():
    try:
        host = os.getenv('DB_HOST', 'localhost')
        port = int(os.getenv('DB_PORT', 3306))
        user = os.getenv('DB_USER', 'root')
        database = os.getenv('DB_NAME', 'security_db')
        
        print(f"Connecting to DB: {user}@{host}:{port}/{database}")
        
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=os.getenv('DB_PASSWORD', ''),
            database=database,
            connect_timeout=5
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error connecting to database: {err}")
        raise err

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/catalogo.html')
def catalog():
    return app.send_static_file('catalogo.html')

# Dynamic Login Page
@app.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect('/private.html')
    return render_template('login.html')

# Dynamic Register Page
@app.route('/register', methods=['GET'])
def register_page():
    if 'user_id' in session:
        return redirect('/private.html')
    return render_template('register.html')

# API for Login
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'redirect': '/private.html'})
        else:
            return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Database error: {err}'}), 500

# API for Registration
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')

    # Validation
    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuario y contraseña son requeridos'}), 400

    if len(username) < 3 or len(username) > 50:
        return jsonify({'success': False, 'message': 'El usuario debe tener entre 3 y 50 caracteres'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}), 400

    # Validate username format (alphanumeric and underscore only)
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return jsonify({'success': False, 'message': 'El usuario solo puede contener letras, números y guiones bajos'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'El usuario ya está registrado'}), 409

        # Create password hash
        password_hash = generate_password_hash(password)

        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Usuario registrado exitosamente'}), 201

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error en la base de datos: {err}'}), 500

@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    name = data.get('name')
    lastname = data.get('lastname')
    email = data.get('email')
    message = data.get('message')

    # Send Email
    try:
        mail_server = os.getenv('MAIL_SERVER')
        mail_port = int(os.getenv('MAIL_PORT', 587))
        mail_user = os.getenv('MAIL_USERNAME')
        mail_pass = os.getenv('MAIL_PASSWORD')
        mail_sender = os.getenv('MAIL_DEFAULT_SENDER', mail_user)

        if not all([mail_server, mail_user, mail_pass]):
            # If not configured, just log to console and simulate success
            print(f"DEBUG: Contact form received from {name} {lastname} ({email}): {message}")
            return jsonify({'success': True, 'message': 'Mensaje recibido (Modo Debug)'})

        msg = MIMEMultipart()
        msg['From'] = mail_sender
        msg['To'] = mail_sender # For now, send to the same address as notification
        msg['Subject'] = f"Nuevo contacto: {name} {lastname}"

        body = f"Nombre: {name} {lastname}\nEmail: {email}\n\nMensaje:\n{message}"
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(mail_server, mail_port)
        server.starttls()
        server.login(mail_user, mail_pass)
        text = msg.as_string()
        server.sendmail(mail_sender, mail_sender, text)
        server.quit()

        return jsonify({'success': True, 'message': 'Mensaje enviado correctamente'})
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({'success': False, 'message': f'Error al enviar mensaje: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'redirect': '/'})

# API to check session status (for frontend JS)
@app.route('/api/session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({'loggedIn': True, 'username': session['username']})
    return jsonify({'loggedIn': False})

# Private Dashboard Route
@app.route('/private')
def private_dashboard():
    if 'user_id' not in session:
        return redirect('/login.html')
    return render_template('private.html')

# API for Private Data (Order History, etc.)
@app.route('/api/private-data', methods=['GET'])
def private_data():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user profile info
        cursor.execute("SELECT username, created_at FROM users WHERE id = %s", (session['user_id'],))
        user_info = cursor.fetchone()
        
        # Get recent orders
        cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (session['user_id'],))
        recent_orders = cursor.fetchall()
        
        for order in recent_orders:
            cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order['id'],))
            order['items'] = cursor.fetchall()
            
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'user': user_info,
            'recentOrders': recent_orders
        })
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Database error: {err}'}), 500

# --- Shopping Cart API ---
import json

def get_product_data():
    """Reads products.json to validate prices and stock"""
    try:
        # Construct path relative to this script
        # Script is in security-web/scripts/
        # JSON is in security-web/js/productos.json
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'js', 'productos.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading products.json: {e}")
        return None

@app.route('/api/orders', methods=['POST'])
def create_order():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para comprar'}), 401

    data = request.json
    cart_items = data.get('items', [])
    
    if not cart_items:
        return jsonify({'success': False, 'message': 'El carrito está vacío'}), 400

    catalog = get_product_data()
    if not catalog:
        return jsonify({'success': False, 'message': 'Error interno: No se pudo cargar el catálogo'}), 500

    products_map = {p['id']: p for p in catalog.get('products', [])}
    
    total_amount = 0
    final_items = []

    # Validate items and calculate total from source of truth
    for item in cart_items:
        pid = item.get('id')
        qty = item.get('quantity', 1)
        
        if pid not in products_map:
            return jsonify({'success': False, 'message': f'Producto ID {pid} no encontrado'}), 400
        
        product = products_map[pid]
        
        if not product.get('inStock'):
             return jsonify({'success': False, 'message': f'Producto {product["name"]} sin stock'}), 400
             
        # Use sale price if available, otherwise regular price
        price = product.get('salePrice') if product.get('salePrice') else product.get('price')
        
        total_amount += price * qty
        
        final_items.append({
            'product_id': pid,
            'sku': product.get('sku', ''),  # Extract SKU from product data
            'product_name': product['name'],
            'quantity': qty,
            'price_unit': price
        })


    try:
        conn = get_db_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        # 1. Create Order
        cursor.execute(
            "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s)",
            (session['user_id'], total_amount, 'completed')
        )
        order_id = cursor.lastrowid

        # 2. Create Order Items (with SKU for IBD automation)
        for item in final_items:
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, sku, product_name, quantity, price_unit) VALUES (%s, %s, %s, %s, %s, %s)",
                (order_id, item['product_id'], item['sku'], item['product_name'], item['quantity'], item['price_unit'])
            )


        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Pedido realizado con éxito', 'orderId': order_id}), 201

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error en base de datos: {err}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error inesperado: {e}'}), 500

@app.route('/api/orders', methods=['GET'])
def get_user_orders():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get orders
        cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC", (session['user_id'],))
        orders = cursor.fetchall()
        
        # Get items for these orders
        for order in orders:
            cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order['id'],))
            order['items'] = cursor.fetchall()
            
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'orders': orders})

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Database error: {err}'}), 500

@app.route('/api/categories')
def get_categories():
    """Returns hierarchical structure of categories and subcategories"""
    try:
        products_data = get_product_data()
        if not products_data:
            return jsonify({'error': 'Could not load product data'}), 500
        
        category_tree = {}
        
        for product in products_data['products']:
            main_cat = product['category']['main']
            subcats = product['category'].get('sub', [])
            
            if main_cat not in category_tree:
                category_tree[main_cat] = set()
            
            for subcat in subcats:
                category_tree[main_cat].add(subcat)
        
        # Convert sets to sorted lists for JSON
        result = {cat: sorted(list(subs)) for cat, subs in category_tree.items()}
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
