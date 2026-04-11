"""
============================================================================
PLASISE BACKEND - DATABASE CONNECTION
Gestión de conexiones a MySQL con connection pooling
============================================================================
"""

import mysql.connector
from mysql.connector import pooling
from flask import g, current_app
import logging

logger = logging.getLogger(__name__)

# Pool de conexiones global
db_pool = None


class Database:
    """Clase para gestionar la conexión a MySQL"""
    
    def __init__(self, app=None):
        self.pool = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar con la aplicación Flask"""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="plasise_pool",
                pool_size=app.config.get('SQLALCHEMY_POOL_SIZE', 10),
                pool_reset_session=True,
                host=app.config['MYSQL_HOST'],
                port=app.config['MYSQL_PORT'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                database=app.config['MYSQL_DATABASE'],
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                autocommit=False,
                use_pure=True
            )
            
            logger.info("Database connection pool creado correctamente")
            
        except mysql.connector.Error as err:
            logger.error(f"Error al crear connection pool: {err}")
            raise
    
    def get_connection(self):
        """Obtener conexión del pool"""
        try:
            return self.pool.get_connection()
        except mysql.connector.Error as err:
            logger.error(f"Error al obtener conexión: {err}")
            raise
    
    def execute_query(self, query, params=None, fetch=True, commit=False):
        """
        Ejecutar query de forma segura
        
        Args:
            query: SQL query
            params: Parámetros para la query (tuple o dict)
            fetch: Si debe hacer fetch de resultados
            commit: Si debe hacer commit
        
        Returns:
            list: Resultados si fetch=True, affected_rows si fetch=False
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute(query, params or ())
            
            if commit:
                conn.commit()
                return cursor.rowcount
            
            if fetch:
                return cursor.fetchall()
            
            return cursor.rowcount
            
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.error(f"Error en query: {err}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def execute_many(self, query, data_list, commit=True):
        """
        Ejecutar múltiples inserts de forma eficiente
        
        Args:
            query: SQL query con placeholders
            data_list: Lista de tuplas con los datos
            commit: Si debe hacer commit
        
        Returns:
            int: Número de filas afectadas
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(buffered=True)
            
            cursor.executemany(query, data_list)
            
            if commit:
                conn.commit()
            
            return cursor.rowcount
            
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.error(f"Error en executemany: {err}")
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_one(self, query, params=None):
        """
        Obtener un único resultado
        
        Args:
            query: SQL query
            params: Parámetros
        
        Returns:
            dict: Resultado o None
        """
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute(query, params or ())
            return cursor.fetchone()
            
        except mysql.connector.Error as err:
            logger.error(f"Error en get_one: {err}")
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def insert(self, table, data):
        """
        Insert simplificado
        
        Args:
            table: Nombre de la tabla
            data: Dict con los datos a insertar
        
        Returns:
            int: ID del registro insertado
        """
        columns = ', '.join(f"`{k}`" for k in data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        
        query = f"INSERT INTO `{table}` ({columns}) VALUES ({placeholders})"
        
        conn = None
        cursor = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor(buffered=True)
            
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.lastrowid
            
        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            logger.error(f"Error en insert: {err}")
            raise
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def update(self, table, data, where_clause, where_params):
        """
        Update simplificado
        
        Args:
            table: Nombre de la tabla
            data: Dict con los datos a actualizar
            where_clause: Cláusula WHERE (ej: "id = %s")
            where_params: Parámetros para WHERE
        
        Returns:
            int: Número de filas afectadas
        """
        set_clause = ', '.join(f"`{k}` = %s" for k in data.keys())
        values = tuple(data.values()) + tuple(where_params)
        
        query = f"UPDATE `{table}` SET {set_clause} WHERE {where_clause}"
        
        return self.execute_query(query, values, fetch=False, commit=True)
    
    def delete(self, table, where_clause, where_params):
        """
        Delete simplificado
        
        Args:
            table: Nombre de la tabla
            where_clause: Cláusula WHERE
            where_params: Parámetros para WHERE
        
        Returns:
            int: Número de filas eliminadas
        """
        query = f"DELETE FROM `{table}` WHERE {where_clause}"
        return self.execute_query(query, where_params, fetch=False, commit=True)


# Instancia global
db = Database()


def init_db(app):
    """Inicializar database con la app"""
    db.init_app(app)
    
    # Crear tablas si no existen (en desarrollo)
    if app.config.get('DEBUG'):
        create_tables_if_not_exist(app)


def create_tables_if_not_exist(app):
    """Crear tablas si no existen (solo desarrollo)"""
    # Esta función puede leer el schema.sql y ejecutarlo
    # Por ahora solo verificamos la conexión
    try:
        conn = db.get_connection()
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        logger.info("Conexión a base de datos verificada")
    except Exception as e:
        logger.error(f"Error verificando base de datos: {e}")


def get_db():
    """Obtener conexión para el contexto de request"""
    if 'db_conn' not in g:
        g.db_conn = db.get_connection()
    return g.db_conn


def close_db(e=None):
    """Cerrar conexión al final del request"""
    conn = g.pop('db_conn', None)
    if conn is not None:
        conn.close()
