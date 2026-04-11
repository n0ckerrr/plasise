"""
============================================================================
PLASISE BACKEND - AUTH ROUTES
Rutas para autenticación: login, registro, logout, recuperación de contraseña
============================================================================
"""

from flask import Blueprint, request, jsonify, session
from app.models.user import User
from app.utils.validators import validate_email, validate_password
from app.utils.decorators import login_required
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registrar nuevo usuario
    
    Body:
        {
            "email": "user@example.com",
            "password": "password123",
            "nombre": "Juan",
            "apellidos": "García",
            "telefono": "+34123456789",
            "empresa": {
                "razon_social": "Mi Empresa SL",
                "cif": "B12345678",
                ...
            }
        }
    
    Returns:
        201: Usuario creado
        400: Error de validación
        409: Email ya existe
    """
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'error': 'Email y contraseña son requeridos'
            }), 400
        
        # Validar email
        if not validate_email(data['email']):
            return jsonify({
                'error': 'Email no válido'
            }), 400
        
        # Validar contraseña
        password_valid, password_error = validate_password(data['password'])
        if not password_valid:
            return jsonify({
                'error': password_error
            }), 400
        
        # Verificar que el email no exista
        existing_user = User.find_by_email(data['email'])
        if existing_user:
            return jsonify({
                'error': 'El email ya está registrado'
            }), 409
        
        # Crear usuario
        user_data = {
            'email': data['email'].lower().strip(),
            'password': data['password'],
            'nombre': data.get('nombre', ''),
            'apellidos': data.get('apellidos', ''),
            'telefono': data.get('telefono'),
            'cargo': data.get('cargo')
        }
        
        # Si viene información de empresa, registrarla
        if data.get('empresa'):
            from app.models.empresa import Empresa
            empresa_id = Empresa.create(data['empresa'])
            user_data['empresa_id'] = empresa_id
            user_data['tipo_usuario'] = 'cliente'
            user_data['rol'] = 'cliente_profesional'
        
        # Crear usuario
        user_id = User.create(user_data)
        
        # Obtener usuario creado
        user = User.find_by_id(user_id)
        
        # TODO: Enviar email de verificación
        
        logger.info(f"Usuario registrado: {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Usuario registrado correctamente',
            'user': user.to_dict(),
            'verification_required': not user.email_verificado
        }), 201
        
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return jsonify({
            'error': 'Error al registrar usuario'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login de usuario
    
    Body:
        {
            "email": "user@example.com",
            "password": "password123",
            "remember_me": true
        }
    
    Returns:
        200: Login exitoso
        401: Credenciales inválidas
        403: Usuario inactivo
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'error': 'Email y contraseña son requeridos'
            }), 400
        
        # Buscar usuario
        user = User.find_by_email(data['email'].lower().strip())
        
        if not user:
            logger.warning(f"Intento de login con email inexistente: {data['email']}")
            return jsonify({
                'error': 'Credenciales inválidas'
            }), 401
        
        # Verificar contraseña
        if not user.verify_password(data['password']):
            logger.warning(f"Intento de login fallido para: {user.email}")
            
            # TODO: Incrementar contador de intentos fallidos
            # TODO: Bloquear usuario después de N intentos
            
            return jsonify({
                'error': 'Credenciales inválidas'
            }), 401
        
        # Verificar que el usuario esté activo
        if not user.is_active():
            return jsonify({
                'error': 'Usuario inactivo. Contacte con soporte.'
            }), 403
        
        # Actualizar último acceso
        user.update_last_access()
        
        # Crear sesión
        session.permanent = data.get('remember_me', False)
        session['user_id'] = user.id
        session['email'] = user.email
        session['tipo_usuario'] = user.tipo_usuario
        session['rol'] = user.rol
        
        # Generar token JWT
        token = user.generate_auth_token(expires_in=3600)
        
        logger.info(f"Login exitoso: {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Login exitoso',
            'user': user.to_dict(),
            'token': token,
            'session_id': session.get('session_id')
        }), 200
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        return jsonify({
            'error': 'Error al iniciar sesión'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Cerrar sesión
    
    Returns:
        200: Sesión cerrada
    """
    try:
        user_email = session.get('email')
        
        # Limpiar sesión
        session.clear()
        
        logger.info(f"Logout: {user_email}")
        
        return jsonify({
            'message': 'Sesión cerrada correctamente'
        }), 200
        
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        return jsonify({
            'error': 'Error al cerrar sesión'
        }), 500


