"""
============================================================================
PLASISE BACKEND - API COMPLETA v2.1
API REST con autenticación, productos, marcas, categorías y carrito
INCLUYE: Filtro de categorías con subcategorías recursivas
============================================================================
"""

from flask import Flask, jsonify, request, session
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'aegis_super_secret_key_vps_stable')

# Configurar CORS para permitir credenciales
CORS(app, supports_credentials=True, origins=['*'])

# Configuración de sesión
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # True en producción con HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True

def get_db():
    """Conexión a la base de datos MySQL"""
    try:
        return mysql.connector.connect(
            host=os.getenv('DB_HOST', '72.61.111.50'),
            port=int(os.getenv('DB_PORT', 3306)),
            user=os.getenv('DB_USER', 'plasise'),
            password=os.getenv('DB_PASSWORD', 'plasise.'),
            database=os.getenv('DB_NAME', 'plasise')
        )
    except mysql.connector.Error as e:
        print(f"Error de conexión a la base de datos: {e}")
        raise

# ========================================
# HEALTH CHECK
# ========================================
@app.route('/health', methods=['GET'])
def health_check():
    """Verificar que la API y la BD están funcionando"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify({
            'status': 'healthy',
            'service': 'PLASISE Backend API',
            'database': 'connected',
            'version': '2.1.0'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# ========================================
# AUTENTICACIÓN
# ========================================

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """Registro de nuevo usuario"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['nombre', 'apellidos', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'El campo {field} es requerido'
                }), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (data['email'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'El email ya está registrado'
            }), 400
        
        # Crear usuario
        password_hash = generate_password_hash(data['password'])
        
        query = """
            INSERT INTO usuarios (nombre, apellidos, email, telefono, password_hash, rol, activo, fecha_registro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['nombre'],
            data['apellidos'],
            data['email'],
            data.get('telefono', ''),
            password_hash,
            'cliente',  # rol por defecto
            1,  # activo
            datetime.now()
        )
        
        cursor.execute(query, values)
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Usuario registrado exitosamente',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        print(f"Error en registro: {e}")
        return jsonify({
            'success': False,
            'error': f'Error al registrar usuario: {str(e)}'
        }), 500


@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """Inicio de sesión"""
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'Email y contraseña son requeridos'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar usuario
        cursor.execute("""
            SELECT id, nombre, apellidos, email, password_hash, rol, activo 
            FROM usuarios 
            WHERE email = %s
        """, (data['email'],))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'Email o contraseña incorrectos'
            }), 401
        
        if not user['activo']:
            return jsonify({
                'success': False,
                'error': 'Usuario desactivado'
            }), 401
        
        # Verificar contraseña
        if not check_password_hash(user['password_hash'], data['password']):
            return jsonify({
                'success': False,
                'error': 'Email o contraseña incorrectos'
            }), 401
        
        # Crear sesión
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_nombre'] = user['nombre']
        session['user_rol'] = user['rol']
        
        return jsonify({
            'success': True,
            'message': 'Inicio de sesión exitoso',
            'user': {
                'id': user['id'],
                'nombre': user['nombre'],
                'apellidos': user['apellidos'],
                'email': user['email'],
                'rol': user['rol']
            }
        }), 200
        
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({
            'success': False,
            'error': f'Error al iniciar sesión: {str(e)}'
        }), 500


@app.route('/api/v1/auth/logout', methods=['POST'])
def logout():
    """Cerrar sesión"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Sesión cerrada exitosamente'
    }), 200


@app.route('/api/v1/auth/session', methods=['GET'])
def check_session():
    """Verificar sesión actual"""
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
    else:
        return jsonify({
            'authenticated': False
        }), 200


