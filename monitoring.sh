#!/bin/bash

# Script de monitoreo para money.wann.com.ar

DOMAIN="money.wann.com.ar"
LOG_FILE="/var/log/money-monitoring.log"
ALERT_EMAIL="admin@money.wann.com.ar"

log_message() {
    echo "$(date): $1" >> $LOG_FILE
}

check_website() {
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN)
    if [ $STATUS -eq 200 ]; then
        log_message "✅ Website OK - Status: $STATUS"
        return 0
    else
        log_message "❌ Website DOWN - Status: $STATUS"
        return 1
    fi
}

check_api() {
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/tickers)
    if [ $STATUS -eq 200 ]; then
        log_message "✅ API OK - Status: $STATUS"
        return 0
    else
        log_message "❌ API DOWN - Status: $STATUS"
        return 1
    fi
}

check_pm2() {
    if pm2 list | grep -q "money-api.*online"; then
        log_message "✅ PM2 Process OK"
        return 0
    else
        log_message "❌ PM2 Process DOWN"
        pm2 restart money-api
        return 1
    fi
}

check_disk_space() {
    USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $USAGE -lt 90 ]; then
        log_message "✅ Disk usage OK: ${USAGE}%"
        return 0
    else
        log_message "⚠️ Disk usage HIGH: ${USAGE}%"
        return 1
    fi
}

# Ejecutar checks
check_website || echo "Website check failed"
check_api || echo "API check failed"
check_pm2 || echo "PM2 check failed"
check_disk_space || echo "Disk space check failed"

# Agregar a crontab: */5 * * * * /var/www/calculadoravix/monitoring.sh