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
    python3 -m pip install -r /code/backend/requirements.txt 2>&1 | grep -v "Requirement already satisfied" || true
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
echo "=========================================="
echo ""

# Ejecutar Flask
exec python3 /code/backend/api_productos.py
