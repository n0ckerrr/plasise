#!/bin/bash
# ==============================================
# PLASISE - Script de inicio automático
# Ubicación: /code/scripts/init.sh
# Este script se ejecuta al iniciar el contenedor
# ==============================================

LOG_FILE="/var/log/plasise_init.log"
echo "$(date): PLASISE Init Script Starting..." >> $LOG_FILE

# 1. Instalar dependencias del sistema si faltan
echo "$(date): Checking system dependencies..." >> $LOG_FILE
if ! dpkg -l | grep -q python3.10-venv; then
    echo "$(date): Installing python3-venv and pip..." >> $LOG_FILE
    apt-get update -qq
    apt-get install -y -qq python3.10-venv python3-pip > /dev/null 2>&1
    echo "$(date): System dependencies installed" >> $LOG_FILE
fi

# 2. Verificar/crear entorno virtual Python
if [ ! -f "/code/venv/bin/python" ] || [ ! -f "/code/venv/bin/flask" ]; then
    echo "$(date): Creating Python virtual environment..." >> $LOG_FILE
    rm -rf /code/venv
    python3 -m venv /code/venv
    echo "$(date): Virtual environment created" >> $LOG_FILE
    
    # 3. Instalar dependencias Python
    echo "$(date): Installing Python dependencies..." >> $LOG_FILE
    /code/venv/bin/pip install --quiet flask flask-cors mysql-connector-python python-dotenv werkzeug requests
    echo "$(date): Dependencies installed" >> $LOG_FILE
else
    # Verificar que flask está instalado
    if ! /code/venv/bin/python -c "import flask" 2>/dev/null; then
        echo "$(date): Flask missing, reinstalling dependencies..." >> $LOG_FILE
        /code/venv/bin/pip install --quiet flask flask-cors mysql-connector-python python-dotenv werkzeug requests
        echo "$(date): Dependencies reinstalled" >> $LOG_FILE
    fi
fi

# 4. Configurar nginx (siempre sobrescribir para asegurar config correcta)
echo "$(date): Configuring nginx..." >> $LOG_FILE
cat > /etc/nginx/sites-available/default << 'NGINX_CONF'
server {
    listen 80 default_server;
    server_name _;
    
    root /code/frontend/pages;
    index index.html;
    
    location / {
        try_files $uri $uri/ $uri.html /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:5000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg)$ {
        expires 1y;
        access_log off;
    }
}
NGINX_CONF

# 5. Crear archivo .env si no existe
if [ ! -f "/code/backend/.env" ]; then
    echo "$(date): Creating .env file..." >> $LOG_FILE
    cat > /code/backend/.env << 'ENV_CONF'
DB_HOST=72.61.111.50
DB_PORT=9966
DB_USER=plasise
DB_PASSWORD=plasise.
DB_NAME=plasise
SECRET_KEY=aegis_super_secret_key_vps_stable
FLASK_ENV=production
HOLDED_API_KEY=5cc163c45bd3b739628642bdf89506c7
ENV_CONF
fi

echo "$(date): PLASISE Init Script Completed!" >> $LOG_FILE
