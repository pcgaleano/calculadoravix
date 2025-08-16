# 📋 ESTRUCTURA DEL PROYECTO - Trading Dashboard

## 🏗️ Arquitectura General

```
money.wann.com.ar/
├── backend/                    # API Python FastAPI
│   ├── main.py                # Servidor principal
│   ├── requirements.txt       # Dependencias Python
│   ├── trading_dashboard.db   # Base de datos SQLite
│   └── venv/                  # Entorno virtual Python
├── frontend/                   # Aplicación React TypeScript
│   ├── src/
│   │   ├── components/        # Componentes React
│   │   ├── services/          # Servicios API
│   │   ├── types/             # Tipos TypeScript
│   │   ├── styles/            # **CONFIGURACIÓN CENTRAL DE ESTILOS**
│   │   ├── App.tsx            # Componente principal
│   │   ├── index.css          # **ESTILOS GLOBALES CENTRALIZADOS**
│   │   └── App.css            # Estilos específicos App
│   ├── public/                # Archivos estáticos
│   └── package.json           # Dependencias Node.js
├── analizar_ticker.py         # Script original análisis
├── trade_analyzer.py          # Lógica de análisis VIX_Fix
├── vix_fix_strategy.py        # Estrategia VIX_Fix
├── ticker_data.py             # Datos de tickers
└── estructura_proyecto.md     # **ESTE ARCHIVO MAESTRO**
```

## 🎨 CONFIGURACIÓN CENTRAL DE ESTILOS

### 📄 Archivo Principal: `frontend/src/index.css`
**UBICACIÓN CENTRAL**: Todos los estilos globales, colores, tipografías y variables se definen aquí.

#### Colores Principales Definidos:
```css
/* Fondo principal */
background-color: #0f172a

/* Colores de texto */
color: #f1f5f9          /* Texto principal */
color: #cbd5e1          /* Texto secundario */
color: #94a3b8          /* Texto terciario */

/* Colores de trading */
color: #4ade80          /* Profit positivo */
color: #f87171          /* Profit negativo */
color: #93c5fd          /* Ticker badges */
color: #fde047          /* Status abierto */
color: #86efac          /* Status cerrado */

/* Colores de fondo */
background-color: #1e293b    /* Cards principales */
background-color: #334155    /* Headers y botones */
background-color: #475569    /* Bordes y separadores */

/* Colores de acción */
background-color: #2563eb    /* Botones primarios */
background-color: #16a34a    /* Botones éxito */
background-color: #dc2626    /* Botones peligro */
```

#### Tipografías Definidas:
```css
/* Principal (monospace) */
font-family: 'JetBrains Mono', Monaco, Consolas, monospace

/* Alternativa (sans-serif) */
font-family: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
```

### 🚨 REGLAS CRÍTICAS PARA ESTILOS:

1. **NUNCA** definir colores hardcodeados en componentes
2. **SIEMPRE** usar las clases CSS definidas en `index.css`
3. **OBLIGATORIO** actualizar `index.css` para nuevos estilos globales
4. **ACTUALIZAR** este archivo maestro cuando se modifique `index.css`

## 🖥️ FRONTEND - React TypeScript

### 📂 Estructura de Componentes:

#### `src/App.tsx` - Componente Principal
- **Función**: Orquestador principal de la aplicación
- **Estado principal**: dashboardData, selectedDate, isLoading, error, apiStatus
- **Auto-refresh**: Intervalo configurable (default: 30 segundos)
- **Conexión API**: Gestión de estado de conexión backend

#### `src/components/Header.tsx`
- **Función**: Cabecera principal con título y botón refresh
- **Props**: onRefresh, isLoading
- **Estilos**: Tema oscuro professional tipo terminal

#### `src/components/StatsCards.tsx`
- **Función**: Tarjetas con métricas principales
- **Props**: totalTrades, tradesExitosos, profitTotal, diasPromedio
- **Layout**: Grid responsivo (1-4 columnas según dispositivo)

#### `src/components/DateSelector.tsx`
- **Función**: Selector de fecha con opciones rápidas
- **Props**: selectedDate, onDateChange, isLoading
- **Opciones**: Hoy, 1 semana, 1 mes, 3 meses, fecha personalizada

#### `src/components/TradesTable.tsx`
- **Función**: Tabla principal de trades abiertos
- **Props**: trades, isLoading
- **Características**: Responsive, colores dinámicos por profit/loss

#### `src/components/RefreshControl.tsx`
- **Función**: Control de actualización automática
- **Props**: isAutoRefreshEnabled, refreshInterval, onToggleAutoRefresh, etc.
- **Intervalos**: 15s, 30s, 60s, 2min, 5min

