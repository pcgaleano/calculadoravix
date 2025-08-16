# 🕰️ **CONFIGURACIÓN DE SCHEDULING AUTOMÁTICO**

## 🎯 **DESCRIPCIÓN GENERAL**

El sistema tiene **DOS tipos de jobs automáticos**:

1. **EOD Job**: Actualización de datos históricos (una vez al día)
2. **Price Updates**: Actualización de precios actuales (cada X minutos)

## ⚙️ **CONFIGURACIÓN PREDETERMINADA**

### 📊 **EOD Job (End of Day)**
```python
# Configuración por defecto:
{
    "enabled": True,
    "time": "18:00",                    # 6:00 PM
    "timezone": "America/New_York",     # Hora de Nueva York
    "market_days_only": True            # Solo Lunes-Viernes
}
```

### 💰 **Price Updates**
```python
# Configuración por defecto:
{
    "enabled": True,
    "interval_minutes": 5,              # Cada 5 minutos
    "running": False                    # Estado actual
}
```

## 🚀 **INICIO AUTOMÁTICO**

Al ejecutar `python backend/main.py`, automáticamente:

1. ✅ **EOD Job** se programa para 18:00 EST diariamente
2. ✅ **Price Updates** inicia cada 5 minutos
3. ✅ Solo ejecuta EOD en días de mercado (Lun-Vie)

## 📱 **ENDPOINTS DE GESTIÓN**

### **EOD Job Management:**

#### Consultar Status
```bash
GET http://127.0.0.1:8000/scheduler/status
```
**Respuesta:**
```json
{
    "running": true,
    "config": {
        "enabled": true,
        "time": "18:00",
        "timezone": "America/New_York",
        "market_days_only": true
    },
    "scheduled_jobs": 1,
    "next_run": "2025-08-16T18:00:00",
    "is_market_day": true
}
```

#### Configurar Horario
```bash
POST http://127.0.0.1:8000/scheduler/configure?enabled=true&time=19:00&timezone=America/Argentina/Buenos_Aires&market_days_only=true
```

#### Iniciar/Detener
```bash
POST http://127.0.0.1:8000/scheduler/start   # Iniciar
POST http://127.0.0.1:8000/scheduler/stop    # Detener
```

#### Ejecutar Manualmente
```bash
GET http://127.0.0.1:8000/scheduler/test-eod  # Test inmediato
POST http://127.0.0.1:8000/run-eod-job       # EOD manual
```

### **Price Updates Management:**

#### Consultar Status
```bash
GET http://127.0.0.1:8000/price-updates/status
```

#### Configurar Intervalo
```bash
POST http://127.0.0.1:8000/price-updates/configure?enabled=true&interval_minutes=2
```

## ⏰ **HORARIOS RECOMENDADOS POR MERCADO**

### 🇺🇸 **NYSE/NASDAQ (Acciones Americanas)**
```bash
# Mercado cierra: 4:00 PM ET
# EOD recomendado: 6:00 PM ET
POST /scheduler/configure?time=18:00&timezone=America/New_York
```

### 🇦🇷 **BCBA (Acciones Argentinas)**
```bash
# Mercado cierra: 5:00 PM ART  
# EOD recomendado: 6:30 PM ART
POST /scheduler/configure?time=18:30&timezone=America/Argentina/Buenos_Aires
```

### 🌍 **Crypto (24/7)**
```bash
# Sin restricción de horarios
# EOD recomendado: Medianoche UTC
POST /scheduler/configure?time=00:00&timezone=UTC&market_days_only=false
```

## 🎛️ **CONFIGURACIONES POR ENTORNO**

### **Desarrollo:**
```bash
# EOD: Manual cuando necesites
POST /scheduler/configure?enabled=false

# Precios: Cada 10 minutos (menos agresivo)
POST /price-updates/configure?interval_minutes=10
```

### **Testing:**
```bash
# EOD: Cada hora para pruebas
POST /scheduler/configure?time=*:00  # Cada hora en punto

# Precios: Cada 1 minuto
POST /price-updates/configure?interval_minutes=1
```

### **Producción:**
```bash
# EOD: 18:00 EST automático
POST /scheduler/configure?enabled=true&time=18:00&timezone=America/New_York

# Precios: Cada 2 minutos
POST /price-updates/configure?interval_minutes=2
```

## 📊 **MONITOREO Y LOGS**

### **Ver Últimos Jobs:**
```bash
GET http://127.0.0.1:8000/eod-job-status?business_date=2025-08-16
```

### **Verificar Integridad:**
```bash
GET http://127.0.0.1:8000/data-integrity-check
```

### **Estadísticas:**
```bash
GET http://127.0.0.1:8000/market-data-stats
```

## 🚨 **SOLUCIÓN DE PROBLEMAS**

### **EOD Job no ejecuta:**
```bash
# 1. Verificar status
GET /scheduler/status

# 2. Verificar si es día de mercado
# "is_market_day": false = No ejecutará

# 3. Forzar ejecución manual
GET /scheduler/test-eod
```

### **Precios no actualizan:**
```bash
# 1. Verificar status
GET /price-updates/status

# 2. Si running: false, reiniciar
POST /price-updates/configure?enabled=true&interval_minutes=5
```

### **Cambiar horario en runtime:**
```bash
# Sin reiniciar servidor:
POST /scheduler/configure?time=19:00
# Automáticamente reconfigura el schedule
```

## 📋 **CHECKLIST DE CONFIGURACIÓN**

### **Setup Inicial:**
- [ ] `pip install schedule pytz` (ya en requirements.txt)
- [ ] Verificar `GET /scheduler/status` 
- [ ] Configurar horario según tu mercado
- [ ] Probar con `GET /scheduler/test-eod`

### **Configuración Producción:**
- [ ] EOD: 18:00 en timezone correcto
- [ ] Price updates: 2-5 minutos 
- [ ] market_days_only: true
- [ ] Monitorear logs diariamente

### **Mantenimiento:**
- [ ] Verificar `/data-integrity-check` semanalmente
- [ ] Revisar `/eod-job-status` para fallos
- [ ] Backup de `trading_dashboard.db` regular

## 🎯 **FLUJO DIARIO AUTOMÁTICO**

```
06:00 AM - Mercados abren
         ├─ Price updates cada X min (automático)

04:00 PM - Mercados cierran  
         ├─ Esperar 2 horas para data settle

06:00 PM - EOD Job ejecuta (automático)
         ├─ Descarga datos del día
         ├─ Valida calidad
         ├─ Guarda en BD
         └─ Log de resultados

Continuo - Price updates siguen
         ├─ Para precios "actuales"
         └─ Dashboard en tiempo real
```

**¡Sistema completamente automatizado! Una vez configurado, funciona solo.**