from flask import Blueprint, jsonify
from app.utils.database import db

resources_bp = Blueprint('resources', __name__)

@resources_bp.route('/', methods=['GET'])
def get_resources():
    resources = db.execute_query("SELECT * FROM recursos WHERE activo = 1 ORDER BY fecha_creacion DESC")
    return jsonify({'resources': resources}), 200
