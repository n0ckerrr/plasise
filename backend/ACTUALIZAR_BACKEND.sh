#!/bin/bash
echo "🚀 Actualizando backend de PLASISE..."
cd /etc/easypanel/projects/n0cker/plasise/code/backend
cp api_productos.py api_productos.py.backup_$(date +%Y%m%d_%H%M%S)
cat > api_productos.py << 'PYTHONEND'
from flask import Flask, jsonify, request, session, Response
from invoice_generator import generate_invoice_pdf

from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
from datetime import datetime
# Integración Holded
try:
    from holded_integration import crear_factura_holded
    HOLDED_ENABLED = True
except ImportError:
    HOLDED_ENABLED = False
    print('Holded integration not available')

# Servicio de emails transaccionales
try:
    from email_service import (
        send_welcome_email,
        send_order_confirmation,
        send_order_shipped,
        send_order_delivered
    )
    EMAIL_ENABLED = True
except ImportError:
    EMAIL_ENABLED = False
    print('Email service not available')


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'aegis_super_secret_key_vps_stable')

# Configuración de seguridad dinámica
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://plasise.es,https://www.plasise.es').split(',')
CORS(app, supports_credentials=True, origins=CORS_ORIGINS, expose_headers=["Content-Type", "Authorization"])

app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

def get_db():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', '72.61.111.50'),
        port=int(os.getenv('DB_PORT', 9966)),
        user=os.getenv('DB_USER', 'plasise'),
        password=os.getenv('DB_PASSWORD', 'plasise.'),
        database=os.getenv('DB_NAME', 'plasise')
    )

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS script_events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                script_name VARCHAR(100) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Table script_events checked/created successfully.")
    except Exception as e:
        print(f"Error initializing DB (script_events): {e}")

init_db()

# ========================================
# HEALTH CHECK
# ========================================
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

# ========================================
# AUTENTICACION
# ========================================
@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        required_fields = ['nombre', 'apellidos', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'El campo {field} es requerido'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'El email ya esta registrado'}), 400
        
        if not data.get('acepta_privacidad'):
            return jsonify({'success': False, 'error': 'Debe aceptar la politica de privacidad'}), 400
        
        password_hash = generate_password_hash(data['password'])
        
        query = """
            INSERT INTO usuarios (nombre, apellidos, email, telefono, password_hash, rol, activo, acepta_privacidad, fecha_aceptacion_privacidad, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['nombre'],
            data['apellidos'],
            data['email'],
            data.get('telefono', ''),
            password_hash,
            'cliente_retail',
            1,
            1,
            datetime.now(),
            datetime.now()
        )
        
        cursor.execute(query, values)
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()

        # Enviar email de bienvenida
        if EMAIL_ENABLED:
            send_welcome_email(
                nombre=data['nombre'],
                email=data['email']
            )
        
        return jsonify({'success': True, 'message': 'Usuario registrado exitosamente', 'user_id': user_id}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'error': 'Email y password son requeridos'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, nombre, apellidos, email, password_hash, rol, activo 
            FROM usuarios WHERE email = %s
        """, (data['email'],))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'error': 'Email o password incorrectos'}), 401
        
        if not user['activo']:
            return jsonify({'success': False, 'error': 'Usuario desactivado'}), 401
        
        if not check_password_hash(user['password_hash'], data['password']):
            return jsonify({'success': False, 'error': 'Email o password incorrectos'}), 401
        
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_nombre'] = user['nombre']
        session['user_rol'] = user['rol']
        
        return jsonify({
            'success': True,
            'message': 'Login exitoso',
            'user': {
                'id': user['id'],
                'nombre': user['nombre'],
                'apellidos': user['apellidos'],
                'email': user['email'],
                'rol': user['rol']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Sesion cerrada'}), 200


@app.route('/api/v1/auth/session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session.get('user_id'),
                'nombre': session.get('user_nombre'),
                'email': session.get('user_email'),
                'rol': session.get('user_rol')
            }
        }), 200
    return jsonify({'authenticated': False}), 200


# ========================================
# PRODUCTOS
# ========================================
@app.route('/api/v1/products', methods=['GET'])
def get_productos():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        search = request.args.get('search', '')
        categoria = request.args.get('categoria', '')
        marca_id = request.args.get('marca_id', '')
        min_price = request.args.get('min_price', '')
        max_price = request.args.get('max_price', '')
        sort = request.args.get('sort', 'name')
        destacado = request.args.get('destacado', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        offset = (page - 1) * per_page
        
        query = "SELECT * FROM productos WHERE activo = 1"
        params = []
        
        if search:
            query += " AND (nombre LIKE %s OR descripcion_corta LIKE %s OR sku LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if categoria:
            query += " AND categoria_id = %s"
            params.append(categoria)
        
        if marca_id:
            query += " AND marca_id = %s"
            params.append(marca_id)
        
        if min_price:
            query += " AND precio_base >= %s"
            params.append(float(min_price))
        
        if max_price:
            query += " AND precio_base <= %s"
            params.append(float(max_price))
        
        if destacado:
            query += " AND destacado = 1"
        
        if sort == 'price_asc':
            query += " ORDER BY precio_base ASC"
        elif sort == 'price_desc':
            query += " ORDER BY precio_base DESC"
        else:
            query += " ORDER BY nombre ASC"
        
        count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        productos = cursor.fetchall()
        
        for p in productos:
            for field in ['precio_base', 'precio_pvp_recomendado', 'coste', 'peso']:
                if p.get(field):
                    p[field] = float(p[field])
            p['stock'] = p.get('stock_actual', 0)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'products': productos,
            'total': total,
            'page': page,
            'current_page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/products/<int:id>', methods=['GET'])
def get_producto(id):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM productos WHERE id = %s AND activo = 1", (id,))
        producto = cursor.fetchone()
        
        if not producto:
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        for field in ['precio_base', 'precio_pvp_recomendado', 'coste', 'peso']:
            if producto.get(field):
                producto[field] = float(producto[field])
                
        producto['stock'] = producto.get('stock_actual', 0)
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'product': producto})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# MARCAS
# ========================================
@app.route('/api/v1/brands', methods=['GET'])
def get_marcas():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM marcas WHERE activo = 1 ORDER BY nombre")
        marcas = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'brands': marcas})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# ========================================
