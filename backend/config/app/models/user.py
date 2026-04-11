"""
============================================================================
PLASISE BACKEND - USER MODEL
Modelo de usuario con autenticación y gestión de permisos
============================================================================
"""

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import secrets
from flask import current_app
from app.utils.database import db


class User:
    """Modelo de Usuario"""
    
    def __init__(self, data=None):
        """
        Inicializar usuario desde dict
        
        Args:
            data: Dict con los datos del usuario
        """
        if data:
            self.id = data.get('id')
            self.email = data.get('email')
            self.password_hash = data.get('password_hash')
            self.nombre = data.get('nombre')
            self.apellidos = data.get('apellidos')
            self.telefono = data.get('telefono')
            self.cargo = data.get('cargo')
            self.empresa_id = data.get('empresa_id')
            self.tipo_usuario = data.get('tipo_usuario', 'cliente')
            self.rol = data.get('rol', 'cliente_retail')
            self.idioma_preferido = data.get('idioma_preferido', 'es')
            self.activo = data.get('activo', 1)
            self.email_verificado = data.get('email_verificado', 0)
            self.ultimo_acceso = data.get('ultimo_acceso')
            self.fecha_registro = data.get('fecha_registro')
    
    @staticmethod
    def find_by_id(user_id):
        """
        Buscar usuario por ID
        
        Args:
            user_id: ID del usuario
        
        Returns:
            User: Instancia de User o None
        """
        query = """
        SELECT u.*, e.razon_social, e.tipo_cliente, e.descuento_global
        FROM usuarios u
        LEFT JOIN empresas e ON u.empresa_id = e.id
        WHERE u.id = %s AND u.activo = 1
        """
        
        result = db.get_one(query, (user_id,))
        return User(result) if result else None
    
    @staticmethod
    def find_by_email(email):
        """
        Buscar usuario por email
        
        Args:
            email: Email del usuario
        
        Returns:
            User: Instancia de User o None
        """
        query = """
        SELECT u.*, e.razon_social, e.tipo_cliente, e.descuento_global
        FROM usuarios u
        LEFT JOIN empresas e ON u.empresa_id = e.id
        WHERE u.email = %s
        """
        
        result = db.get_one(query, (email,))
        return User(result) if result else None
    
    @staticmethod
    def create(data):
        """
        Crear nuevo usuario
        
        Args:
            data: Dict con los datos del usuario
        
        Returns:
            int: ID del usuario creado
        """
        # Hash de password
        if 'password' in data:
            data['password_hash'] = generate_password_hash(data['password'])
            del data['password']
        
        # Valores por defecto
        data.setdefault('activo', 1)
        data.setdefault('email_verificado', 0)
        data.setdefault('tipo_usuario', 'cliente')
        data.setdefault('rol', 'cliente_retail')
        data.setdefault('idioma_preferido', 'es')
        
        # Generar token de verificación
        data['token_verificacion'] = secrets.token_urlsafe(32)
        
        return db.insert('usuarios', data)
    
    def update(self, data):
        """
        Actualizar datos del usuario
        
        Args:
            data: Dict con los datos a actualizar
        
        Returns:
            int: Número de filas actualizadas
        """
        # No permitir actualizar ciertos campos
        protected_fields = ['id', 'password_hash', 'fecha_registro']
        data = {k: v for k, v in data.items() if k not in protected_fields}
        
        if not data:
            return 0
        
        return db.update('usuarios', data, 'id = %s', [self.id])
    
    def verify_password(self, password):
        """
        Verificar contraseña
        
        Args:
            password: Contraseña en texto plano
        
        Returns:
            bool: True si la contraseña es correcta
        """
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """
        Establecer nueva contraseña
        
        Args:
            password: Nueva contraseña en texto plano
        
        Returns:
            int: Número de filas actualizadas
        """
        password_hash = generate_password_hash(password)
        return db.update(
            'usuarios',
            {'password_hash': password_hash},
            'id = %s',
            [self.id]
        )
    
    def generate_auth_token(self, expires_in=3600):
        """
        Generar token JWT para autenticación
        
        Args:
            expires_in: Tiempo de expiración en segundos
        
        Returns:
            str: Token JWT
        """
        payload = {
            'user_id': self.id,
            'email': self.email,
            'tipo_usuario': self.tipo_usuario,
            'rol': self.rol,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
    
    @staticmethod
    def verify_auth_token(token):
        """
        Verificar token JWT
        
        Args:
            token: Token JWT
        
        Returns:
            User: Instancia de User si el token es válido, None si no
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            
            return User.find_by_id(payload['user_id'])
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def update_last_access(self):
        """Actualizar fecha de último acceso"""
        db.update(
            'usuarios',
            {'ultimo_acceso': datetime.now()},
            'id = %s',
            [self.id]
        )
    
    def to_dict(self, include_sensitive=False):
        """
        Convertir usuario a diccionario
        
        Args:
            include_sensitive: Si debe incluir datos sensibles
        
        Returns:
            dict: Datos del usuario
        """
        data = {
            'id': self.id,
            'email': self.email,
            'nombre': self.nombre,
            'apellidos': self.apellidos,
            'telefono': self.telefono,
            'cargo': self.cargo,
            'tipo_usuario': self.tipo_usuario,
            'rol': self.rol,
            'idioma_preferido': self.idioma_preferido,
            'activo': bool(self.activo),
            'email_verificado': bool(self.email_verificado),
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
        
        if hasattr(self, 'razon_social'):
            data['empresa'] = {
                'id': self.empresa_id,
                'razon_social': getattr(self, 'razon_social', None),
                'tipo_cliente': getattr(self, 'tipo_cliente', None),
                'descuento_global': float(getattr(self, 'descuento_global', 0))
            }
        
        return data
    
    def has_permission(self, permission):
        """
        Verificar si el usuario tiene un permiso específico
        
        Args:
            permission: Nombre del permiso
        
        Returns:
            bool: True si tiene el permiso
        """
        # Superadmins tienen todos los permisos
        if self.rol == 'super_admin':
            return True
        
        # Mapeo de permisos por rol
        permissions_map = {
            'admin': ['view_admin', 'manage_products', 'manage_orders', 'manage_users'],
            'comercial': ['view_admin', 'manage_orders', 'view_customers'],
            'tecnico': ['view_admin', 'view_products'],
            'cliente_profesional': ['view_catalog', 'place_orders', 'view_resources'],
            'cliente_retail': ['view_catalog', 'place_orders']
        }
        
        user_permissions = permissions_map.get(self.rol, [])
        return permission in user_permissions
    
    def is_admin(self):
        """Verificar si es administrador"""
        return self.tipo_usuario == 'admin' or self.rol in ['super_admin', 'admin']
    
    def is_active(self):
        """Verificar si está activo"""
        return bool(self.activo)
    
    def is_verified(self):
        """Verificar si el email está verificado"""
        return bool(self.email_verificado)
    
    @staticmethod
    def get_all(filters=None, page=1, per_page=20):
        """
        Obtener listado de usuarios con filtros
        
        Args:
            filters: Dict con filtros opcionales
            page: Página actual
            per_page: Items por página
        
        Returns:
            dict: {'usuarios': [...], 'total': N, 'pages': N}
        """
        filters = filters or {}
        
        # Query base
        query = """
        SELECT u.*, e.razon_social, e.tipo_cliente
        FROM usuarios u
        LEFT JOIN empresas e ON u.empresa_id = e.id
        WHERE 1=1
        """
        
        params = []
        
        # Aplicar filtros
        if filters.get('tipo_usuario'):
            query += " AND u.tipo_usuario = %s"
            params.append(filters['tipo_usuario'])
        
        if filters.get('activo') is not None:
            query += " AND u.activo = %s"
            params.append(filters['activo'])
        
        if filters.get('search'):
            query += """ AND (
                u.email LIKE %s OR 
                u.nombre LIKE %s OR 
                u.apellidos LIKE %s OR
                e.razon_social LIKE %s
            )"""
            search_term = f"%{filters['search']}%"
            params.extend([search_term] * 4)
        
        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM ({query}) as subquery"
        total = db.get_one(count_query, params)['total']
        
        # Ordenar y paginar
        query += " ORDER BY u.fecha_registro DESC"
        query += f" LIMIT {per_page} OFFSET {(page - 1) * per_page}"
        
        # Ejecutar query
        results = db.execute_query(query, params)
        usuarios = [User(row).to_dict() for row in results]
        
        return {
            'usuarios': usuarios,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page,
            'per_page': per_page
        }
