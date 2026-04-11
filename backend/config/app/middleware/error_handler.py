"""
============================================================================
PLASISE BACKEND - ERROR HANDLER
Manejador centralizado de errores HTTP y excepciones
============================================================================
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """
    Registrar manejadores de errores en la aplicación
    
    Args:
        app: Instancia de Flask
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Manejar errores 400 Bad Request"""
        return jsonify({
            'error': 'Solicitud inválida',
            'message': str(error.description) if hasattr(error, 'description') else str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Manejar errores 401 Unauthorized"""
        return jsonify({
            'error': 'No autorizado',
            'message': 'Debes iniciar sesión para acceder a este recurso'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Manejar errores 403 Forbidden"""
        return jsonify({
            'error': 'Acceso denegado',
            'message': 'No tienes permisos para acceder a este recurso'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Manejar errores 404 Not Found"""
        return jsonify({
            'error': 'No encontrado',
            'message': 'El recurso solicitado no existe'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Manejar errores 405 Method Not Allowed"""
        return jsonify({
            'error': 'Método no permitido',
            'message': f'El método {error.description} no está permitido para esta ruta'
        }), 405
    
    @app.errorhandler(409)
    def conflict(error):
        """Manejar errores 409 Conflict"""
        return jsonify({
            'error': 'Conflicto',
            'message': str(error.description) if hasattr(error, 'description') else 'El recurso ya existe'
        }), 409
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Manejar errores 422 Unprocessable Entity"""
        return jsonify({
            'error': 'Datos no procesables',
            'message': str(error.description) if hasattr(error, 'description') else 'Los datos proporcionados no son válidos'
        }), 422
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """Manejar errores 429 Too Many Requests"""
        return jsonify({
            'error': 'Demasiadas solicitudes',
            'message': 'Has excedido el límite de solicitudes. Intenta más tarde.'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Manejar errores 500 Internal Server Error"""
        logger.error(f"Error 500: {str(error)}", exc_info=True)
        return jsonify({
            'error': 'Error interno del servidor',
            'message': 'Ha ocurrido un error. Por favor, contacta con soporte.'
        }), 500
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """Manejar errores 503 Service Unavailable"""
        return jsonify({
            'error': 'Servicio no disponible',
            'message': 'El servicio está temporalmente fuera de línea. Intenta más tarde.'
        }), 503
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Manejar excepciones HTTP genéricas"""
        return jsonify({
            'error': error.name,
            'message': error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Manejar excepciones no controladas"""
        logger.error(f"Excepción no controlada: {str(error)}", exc_info=True)
        
        # En desarrollo, mostrar el error completo
        if app.debug:
            return jsonify({
                'error': 'Error no controlado',
                'message': str(error),
                'type': type(error).__name__
            }), 500
        
        # En producción, ocultar detalles
        return jsonify({
            'error': 'Error interno del servidor',
            'message': 'Ha ocurrido un error inesperado. Por favor, contacta con soporte.'
        }), 500


class APIException(Exception):
    """
    Excepción personalizada para la API
    
    Usage:
        raise APIException('Usuario no encontrado', status_code=404)
    """
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


class ValidationError(APIException):
    """Error de validación"""
    def __init__(self, message, payload=None):
        super().__init__(message, status_code=422, payload=payload)


class NotFoundError(APIException):
    """Recurso no encontrado"""
    def __init__(self, message="Recurso no encontrado", payload=None):
        super().__init__(message, status_code=404, payload=payload)


class UnauthorizedError(APIException):
    """No autorizado"""
    def __init__(self, message="No autorizado", payload=None):
        super().__init__(message, status_code=401, payload=payload)


class ForbiddenError(APIException):
    """Acceso denegado"""
    def __init__(self, message="Acceso denegado", payload=None):
        super().__init__(message, status_code=403, payload=payload)
