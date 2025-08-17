#!/bin/bash

set -e  # Exit on any error

echo "🚀 Deploy Apache en Producción: money.wann.com.ar"

# Variables
DOMAIN="money.wann.com.ar"
APP_DIR="/var/www/calculadoravix"
USER="www-data"

# 1. Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar Apache y dependencias
echo "🔧 Instalando Apache y dependencias..."
sudo apt install -y apache2 python3 python3-pip python3-venv git curl nodejs npm

# 3. Habilitar módulos Apache necesarios
echo "⚙️ Habilitando módulos Apache..."
sudo a2enmod ssl
sudo a2enmod rewrite
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo a2enmod deflate
sudo a2enmod expires
sudo a2enmod evasive

# 4. Instalar PM2
echo "⚙️ Instalando PM2..."
sudo npm install -g pm2

# 5. Crear directorio de aplicación
echo "📁 Configurando directorios..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# 6. Clonar repositorio
echo "📥 Clonando repositorio..."
cd $APP_DIR
sudo -u $USER git clone https://github.com/pcgaleano/calculadoravix.git .

# 7. Configurar entorno Python
echo "🐍 Configurando Python..."
sudo -u $USER python3 -m venv venv
sudo -u $USER $APP_DIR/venv/bin/pip install -r backend/requirements.txt

# 8. Configurar Apache Virtual Host
echo "🌐 Configurando Apache..."
sudo cp apache.conf /etc/apache2/sites-available/$DOMAIN.conf
sudo a2ensite $DOMAIN.conf
sudo a2dissite 000-default.conf
sudo apache2ctl configtest
sudo systemctl reload apache2

# 9. Configurar SSL
echo "🔐 Configurando SSL..."
sudo apt install certbot python3-certbot-apache -y
sudo certbot --apache -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# 10. Crear logs directory
echo "📝 Configurando logs..."
sudo mkdir -p $APP_DIR/logs
sudo chown $USER:$USER $APP_DIR/logs

# 11. Iniciar aplicación con PM2
echo "🔥 Iniciando aplicación..."
cd $APP_DIR
sudo -u $USER $APP_DIR/venv/bin/python -m pm2 start ecosystem.config.js

# 12. Configurar PM2 startup
echo "⚡ Configurando auto-start..."
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp /home/$USER
sudo -u $USER pm2 save

# 13. Configurar firewall
echo "🛡️ Configurando firewall..."
sudo ufw allow 'Apache Full'
sudo ufw allow ssh
sudo ufw --force enable

# 14. Optimizar Apache para producción
echo "⚡ Optimizando Apache..."
sudo tee /etc/apache2/conf-available/performance.conf > /dev/null << EOF
# Performance optimizations
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 5

# Compression
LoadModule deflate_module modules/mod_deflate.so
<Location />
    SetOutputFilter DEFLATE
    SetEnvIfNoCase Request_URI \.(?:gif|jpe?g|png)$ no-gzip dont-vary
    SetEnvIfNoCase Request_URI \.(?:exe|t?gz|zip|bz2|sit|rar)$ no-gzip dont-vary
</Location>

# Security
ServerTokens Prod
ServerSignature Off
EOF

sudo a2enconf performance
sudo systemctl reload apache2

# 15. Carga inicial de datos
echo "📊 Ejecutando carga inicial..."
sleep 30  # Esperar que inicie la app
curl -X POST "http://localhost:8000/initial-data-load" || echo "⚠️ Carga inicial falló, ejecutar manualmente"

# 16. Configurar backup
echo "💾 Configurando backup..."
sudo mkdir -p /backup
sudo crontab -l | { cat; echo "0 2 * * * tar -czf /backup/calculadora-\$(date +%Y%m%d).tar.gz $APP_DIR/backend/trading_dashboard.db"; } | sudo crontab -

# 17. Configurar log rotation
echo "📝 Configurando rotación de logs..."
sudo tee /etc/logrotate.d/calculadoravix > /dev/null << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 644 $USER $USER
    postrotate
        pm2 reloadLogs
    endscript
}
EOF

echo "✅ Deploy Apache completado!"
echo "🌐 Sitio disponible en: https://$DOMAIN"
echo "📋 API docs en: https://$DOMAIN/docs"
echo "📊 Status Apache: sudo systemctl status apache2"
echo "📊 Status PM2: pm2 status"
echo "📝 Logs Apache: sudo tail -f /var/log/apache2/$DOMAIN_access.log"
echo "📝 Logs App: pm2 logs money-api"