# CATEGORIAS
# ========================================
@app.route('/api/v1/categories', methods=['GET'])
def get_categorias():
    """Obtener categorías en formato jerárquico"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Parámetro para formato plano o árbol
        format_type = request.args.get('format', 'tree')
        parent_id = request.args.get('parent_id', None)
        
        if format_type == 'flat':
            # Formato plano - todas las categorías
            cursor.execute("SELECT * FROM categorias WHERE activo = 1 ORDER BY nivel, orden")
            categorias = cursor.fetchall()
        elif parent_id:
            # Solo hijos de un parent específico
            cursor.execute("SELECT * FROM categorias WHERE activo = 1 AND parent_id = %s ORDER BY orden", (parent_id,))
            categorias = cursor.fetchall()
        else:
            # Formato árbol - construir jerarquía
            cursor.execute("SELECT * FROM categorias WHERE activo = 1 ORDER BY nivel, orden")
            all_cats = cursor.fetchall()
            
            # Construir árbol
            cats_by_id = {cat['id']: {**cat, 'children': []} for cat in all_cats}
            root_cats = []
            
            for cat in all_cats:
                if cat['parent_id'] is None:
                    root_cats.append(cats_by_id[cat['id']])
                else:
                    parent = cats_by_id.get(cat['parent_id'])
                    if parent:
                        parent['children'].append(cats_by_id[cat['id']])
            
            cursor.close()
            conn.close()
            return jsonify({'success': True, 'categories': root_cats})
        
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'categories': categorias})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/categories/<int:id>', methods=['GET'])
def get_categoria(id):
    """Obtener una categoría específica con sus hijos"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener categoría
        cursor.execute("SELECT * FROM categorias WHERE id = %s AND activo = 1", (id,))
        categoria = cursor.fetchone()
        
        if not categoria:
            return jsonify({'success': False, 'error': 'Categoría no encontrada'}), 404
        
        # Obtener hijos
        cursor.execute("SELECT * FROM categorias WHERE parent_id = %s AND activo = 1 ORDER BY orden", (id,))
        categoria['children'] = cursor.fetchall()
        
        # Obtener padre si existe
        if categoria['parent_id']:
            cursor.execute("SELECT id, nombre, slug FROM categorias WHERE id = %s", (categoria['parent_id'],))
            categoria['parent'] = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'category': categoria})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# CARRITO
