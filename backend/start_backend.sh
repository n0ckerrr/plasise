#!/bin/bash

# ============================================================================
# PLASISE - Script de Inicio del Backend
# Se ejecuta automáticamente cuando arranca el contenedor Docker
# ============================================================================

echo "=========================================="
echo "🚀 Iniciando Backend PLASISE"
echo "=========================================="

# Ir al directorio del backend
cd /code/backend

# Verificar que existe el archivo de requisitos
if [ -f /code/backend/requirements.txt ]; then
    echo "✓ Archivo requirements.txt encontrado"
    
    # Instalar dependencias si es necesario
    echo "📦 Verificando dependencias..."
    
    # Asegurar que pip y dependencias del sistema están instaladas (si usamos easypanel/base en lugar del Dockerfile)
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        echo "🔧 Instalando python3-pip y dependencias de MySQL..."
        apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip python3-dev default-libmysqlclient-dev pkg-config gcc || true
    fi
    
    python3 -m pip install --break-system-packages --ignore-installed --no-cache-dir -r /code/backend/requirements.txt 2>&1 | grep -v "already satisfied" || \
    python3 -m pip install --ignore-installed --no-cache-dir -r /code/backend/requirements.txt 2>&1 | grep -v "already satisfied" || true
    
    # Diagnóstico: Listar paquetes instalados
    echo "📋 Paquetes instalados:"
    python3 -m pip list | head -n 20
else
    echo "⚠️  No se encontró requirements.txt"
fi

# Verificar variables de entorno
echo ""
echo "🔧 Verificando configuración..."
if [ -f .env ]; then
    echo "✓ Archivo .env encontrado"
    source .env
else
    echo "⚠️  Advertencia: No se encontró archivo .env"
fi

# Verificar conexión a base de datos
echo ""
echo "🗄️  Verificando conexión a base de datos..."
python3 verify_db.py 2>&1 || echo "⚠️  Advertencia: Error al verificar BD"

# Crear directorio de logs si no existe
mkdir -p /code/backend/logs
echo "✓ Directorio de logs creado/verificado"

# Iniciar Flask
echo ""
echo "=========================================="
echo "🎯 Iniciando Flask Application..."
echo "=========================================="
echo "📍 Puerto: 5000"
echo "📍 Host: 0.0.0.0"
echo "🔍 Verificando procesos en puerto 5000..."
curl -s http://localhost:5000/health && echo "✅ Servicio ya respondiendo?!" || echo "✓ Puerto 5000 despejado"
echo "=========================================="
echo ""

# Ejecutar Flask
exec python3 /code/backend/api_productos.py
