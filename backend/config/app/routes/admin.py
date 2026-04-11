from flask import Blueprint, jsonify
from app.utils.decorators import admin_required
from app.utils.database import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    stats = {
        'productos': db.get_one("SELECT COUNT(*) as c FROM productos")['c'],
        'usuarios': db.get_one("SELECT COUNT(*) as c FROM usuarios")['c'],
        'pedidos': db.get_one("SELECT COUNT(*) as c FROM pedidos WHERE estado != 'carrito'")['c']
    }
    return jsonify(stats), 200