# ========================================
@app.route('/api/v1/cart', methods=['GET'])
def get_cart():
    if 'user_id' not in session:
        return jsonify({'success': True, 'items': [], 'items_count': 0, 'total': 0})
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT c.*, p.nombre, p.sku, p.precio_base, p.imagen_principal
            FROM carrito c
            JOIN productos p ON c.producto_id = p.id
            WHERE c.usuario_id = %s
        """
        cursor.execute(query, (session['user_id'],))
        items = cursor.fetchall()
        
        total = 0
        for item in items:
            item['precio_base'] = float(item['precio_base'])
            item['subtotal'] = item['precio_base'] * item['cantidad']
            total += item['subtotal']
            item['product'] = {
                'id': item['producto_id'],
                'nombre': item['nombre'],
                'sku': item['sku'],
                'precio_base': item['precio_base'],
                'imagen_principal': item['imagen_principal']
            }
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'items': items, 'items_count': len(items), 'total': total})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Debe iniciar sesion'}), 401
    
    try:
        data = request.get_json()
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad', 1)
        
        if not producto_id:
            return jsonify({'success': False, 'error': 'producto_id es requerido'}), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id FROM productos WHERE id = %s AND activo = 1", (producto_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        cursor.execute("SELECT id, cantidad FROM carrito WHERE usuario_id = %s AND producto_id = %s", 
                      (session['user_id'], producto_id))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("UPDATE carrito SET cantidad = %s WHERE id = %s", 
                          (existing['cantidad'] + cantidad, existing['id']))
        else:
            cursor.execute("INSERT INTO carrito (usuario_id, producto_id, cantidad, fecha_agregado) VALUES (%s, %s, %s, %s)",
                          (session['user_id'], producto_id, cantidad, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Producto agregado al carrito'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/cart/remove/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Debe iniciar sesion'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM carrito WHERE id = %s AND usuario_id = %s", (item_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Producto eliminado del carrito'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# ADMIN - GESTIÓN DE PRODUCTOS
# ========================================

@app.route('/api/v1/admin/products/<int:id>', methods=['PUT'])
def update_producto(id):
    """Actualizar un producto"""
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar que existe
        cursor.execute("SELECT id FROM productos WHERE id = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        # Construir query de actualización
        fields = []
        values = []
        
        if 'nombre' in data:
            fields.append("nombre = %s")
            values.append(data['nombre'])
        if 'sku' in data:
            fields.append("sku = %s")
            values.append(data['sku'])
        if 'precio_base' in data:
            fields.append("precio_base = %s")
            values.append(data['precio_base'])
        if 'stock' in data:
            fields.append("stock = %s")
            values.append(data['stock'])
        if 'categoria_id' in data:
            fields.append("categoria_id = %s")
            values.append(data['categoria_id'])
        if 'descripcion_corta' in data:
            fields.append("descripcion_corta = %s")
            values.append(data['descripcion_corta'])
        if 'descripcion_larga' in data:
            fields.append("descripcion_larga = %s")
            values.append(data['descripcion_larga'])
        if 'marca_id' in data:
            fields.append("marca_id = %s")
            values.append(data['marca_id'])
        if 'activo' in data:
            fields.append("activo = %s")
            values.append(data['activo'])
        
        if not fields:
            return jsonify({'success': False, 'error': 'No hay campos para actualizar'}), 400
        
        values.append(id)
        query = f"UPDATE productos SET {', '.join(fields)} WHERE id = %s"
        
        cursor.execute(query, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Producto actualizado correctamente'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/products/<int:id>/category', methods=['PUT'])
def update_producto_category(id):
    """Actualizar solo la categoría de un producto"""
    try:
        data = request.get_json()
        categoria_id = data.get('categoria_id')
        
        if not categoria_id:
            return jsonify({'success': False, 'error': 'categoria_id es requerido'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Verificar que el producto existe
        cursor.execute("SELECT id FROM productos WHERE id = %s", (id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Producto no encontrado'}), 404
        
        # Verificar que la categoría existe
        cursor.execute("SELECT id FROM categorias WHERE id = %s AND activo = 1", (categoria_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Categoría no encontrada'}), 404
        
        # Actualizar
        cursor.execute("UPDATE productos SET categoria_id = %s WHERE id = %s", (categoria_id, id))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Categoría actualizada correctamente'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/products/bulk-category', methods=['PUT'])
def update_bulk_category():
    """Actualizar categoría de múltiples productos"""
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])
        categoria_id = data.get('categoria_id')
        
        if not product_ids or not categoria_id:
            return jsonify({'success': False, 'error': 'product_ids y categoria_id son requeridos'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        placeholders = ','.join(['%s'] * len(product_ids))
        cursor.execute(
            f"UPDATE productos SET categoria_id = %s WHERE id IN ({placeholders})",
            [categoria_id] + product_ids
        )
        
        updated = cursor.rowcount
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'{updated} productos actualizados',
            'updated_count': updated
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




@app.route('/api/v1/cart/update/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    """Actualizar cantidad de un item en el carrito"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Debe iniciar sesión'
            }), 401
        
        data = request.get_json()
        cantidad = data.get('cantidad', 1)
        
        if cantidad < 1:
            return jsonify({
                'success': False,
                'error': 'La cantidad debe ser al menos 1'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM carrito 
            WHERE id = %s AND usuario_id = %s
        """, (item_id, session['user_id']))
        
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Item no encontrado'
            }), 404
        
        cursor.execute("""
            UPDATE carrito SET cantidad = %s 
            WHERE id = %s AND usuario_id = %s
        """, (cantidad, item_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Cantidad actualizada'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500



# ========================================
# PERFIL DE USUARIO
# ========================================

@app.route('/api/v1/auth/profile', methods=['GET'])
def get_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre, apellidos, email, telefono, empresa, cif, rol, activo, fecha_registro
            FROM usuarios WHERE id = %s
        """, (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if not user:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
        if user.get('fecha_registro'):
            user['fecha_registro'] = user['fecha_registro'].isoformat()
        return jsonify({'success': True, 'user': user})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v1/auth/profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        fields, values = [], []
        for field in ['nombre', 'apellidos', 'telefono', 'empresa', 'cif']:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(data[field])
        if not fields:
            return jsonify({'success': False, 'error': 'No hay campos'}), 400
        values.append(session['user_id'])
        cursor.execute(f"UPDATE usuarios SET {', '.join(fields)} WHERE id = %s", values)
        conn.commit()
        cursor.close()
        conn.close()
        if 'nombre' in data:
            session['user_nombre'] = data['nombre']
        return jsonify({'success': True, 'message': 'Perfil actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v1/auth/change-password', methods=['PUT'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        data = request.get_json()
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'success': False, 'error': 'Contraseñas requeridas'}), 400
        if len(data['new_password']) < 6:
            return jsonify({'success': False, 'error': 'Mínimo 6 caracteres'}), 400
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM usuarios WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        if not user or not check_password_hash(user['password_hash'], data['current_password']):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Contraseña actual incorrecta'}), 400
        cursor.execute("UPDATE usuarios SET password_hash = %s WHERE id = %s", 
                      (generate_password_hash(data['new_password']), session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Contraseña cambiada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# ESTADÍSTICAS DE USUARIO
# ========================================

@app.route('/api/v1/user/stats', methods=['GET'])
def get_user_stats():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) as total_pedidos, COALESCE(SUM(total), 0) as total_gastado
            FROM pedidos WHERE usuario_id = %s AND estado NOT IN ('cancelado', 'carrito')
        """, (session['user_id'],))
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({
            'success': True,
            'total_pedidos': stats['total_pedidos'] or 0,
            'total_gastado': float(stats['total_gastado'] or 0)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# DIRECCIONES DEL USUARIO
# ========================================

@app.route('/api/v1/user/addresses', methods=['GET'])
def get_addresses():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM direcciones_usuario WHERE usuario_id = %s AND activo = 1
            ORDER BY principal DESC, id DESC
        """, (session['user_id'],))
        addresses = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'addresses': addresses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v1/user/addresses', methods=['POST'])
def add_address():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        if data.get('principal'):
            cursor.execute("UPDATE direcciones_usuario SET principal = 0 WHERE usuario_id = %s", (session['user_id'],))
        cursor.execute("""
            INSERT INTO direcciones_usuario (usuario_id, nombre, direccion, cp, ciudad, provincia, telefono, principal, activo)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
        """, (session['user_id'], data.get('nombre', 'Mi dirección'), data.get('direccion'), data.get('cp'),
              data.get('ciudad'), data.get('provincia'), data.get('telefono', ''), 1 if data.get('principal') else 0))
        conn.commit()
        address_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'address_id': address_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v1/user/addresses/<int:id>', methods=['DELETE'])
def delete_address(id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE direcciones_usuario SET activo = 0 WHERE id = %s AND usuario_id = %s", (id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# ADMIN - GESTIÓN DE MARCAS
# ========================================

@app.route('/api/v1/admin/brands', methods=['GET'])
def admin_brands():
    """Listar todas las marcas para admin (incluye inactivas y conteo de productos)"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT m.*, COUNT(p.id) as productos_count
            FROM marcas m
            LEFT JOIN productos p ON p.marca_id = m.id AND p.activo = 1
            GROUP BY m.id
            ORDER BY m.nombre
        """)
        brands = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'brands': brands})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/brands', methods=['POST'])
def admin_brands_create():
    """Crear nueva marca"""
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({'success': False, 'error': 'Nombre es requerido'}), 400

        # Generar slug
        slug = data['nombre'].lower().strip()
        slug = slug.replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO marcas (nombre, slug, web_oficial, descripcion, activo, fecha_creacion)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            data['nombre'],
            slug,
            data.get('web_oficial', ''),
            data.get('descripcion', ''),
            data.get('activo', 1)
        ))
        conn.commit()
        new_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Marca creada', 'id': new_id}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/brands/<int:id>', methods=['PUT'])
