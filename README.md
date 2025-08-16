# 🚀 Trading Dashboard - Sistema Profesional VIX_Fix

Una aplicación web profesional para análisis de trading con estrategia VIX_Fix. Incluye backend en Python (FastAPI) y frontend en React con Tailwind CSS.

## ✨ Características

- **Dashboard Profesional**: Interfaz tipo terminal de Wall Street
- **20 Tickers Diversificados**: Acciones argentinas, ETFs y crypto
- **Análisis VIX_Fix**: Sistema probado de detección de oportunidades
- **Tracking en Tiempo Real**: Precios actualizados automáticamente
- **Target de 4%**: Gestión profesional de objetivos
- **Grilla Avanzada**: Estado de trades, P&L, días transcurridos
- **Responsive Design**: Optimizado para desktop y móvil

## 🏗️ Arquitectura

```
inversorcortoplazo/
├── backend/                    # API Python FastAPI
├── frontend/                   # App React + Tailwind
├── analizar_ticker.py         # Script original
├── trade_analyzer.py          # Lógica de análisis
├── vix_fix_strategy.py        # Estrategia VIX_Fix
└── ticker_data.py             # Datos de tickers
```

## 🚀 Instalación y Uso

### Backend (Python)

```bash
# 1. Instalar dependencias del backend
cd backend
pip install -r requirements.txt

# 2. Ejecutar la API
python main.py
```

La API estará disponible en: http://127.0.0.1:8000

### Frontend (React)

```bash
# 1. Instalar dependencias del frontend
cd frontend
npm install

# 2. Ejecutar la aplicación
npm start
```

La aplicación estará disponible en: http://localhost:3000

## 📊 Tickers Incluidos

### Acciones Argentinas (10)
- GGAL.BA, PAMP.BA, YPFD.BA, ALUA.BA, TECO2.BA
- MIRG.BA, CEPU.BA, BMA.BA, SUPV.BA, LOMA.BA

### ETFs Internacionales (5)
- SPY, QQQ, IWM, EEM, GLD

### Criptomonedas (5)
- BTC-USD, ETH-USD, ADA-USD, DOT-USD, MATIC-USD

## 🎯 Funcionalidades

### 1. Dashboard Principal
- **Trades Abiertos**: Lista completa de posiciones activas
- **P&L en Tiempo Real**: Profits actuales vs target de 4%
- **Días Transcurridos**: Control de tiempo por posición
- **Estados**: ABIERTO vs TARGET_ALCANZADO

### 2. Análisis por Fecha
- Selector de fecha personalizable
- Opciones rápidas: Hoy, 1 semana, 1 mes, 3 meses
- Análisis automático desde fecha seleccionada

### 3. Métricas Profesionales
- **Tasa de Éxito**: % de trades que alcanzan el 4%
- **P&L Total**: Ganancia/pérdida acumulada
- **Días Promedio**: Tiempo medio por trade
- **Trades Activos**: Posiciones pendientes

## 🛠️ API Endpoints

```bash
GET  /health              # Health check
GET  /tickers             # Lista de tickers disponibles
GET  /price/{ticker}      # Precio actual de un ticker
GET  /dashboard?fecha=    # Datos del dashboard
POST /analyze             # Analizar ticker específico
GET  /analyze-all         # Analizar todos los tickers
```

## 🎨 Diseño Profesional

- **Tema Oscuro**: Perfecto para trading profesional
- **Tipografía Monospace**: JetBrains Mono para mejor legibilidad
- **Colores Intuitivos**: Verde (profit), Rojo (pérdida), Azul (neutro)
- **Animaciones Suaves**: Transiciones profesionales
- **Responsive**: Funciona en cualquier dispositivo

## 📈 Ejemplo de Uso

1. **Selecciona una fecha**: Por ejemplo, 1 mes atrás
2. **Ve los trades abiertos**: La tabla muestra todas las posiciones activas
3. **Analiza el P&L**: Cada trade muestra su profit actual vs el target de 4%
4. **Toma decisiones**: Los que alcanzaron 4% están listos para cerrar

## 🔧 Configuración Avanzada

### Cambiar Target de Profit
En `backend/main.py`, modificar:
```python
DEFAULT_PROFIT_TARGET = 0.04  # 4% -> cambiar por el valor deseado
```

### Agregar Nuevos Tickers
En `backend/main.py`, agregar a `MAIN_TICKERS`:
```python
MAIN_TICKERS = [
    # ... existentes
    "NUEVO_TICKER.BA",  # Agregar aquí
]
```

### Cambiar Intervalo de Actualización
En `frontend/src/App.tsx`:
```typescript
// Cambiar 30000 (30 segundos) por el valor deseado
setInterval(() => { ... }, 30000);
```

## 🚨 Solución de Problemas

### Backend no inicia
```bash
# Verificar que tienes todas las dependencias
pip install -r backend/requirements.txt

# Verificar que el puerto 8000 esté libre
netstat -an | findstr :8000
```

### Frontend no conecta
- Verificar que el backend esté ejecutándose en http://127.0.0.1:8000
- Revisar la consola del navegador para errores de CORS

### Sin datos de tickers
- Verificar conexión a internet
- Algunos tickers pueden no tener datos en ciertos períodos

## 🎯 Próximas Funcionalidades

- [ ] Alertas push cuando trades alcanzan el target
- [ ] Targets personalizados por ticker
- [ ] Backtesting histórico
- [ ] Exportar datos a Excel/CSV
- [ ] Integración con brokers (APIs)
- [ ] Análisis técnico avanzado
- [ ] Notificaciones por email/Telegram

## 💡 Tips de Uso

1. **Horarios de Trading**: La aplicación funciona 24/7, pero ten en cuenta los horarios de cada mercado
2. **Actualización**: Los precios se actualizan cada 30 segundos automáticamente
3. **Performance**: Para mejor rendimiento, selecciona períodos más cortos
4. **Backup**: Los análisis se guardan en la base de datos SQLite local

---

**¡Disfruta de tu nuevo dashboard de trading profesional!** 📊🚀

*"La diferencia entre un trader amateur y uno profesional es la disciplina en el seguimiento de sus posiciones"*