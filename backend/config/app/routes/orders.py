from flask import Blueprint, jsonify, g
from app.utils.decorators import login_required
from app.utils.database import db

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/', methods=['GET'])
@login_required
def get_orders():
    orders = db.execute_query("SELECT * FROM pedidos WHERE usuario_id = %s AND estado != 'carrito' ORDER BY fecha DESC", (g.current_user.id,))
    return jsonify({'orders': orders}), 200
