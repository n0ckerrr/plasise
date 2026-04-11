from flask import Blueprint, jsonify, g
from app.utils.decorators import login_required
from app.utils.database import db

users_bp = Blueprint('users', __name__)

@users_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    return jsonify(g.current_user.to_dict()), 200