def admin_brands_update(id):
    """Actualizar marca"""
    try:
        data = request.get_json()

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM marcas WHERE id = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Marca no encontrada'}), 404

        fields = []
        values = []

        if 'nombre' in data:
            fields.append("nombre = %s")
            values.append(data['nombre'])
            # Actualizar slug también
            slug = data['nombre'].lower().strip()
            slug = slug.replace(' ', '-').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
            fields.append("slug = %s")
            values.append(slug)
        if 'web_oficial' in data:
            fields.append("web_oficial = %s")
            values.append(data['web_oficial'])
        if 'descripcion' in data:
            fields.append("descripcion = %s")
            values.append(data['descripcion'])
        if 'logo_url' in data:
            fields.append("logo_url = %s")
            values.append(data['logo_url'])
        if 'activo' in data:
            fields.append("activo = %s")
            values.append(data['activo'])

        if not fields:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'No hay campos para actualizar'}), 400

        values.append(id)
        query = f"UPDATE marcas SET {', '.join(fields)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Marca actualizada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/brands/<int:id>', methods=['DELETE'])
def admin_brands_delete(id):
    """Desactivar marca (soft delete)"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("UPDATE marcas SET activo = 0 WHERE id = %s", (id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Marca eliminada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# ADMIN - GESTIÓN DE USUARIOS
# ========================================

@app.route('/api/v1/admin/users', methods=['GET'])
def admin_users():
    """Listar usuarios para admin con paginación y filtros"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        search = request.args.get('search', '')
        rol = request.args.get('rol', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page

        query = """
            SELECT u.id, u.email, u.nombre, u.apellidos, u.telefono, u.rol, u.activo,
                   u.fecha_registro, u.ultimo_acceso, u.tipo_usuario,
                   e.nombre_comercial as empresa
            FROM usuarios u
            LEFT JOIN empresas e ON u.empresa_id = e.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (u.nombre LIKE %s OR u.apellidos LIKE %s OR u.email LIKE %s OR e.nombre_comercial LIKE %s)"
            s = f"%{search}%"
            params.extend([s, s, s, s])

        if rol:
            query += " AND u.rol = %s"
            params.append(rol)

        # Count
        count_query = query.replace(
            "SELECT u.id, u.email, u.nombre, u.apellidos, u.telefono, u.rol, u.activo,\n                   u.fecha_registro, u.ultimo_acceso, u.tipo_usuario,\n                   e.nombre_comercial as empresa",
            "SELECT COUNT(*) as total"
        )
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        query += " ORDER BY u.fecha_registro DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])

        cursor.execute(query, params)
        users = cursor.fetchall()

        # Serializar fechas
        for u in users:
            if u.get('fecha_registro'):
                u['fecha_registro'] = u['fecha_registro'].isoformat()
            if u.get('ultimo_acceso'):
                u['ultimo_acceso'] = u['ultimo_acceso'].isoformat()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/users/<int:id>', methods=['PUT'])
def admin_users_update(id):
    """Actualizar usuario"""
    try:
        data = request.get_json()

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404

        fields = []
        values = []

        if 'nombre' in data:
            fields.append("nombre = %s")
            values.append(data['nombre'])
        if 'apellidos' in data:
            fields.append("apellidos = %s")
            values.append(data['apellidos'])
        if 'telefono' in data:
            fields.append("telefono = %s")
            values.append(data['telefono'])
        if 'rol' in data:
            fields.append("rol = %s")
            values.append(data['rol'])
        if 'activo' in data:
            fields.append("activo = %s")
            values.append(data['activo'])

        if not fields:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'No hay campos para actualizar'}), 400

        values.append(id)
        query = f"UPDATE usuarios SET {', '.join(fields)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Usuario actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/users/<int:id>', methods=['DELETE'])
def admin_users_delete(id):
    """Desactivar usuario (soft delete)"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("UPDATE usuarios SET activo = 0 WHERE id = %s", (id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Usuario desactivado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# ADMIN - DASHBOARD
# ========================================
@app.route('/api/v1/admin/dashboard/stats', methods=['GET'])
def admin_dashboard_stats():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Productos total
        cursor.execute("SELECT COUNT(*) as total FROM productos")
        productos = cursor.fetchone()['total']
        
        # Productos sin stock
        cursor.execute("SELECT COUNT(*) as total FROM productos WHERE stock_actual <= 0")
        sin_stock = cursor.fetchone()['total']
        
        # Usuarios total
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        usuarios = cursor.fetchone()['total']
        
        # Pedidos este mes
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute("SELECT COUNT(*) as total, SUM(total) as ventas FROM pedidos WHERE DATE_FORMAT(fecha, '%Y-%m') = %s AND estado != 'cancelado'", (current_month,))
        mes_stats = cursor.fetchone()
        pedidos_mes = mes_stats['total']
        ventas_mes = float(mes_stats['ventas'] or 0)
        
        # Pedidos pendientes
        cursor.execute("SELECT COUNT(*) as total FROM pedidos WHERE estado = 'pendiente'")
        pedidos_pendientes = cursor.fetchone()['total']
        
        # Ultimos 5 pedidos
        cursor.execute("""
            SELECT p.id, p.total, p.estado, p.fecha, p.numero_pedido, u.nombre, u.email
            FROM pedidos p
            LEFT JOIN usuarios u ON p.usuario_id = u.id
            ORDER BY p.fecha DESC LIMIT 5
        """)
        ultimos_pedidos = cursor.fetchall()
        
        for p in ultimos_pedidos:
            p['total'] = float(p['total'])
            p['fecha'] = p['fecha'].isoformat()
            
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'productos': productos,
                'usuarios': usuarios,
                'pedidos_mes': pedidos_mes,
                'ventas_mes': ventas_mes,
                'pedidos_pendientes': pedidos_pendientes,
                'sin_stock': sin_stock
            },
            'ultimos_pedidos': ultimos_pedidos
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# PEDIDOS DEL USUARIO
# ========================================