### 📊 Servicios y Tipos:

#### `src/services/api.ts`
- **Clase**: tradingAPI
- **Base URL**: http://127.0.0.1:8000
- **Métodos**:
  - healthCheck()
  - getDashboardData(fecha)
  - getCurrentPrice(ticker)
  - refreshPrices()

#### `src/types/index.ts`
- **TradeResult**: Estructura de trade individual
- **DashboardData**: Estructura de respuesta dashboard
- **Propiedades principales**: ticker, fecha_compra, precio_compra, profit_pct, estado

### 🎭 Dependencias Frontend:
- React 19.1.1
- TypeScript 4.9.5
- Axios 1.11.0 (HTTP client)
- Lucide React 0.536.0 (iconos)
- @headlessui/react 2.2.7 (componentes UI)

## 🐍 BACKEND - Python FastAPI

### 📄 Archivo Principal: `backend/main.py`

#### Configuración Global:
```python
DEFAULT_PROFIT_TARGET = 0.04  # 4%
DEFAULT_MAX_DAYS = 30
```

#### Tickers Principales (70 total):
- **Acciones Argentinas (.BA)**: GGAL.BA, PAMP.BA, YPFD.BA, etc.
- **ADRs Argentinos**: GGAL, PAM, YPF, etc.
- **ETFs**: SPY, QQQ, IWM, EEM, GLD
- **Big Tech**: AAPL, MSFT, GOOGL, AMZN, TSLA, etc.
- **Criptomonedas (-USD)**: BTC-USD, ETH-USD, etc.

#### Endpoints API:
```python
GET  /                    # Info general API
GET  /health             # Health check
GET  /tickers            # Lista tickers disponibles
GET  /price/{ticker}     # Precio actual ticker
GET  /dashboard?fecha=   # Datos dashboard principal
POST /analyze            # Analizar ticker específico
GET  /analyze-all        # Analizar todos los tickers
POST /refresh-prices     # Actualizar precios manualmente
GET  /prices/all         # Todos los precios desde cache
POST /clear-analysis-cache  # Limpiar cache análisis
```

#### Base de Datos SQLite:
- **trading_dashboard.db**: Base principal
- **Tablas**:
  - `trades`: Información de trades
  - `configuracion`: Configuración global
  - `precios_cache`: Cache de precios (actualizado cada 5min)
  - `analisis_cache`: Cache de análisis (1 hora TTL)

#### Clases de Análisis:
- **TradeAnalyzer**: Análisis de trades VIX_Fix
- **VixFixStrategy**: Implementación estrategia VIX_Fix

### 🔧 Dependencias Backend:
- FastAPI
- Uvicorn (servidor ASGI)
- yfinance (datos financieros)
- pandas (manipulación datos)
- sqlite3 (base de datos)
- pydantic (validación datos)

## 📈 SCRIPTS DE ANÁLISIS

### `trade_analyzer.py`
- **Clase**: TradeAnalyzer
- **Función**: Análisis de trades con estrategia VIX_Fix
- **Métodos principales**:
  - analizar_trades(ticker, fecha_inicio, fecha_fin)
  - calcular_metricas()

### `vix_fix_strategy.py`
- **Clase**: VixFixStrategy
- **Función**: Implementación estrategia VIX_Fix
- **Parámetros**: Configurables según estrategia

### `analizar_ticker.py`
- **Función**: Script original de análisis
- **Uso**: Análisis individual de tickers

### `ticker_data.py`
- **Función**: Definición y gestión de datos de tickers
- **Contenido**: Lista de tickers, categorías, metadatos

## 🚀 SCRIPTS DE EJECUCIÓN

### Windows:
- `start_all.bat`: Inicia backend y frontend
- `start_backend.bat`: Solo backend
- `start_frontend.bat`: Solo frontend

### Linux:
- `start_all.sh`: Inicia backend y frontend
- `start_backend.sh`: Solo backend
- `start_frontend.sh`: Solo frontend

## 🔄 FLUJO DE DATOS

1. **Frontend** solicita datos vía `tradingAPI`
2. **Backend** consulta cache o calcula análisis
3. **TradeAnalyzer** procesa datos con **VixFixStrategy**
4. **Base de datos** almacena/consulta cache y resultados
5. **Auto-refresh** actualiza datos cada 30 segundos

## 🎯 FUNCIONALIDADES PRINCIPALES

### Dashboard Principal:
- **Trades Abiertos**: Lista de posiciones activas
- **Métricas**: Total trades, éxito, P&L, días promedio
- **Precios en Tiempo Real**: Actualización automática
- **Estados**: ABIERTO, TARGET_ALCANZADO