# ========================================
# PRODUCTOS - CON FILTRO DE SUBCATEGORÍAS
# ========================================
@app.route('/api/v1/products', methods=['GET'])
def get_productos():
    """Obtener lista de productos con filtros - INCLUYE SUBCATEGORÍAS"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Parámetros de búsqueda y filtrado
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
        
        # Construir query base
        query = "SELECT * FROM productos WHERE activo = 1"
        params = []
        
        # Aplicar filtros
        if search:
            query += " AND (nombre LIKE %s OR descripcion_corta LIKE %s OR descripcion_larga LIKE %s OR sku LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param, search_param])
        
        # ============================================
        # FILTRO DE CATEGORÍA CON SUBCATEGORÍAS
        # ============================================
        if categoria:
            try:
                cat_id = int(categoria)
                # Obtener la categoría y todas sus subcategorías recursivamente
                cursor.execute('''
                    WITH RECURSIVE cat_tree AS (
                        SELECT id FROM categorias WHERE id = %s
                        UNION ALL
                        SELECT c.id FROM categorias c
                        INNER JOIN cat_tree ct ON c.parent_id = ct.id
                    )
                    SELECT id FROM cat_tree
                ''', (cat_id,))
                cat_ids = [row['id'] for row in cursor.fetchall()]
                
                if cat_ids:
                    placeholders = ','.join(['%s'] * len(cat_ids))
                    query += f" AND categoria_id IN ({placeholders})"
                    params.extend(cat_ids)
                    print(f"[DEBUG] Buscando en categorías: {cat_ids}")
                else:
                    query += " AND categoria_id = %s"
                    params.append(cat_id)
            except (ValueError, TypeError) as e:
                print(f"[WARN] categoria inválida: {categoria} - {e}")
                pass
        
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
        
        # Ordenar
        if sort == 'price_asc':
            query += " ORDER BY precio_base ASC"
        elif sort == 'price_desc':
            query += " ORDER BY precio_base DESC"
        else:
            query += " ORDER BY nombre ASC"
        
        # Contar total de productos
        count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Aplicar paginación
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        # Ejecutar query
        cursor.execute(query, params)
        productos = cursor.fetchall()
        
        # Convertir decimales a float para JSON
        for p in productos:
            if p.get('precio_base'):
                p['precio_base'] = float(p['precio_base'])
            if p.get('precio_pvp_recomendado'):
                p['precio_pvp_recomendado'] = float(p['precio_pvp_recomendado'])
            if p.get('coste'):
                p['coste'] = float(p['coste'])
            if p.get('peso'):
                p['peso'] = float(p['peso'])
        
        cursor.close()
        conn.close()
        
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'success': True,
            'products': productos,
            'total': total,
            'page': page,
            'current_page': page,
            'per_page': per_page,
            'pages': pages
        }), 200
        
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/products/<int:id>', methods=['GET'])
def get_producto(id):
    """Obtener un producto específico"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM productos WHERE id = %s AND activo = 1", (id,))
        producto = cursor.fetchone()
        
        if not producto:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Producto no encontrado'
            }), 404
        
        # Convertir decimales
        if producto.get('precio_base'):
            producto['precio_base'] = float(producto['precio_base'])
        if producto.get('precio_pvp_recomendado'):
            producto['precio_pvp_recomendado'] = float(producto['precio_pvp_recomendado'])
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'product': producto
        }), 200
        
    except Exception as e:
        print(f"Error al obtener producto: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================================
# MARCAS
# ========================================
@app.route('/api/v1/brands', methods=['GET'])
def get_marcas():
    """Obtener lista de marcas"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM marcas WHERE activo = 1 ORDER BY nombre")
        marcas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'brands': marcas
        }), 200
        
    except Exception as e:
        print(f"Error al obtener marcas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================================
# CATEGORÍAS - CON ESTRUCTURA JERÁRQUICA
# ========================================
@app.route('/api/v1/categories', methods=['GET'])
def get_categorias():
    """Obtener lista de categorías con estructura jerárquica"""
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM categorias WHERE activo = 1 ORDER BY orden, nombre")
        all_cats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Convertir fechas a string para JSON
        for cat in all_cats:
            if cat.get('fecha_creacion'):
                cat['fecha_creacion'] = str(cat['fecha_creacion'])
            if cat.get('fecha_actualizacion'):
                cat['fecha_actualizacion'] = str(cat['fecha_actualizacion'])
        
        # Construir árbol jerárquico
        def build_tree(parent_id=None):
            children = []
            for cat in all_cats:
                if cat.get('parent_id') == parent_id:
                    cat_copy = cat.copy()
                    cat_copy['children'] = build_tree(cat['id'])
                    children.append(cat_copy)
            return children
        
        tree = build_tree()
        
        return jsonify({
            'success': True,
            'categories': tree
        }), 200
        
    except Exception as e:
        print(f"Error al obtener categorías: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================================
# CARRITO
# ========================================
@app.route('/api/v1/cart', methods=['GET'])
def get_cart():
    """Obtener contenido del carrito"""
    try:
        if 'user_id' not in session:
            # Carrito vacío para usuarios no autenticados
            return jsonify({
                'success': True,
                'items': [],
                'items_count': 0,
                'total': 0
            }), 200
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener items del carrito con información del producto
        query = """
            SELECT c.*, p.nombre, p.sku, p.precio_base, p.imagen_principal
            FROM carrito c
            JOIN productos p ON c.producto_id = p.id
            WHERE c.usuario_id = %s
        """
        cursor.execute(query, (session['user_id'],))
        items = cursor.fetchall()
        
        # Calcular total y convertir decimales
        total = 0
        for item in items:
            item['precio_base'] = float(item['precio_base'])
            item['subtotal'] = item['precio_base'] * item['cantidad']
            total += item['subtotal']
            
            # Crear objeto producto anidado
            item['product'] = {
                'id': item['producto_id'],
                'nombre': item['nombre'],
                'sku': item['sku'],
                'precio_base': item['precio_base'],
                'imagen_principal': item['imagen_principal']
            }
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'items': items,
            'items_count': len(items),
            'total': total
        }), 200
        
    except Exception as e:
        print(f"Error al obtener carrito: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/cart/add', methods=['POST'])
def add_to_cart():
    """Añadir producto al carrito"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Debe iniciar sesión para agregar productos al carrito'
            }), 401
        
        data = request.get_json()
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad', 1)
        
        if not producto_id:
            return jsonify({
                'success': False,
                'error': 'producto_id es requerido'
            }), 400
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el producto existe
        cursor.execute("SELECT id, stock FROM productos WHERE id = %s AND activo = 1", (producto_id,))
        producto = cursor.fetchone()
        
        if not producto:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Producto no encontrado'
            }), 404
        
        # Verificar si ya está en el carrito
        cursor.execute("""
            SELECT id, cantidad FROM carrito 
            WHERE usuario_id = %s AND producto_id = %s
        """, (session['user_id'], producto_id))
        
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Actualizar cantidad
            nueva_cantidad = existing_item['cantidad'] + cantidad
            cursor.execute("""
                UPDATE carrito SET cantidad = %s 
                WHERE id = %s
            """, (nueva_cantidad, existing_item['id']))
        else:
            # Insertar nuevo item
            cursor.execute("""
                INSERT INTO carrito (usuario_id, producto_id, cantidad, fecha_agregado)
                VALUES (%s, %s, %s, %s)
            """, (session['user_id'], producto_id, cantidad, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Producto añadido al carrito'
        }), 200
        
    except Exception as e:
        print(f"Error al añadir al carrito: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/v1/cart/remove/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    """Eliminar producto del carrito"""
    try:
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Debe iniciar sesión'
            }), 401
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM carrito 
            WHERE id = %s AND usuario_id = %s
        """, (item_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Producto eliminado del carrito'
        }), 200
        
    except Exception as e:
        print(f"Error al eliminar del carrito: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================================
# EJECUTAR APLICACIÓN
# ========================================
if __name__ == '__main__':
    print("=" * 60)
    print("PLASISE Backend API v2.1.0")
    print("INCLUYE: Filtro de categorías con subcategorías")
    print("=" * 60)
    print(f"Base de datos: {os.getenv('DB_HOST', '72.61.111.50')}:{os.getenv('DB_PORT', 3306)}")
    print(f"Database: {os.getenv('DB_NAME', 'plasise')}")
    print("Endpoints disponibles:")
    print("  - GET  /health")
    print("  - POST /api/v1/auth/register")
    print("  - POST /api/v1/auth/login")
    print("  - POST /api/v1/auth/logout")
    print("  - GET  /api/v1/auth/session")
    print("  - GET  /api/v1/products")
    print("  - GET  /api/v1/products/<id>")
    print("  - GET  /api/v1/brands")
    print("  - GET  /api/v1/categories (con árbol jerárquico)")
    print("  - GET  /api/v1/cart")
    print("  - POST /api/v1/cart/add")
    print("  - DELETE /api/v1/cart/remove/<id>")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)