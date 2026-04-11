"""
============================================================================
PLASISE BACKEND - LOGGING SETUP
Configuración de logging estructurado
============================================================================
"""

import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger


def setup_logging(app):
    """
    Configurar logging para la aplicación
    
    Args:
        app: Instancia de Flask
    """
    # Crear directorio de logs si no existe
    log_dir = os.path.dirname(app.config.get('LOG_FILE', 'logs/app.log'))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Nivel de logging
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    
    # Formato para desarrollo (texto plano)
    if app.debug:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        )
    else:
        # Formato JSON para producción
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s'
        )
    
    # Handler para archivo
    file_handler = RotatingFileHandler(
        app.config.get('LOG_FILE', 'logs/app.log'),
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configurar logger de la app
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Configurar logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Handler para errores críticos (email, slack, etc.)
    if not app.debug:
        error_handler = RotatingFileHandler(
            'logs/errors.log',
            maxBytes=10485760,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        app.logger.addHandler(error_handler)
    
    # Silenciar logs de librerías ruidosas
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    app.logger.info("Logging configurado correctamente")
