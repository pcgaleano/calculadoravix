#!/bin/bash

set -e  # Exit on any error

echo "🚀 Deploy en Producción: money.wann.com.ar"

# Variables
DOMAIN="money.wann.com.ar"
APP_DIR="/var/www/calculadoravix"
USER="www-data"

# 1. Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias del sistema
echo "🔧 Instalando dependencias..."
sudo apt install -y python3 python3-pip python3-venv nginx git curl nodejs npm

# 3. Instalar PM2
echo "⚙️ Instalando PM2..."
sudo npm install -g pm2

# 4. Crear directorio de aplicación
echo "📁 Configurando directorios..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# 5. Clonar repositorio
echo "📥 Clonando repositorio..."
cd $APP_DIR
sudo -u $USER git clone https://github.com/pcgaleano/calculadoravix.git .

# 6. Configurar entorno Python
echo "🐍 Configurando Python..."
sudo -u $USER python3 -m venv venv
sudo -u $USER $APP_DIR/venv/bin/pip install -r backend/requirements.txt

# 7. Configurar Nginx
echo "🌐 Configurando Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/$DOMAIN
sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 8. Configurar SSL
echo "🔐 Configurando SSL..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# 9. Crear logs directory
echo "📝 Configurando logs..."
sudo mkdir -p $APP_DIR/logs
sudo chown $USER:$USER $APP_DIR/logs

# 10. Iniciar aplicación con PM2
echo "🔥 Iniciando aplicación..."
cd $APP_DIR
sudo -u $USER $APP_DIR/venv/bin/python -m pm2 start ecosystem.config.js

# 11. Configurar PM2 startup
echo "⚡ Configurando auto-start..."
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp /home/$USER
sudo -u $USER pm2 save

# 12. Configurar firewall
echo "🛡️ Configurando firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

# 13. Carga inicial de datos
echo "📊 Ejecutando carga inicial..."
sleep 30  # Esperar que inicie la app
curl -X POST "http://localhost:8000/initial-data-load" || echo "⚠️ Carga inicial falló, ejecutar manualmente"

# 14. Configurar backup
echo "💾 Configurando backup..."
sudo crontab -l | { cat; echo "0 2 * * * tar -czf /backup/calculadora-$(date +\%Y\%m\%d).tar.gz $APP_DIR/backend/trading_dashboard.db"; } | sudo crontab -

echo "✅ Deploy completado!"
echo "🌐 Sitio disponible en: https://$DOMAIN"
echo "📋 API docs en: https://$DOMAIN/docs"
echo "📊 Status: pm2 status"
echo "📝 Logs: pm2 logs money-api"