### Análisis por Fecha:
- **Selector flexible**: Desde fecha específica hasta hoy
- **Opciones rápidas**: 1 semana, 1 mes, 3 meses
- **Análisis histórico**: Backtesting completo

### Control de Actualización:
- **Auto-refresh configurable**: 15s a 5min
- **Refresh manual**: Bajo demanda
- **Indicador de estado**: Última actualización

## 🔐 CONFIGURACIÓN Y PERSONALIZACIÓN

### Cambio de Target de Profit:
```python
# backend/main.py línea 47
DEFAULT_PROFIT_TARGET = 0.04  # Cambiar por valor deseado
```

### Agregar Nuevos Tickers:
```python
# backend/main.py línea 51-70
MAIN_TICKERS = [
    # Agregar nuevos tickers aquí
]
```

### Cambio de Intervalos Frontend:
```typescript
// src/App.tsx línea 23
const [refreshInterval, setRefreshInterval] = useState<number>(30000);
```

## 🎨 MANTENIMIENTO DE ESTILOS

### Al Agregar Nuevos Estilos Globales:
1. Editar `frontend/src/index.css`
2. Agregar nuevas clases CSS
3. **ACTUALIZAR** esta sección en estructura_proyecto.md
4. Documentar nuevos colores/variables aquí

### Al Crear Nuevos Componentes:
1. Revisar estilos existentes en `index.css`
2. Usar clases predefinidas (trading-card, trading-button, etc.)
3. NO crear colores hardcodeados
4. Documentar nuevos componentes en este archivo

## 🔍 DEBUGGING Y LOGS

### Backend:
- Logs de actualización de precios cada 5 minutos
- Error handling por ticker individual
- Health check endpoint

### Frontend:
- Console.error para errores de API
- Estado de conexión API visible
- Indicadores de loading por operación

## 🚀 SISTEMA EOD OPTIMIZADO - NUEVA ARQUITECTURA

### 📊 **Tabla Principal: market_data_eod**
```sql
-- OHLCV diario con quality control
CREATE TABLE market_data_eod (
    symbol TEXT NOT NULL,
    business_date DATE NOT NULL,
    open_price, high_price, low_price, close_price DECIMAL(12,4),
    volume BIGINT,
    data_quality_score INTEGER DEFAULT 100,  -- 0-100
    anomaly_flags TEXT,  -- JSON con flags de calidad
    UNIQUE(symbol, business_date)
);
```

### ⚡ **Job EOD Automatizado**
- **Frecuencia**: Una vez al día (post-mercado)
- **Validación automática**: OHLC sequence, continuity, anomalies
- **Manejo de errores**: Tracking por símbolo, recovery automático
- **Quality scoring**: 0-100 por cada registro

### 🔍 **Sistema de Integridad**
- **Gap detection**: Identifica días faltantes
- **Data repair**: Recuperación automática de gaps
- **Quality monitoring**: Alertas de datos sospechosos
- **Audit trail**: Logs completos de procesamiento

### 📱 **Nuevos Endpoints API**
```python
POST /run-eod-job              # Ejecutar job EOD manual
GET  /eod-job-status           # Status de jobs por fecha
GET  /data-integrity-check     # Verificar integridad de datos
POST /repair-data-gaps         # Reparar gaps específicos
GET  /market-data-stats        # Estadísticas generales
```

### 🎯 **TradeAnalyzer Híbrido**
- **BD Local primero**: Lee desde market_data_eod (súper rápido)
- **Fallback automático**: yfinance si faltan datos
- **Compatibilidad total**: Misma API que antes
- **Performance**: 50x más rápido para análisis

### 🛡️ **Validaciones de Calidad**
```python
# Automáticas por cada dato:
- OHLC sequence válida (Low ≤ Open,Close ≤ High)
- Precios positivos
- Continuidad de precios (gaps <20%)
- Volatilidad extrema (>50% cambio)
- Volumen negativo
```

## 📝 ÚLTIMA ACTUALIZACIÓN

**Fecha**: 2025-08-16
**Versión**: 2.0.0 - Sistema EOD Optimizado
**Cambios**: 
- Nueva tabla market_data_eod con quality control
- Job EOD automatizado con validaciones
- Sistema híbrido BD local + yfinance fallback
- API de integridad y recuperación de datos
- Performance 50x mejorada para análisis

---

**NOTA IMPORTANTE**: Este archivo debe actualizarse cada vez que se modifique la estructura del proyecto, se agreguen nuevos componentes, se cambien estilos globales o se modifiquen configuraciones principales.