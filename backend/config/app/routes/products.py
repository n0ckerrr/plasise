"""
============================================================================
PLASISE BACKEND - PRODUCTS ROUTES
Endpoints para gestión de productos
============================================================================
"""

from flask import Blueprint, request, jsonify, g
from app.utils.decorators import login_required, admin_required
from app.utils.database import db
import logging

logger = logging.getLogger(__name__)

products_bp = Blueprint('products', __name__)


@products_bp.route('/', methods=['GET'])
def get_products():
    """Listar productos con filtros"""
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = "SELECT * FROM v_productos_completos WHERE 1=1"
        params = []
        
        # Filtros
        if request.args.get('category_id'):
            query += " AND categoria_id = %s"
            params.append(request.args.get('category_id'))
        
        if request.args.get('brand_id'):
            query += " AND marca_id = %s"
            params.append(request.args.get('brand_id'))
        
        if request.args.get('search'):
            query += " AND (nombre LIKE %s OR sku LIKE %s)"
            term = f"%{request.args.get('search')}%"
            params.extend([term, term])
        
        # Count total
        count = db.get_one(f"SELECT COUNT(*) as t FROM ({query}) x", params)['t']
        
        # Paginar
        query += f" LIMIT {per_page} OFFSET {(page-1)*per_page}"
        products = db.execute_query(query, params)
        
        return jsonify({
            'products': products,
            'total': count,
            'pages': (count + per_page - 1) // per_page,
            'current_page': page
        }), 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Detalle de producto"""
    try:
        product = db.get_one("SELECT * FROM v_productos_completos WHERE id = %s", (product_id,))
        if not product:
            return jsonify({'error': 'No encontrado'}), 404
        return jsonify(product), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
