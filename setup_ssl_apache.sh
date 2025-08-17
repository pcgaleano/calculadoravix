#!/bin/bash

echo "🔐 Configurando SSL para Apache + money.wann.com.ar"

# Instalar Certbot para Apache
sudo apt update
sudo apt install certbot python3-certbot-apache -y

# Obtener certificado SSL
sudo certbot --apache -d money.wann.com.ar -d www.money.wann.com.ar --non-interactive --agree-tos --email admin@money.wann.com.ar

# Verificar configuración SSL
sudo apache2ctl configtest

# Recargar Apache
sudo systemctl reload apache2

# Configurar renovación automática
echo "0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload apache2" | sudo crontab -

echo "✅ SSL configurado exitosamente para Apache"