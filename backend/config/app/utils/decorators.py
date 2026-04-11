"""
============================================================================
PLASISE BACKEND - DECORATORS
Decoradores para proteger rutas y verificar permisos
============================================================================
"""

from functools import wraps
from flask import session, request, jsonify, g
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


def login_required(f):
    """
    Decorador para rutas que requieren autenticación
    
    Usage:
        @app.route('/protected')
        @login_required
        def protected():
            return {'message': 'Authenticated'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar sesión
        user_id = session.get('user_id')
        
        # Si no hay sesión, verificar token JWT
        if not user_id:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                user = User.verify_auth_token(token)
                if user:
                    g.current_user = user
                    return f(*args, **kwargs)
        else:
            # Cargar usuario de sesión
            user = User.find_by_id(user_id)
            if user and user.is_active():
                g.current_user = user
                return f(*args, **kwargs)
        
        return jsonify({
            'error': 'Autenticación requerida'
        }), 401
    
    return decorated_function


def admin_required(f):
    """
    Decorador para rutas que requieren ser administrador
    
    Usage:
        @app.route('/admin')
        @admin_required
        def admin_panel():
            return {'message': 'Admin only'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Primero verificar autenticación
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'error': 'Autenticación requerida'
            }), 401
        
        user = User.find_by_id(user_id)
        
        if not user or not user.is_active():
            return jsonify({
                'error': 'Usuario no autorizado'
            }), 403
        
        if not user.is_admin():
            logger.warning(f"Acceso denegado a ruta admin para: {user.email}")
            return jsonify({
                'error': 'Acceso denegado. Se requieren permisos de administrador'
            }), 403
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def permission_required(permission):
    """
    Decorador para verificar permisos específicos
    
    Args:
        permission: String con el nombre del permiso
    
    Usage:
        @app.route('/manage-products')
        @permission_required('manage_products')
        def manage_products():
            return {'message': 'Can manage products'}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            
            if not user_id:
                return jsonify({
                    'error': 'Autenticación requerida'
                }), 401
            
            user = User.find_by_id(user_id)
            
            if not user or not user.is_active():
                return jsonify({
                    'error': 'Usuario no autorizado'
                }), 403
            
            if not user.has_permission(permission):
                logger.warning(f"Permiso denegado '{permission}' para: {user.email}")
                return jsonify({
                    'error': f'No tienes permiso para: {permission}'
                }), 403
            
            g.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def verified_email_required(f):
    """
    Decorador para rutas que requieren email verificado
    
    Usage:
        @app.route('/place-order')
        @login_required
        @verified_email_required
        def place_order():
            return {'message': 'Email verified'}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            return jsonify({
                'error': 'Autenticación requerida'
            }), 401
        
        user = g.current_user
        
        if not user.is_verified():
            return jsonify({
                'error': 'Debes verificar tu email antes de continuar',
                'verification_required': True
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def rate_limit(max_calls=100, period=3600):
    """
    Decorador para rate limiting simple
    
    Args:
        max_calls: Número máximo de llamadas
        period: Período en segundos
    
    Usage:
        @app.route('/api/expensive')
        @rate_limit(max_calls=10, period=60)
        def expensive_endpoint():
            return {'data': 'expensive computation'}
    
    Note: Para producción usar Flask-Limiter
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implementar rate limiting real con Redis
            # Por ahora solo pasamos
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_json(required_fields=None):
    """
    Decorador para validar que el request contenga JSON
    y tenga los campos requeridos
    
    Args:
        required_fields: Lista de campos requeridos
    
    Usage:
        @app.route('/create-product', methods=['POST'])
        @validate_json(['name', 'price'])
        def create_product():
            data = request.get_json()
            return {'product': data}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Content-Type debe ser application/json'
                }), 400
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'error': 'Body no puede estar vacío'
                }), 400
            
            if required_fields:
                missing_fields = [
                    field for field in required_fields 
                    if field not in data or data[field] is None
                ]
                
                if missing_fields:
                    return jsonify({
                        'error': f'Campos requeridos faltantes: {", ".join(missing_fields)}'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def cache_result(timeout=300):
    """
    Decorador para cachear resultados de una función
    
    Args:
        timeout: Tiempo de cache en segundos
    
    Usage:
        @app.route('/expensive-query')
        @cache_result(timeout=600)
        def expensive_query():
            return {'data': 'expensive data'}
    
    Note: Requiere Flask-Caching configurado
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implementar cache real con Redis/Flask-Caching
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