@app.route('/api/v1/user/orders', methods=['GET'])
def get_user_orders():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        offset = (page - 1) * per_page
        estado = request.args.get('estado', '')
        search = request.args.get('search', '')
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM pedidos WHERE usuario_id = %s AND estado != 'carrito'"
        params = [session['user_id']]
        if estado:
            query += " AND estado = %s"
            params.append(estado)
        if search:
            query += " AND (numero_pedido LIKE %s)"
            params.append(f'%{search}%')
        count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        query += " ORDER BY fecha DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        cursor.execute(query, params)
        orders = cursor.fetchall()
        for order in orders:
            if order.get('fecha'):
                order['fecha_pedido'] = order['fecha'].isoformat()
            if order.get('total'):
                order['total'] = float(order['total'])
            cursor.execute("""
                SELECT pi.*, p.nombre, p.sku, p.imagen_principal as imagen
                FROM pedidos_items pi JOIN productos p ON pi.producto_id = p.id
                WHERE pi.pedido_id = %s
            """, (order['id'],))
            items = cursor.fetchall()
            for item in items:
                if item.get('precio'):
                    item['precio'] = float(item['precio'])
            order['items'] = items
        cursor.close()
        conn.close()
        pages = (total + per_page - 1) // per_page
        return jsonify({'success': True, 'orders': orders, 'total': total, 'page': page, 'pages': pages})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v1/user/orders/<int:id>', methods=['GET'])
