"""
============================================================================
PLASISE BACKEND - AUTH MIDDLEWARE
Middleware para autenticación automática en cada request
============================================================================
"""

from flask import session, request, g
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


def auth_middleware():
    """
    Middleware que se ejecuta antes de cada request
    para cargar el usuario autenticado en g.current_user
    """
    g.current_user = None
    
    # Rutas públicas que no requieren autenticación
    public_routes = [
        '/health',
        '/',
        '/api/v1/auth/login',
        '/api/v1/auth/register',
        '/api/v1/auth/forgot-password',
        '/api/v1/auth/reset-password',
        '/api/v1/auth/verify-email',
        '/api/v1/products',
        '/api/v1/categories',
        '/api/v1/brands',
        '/api/v1/blog'
    ]
    
    # Si la ruta es pública, no hacer nada
    if any(request.path.startswith(route) for route in public_routes):
        return
    
    # Intentar cargar usuario de sesión
    user_id = session.get('user_id')
    
    if user_id:
        user = User.find_by_id(user_id)
        if user and user.is_active():
            g.current_user = user
            return
    
    # Si no hay sesión, intentar con token JWT
    auth_header = request.headers.get('Authorization')
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user = User.verify_auth_token(token)
        
        if user and user.is_active():
            g.current_user = user
