from flask import Blueprint, jsonify
from app.utils.database import db

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/', methods=['GET'])
def get_posts():
    posts = db.execute_query("SELECT * FROM blog_posts WHERE estado = 'publicado' ORDER BY fecha_publicacion DESC LIMIT 10")
    return jsonify({'posts': posts}), 200
