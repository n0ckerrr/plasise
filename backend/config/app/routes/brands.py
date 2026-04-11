from flask import Blueprint, jsonify
from app.utils.database import db

brands_bp = Blueprint('brands', __name__)

@brands_bp.route('/', methods=['GET'])
def get_brands():
    brands = db.execute_query("SELECT * FROM marcas WHERE activo = 1 ORDER BY nombre")
    return jsonify({'brands': brands}), 200