def get_user_order_detail(id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pedidos WHERE id = %s AND usuario_id = %s", (id, session['user_id']))
        order = cursor.fetchone()
        if not order:
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
        if order.get('fecha'):
            order['fecha_pedido'] = order['fecha'].isoformat()
        for field in ['total', 'subtotal', 'impuestos', 'descuento']:
            if order.get(field):
                order[field] = float(order[field])
        order['iva'] = order.get('impuestos', 0)
        cursor.execute("""
            SELECT pi.*, p.nombre, p.sku, p.imagen_principal as imagen
            FROM pedidos_items pi JOIN productos p ON pi.producto_id = p.id
            WHERE pi.pedido_id = %s
        """, (id,))
        items = cursor.fetchall()
        for item in items:
            if item.get('precio'):
                item['precio'] = float(item['precio'])
        order['items'] = items
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'order': order})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v1/user/orders/stats', methods=['GET'])
def get_orders_stats():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) as total,
                SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN estado = 'enviado' THEN 1 ELSE 0 END) as enviados,
                SUM(CASE WHEN estado = 'entregado' THEN 1 ELSE 0 END) as entregados
            FROM pedidos WHERE usuario_id = %s AND estado != 'carrito'
        """, (session['user_id'],))
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({
            'success': True,
            'total': stats['total'] or 0,
            'pendientes': stats['pendientes'] or 0,
            'enviados': stats['enviados'] or 0,
            'entregados': stats['entregados'] or 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500





# ========================================
# CHECKOUT - PROCESO DE COMPRA
# ========================================

@app.route('/api/v1/checkout', methods=['POST'])
def checkout():
    """Procesar pedido desde el carrito"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    try:
        data = request.get_json()
        direccion_id = data.get('direccion_envio_id')
        metodo_pago = data.get('metodo_pago', 'transferencia')
        notas = data.get('notas', '')
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener items del carrito
        cursor.execute("""
            SELECT c.*, p.nombre, p.precio_base, p.stock
            FROM carrito c
            JOIN productos p ON c.producto_id = p.id
            WHERE c.usuario_id = %s
        """, (session['user_id'],))
        
        cart_items = cursor.fetchall()
        
        if not cart_items:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'El carrito está vacío'}), 400
        
        # Verificar stock
        for item in cart_items:
            if item['stock'] is not None and item['cantidad'] > item['stock']:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False, 
                    'error': f"Stock insuficiente para {item['nombre']}"
                }), 400
        
        # Obtener dirección de envío
        direccion_texto = ''
        if direccion_id:
            cursor.execute("""
                SELECT * FROM direcciones_usuario 
                WHERE id = %s AND usuario_id = %s
            """, (direccion_id, session['user_id']))
            direccion = cursor.fetchone()
            if direccion:
                direccion_texto = f"{direccion['direccion']}, {direccion['cp']} {direccion['ciudad']}, {direccion['provincia']}"
                if direccion.get('telefono'):
                    direccion_texto += f" - Tel: {direccion['telefono']}"
        
        # Calcular totales
        subtotal = sum(float(item['precio_base']) * item['cantidad'] for item in cart_items)
        impuestos = subtotal * 0.21  # 21% IVA
        total = subtotal + impuestos
        
        # Generar número de pedido único
        numero_pedido = 'PED-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Crear pedido
        cursor.execute("""
            INSERT INTO pedidos (numero_pedido, usuario_id, estado, subtotal, impuestos, total, 
                                metodo_pago, direccion_envio, notas_cliente, fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (numero_pedido, session['user_id'], 'pendiente', subtotal, impuestos, total, 
              metodo_pago, direccion_texto, notas))
        
        pedido_id = cursor.lastrowid
        
        # Crear items del pedido
        for item in cart_items:
            precio = float(item['precio_base'])
            cursor.execute("""
                INSERT INTO pedidos_items (pedido_id, producto_id, cantidad, precio)
                VALUES (%s, %s, %s, %s)
            """, (pedido_id, item['producto_id'], item['cantidad'], precio))
            
            # Descontar stock
            if item['stock'] is not None:
                cursor.execute("""
                    UPDATE productos SET stock = stock - %s WHERE id = %s
                """, (item['cantidad'], item['producto_id']))
        
        # Vaciar carrito
        cursor.execute("DELETE FROM carrito WHERE usuario_id = %s", (session['user_id'],))

        # === INTEGRACIÓN HOLDED ===
        # Crear factura en Holded automáticamente
        if HOLDED_ENABLED:
            try:
                # Obtener datos del usuario para Holded
                cursor2 = conn.cursor(dictionary=True)
                cursor2.execute("""
                    SELECT u.*, d.direccion, d.ciudad, d.cp as codigo_postal, d.provincia, d.telefono as tel_envio
                    FROM usuarios u
                    LEFT JOIN direcciones_usuario d ON d.usuario_id = u.id AND d.id = %s
                    WHERE u.id = %s
                """, (direccion_id, session['user_id']))
                usuario_holded = cursor2.fetchone()
                cursor2.close()
                
                if usuario_holded:
                    # Preparar datos para Holded
                    pedido_holded = {
                        'id': pedido_id,
                        'numero_pedido': numero_pedido,
                        'total': total,
                        'notas': notas
                    }
                    
                    usuario_data = {
                        'nombre': usuario_holded.get('nombre', ''),
                        'apellidos': usuario_holded.get('apellidos', ''),
                        'email': usuario_holded.get('email', ''),
                        'telefono': usuario_holded.get('telefono', '') or usuario_holded.get('tel_envio', ''),
                        'nif': usuario_holded.get('nif', ''),
                        'direccion': usuario_holded.get('direccion', ''),
                        'ciudad': usuario_holded.get('ciudad', ''),
                        'codigo_postal': usuario_holded.get('codigo_postal', ''),
                        'provincia': usuario_holded.get('provincia', '')
                    }
                    
                    items_holded = []
                    for item in cart_items:
                        items_holded.append({
                            'nombre': item.get('nombre', 'Producto'),
                            'sku': item.get('sku', ''),
                            'cantidad': item.get('cantidad', 1),
                            'precio': float(item.get('precio_base', 0)),
                            'iva': 21
                        })
                    
                    # Llamar a Holded
                    resultado_holded = crear_factura_holded(pedido_holded, usuario_data, items_holded)
                    
                    if resultado_holded.get('success'):
                        # Guardar ID de factura Holded en el pedido
                        cursor3 = conn.cursor()
                        cursor3.execute("""
                            UPDATE pedidos SET holded_factura_id = %s WHERE id = %s
                        """, (resultado_holded.get('factura_id'), pedido_id))
                        conn.commit()
                        cursor3.close()
                        print(f"Factura Holded creada: {resultado_holded.get('factura_id')}")
                    else:
                        print(f"Error creando factura Holded: {resultado_holded.get('error')}")
                        
            except Exception as holded_error:
                print(f"Error en integración Holded: {holded_error}")
                # No fallamos el checkout si Holded falla
        # === FIN INTEGRACIÓN HOLDED ===
        
        conn.commit()

        # Obtener datos del usuario y enviar email de confirmación
        if EMAIL_ENABLED:
            try:
                conn2 = get_db()
                cur2 = conn2.cursor(dictionary=True)
                cur2.execute("SELECT nombre, email FROM usuarios WHERE id = %s", (session['user_id'],))
                usuario_email = cur2.fetchone()
                cur2.close()
                conn2.close()
                if usuario_email:
                    email_items = [
                        {'nombre': i.get('nombre', ''), 'cantidad': i.get('cantidad', 1),
                         'precio': float(i.get('precio_base', 0))}
                        for i in cart_items
                    ]
                    send_order_confirmation(
                        numero_pedido=numero_pedido,
                        nombre=usuario_email['nombre'],
                        email=usuario_email['email'],
                        items=email_items,
                        subtotal=subtotal,
                        iva=impuestos,
                        total=total,
                        metodo_pago=metodo_pago
                    )
            except Exception as email_err:
                print(f'[EMAIL] Error en confirmación de pedido: {email_err}')

        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Pedido creado correctamente',
            'pedido_id': pedido_id,
            'numero_pedido': numero_pedido,
            'total': total
        })
        
    except Exception as e:
        print(f"Error en checkout: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




# ========================================
# ADMIN - GESTIÓN DE PEDIDOS
# ========================================

def require_admin():
    """Verificar que el usuario es admin"""
    if 'user_id' not in session:
        return False
    if session.get('user_rol') != 'admin':
        return False
    return True

@app.route('/api/v1/admin/orders/stats', methods=['GET'])
def admin_orders_stats():
    """Estadísticas de pedidos para admin"""
    if not require_admin():
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as pendientes,
                SUM(CASE WHEN estado = 'confirmado' THEN 1 ELSE 0 END) as confirmados,
                SUM(CASE WHEN estado = 'en_preparacion' THEN 1 ELSE 0 END) as en_preparacion,
                SUM(CASE WHEN estado = 'enviado' THEN 1 ELSE 0 END) as enviados,
                SUM(CASE WHEN estado = 'entregado' THEN 1 ELSE 0 END) as entregados,
                SUM(CASE WHEN estado = 'cancelado' THEN 1 ELSE 0 END) as cancelados
            FROM pedidos WHERE estado != 'carrito'
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total': stats['total'] or 0,
            'pendientes': stats['pendientes'] or 0,
            'confirmados': stats['confirmados'] or 0,
            'en_preparacion': stats['en_preparacion'] or 0,
            'enviados': stats['enviados'] or 0,
            'entregados': stats['entregados'] or 0,
            'cancelados': stats['cancelados'] or 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/orders', methods=['GET'])
def admin_get_orders():
    """Listar todos los pedidos (admin)"""
    if not require_admin():
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        estado = request.args.get('estado', '')
        search = request.args.get('search', '')
        fecha_desde = request.args.get('fecha_desde', '')
        fecha_hasta = request.args.get('fecha_hasta', '')
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT p.*, u.nombre as cliente_nombre, u.apellidos as cliente_apellidos, u.email as cliente_email
            FROM pedidos p
            LEFT JOIN usuarios u ON p.usuario_id = u.id
            WHERE p.estado != 'carrito'
        """
        params = []
        
        if estado:
            query += " AND p.estado = %s"
            params.append(estado)
        
        if search:
            query += " AND (p.numero_pedido LIKE %s OR u.nombre LIKE %s OR u.email LIKE %s)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        if fecha_desde:
            query += " AND DATE(p.fecha) >= %s"
            params.append(fecha_desde)
        
        if fecha_hasta:
            query += " AND DATE(p.fecha) <= %s"
            params.append(fecha_hasta)
        
        # Contar total
        count_query = query.replace("SELECT p.*, u.nombre as cliente_nombre, u.apellidos as cliente_apellidos, u.email as cliente_email", "SELECT COUNT(*) as total")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Obtener pedidos
        query += " ORDER BY p.fecha DESC LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        orders = cursor.fetchall()
        
        for order in orders:
            if order.get('fecha'):
                order['fecha'] = order['fecha'].isoformat()
            for field in ['total', 'subtotal', 'impuestos', 'descuento']:
                if order.get(field):
                    order[field] = float(order[field])
        
        cursor.close()
        conn.close()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'success': True,
            'orders': orders,
            'total': total,
            'page': page,
            'pages': pages
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/orders/<int:id>', methods=['GET'])
def admin_get_order(id):
    """Obtener detalle de un pedido (admin)"""
    if not require_admin():
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.*, u.nombre as cliente_nombre, u.apellidos as cliente_apellidos, u.email as cliente_email
            FROM pedidos p
            LEFT JOIN usuarios u ON p.usuario_id = u.id
            WHERE p.id = %s
        """, (id,))
        
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Pedido no encontrado'}), 404
        
        if order.get('fecha'):
            order['fecha'] = order['fecha'].isoformat()
        for field in ['total', 'subtotal', 'impuestos', 'descuento']:
            if order.get(field):
                order[field] = float(order[field])
        
        # Obtener items
        cursor.execute("""
            SELECT pi.*, p.nombre, p.sku, p.imagen_principal as imagen
            FROM pedidos_items pi
            JOIN productos p ON pi.producto_id = p.id
            WHERE pi.pedido_id = %s
        """, (id,))
        
        items = cursor.fetchall()
        for item in items:
            if item.get('precio'):
                item['precio'] = float(item['precio'])
        
        order['items'] = items
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'order': order})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/orders/<int:id>', methods=['PUT'])
def admin_update_order(id):
    """Actualizar estado de un pedido (admin)"""
    if not require_admin():
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
    
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if 'estado' in data:
            updates.append("estado = %s")
            values.append(data['estado'])
            
            # Actualizar fechas según estado
            if data['estado'] == 'confirmado':
                updates.append("fecha_confirmacion = NOW()")
            elif data['estado'] == 'enviado':
                updates.append("fecha_envio = NOW()")
            elif data['estado'] == 'entregado':
                updates.append("fecha_entrega = NOW()")
        
        if 'numero_seguimiento' in data:
            updates.append("numero_seguimiento = %s")
            values.append(data['numero_seguimiento'])
        
        if 'notas_internas' in data:
            updates.append("notas_internas = %s")
            values.append(data['notas_internas'])
        
        updates.append("fecha_actualizacion = NOW()")
        
        if updates:
            values.append(id)
            query = f"UPDATE pedidos SET {', '.join(updates)} WHERE id = %s"
            cursor.execute(query, values)
            conn.commit()

        # Enviar email según cambio de estado
        nuevo_estado = data.get('estado', '')
        if EMAIL_ENABLED and nuevo_estado in ('enviado', 'entregado'):
            try:
                cur2 = conn.cursor(dictionary=True)
                cur2.execute("""
                    SELECT p.numero_pedido, u.nombre, u.email
                    FROM pedidos p
                    JOIN usuarios u ON p.usuario_id = u.id
                    WHERE p.id = %s
                """, (id,))
                pedido_info = cur2.fetchone()
                cur2.close()
                if pedido_info:
                    if nuevo_estado == 'enviado':
                        send_order_shipped(
                            numero_pedido=pedido_info['numero_pedido'],
                            nombre=pedido_info['nombre'],
                            email=pedido_info['email'],
                            tracking=data.get('numero_seguimiento', ''),
                            transportista=data.get('transportista', '')
                        )
                    elif nuevo_estado == 'entregado':
                        send_order_delivered(
                            numero_pedido=pedido_info['numero_pedido'],
                            nombre=pedido_info['nombre'],
                            email=pedido_info['email']
                        )
            except Exception as email_err:
                print(f'[EMAIL] Error en notificación de estado: {email_err}')

        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Pedido actualizado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/admin/events', methods=['GET'])
def admin_get_events():
    """Obtener historial de eventos de scripts"""
    if not require_admin():
        return jsonify({'success': False, 'error': 'No autorizado'}), 403
        
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        script_name = request.args.get('script_name', '')
        event_type = request.args.get('event_type', '')
        
        offset = (page - 1) * per_page
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Build query
        query = "SELECT * FROM script_events WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM script_events WHERE 1=1"
        params = []
        
        if script_name:
            query += " AND script_name LIKE %s"
            count_query += " AND script_name LIKE %s"
            params.append(f"%{script_name}%")
            
        if event_type:
            query += " AND event_type = %s"
            count_query += " AND event_type = %s"
            params.append(event_type)
            
        query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
        
        # Get total
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated data
        params.append(per_page)
        params.append(offset)
        cursor.execute(query, params)
        events = cursor.fetchall()
        
        # Format timestamps for JSON serialization
        for event in events:
            if event.get('timestamp'):
                event['timestamp'] = event['timestamp'].isoformat()
                
        cursor.close()
        conn.close()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'success': True, 
            'events': events,
            'total': total,
            'page': page,
            'pages': pages,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========================================
# VERIFICAR PEDIDOS
# ========================================
@app.route('/api/v1/orders/check', methods=['GET'])
def check_user_orders():
    """Verificar si el usuario tiene pedidos completados"""
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'has_orders': False
        }), 200
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Contar pedidos del usuario (excluyendo carritos)
        cursor.execute("""
            SELECT COUNT(*) as total FROM pedidos 
            WHERE usuario_id = %s AND estado != 'carrito'
        """, (session['user_id'],))
        
        result = cursor.fetchone()
        has_orders = result['total'] > 0 if result else False
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'has_orders': has_orders,
            'order_count': result['total'] if result else 0
        }), 200
        
    except Exception as e:
        # Si hay error (tabla no existe, etc), devolver false
        return jsonify({
            'success': True,
            'has_orders': False,
            'order_count': 0
        }), 200





# ========================================
# MIS PEDIDOS
# ========================================
@app.route('/api/v1/orders', methods=['GET'])
def get_my_orders():
    """Obtener pedidos del usuario logueado"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'orders': [], 'error': 'No autenticado'}), 200
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, fecha_pedido as fecha, estado, total
            FROM pedidos 
            WHERE usuario_id = %s AND estado != 'carrito'
            ORDER BY fecha_pedido DESC
            LIMIT 50
        """, (session['user_id'],))
        
        pedidos = cursor.fetchall()
        
        for pedido in pedidos:
            cursor.execute("""
                SELECT pd.producto_id, pd.cantidad, pd.precio_unitario as precio,
                       p.nombre, p.sku, p.imagen_principal as imagen
                FROM pedidos_detalle pd
                LEFT JOIN productos p ON pd.producto_id = p.id
                WHERE pd.pedido_id = %s
            """, (pedido['id'],))
            
            items = cursor.fetchall()
            for item in items:
                if item.get('precio'):
                    item['precio'] = float(item['precio'])
            pedido['items'] = items
            
            if pedido.get('total'):
                pedido['total'] = float(pedido['total'])
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'orders': pedidos}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'orders': [], 'error': str(e)}), 200


@app.route('/api/v1/user/orders/<int:id>/invoice', methods=['GET'])
def get_order_invoice(id):
    """Generar factura PDF para un pedido del usuario actual"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'No autenticado'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener pedido y verificar propiedad
        cursor.execute("""
            SELECT p.*, u.nombre as cliente_nombre, u.email as cliente_email, u.cif, u.empresa
            FROM pedidos p
            JOIN usuarios u ON p.usuario_id = u.id
            WHERE p.id = %s AND p.usuario_id = %s
        """, (id, session['user_id']))
        
        order = cursor.fetchone()
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Pedido no encontrado o no autorizado'}), 404
        
        # Formatear fecha para el PDF
        if order.get('fecha_pedido'):
            order['fecha'] = order['fecha_pedido'].strftime('%d/%m/%Y')
        else:
            order['fecha'] = datetime.now().strftime('%d/%m/%Y')
            
        # Obtener items
        cursor.execute("""
            SELECT pd.*, p.nombre
            FROM pedidos_detalle pd
            JOIN productos p ON pd.producto_id = p.id
            WHERE pd.pedido_id = %s
        """, (id,))
        
        items = cursor.fetchall()
        for item in items:
            item['precio_unitario'] = float(item.get('precio_unitario', 0))
            
        order['items'] = items
        order['total'] = float(order.get('total', 0))
        
        # Generar PDF
        pdf_content = generate_invoice_pdf(order)
        
        cursor.close()
        conn.close()
        
        return Response(
            pdf_content,
            mimetype="application/pdf",
            headers={"Content-disposition": f"attachment; filename=Factura_Plasise_{id}.pdf"}
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# ========================================
# ENDPOINTS DE NAVEGACIÓN POR CATEGORÍAS
# ========================================

@app.route('/api/v1/categories/<int:cat_id>/brands', methods=['GET'])
def get_brands_by_category(cat_id):
    """Obtener marcas que tienen productos en una categoría"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT m.id, m.nombre, COUNT(DISTINCT p.id) as productos
            FROM marcas m
            JOIN productos p ON p.marca_id = m.id
            WHERE p.categoria_id = %s AND p.activo = 1 AND m.activo = 1
            GROUP BY m.id, m.nombre
            HAVING productos > 0
            ORDER BY m.nombre
        """, (cat_id,))
        
        brands = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'brands': brands})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/categories/<int:cat_id>/brands/<int:brand_id>/subcategories', methods=['GET'])
