from flask import Blueprint, jsonify
from app.utils.database import db

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/', methods=['GET'])
def get_categories():
    categories = db.execute_query("SELECT * FROM categorias WHERE activo = 1 ORDER BY orden")
    return jsonify({'categories': categories}), 200