@auth_bp.route('/session', methods=['GET'])
def get_session():
    """
    Obtener información de sesión actual
    
    Returns:
        200: Información de sesión
        401: No hay sesión activa
    """
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'authenticated': False,
                'user': None
            }), 200
        
        # Obtener usuario
        user = User.find_by_id(user_id)
        
        if not user:
            session.clear()
            return jsonify({
                'authenticated': False,
                'user': None
            }), 200
        
        return jsonify({
            'authenticated': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo sesión: {str(e)}")
        return jsonify({
            'error': 'Error al obtener sesión'
        }), 500


@auth_bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    """
    Verificar email con token
    
    Args:
        token: Token de verificación
    
    Returns:
        200: Email verificado
        400: Token inválido o expirado
    """
    try:
        from app.utils.database import db
        
        # Buscar usuario con el token
        query = "SELECT * FROM usuarios WHERE token_verificacion = %s AND activo = 1"
        user_data = db.get_one(query, (token,))
        
        if not user_data:
            return jsonify({
                'error': 'Token inválido o expirado'
            }), 400
        
        # Marcar email como verificado
        db.update(
            'usuarios',
            {
                'email_verificado': 1,
                'token_verificacion': None
            },
            'id = %s',
            [user_data['id']]
        )
        
        logger.info(f"Email verificado: {user_data['email']}")
        
        return jsonify({
            'message': 'Email verificado correctamente'
        }), 200
        
    except Exception as e:
        logger.error(f"Error verificando email: {str(e)}")
        return jsonify({
            'error': 'Error al verificar email'
        }), 500


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Solicitar recuperación de contraseña
    
    Body:
        {
            "email": "user@example.com"
        }
    
    Returns:
        200: Email enviado (siempre, aunque no exista)
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('email'):
            return jsonify({
                'error': 'Email es requerido'
            }), 400
        
        user = User.find_by_email(data['email'].lower().strip())
        
        if user and user.is_active():
            import secrets
            from datetime import datetime, timedelta
            from app.utils.database import db
            
            # Generar token de recuperación
            reset_token = secrets.token_urlsafe(32)
            expira = datetime.now() + timedelta(hours=24)
            
            # Guardar token
            db.update(
                'usuarios',
                {
                    'token_reset_password': reset_token,
                    'token_reset_expira': expira
                },
                'id = %s',
                [user.id]
            )
            
            # TODO: Enviar email con link de recuperación
            logger.info(f"Token de recuperación generado para: {user.email}")
        
        # Siempre responder lo mismo para no revelar si el email existe
        return jsonify({
            'message': 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'
        }), 200
        
    except Exception as e:
        logger.error(f"Error en forgot password: {str(e)}")
        return jsonify({
            'error': 'Error al procesar solicitud'
        }), 500


@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    """
    Restablecer contraseña con token
    
    Body:
        {
            "password": "nueva_password123"
        }
    
    Returns:
        200: Contraseña restablecida
        400: Token inválido o expirado
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('password'):
            return jsonify({
                'error': 'Nueva contraseña es requerida'
            }), 400
        
        # Validar contraseña
        password_valid, password_error = validate_password(data['password'])
        if not password_valid:
            return jsonify({
                'error': password_error
            }), 400
        
        from datetime import datetime
        from app.utils.database import db
        
        # Buscar usuario con token válido
        query = """
        SELECT * FROM usuarios 
        WHERE token_reset_password = %s 
        AND token_reset_expira > %s
        AND activo = 1
        """
        user_data = db.get_one(query, (token, datetime.now()))
        
        if not user_data:
            return jsonify({
                'error': 'Token inválido o expirado'
            }), 400
        
        # Cambiar contraseña
        user = User(user_data)
        user.set_password(data['password'])
        
        # Limpiar token
        db.update(
            'usuarios',
            {
                'token_reset_password': None,
                'token_reset_expira': None
            },
            'id = %s',
            [user.id]
        )
        
        logger.info(f"Contraseña restablecida para: {user.email}")
        
        return jsonify({
            'message': 'Contraseña restablecida correctamente'
        }), 200
        
    except Exception as e:
        logger.error(f"Error restableciendo contraseña: {str(e)}")
        return jsonify({
            'error': 'Error al restablecer contraseña'
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    Cambiar contraseña (usuario autenticado)
    
    Body:
        {
            "current_password": "password_actual",
            "new_password": "nueva_password123"
        }
    
    Returns:
        200: Contraseña cambiada
        400: Contraseña actual incorrecta
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'error': 'Contraseña actual y nueva son requeridas'
            }), 400
        
        # Obtener usuario de sesión
        user = User.find_by_id(session['user_id'])
        
        # Verificar contraseña actual
        if not user.verify_password(data['current_password']):
            return jsonify({
                'error': 'Contraseña actual incorrecta'
            }), 400
        
        # Validar nueva contraseña
        password_valid, password_error = validate_password(data['new_password'])
        if not password_valid:
            return jsonify({
                'error': password_error
            }), 400
        
        # Cambiar contraseña
        user.set_password(data['new_password'])
        
        logger.info(f"Contraseña cambiada para: {user.email}")
        
        return jsonify({
            'message': 'Contraseña cambiada correctamente'
        }), 200
        
    except Exception as e:
        logger.error(f"Error cambiando contraseña: {str(e)}")
        return jsonify({
            'error': 'Error al cambiar contraseña'
        }), 500
