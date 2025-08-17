#!/bin/bash

echo "🔐 Configurando SSL para money.wann.com.ar"

# Instalar Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx -y

# Obtener certificado SSL
sudo certbot --nginx -d money.wann.com.ar -d www.money.wann.com.ar --non-interactive --agree-tos --email admin@money.wann.com.ar

# Configurar renovación automática
sudo crontab -e
# Agregar línea: 0 12 * * * /usr/bin/certbot renew --quiet

echo "✅ SSL configurado exitosamente"