def get_subcategories_by_category_brand(cat_id, brand_id):
    """Obtener subcategorías de una categoría que tienen productos de una marca"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener subcategorías (hijos) de la categoría principal que tengan productos de la marca
        cursor.execute("""
            SELECT c.id, c.nombre, COUNT(DISTINCT p.id) as productos
            FROM categorias c
            JOIN productos p ON p.categoria_id = c.id
            WHERE c.parent_id = %s AND p.marca_id = %s AND p.activo = 1 AND c.activo = 1
            GROUP BY c.id, c.nombre
            HAVING productos > 0
            ORDER BY c.orden, c.nombre
        """, (cat_id, brand_id))
        
        subcats = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'subcategories': subcats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
PYTHONEND

cat > start_backend.sh << 'BASHEND'
#!/bin/bash

# ============================================================================
# PLASISE - Script de Inicio del Backend
# Se ejecuta automáticamente cuando arranca el contenedor Docker
# ============================================================================

echo "=========================================="
echo "🚀 Iniciando Backend PLASISE"
echo "=========================================="

# Ir al directorio del backend
cd /code/backend

# Verificar que existe el archivo de requisitos
if [ -f /code/backend/requirements.txt ]; then
    echo "✓ Archivo requirements.txt encontrado"
    
    # Instalar dependencias si es necesario
    echo "📦 Verificando dependencias..."
    
    # Asegurar que pip y dependencias del sistema están instaladas (si usamos easypanel/base en lugar del Dockerfile)
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        echo "🔧 Instalando python3-pip y dependencias de MySQL..."
        apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip python3-dev default-libmysqlclient-dev pkg-config gcc || true
    fi
    
    python3 -m pip install --break-system-packages --ignore-installed --no-cache-dir -r /code/backend/requirements.txt 2>&1 | grep -v "already satisfied" || \
    python3 -m pip install --ignore-installed --no-cache-dir -r /code/backend/requirements.txt 2>&1 | grep -v "already satisfied" || true
    
    # Diagnóstico: Listar paquetes instalados
    echo "📋 Paquetes instalados:"
    python3 -m pip list | head -n 20
else
    echo "⚠️  No se encontró requirements.txt"
fi

# Verificar variables de entorno
echo ""
echo "🔧 Verificando configuración..."
if [ -f .env ]; then
    echo "✓ Archivo .env encontrado"
    source .env
else
    echo "⚠️  Advertencia: No se encontró archivo .env"
fi

# Verificar conexión a base de datos
echo ""
echo "🗄️  Verificando conexión a base de datos..."
python3 verify_db.py 2>&1 || echo "⚠️  Advertencia: Error al verificar BD"

# Crear directorio de logs si no existe
mkdir -p /code/backend/logs
echo "✓ Directorio de logs creado/verificado"

# Iniciar Flask
echo ""
echo "=========================================="
echo "🎯 Iniciando Flask Application..."
echo "=========================================="
echo "📍 Puerto: 5000"
echo "📍 Host: 0.0.0.0"
echo "🔍 Verificando procesos en puerto 5000..."
curl -s http://localhost:5000/health && echo "✅ Servicio ya respondiendo?!" || echo "✓ Puerto 5000 despejado"
echo "=========================================="
echo ""

# Ejecutar Flask
exec python3 /code/backend/api_productos.py
BASHEND

chmod +x start_backend.sh

echo "✅ Backend actualizado!"
echo "🔄 Ahora reinicia el contenedor desde EasyPanel"
