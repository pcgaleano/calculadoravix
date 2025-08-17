#!/bin/bash

# Script de monitoreo específico para Apache + money.wann.com.ar

DOMAIN="money.wann.com.ar"
LOG_FILE="/var/log/money-apache-monitoring.log"
ALERT_EMAIL="admin@money.wann.com.ar"

log_message() {
    echo "$(date): $1" >> $LOG_FILE
}

check_apache_status() {
    if systemctl is-active --quiet apache2; then
        log_message "✅ Apache2 service running"
        return 0
    else
        log_message "❌ Apache2 service DOWN"
        sudo systemctl restart apache2
        return 1
    fi
}

check_apache_config() {
    if sudo apache2ctl configtest 2>/dev/null; then
        log_message "✅ Apache config OK"
        return 0
    else
        log_message "❌ Apache config ERROR"
        return 1
    fi
}

check_ssl_cert() {
    EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
    EXPIRY_DATE=$(date -d "$EXPIRY" +%s)
    CURRENT_DATE=$(date +%s)
    DAYS_LEFT=$(( ($EXPIRY_DATE - $CURRENT_DATE) / 86400 ))
    
    if [ $DAYS_LEFT -gt 30 ]; then
        log_message "✅ SSL cert OK - $DAYS_LEFT days left"
        return 0
    else
        log_message "⚠️ SSL cert expires in $DAYS_LEFT days"
        return 1
    fi
}

check_apache_performance() {
    # Check Apache processes
    APACHE_PROCS=$(ps aux | grep apache2 | grep -v grep | wc -l)
    log_message "📊 Apache processes: $APACHE_PROCS"
    
    # Check memory usage
    MEMORY_USAGE=$(ps aux | grep apache2 | grep -v grep | awk '{sum+=$6} END {print sum/1024}')
    log_message "📊 Apache memory usage: ${MEMORY_USAGE}MB"
    
    # Check connections
    CONNECTIONS=$(ss -tuln | grep :443 | wc -l)
    log_message "📊 HTTPS connections: $CONNECTIONS"
}

check_error_logs() {
    # Check for errors in last 5 minutes
    ERRORS=$(sudo tail -n 100 /var/log/apache2/money.wann.com.ar_error.log | grep "$(date +'%Y-%m-%d %H:%M' -d '5 minutes ago')" | wc -l)
    if [ $ERRORS -gt 10 ]; then
        log_message "⚠️ High error rate: $ERRORS errors in last 5 minutes"
        return 1
    else
        log_message "✅ Error rate normal: $ERRORS errors"
        return 0
    fi
}

# Ejecutar todos los checks
check_apache_status
check_apache_config
check_ssl_cert
check_apache_performance
check_error_logs

# Agregar a crontab:
# */5 * * * * /var/www/calculadoravix/apache_monitoring.sh