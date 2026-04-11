"""PLASISE - Cart Routes"""
from flask import Blueprint, request, jsonify, g
from app.utils.decorators import login_required
from app.utils.database import db

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/', methods=['GET'])
@login_required
def get_cart():
    """Obtener carrito"""
    user_id = g.current_user.id
    cart = db.get_one("SELECT * FROM pedidos WHERE usuario_id = %s AND estado = 'carrito'", (user_id,))
    
    if not cart:
        return jsonify({'items': [], 'items_count': 0, 'total': 0}), 200
    
    items = db.execute_query("""
        SELECT pd.*, p.nombre, p.imagen_principal
        FROM pedidos_detalle pd
        JOIN productos p ON pd.producto_id = p.id
        WHERE pd.pedido_id = %s
    """, (cart['id'],))
    
    return jsonify({
        'items': items,
        'items_count': len(items),
        'total': float(cart['total'] or 0)
    }), 200

@cart_bp.route('/add', methods=['POST'])
@login_required
def add_to_cart():
    """Añadir al carrito"""
    data = request.get_json()
    user_id = g.current_user.id
    
    # Obtener o crear carrito
    cart = db.get_one("SELECT * FROM pedidos WHERE usuario_id = %s AND estado = 'carrito'", (user_id,))
    if not cart:
        cart_id = db.insert('pedidos', {'usuario_id': user_id, 'estado': 'carrito'})
    else:
        cart_id = cart['id']
    
    # Añadir item
    producto = db.get_one("SELECT * FROM productos WHERE id = %s", (data['producto_id'],))
    db.insert('pedidos_detalle', {
        'pedido_id': cart_id,
        'producto_id': data['producto_id'],
        'sku': producto['sku'],
        'nombre_producto': producto['nombre'],
        'cantidad': data.get('cantidad', 1),
        'precio_unitario': producto['precio_base'],
        'subtotal': producto['precio_base'] * data.get('cantidad', 1),
        'total': producto['precio_base'] * data.get('cantidad', 1)
    })
    
    return jsonify({'message': 'Añadido'}), 200
