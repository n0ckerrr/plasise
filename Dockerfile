# ============================================================================
# PLASISE - Dockerfile para Backend Flask
# ============================================================================

FROM python:3.11-slim

# Metadata
LABEL maintainer="PLASISE"
LABEL description="Backend Flask para PLASISE - Sistema de gestión de productos"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de la aplicación
WORKDIR /code/backend

# Copiar requirements primero (mejor cacheo)
COPY backend/requirements.txt .

# Instalar dependencias de Python
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY backend/ .

# Copiar script de inicio
COPY start_backend.sh /usr/local/bin/start_backend.sh
RUN chmod +x /usr/local/bin/start_backend.sh

# Crear directorios necesarios
RUN mkdir -p /code/backend/logs && \
    mkdir -p /code/backend/config && \
    chmod -R 755 /code/backend

# Exponer puerto
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/v1/health || exit 1

# Comando de inicio
CMD ["/usr/local/bin/start_backend.sh"]
