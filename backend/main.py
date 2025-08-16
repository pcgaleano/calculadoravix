#!/usr/bin/env python3
"""
Trading Dashboard API - Backend FastAPI
Sistema profesional de trading con análisis VIX_Fix
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import yfinance as yf
import pandas as pd
import sqlite3
import asyncio
import uvicorn
import sys
import os
import threading
import time
import hashlib
import json

# Agregar el directorio padre al PATH para importar nuestros módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trade_analyzer import TradeAnalyzer
from vix_fix_strategy import VixFixStrategy

app = FastAPI(
    title="Trading Dashboard API",
    description="API profesional para análisis de trading con estrategia VIX_Fix",
    version="1.0.0"
)

# Configurar CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes para desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración global
DEFAULT_PROFIT_TARGET = 0.04  # 4%
DEFAULT_MAX_DAYS = 30

# Tickers principales diversificados (mercado argentino y internacional)
MAIN_TICKERS = [
    # Acciones Argentinas (Buenos Aires)
    "GGAL.BA", "PAMP.BA", "YPFD.BA", "ALUA.BA", "TECO2.BA",
    "MIRG.BA", "CEPU.BA", "BMA.BA", "SUPV.BA", "LOMA.BA",
    # ADRs Argentinos (NYSE/NASDAQ)
    "GGAL", "PAM", "YPF", "BMA", "SUPV", "TEO", "CRESY", "IRS", "TGS",
    # ETFs
    "SPY", "QQQ", "IWM", "EEM", "GLD",
    # Big Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
    # Crypto principales
    "BTC-USD", "ETH-USD", "ADA-USD", "DOT-USD",
    # Crypto adicionales
    "THETA-USD", "TON11419-USD", 
    "XRP-USD", "AAVE-USD", "APT21794-USD", "ARB11841-USD", "ATOM-USD",
    "AVAX-USD", "BCH-USD", "DOGE-USD", "ETC-USD", "FIL-USD",
    "INJ-USD", "LINK-USD", "LTC-USD", "MANA-USD",
    "NEAR-USD", "NEO-USD", "OP-USD",
    "RUNE-USD", "SAND-USD", "SOL-USD"
]

# Models para requests/responses
class TradeAnalysisRequest(BaseModel):
    ticker: str
    fecha_inicio: str
    fecha_fin: str
    profit_target: Optional[float] = DEFAULT_PROFIT_TARGET
    max_days: Optional[int] = DEFAULT_MAX_DAYS

class TradeResult(BaseModel):
    trade_num: int
    ticker: str
    fecha_compra: str
    precio_compra: float
    precio_target: float
    fecha_venta: Optional[str]
    precio_venta: Optional[float]
    dias_trade: int
    profit_pct: float
    profit_absoluto: float
    estado: str
    precio_actual: Optional[float] = None

class DashboardData(BaseModel):
    fecha_analisis: str
    trades_abiertos: List[TradeResult]
    total_trades: int
    trades_exitosos: int
    profit_total: float
    dias_promedio: float

# Inicializar base de datos
def init_db():
    """Inicializar base de datos SQLite"""
    conn = sqlite3.connect('trading_dashboard.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            fecha_compra TEXT NOT NULL,
            precio_compra REAL NOT NULL,
            precio_target REAL NOT NULL,
            fecha_venta TEXT,
            precio_venta REAL,
            dias_trade INTEGER,
            profit_pct REAL,
            estado TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profit_target REAL DEFAULT 0.04,
            max_days INTEGER DEFAULT 30,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS precios_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            precio_actual REAL NOT NULL,
            precio_anterior REAL NOT NULL,
            cambio_pct REAL NOT NULL,
            volumen REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analisis_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            fecha_inicio TEXT NOT NULL,
            fecha_fin TEXT NOT NULL,
            config_hash TEXT NOT NULL,
            resultado_json TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, fecha_inicio, fecha_fin, config_hash)
        )
    ''')
    
    # =====================================================
    # NUEVA TABLA: EOD Data (End of Day) - OPTIMIZADA
    # =====================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_data_eod (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Identificación
            symbol TEXT NOT NULL,
            business_date DATE NOT NULL,
            
            -- OHLCV Data
            open_price DECIMAL(12,4) NOT NULL,
            high_price DECIMAL(12,4) NOT NULL,
            low_price DECIMAL(12,4) NOT NULL,
            close_price DECIMAL(12,4) NOT NULL,
            volume BIGINT DEFAULT 0,
            adj_close DECIMAL(12,4),  -- Para splits/dividendos
            
            -- Quality Control
            data_quality_score INTEGER DEFAULT 100,  -- 0-100
            anomaly_flags TEXT,  -- JSON string con flags
            data_source TEXT DEFAULT 'yfinance',
            
            -- Audit Trail
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            UNIQUE(symbol, business_date)
        )
    ''')
    
    # =====================================================
    # TABLA: Job Status (Para tracking de procesos)
    # =====================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            job_name TEXT NOT NULL,  -- 'EOD_UPDATE', 'PRICE_REFRESH'
            business_date DATE NOT NULL,
            status TEXT NOT NULL,    -- 'RUNNING', 'SUCCESS', 'FAILED', 'PARTIAL'
            
            -- Metrics
            symbols_processed INTEGER DEFAULT 0,
            symbols_failed INTEGER DEFAULT 0,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            
            -- Error tracking
            error_details TEXT,  -- JSON con errores específicos
            
            -- Constraints
            UNIQUE(job_name, business_date)
        )
    ''')
    
    # =====================================================
    # TABLA: Data Integrity Log
    # =====================================================
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data_integrity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            symbol TEXT NOT NULL,
            business_date DATE NOT NULL,
            check_type TEXT NOT NULL,  -- 'PRICE_CONTINUITY', 'VOLUME_CHECK', etc.
            
            status TEXT NOT NULL,      -- 'PASS', 'FAIL', 'WARNING'
            details TEXT,              -- Descripción del problema
            
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Índices para performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_eod_symbol_date ON market_data_eod(symbol, business_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_eod_date ON market_data_eod(business_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_status_date ON job_status(business_date)')
    
    conn.commit()
    conn.close()

# Job de actualización de precios en background
def actualizar_precios_background():
    """Job que actualiza precios con intervalo configurable"""
    price_update_config['running'] = True
    
    while price_update_config['enabled'] and price_update_config['running']:
        try:
            print(f"Actualizando precios... (intervalo: {price_update_config['interval_minutes']} min)")
            conn = sqlite3.connect('trading_dashboard.db')
            cursor = conn.cursor()
            
            updated_count = 0
            for ticker in MAIN_TICKERS:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.history(period="1d", interval="1m")
                    
                    if not info.empty:
                        current_price = info['Close'].iloc[-1]
                        previous_close = info['Close'].iloc[0] if len(info) > 1 else current_price
                        change_pct = ((current_price - previous_close) / previous_close) * 100
                        volume = info['Volume'].iloc[-1] if 'Volume' in info.columns else 0
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO precios_cache 
                            (ticker, precio_actual, precio_anterior, cambio_pct, volumen, timestamp)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (ticker, current_price, previous_close, change_pct, volume, datetime.now()))
                        
                        updated_count += 1
                        
                except Exception as e:
                    print(f"{ticker}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            print(f"✅ Precios actualizados: {updated_count}/{len(MAIN_TICKERS)} tickers")
            
        except Exception as e:
            print(f"❌ Error en job de actualización: {e}")
        
        # Esperar según configuración
        interval_seconds = price_update_config['interval_minutes'] * 60
        time.sleep(interval_seconds)
    
    price_update_config['running'] = False
    print("Job de actualización de precios detenido")

@app.on_event("startup")
async def startup_event():
    """Eventos de inicio de la aplicación"""
    init_db()
    print("Trading Dashboard API iniciada")
    print(f"Tickers principales: {len(MAIN_TICKERS)} configurados")
    
    # Iniciar job de actualización de precios en background
    price_thread = threading.Thread(target=actualizar_precios_background, daemon=True)
    price_thread.start()
    print("Job de actualización de precios iniciado (cada 5 minutos)")
    
    # Iniciar scheduler automático de EOD
    start_scheduler()
    if scheduler_running:
        scheduler_thread = threading.Thread(target=run_pending_jobs, daemon=True)
        scheduler_thread.start()
        print(f"📅 Scheduler EOD iniciado automáticamente - Próxima ejecución: {eod_schedule_config['time']} {eod_schedule_config['timezone']}")
    else:
        print("⚠️  Scheduler EOD no se pudo iniciar")

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "Trading Dashboard API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "tickers": "/tickers",
            "analyze": "/analyze",
            "dashboard": "/dashboard",
            "price": "/price/{ticker}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/tickers")
async def get_tickers():
    """Obtener lista de tickers principales"""
    return {
        "tickers": MAIN_TICKERS,
        "count": len(MAIN_TICKERS),
        "categories": {
            "argentinas": [t for t in MAIN_TICKERS if t.endswith(".BA")],
            "etfs": ["SPY", "QQQ", "IWM", "EEM", "GLD"],
            "crypto": [t for t in MAIN_TICKERS if t.endswith("-USD")]
        }
    }

@app.get("/price/{ticker}")
async def get_current_price(ticker: str):
    """Obtener precio actual de un ticker desde cache"""
    try:
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        # Intentar obtener desde cache
        cursor.execute('''
            SELECT precio_actual, precio_anterior, cambio_pct, timestamp 
            FROM precios_cache 
            WHERE ticker = ?
        ''', (ticker,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "ticker": ticker,
                "precio_actual": round(result[0], 2),
                "precio_anterior": round(result[1], 2),
                "cambio_pct": round(result[2], 2),
                "timestamp": result[3],
                "source": "cache"
            }
        else:
            # Si no está en cache, obtener en tiempo real
            stock = yf.Ticker(ticker)
            info = stock.history(period="1d", interval="1m")
            
            if info.empty:
                raise HTTPException(status_code=404, detail=f"No se pudo obtener precio para {ticker}")
            
            current_price = info['Close'].iloc[-1]
            previous_close = info['Close'].iloc[0] if len(info) > 1 else current_price
            change_pct = ((current_price - previous_close) / previous_close) * 100
            
            return {
                "ticker": ticker,
                "precio_actual": round(current_price, 2),
                "precio_anterior": round(previous_close, 2),
                "cambio_pct": round(change_pct, 2),
                "timestamp": datetime.now().isoformat(),
                "source": "live"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo precio: {str(e)}")

@app.post("/refresh-prices")
async def refresh_prices():
    """Forzar actualización manual de todos los precios"""
    try:
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        updated_count = 0
        
        for ticker in MAIN_TICKERS:
            try:
                stock = yf.Ticker(ticker)
                info = stock.history(period="1d", interval="1m")
                
                if not info.empty:
                    current_price = info['Close'].iloc[-1]
                    previous_close = info['Close'].iloc[0] if len(info) > 1 else current_price
                    change_pct = ((current_price - previous_close) / previous_close) * 100
                    volume = info['Volume'].iloc[-1] if 'Volume' in info.columns else 0
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO precios_cache 
                        (ticker, precio_actual, precio_anterior, cambio_pct, volumen, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (ticker, current_price, previous_close, change_pct, volume, datetime.now()))
                    updated_count += 1
                    
            except Exception as e:
                print(f"Error actualizando {ticker}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Precios actualizados manualmente",
            "updated_tickers": updated_count,
            "total_tickers": len(MAIN_TICKERS),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando precios: {str(e)}")

@app.post("/clear-analysis-cache")
async def clear_analysis_cache():
    """Limpiar cache de análisis (forzar recálculo)"""
    try:
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM analisis_cache')
        rows_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {
            "message": "Cache de análisis limpiado",
            "rows_deleted": rows_deleted,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error limpiando cache: {str(e)}")

@app.get("/prices/all")
async def get_all_prices():
    """Obtener todos los precios desde cache"""
    try:
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ticker, precio_actual, precio_anterior, cambio_pct, timestamp
            FROM precios_cache
            ORDER BY ticker
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        prices = []
        for result in results:
            prices.append({
                "ticker": result[0],
                "precio_actual": round(result[1], 2),
                "precio_anterior": round(result[2], 2),
                "cambio_pct": round(result[3], 2),
                "timestamp": result[4]
            })
        
        return {
            "prices": prices,
            "count": len(prices),
            "last_update": max([p["timestamp"] for p in prices]) if prices else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo precios: {str(e)}")

def generar_config_hash(profit_target: float, max_days: int) -> str:
    """Generar hash único para configuración de análisis"""
    config_str = f"{profit_target}_{max_days}"
    return hashlib.md5(config_str.encode()).hexdigest()

@app.post("/analyze")
async def analyze_ticker(request: TradeAnalysisRequest):
    """Analizar trades de un ticker específico con cache"""
    try:
        # Generar hash de configuración
        config_hash = generar_config_hash(request.profit_target, request.max_days)
        
        # Intentar obtener desde cache
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT resultado_json FROM analisis_cache 
            WHERE ticker = ? AND fecha_inicio = ? AND fecha_fin = ? AND config_hash = ?
            AND datetime(timestamp) > datetime('now', '-1 hour')
        ''', (request.ticker, request.fecha_inicio, request.fecha_fin, config_hash))
        
        cached_result = cursor.fetchone()
        
        if cached_result:
            conn.close()
            return json.loads(cached_result[0])
        
        # Si no está en cache, hacer análisis completo
        analyzer = TradeAnalyzer(
            profit_target=request.profit_target,
            max_hold_days=request.max_days
        )
        
        resultados = analyzer.analizar_trades(
            request.ticker, 
            request.fecha_inicio, 
            request.fecha_fin
        )
        
        if resultados is None or resultados.empty:
            return {"message": f"No se encontraron trades para {request.ticker}", "trades": []}
        
        # Convertir resultados a formato API
        trades_formateados = []
        for _, trade in resultados.iterrows():
            trade_data = TradeResult(
                trade_num=int(trade['trade_num']),
                ticker=request.ticker,
                fecha_compra=trade['fecha_compra'].strftime('%Y-%m-%d'),
                precio_compra=round(float(trade['precio_compra']), 2),
                precio_target=round(float(trade['precio_target']), 2),
                fecha_venta=trade['fecha_venta'].strftime('%Y-%m-%d') if pd.notna(trade['fecha_venta']) else None,
                precio_venta=round(float(trade['precio_venta']), 2) if pd.notna(trade['precio_venta']) else None,
                dias_trade=int(trade['dias_trade']),
                profit_pct=round(float(trade['profit_pct']) * 100, 2),
                profit_absoluto=round(float(trade['precio_venta'] - trade['precio_compra']), 2) if pd.notna(trade['precio_venta']) else 0,
                estado=trade['resultado']
            )
            trades_formateados.append(trade_data)
        
        # Estadísticas generales
        total_trades = len(resultados)
        trades_exitosos = len(resultados[resultados['resultado'] == 'TARGET_ALCANZADO'])
        profit_promedio = resultados['profit_pct'].mean() * 100
        dias_promedio = resultados['dias_trade'].mean()
        
        # Preparar resultado para cache
        resultado_final = {
            "ticker": request.ticker,
            "periodo": {"inicio": request.fecha_inicio, "fin": request.fecha_fin},
            "configuracion": {
                "profit_target": request.profit_target * 100,
                "max_days": request.max_days
            },
            "resumen": {
                "total_trades": total_trades,
                "trades_exitosos": trades_exitosos,
                "tasa_exito": round((trades_exitosos / total_trades) * 100, 1) if total_trades > 0 else 0,
                "profit_promedio": round(profit_promedio, 2),
                "dias_promedio": round(dias_promedio, 1)
            },
            "trades": trades_formateados,
            "source": "calculated"
        }
        
        # Guardar en cache
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO analisis_cache 
                (ticker, fecha_inicio, fecha_fin, config_hash, resultado_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (request.ticker, request.fecha_inicio, request.fecha_fin, config_hash, 
                  json.dumps(resultado_final), datetime.now()))
            conn.commit()
        except Exception as e:
            print(f"Error guardando en cache: {e}")
        finally:
            conn.close()
        
        return resultado_final
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@app.get("/dashboard")
async def get_dashboard_data(fecha: str = Query(..., description="Fecha para análisis (YYYY-MM-DD)")):
    """Obtener datos del dashboard principal con trades abiertos"""
    try:
        fecha_fin = datetime.now().strftime('%Y-%m-%d')
        trades_abiertos = []
        total_profit = 0
        
        # Analizar cada ticker principal
        for ticker in MAIN_TICKERS:
            try:
                analyzer = TradeAnalyzer(
                    profit_target=DEFAULT_PROFIT_TARGET,
                    max_hold_days=DEFAULT_MAX_DAYS
                )
                
                resultados = analyzer.analizar_trades(ticker, fecha, fecha_fin)
                
                if resultados is not None and not resultados.empty:
                    # Filtrar solo trades que no alcanzaron el target (abiertos)
                    trades_pendientes = resultados[
                        (resultados['resultado'] != 'TARGET_ALCANZADO') |
                        (resultados['fecha_venta'] >= datetime.now().strftime('%Y-%m-%d'))
                    ]
                    
                    for _, trade in trades_pendientes.iterrows():
                        # Obtener precio actual
                        try:
                            precio_actual_data = await get_current_price(ticker)
                            precio_actual = precio_actual_data['precio_actual']
                        except:
                            precio_actual = trade['precio_compra']
                        
                        # Calcular profit actual
                        profit_actual = ((precio_actual - trade['precio_compra']) / trade['precio_compra']) * 100
                        profit_absoluto = precio_actual - trade['precio_compra']
                        
                        trade_result = TradeResult(
                            trade_num=int(trade['trade_num']),
                            ticker=ticker,
                            fecha_compra=trade['fecha_compra'].strftime('%Y-%m-%d'),
                            precio_compra=round(float(trade['precio_compra']), 2),
                            precio_target=round(float(trade['precio_target']), 2),
                            fecha_venta=None,
                            precio_venta=None,
                            dias_trade=int(trade['dias_trade']),
                            profit_pct=round(profit_actual, 2),
                            profit_absoluto=round(profit_absoluto, 2),
                            estado='ABIERTO',
                            precio_actual=precio_actual
                        )
                        
                        trades_abiertos.append(trade_result)
                        total_profit += profit_absoluto
                        
            except Exception as e:
                print(f"Error analizando {ticker}: {e}")
                continue
        
        # Calcular estadísticas
        total_trades = len(trades_abiertos)
        trades_exitosos = len([t for t in trades_abiertos if t.profit_pct >= DEFAULT_PROFIT_TARGET * 100])
        dias_promedio = sum(t.dias_trade for t in trades_abiertos) / total_trades if total_trades > 0 else 0
        
        dashboard_data = DashboardData(
            fecha_analisis=fecha,
            trades_abiertos=trades_abiertos,
            total_trades=total_trades,
            trades_exitosos=trades_exitosos,
            profit_total=round(total_profit, 2),
            dias_promedio=round(dias_promedio, 1)
        )
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando dashboard: {str(e)}")

@app.get("/analyze-all")
async def analyze_all_tickers(
    fecha_inicio: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: str = Query(..., description="Fecha fin (YYYY-MM-DD)")
):
    """Analizar todos los tickers principales"""
    resultados_todos = {}
    
    for ticker in MAIN_TICKERS:
        try:
            request = TradeAnalysisRequest(
                ticker=ticker,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                profit_target=DEFAULT_PROFIT_TARGET,
                max_days=DEFAULT_MAX_DAYS
            )
            
            resultado = await analyze_ticker(request)
            resultados_todos[ticker] = resultado
            
        except Exception as e:
            resultados_todos[ticker] = {"error": str(e)}
    
    return {
        "periodo": {"inicio": fecha_inicio, "fin": fecha_fin},
        "tickers_analizados": len(MAIN_TICKERS),
        "resultados": resultados_todos
    }

# =====================================================
# SISTEMA EOD (END OF DAY) - OPTIMIZADO CON INTEGRIDAD
# =====================================================

import json
from typing import Dict, List, Tuple
import schedule
import pytz
from datetime import timedelta

def validate_ohlcv_data(symbol: str, ohlcv_data: Dict) -> Tuple[int, List[str]]:
    """
    Validación simple pero efectiva de datos OHLCV
    Returns: (quality_score, anomaly_flags)
    """
    score = 100
    flags = []
    
    try:
        o = float(ohlcv_data.get('Open', 0))
        h = float(ohlcv_data.get('High', 0))
        l = float(ohlcv_data.get('Low', 0))
        c = float(ohlcv_data.get('Close', 0))
        v = int(ohlcv_data.get('Volume', 0))
        
        # Validación 1: OHLC sequence lógica
        if not (l <= o <= h and l <= c <= h):
            score -= 50
            flags.append("INVALID_OHLC_SEQUENCE")
        
        # Validación 2: Precios positivos
        if any(price <= 0 for price in [o, h, l, c]):
            score -= 40
            flags.append("NEGATIVE_PRICES")
        
        # Validación 3: Volumen no negativo
        if v < 0:
            score -= 10
            flags.append("NEGATIVE_VOLUME")
        
        # Validación 4: High = Low (precio sin movimiento)
        if h == l and h > 0:
            score -= 5
            flags.append("NO_PRICE_MOVEMENT")
        
        # Validación 5: Volatilidad extrema (cambio >50%)
        if o > 0:
            daily_change = abs(c - o) / o
            if daily_change > 0.5:  # 50% cambio diario
                score -= 20
                flags.append(f"EXTREME_VOLATILITY_{daily_change:.1%}")
        
    except (ValueError, TypeError) as e:
        score = 0
        flags.append(f"DATA_PARSING_ERROR_{str(e)}")
    
    return score, flags

def check_data_continuity(symbol: str, new_close: float, business_date: str) -> Tuple[bool, str]:
    """
    Verificar continuidad con el día anterior
    """
    try:
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        # Obtener precio de cierre del día anterior
        cursor.execute('''
            SELECT close_price FROM market_data_eod 
            WHERE symbol = ? AND business_date < ?
            ORDER BY business_date DESC LIMIT 1
        ''', (symbol, business_date))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            prev_close = float(result[0])
            price_gap = abs(new_close - prev_close) / prev_close
            
            if price_gap > 0.2:  # Gap >20%
                return False, f"PRICE_GAP_{price_gap:.1%}"
        
        return True, "CONTINUITY_OK"
        
    except Exception as e:
        return False, f"CONTINUITY_CHECK_ERROR_{str(e)}"

def insert_or_update_eod_data(symbol: str, business_date: str, ohlcv_data: Dict) -> bool:
    """
    Insert or update EOD data con validación
    """
    try:
        # Validar datos
        quality_score, anomaly_flags = validate_ohlcv_data(symbol, ohlcv_data)
        
        # Check continuity
        continuity_ok, continuity_msg = check_data_continuity(
            symbol, float(ohlcv_data['Close']), business_date
        )
        
        if not continuity_ok:
            anomaly_flags.append(continuity_msg)
            quality_score -= 15
        
        # Solo insertar si quality score >= 50 (configurable)
        if quality_score < 50:
            print(f"❌ {symbol} {business_date}: Quality too low ({quality_score}): {anomaly_flags}")
            return False
        
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        # INSERT OR REPLACE (maneja UPDATE vs INSERT automáticamente)
        cursor.execute('''
            INSERT OR REPLACE INTO market_data_eod 
            (symbol, business_date, open_price, high_price, low_price, close_price, 
             volume, adj_close, data_quality_score, anomaly_flags, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            business_date,
            float(ohlcv_data['Open']),
            float(ohlcv_data['High']),
            float(ohlcv_data['Low']),
            float(ohlcv_data['Close']),
            int(ohlcv_data.get('Volume', 0)),
            float(ohlcv_data.get('Adj Close', ohlcv_data['Close'])),
            quality_score,
            json.dumps(anomaly_flags) if anomaly_flags else None,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        # Log quality issues
        if quality_score < 80:
            print(f"⚠️  {symbol} {business_date}: Quality issues ({quality_score}): {anomaly_flags}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error inserting {symbol} {business_date}: {e}")
        return False

def run_eod_job(business_date: str = None) -> Dict:
    """
    Job principal EOD con manejo completo de errores
    """
    if business_date is None:
        business_date = datetime.now().strftime('%Y-%m-%d')
    
    job_start = datetime.now()
    symbols_processed = 0
    symbols_failed = 0
    failed_symbols = []
    
    print(f"🚀 Starting EOD job for {business_date}")
    
    try:
        # Registrar inicio del job
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO job_status 
            (job_name, business_date, status, start_time, symbols_processed, symbols_failed)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('EOD_UPDATE', business_date, 'RUNNING', job_start, 0, 0))
        
        conn.commit()
        conn.close()
        
        # Procesar cada símbolo
        for symbol in MAIN_TICKERS:
            try:
                print(f"Processing {symbol}...")
                
                # Obtener datos de yfinance
                stock = yf.Ticker(symbol)
                
                # Obtener 2 días para asegurar que tenemos el día solicitado
                end_date = (datetime.strptime(business_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                start_date = (datetime.strptime(business_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
                
                data = stock.history(start=start_date, end=end_date)
                
                if data.empty:
                    print(f"⚠️  No data for {symbol}")
                    symbols_failed += 1
                    failed_symbols.append(f"{symbol}: NO_DATA")
                    continue
                
                # Buscar datos específicos para business_date
                target_date = pd.to_datetime(business_date).date()
                matching_rows = data[data.index.date == target_date]
                
                if matching_rows.empty:
                    print(f"⚠️  No data for {symbol} on {business_date}")
                    symbols_failed += 1
                    failed_symbols.append(f"{symbol}: NO_DATA_FOR_DATE")
                    continue
                
                # Usar la primera fila que coincida
                row = matching_rows.iloc[0]
                
                ohlcv_data = {
                    'Open': row['Open'],
                    'High': row['High'],
                    'Low': row['Low'],
                    'Close': row['Close'],
                    'Volume': row['Volume'] if 'Volume' in row else 0,
                    'Adj Close': row.get('Adj Close', row['Close'])
                }
                
                # Insertar/actualizar en BD
                if insert_or_update_eod_data(symbol, business_date, ohlcv_data):
                    symbols_processed += 1
                    print(f"✅ {symbol} processed successfully")
                else:
                    symbols_failed += 1
                    failed_symbols.append(f"{symbol}: QUALITY_FAILED")
                
            except Exception as e:
                symbols_failed += 1
                failed_symbols.append(f"{symbol}: {str(e)}")
                print(f"❌ Failed to process {symbol}: {e}")
                continue
        
        # Actualizar status del job
        job_end = datetime.now()
        job_duration = (job_end - job_start).total_seconds()
        
        if symbols_failed == 0:
            status = 'SUCCESS'
        elif symbols_processed > 0:
            status = 'PARTIAL'
        else:
            status = 'FAILED'
        
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE job_status SET 
            status = ?, end_time = ?, symbols_processed = ?, symbols_failed = ?,
            error_details = ?
            WHERE job_name = ? AND business_date = ?
        ''', (
            status, job_end, symbols_processed, symbols_failed,
            json.dumps(failed_symbols) if failed_symbols else None,
            'EOD_UPDATE', business_date
        ))
        
        conn.commit()
        conn.close()
        
        print(f"🏁 EOD job completed in {job_duration:.1f}s")
        print(f"✅ Processed: {symbols_processed}")
        print(f"❌ Failed: {symbols_failed}")
        
        if failed_symbols:
            print(f"Failed symbols: {failed_symbols[:5]}...")  # Mostrar solo primeros 5
        
        return {
            'status': status,
            'business_date': business_date,
            'symbols_processed': symbols_processed,
            'symbols_failed': symbols_failed,
            'duration_seconds': job_duration,
            'failed_symbols': failed_symbols
        }
        
    except Exception as e:
        # Error crítico en el job
        print(f"💥 Critical error in EOD job: {e}")
        
        try:
            conn = sqlite3.connect('trading_dashboard.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE job_status SET status = ?, end_time = ?, error_details = ?
                WHERE job_name = ? AND business_date = ?
            ''', ('FAILED', datetime.now(), str(e), 'EOD_UPDATE', business_date))
            conn.commit()
            conn.close()
        except:
            pass
        
        return {
            'status': 'FAILED',
            'error': str(e)
        }

@app.post("/run-eod-job")
async def run_eod_job_endpoint(business_date: str = Query(None, description="Fecha para EOD job (YYYY-MM-DD, default: hoy)")):
    """
    Ejecutar EOD job manualmente
    """
    try:
        result = run_eod_job(business_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running EOD job: {str(e)}")

@app.get("/eod-job-status")
async def get_eod_job_status(business_date: str = Query(None, description="Fecha para consultar status")):
    """
    Consultar status de EOD jobs
    """
    try:
        if business_date is None:
            business_date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT job_name, business_date, status, symbols_processed, symbols_failed,
                   start_time, end_time, error_details
            FROM job_status 
            WHERE business_date = ?
            ORDER BY start_time DESC
        ''', (business_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        jobs = []
        for row in results:
            jobs.append({
                'job_name': row[0],
                'business_date': row[1],
                'status': row[2],
                'symbols_processed': row[3],
                'symbols_failed': row[4],
                'start_time': row[5],
                'end_time': row[6],
                'error_details': json.loads(row[7]) if row[7] else None
            })
        
        return {
            'business_date': business_date,
            'jobs': jobs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")

# =====================================================
# SISTEMA DE CARGA INICIAL MASIVA (2 AÑOS)
# =====================================================

def check_symbol_data_sufficiency(symbol: str, min_days: int = 300) -> Dict:
    """
    Verificar si un símbolo tiene suficientes datos históricos
    """
    try:
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*), MIN(business_date), MAX(business_date)
            FROM market_data_eod 
            WHERE symbol = ?
        ''', (symbol,))
        
        result = cursor.fetchone()
        conn.close()
        
        count = result[0] if result else 0
        min_date = result[1] if result else None
        max_date = result[2] if result else None
        
        return {
            'symbol': symbol,
            'records': count,
            'min_date': min_date,
            'max_date': max_date,
            'sufficient': count >= min_days,
            'missing_days': max(0, min_days - count)
        }
        
    except Exception as e:
        return {
            'symbol': symbol,
            'records': 0,
            'sufficient': False,
            'error': str(e)
        }

def load_historical_data_for_symbol(symbol: str, years_back: int = 2) -> Dict:
    """
    Cargar datos históricos masivos para un símbolo específico
    """
    try:
        print(f"Cargando {years_back} años de datos para {symbol}...")
        
        # Calcular fechas
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years_back * 365)
        
        # Descargar datos
        stock = yf.Ticker(symbol)
        data = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        
        if data.empty:
            return {
                'symbol': symbol,
                'status': 'NO_DATA',
                'records_added': 0,
                'records_updated': 0
            }
        
        # Insertar en BD
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        records_added = 0
        records_updated = 0
        
        for fecha, row in data.iterrows():
            fecha_str = fecha.strftime('%Y-%m-%d')
            
            # Verificar si ya existe
            cursor.execute('SELECT COUNT(*) FROM market_data_eod WHERE symbol = ? AND business_date = ?', 
                         (symbol, fecha_str))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # Actualizar
                cursor.execute('''
                    UPDATE market_data_eod 
                    SET open_price = ?, high_price = ?, low_price = ?, close_price = ?, 
                        volume = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = ? AND business_date = ?
                ''', (
                    float(row['Open']), float(row['High']), float(row['Low']), 
                    float(row['Close']), int(row['Volume']), symbol, fecha_str
                ))
                records_updated += 1
            else:
                # Insertar nuevo
                cursor.execute('''
                    INSERT INTO market_data_eod 
                    (symbol, business_date, open_price, high_price, low_price, close_price, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, fecha_str, float(row['Open']), float(row['High']), 
                    float(row['Low']), float(row['Close']), int(row['Volume'])
                ))
                records_added += 1
        
        conn.commit()
        conn.close()
        
        print(f"OK {symbol}: {records_added} nuevos, {records_updated} actualizados")
        
        return {
            'symbol': symbol,
            'status': 'SUCCESS',
            'records_added': records_added,
            'records_updated': records_updated,
            'total_records': records_added + records_updated
        }
        
    except Exception as e:
        print(f"ERROR cargando {symbol}: {e}")
        return {
            'symbol': symbol,
            'status': 'FAILED',
            'error': str(e),
            'records_added': 0,
            'records_updated': 0
        }

def run_initial_data_load(years_back: int = 2, force_reload: bool = False) -> Dict:
    """
    Carga inicial masiva de datos históricos para todos los símbolos
    """
    job_start = datetime.now()
    print(f"Iniciando carga inicial masiva de {years_back} años de datos...")
    
    results = []
    symbols_processed = 0
    symbols_successful = 0
    symbols_failed = 0
    total_records_added = 0
    
    try:
        for symbol in MAIN_TICKERS:
            # Verificar si necesita datos (a menos que force_reload=True)
            if not force_reload:
                sufficiency = check_symbol_data_sufficiency(symbol, min_days=years_back * 250)  # ~250 días hábiles por año
                if sufficiency['sufficient']:
                    print(f"SKIP {symbol}: Suficientes datos ({sufficiency['records']} registros)")
                    continue
            
            # Cargar datos históricos
            result = load_historical_data_for_symbol(symbol, years_back)
            results.append(result)
            
            symbols_processed += 1
            
            if result['status'] == 'SUCCESS':
                symbols_successful += 1
                total_records_added += result.get('records_added', 0)
            else:
                symbols_failed += 1
            
            # Pausa para no sobrecargar APIs
            time.sleep(0.5)
        
        job_end = datetime.now()
        duration = (job_end - job_start).total_seconds()
        
        # Registrar en job_status
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO job_status 
            (job_name, business_date, status, symbols_processed, symbols_failed, 
             start_time, end_time, error_details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'INITIAL_DATA_LOAD', 
            datetime.now().strftime('%Y-%m-%d'),
            'SUCCESS' if symbols_failed == 0 else 'PARTIAL',
            symbols_successful,
            symbols_failed,
            job_start,
            job_end,
            json.dumps([r for r in results if r['status'] == 'FAILED']) if symbols_failed > 0 else None
        ))
        
        conn.commit()
        conn.close()
        
        print(f"Carga inicial completada:")
        print(f"   - Simbolos procesados: {symbols_processed}")
        print(f"   - Exitosos: {symbols_successful}")
        print(f"   - Fallidos: {symbols_failed}")
        print(f"   - Registros agregados: {total_records_added}")
        print(f"   - Duracion: {duration:.1f} segundos")
        
        return {
            'status': 'SUCCESS' if symbols_failed == 0 else 'PARTIAL',
            'symbols_processed': symbols_processed,
            'symbols_successful': symbols_successful,
            'symbols_failed': symbols_failed,
            'total_records_added': total_records_added,
            'duration_seconds': duration,
            'details': results
        }
        
    except Exception as e:
        print(f"ERROR en carga inicial: {e}")
        return {
            'status': 'FAILED',
            'error': str(e),
            'symbols_processed': symbols_processed,
            'symbols_successful': symbols_successful,
            'symbols_failed': symbols_failed
        }

@app.post("/initial-data-load")
async def run_initial_data_load_endpoint(
    years_back: int = Query(2, description="Años de datos históricos a cargar"),
    force_reload: bool = Query(False, description="Forzar recarga incluso si hay datos")
):
    """
    Ejecutar carga inicial masiva de datos históricos
    """
    try:
        result = run_initial_data_load(years_back, force_reload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in initial data load: {str(e)}")

@app.get("/data-sufficiency-check")
async def check_all_symbols_data_sufficiency(min_days: int = Query(300, description="Días mínimos requeridos")):
    """
    Verificar suficiencia de datos para todos los símbolos
    """
    try:
        results = []
        insufficient_symbols = []
        
        for symbol in MAIN_TICKERS:
            sufficiency = check_symbol_data_sufficiency(symbol, min_days)
            results.append(sufficiency)
            
            if not sufficiency.get('sufficient', False):
                insufficient_symbols.append(symbol)
        
        return {
            'total_symbols': len(MAIN_TICKERS),
            'sufficient_symbols': len([r for r in results if r.get('sufficient', False)]),
            'insufficient_symbols': len(insufficient_symbols),
            'insufficient_list': insufficient_symbols,
            'details': results,
            'recommendation': (
                "Ejecutar /initial-data-load para cargar datos históricos" 
                if insufficient_symbols 
                else "Todos los símbolos tienen datos suficientes"
            )
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking data sufficiency: {str(e)}")

# =====================================================
# SISTEMA DE INTEGRIDAD Y RECUPERACIÓN
# =====================================================

def check_data_integrity() -> Dict:
    """
    Verificar integridad de datos históricos
    """
    try:
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        # Check 1: Buscar gaps en fechas
        cursor.execute('''
            SELECT symbol, business_date, 
                   LAG(business_date) OVER (PARTITION BY symbol ORDER BY business_date) as prev_date
            FROM market_data_eod
            ORDER BY symbol, business_date
        ''')
        
        data_gaps = []
        for row in cursor.fetchall():
            symbol, current_date, prev_date = row
            if prev_date:
                current = datetime.strptime(current_date, '%Y-%m-%d').date()
                previous = datetime.strptime(prev_date, '%Y-%m-%d').date()
                gap_days = (current - previous).days
                
                if gap_days > 5:  # Más de 5 días = posible gap de mercado
                    data_gaps.append({
                        'symbol': symbol,
                        'gap_from': prev_date,
                        'gap_to': current_date,
                        'gap_days': gap_days
                    })
        
        # Check 2: Buscar datos con quality score bajo
        cursor.execute('''
            SELECT symbol, business_date, data_quality_score, anomaly_flags
            FROM market_data_eod
            WHERE data_quality_score < 80
            ORDER BY data_quality_score ASC
        ''')
        
        low_quality = []
        for row in cursor.fetchall():
            low_quality.append({
                'symbol': row[0],
                'business_date': row[1],
                'quality_score': row[2],
                'anomaly_flags': json.loads(row[3]) if row[3] else []
            })
        
        # Check 3: Verificar símbolos con muy pocos datos
        cursor.execute('''
            SELECT symbol, COUNT(*) as record_count
            FROM market_data_eod
            GROUP BY symbol
            HAVING COUNT(*) < 30  -- Menos de 30 días
            ORDER BY COUNT(*) ASC
        ''')
        
        insufficient_data = []
        for row in cursor.fetchall():
            insufficient_data.append({
                'symbol': row[0],
                'record_count': row[1]
            })
        
        conn.close()
        
        return {
            'data_gaps': data_gaps,
            'low_quality_records': low_quality,
            'insufficient_data_symbols': insufficient_data,
            'total_gaps': len(data_gaps),
            'total_low_quality': len(low_quality),
            'total_insufficient': len(insufficient_data)
        }
        
    except Exception as e:
        return {'error': str(e)}

def repair_data_gaps(symbol: str, start_date: str, end_date: str) -> Dict:
    """
    Reparar gaps de datos para un símbolo específico
    """
    try:
        print(f"🔧 Repairing data gaps for {symbol} from {start_date} to {end_date}")
        
        # Generar lista de fechas de negocio entre start_date y end_date
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        business_dates = []
        current = start
        while current <= end:
            # Solo días de semana (aproximación simple)
            if current.weekday() < 5:  # 0=Monday, 4=Friday
                business_dates.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
        
        repaired_count = 0
        failed_dates = []
        
        for date in business_dates:
            # Verificar si ya existe
            conn = sqlite3.connect('trading_dashboard.db')
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM market_data_eod WHERE symbol = ? AND business_date = ?',
                (symbol, date)
            )
            exists = cursor.fetchone()[0] > 0
            conn.close()
            
            if not exists:
                try:
                    # Intentar obtener datos para esta fecha
                    stock = yf.Ticker(symbol)
                    next_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                    data = stock.history(start=date, end=next_date)
                    
                    if not data.empty:
                        row = data.iloc[0]
                        ohlcv_data = {
                            'Open': row['Open'],
                            'High': row['High'],
                            'Low': row['Low'],
                            'Close': row['Close'],
                            'Volume': row['Volume'] if 'Volume' in row else 0,
                            'Adj Close': row.get('Adj Close', row['Close'])
                        }
                        
                        if insert_or_update_eod_data(symbol, date, ohlcv_data):
                            repaired_count += 1
                            print(f"✅ Repaired {symbol} {date}")
                        else:
                            failed_dates.append(f"{date}: QUALITY_FAILED")
                    else:
                        failed_dates.append(f"{date}: NO_DATA")
                        
                except Exception as e:
                    failed_dates.append(f"{date}: {str(e)}")
        
        return {
            'symbol': symbol,
            'period': f"{start_date} to {end_date}",
            'dates_checked': len(business_dates),
            'dates_repaired': repaired_count,
            'failed_dates': failed_dates
        }
        
    except Exception as e:
        return {'error': str(e)}

@app.get("/data-integrity-check")
async def data_integrity_check():
    """
    Endpoint para verificar integridad de datos
    """
    try:
        result = check_data_integrity()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking data integrity: {str(e)}")

@app.post("/repair-data-gaps")
async def repair_data_gaps_endpoint(
    symbol: str = Query(..., description="Símbolo a reparar"),
    start_date: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Fecha fin (YYYY-MM-DD)")
):
    """
    Endpoint para reparar gaps de datos
    """
    try:
        result = repair_data_gaps(symbol, start_date, end_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error repairing data gaps: {str(e)}")

@app.get("/market-data-stats")
async def get_market_data_stats():
    """
    Estadísticas generales de los datos almacenados
    """
    try:
        conn = sqlite3.connect('trading_dashboard.db')
        cursor = conn.cursor()
        
        # Stats básicas
        cursor.execute('SELECT COUNT(*) FROM market_data_eod')
        total_records = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT symbol) FROM market_data_eod')
        unique_symbols = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(business_date), MAX(business_date) FROM market_data_eod')
        date_range = cursor.fetchone()
        
        # Quality stats
        cursor.execute('''
            SELECT 
                AVG(data_quality_score) as avg_quality,
                MIN(data_quality_score) as min_quality,
                COUNT(*) FILTER (WHERE data_quality_score < 80) as low_quality_count
            FROM market_data_eod
        ''')
        quality_stats = cursor.fetchone()
        
        # Records por símbolo
        cursor.execute('''
            SELECT symbol, COUNT(*) as record_count
            FROM market_data_eod
            GROUP BY symbol
            ORDER BY COUNT(*) DESC
        ''')
        symbol_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_records': total_records,
            'unique_symbols': unique_symbols,
            'date_range': {
                'from': date_range[0],
                'to': date_range[1]
            },
            'quality_stats': {
                'average_quality_score': round(quality_stats[0], 2) if quality_stats[0] else 0,
                'minimum_quality_score': quality_stats[1],
                'low_quality_records': quality_stats[2]
            },
            'symbol_coverage': [
                {'symbol': row[0], 'record_count': row[1]}
                for row in symbol_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting market data stats: {str(e)}")

# =====================================================
# SISTEMA DE SCHEDULING AUTOMÁTICO
# =====================================================

# Configuración de horarios por exchange
MARKET_SCHEDULES = {
    'NYSE': {
        'timezone': 'America/New_York',
        'eod_time': '18:00',  # 6 PM ET (después del cierre 4 PM)
        'market_days': [0, 1, 2, 3, 4]  # Lunes-Viernes
    },
    'BCBA': {
        'timezone': 'America/Argentina/Buenos_Aires', 
        'eod_time': '18:30',  # 6:30 PM ART
        'market_days': [0, 1, 2, 3, 4]
    }
}

# Variables globales para control del scheduler
scheduler_running = False
eod_schedule_config = {
    'enabled': True,
    'time': '18:00',  # Hora EOD por defecto
    'timezone': 'America/New_York',
    'market_days_only': True
}

# Configuración para actualización de precios
price_update_config = {
    'enabled': True,
    'interval_minutes': 5,  # Cada 5 minutos por defecto
    'running': False
}

def is_market_day(timezone_str: str = 'America/New_York') -> bool:
    """
    Verificar si hoy es día de mercado (Lunes-Viernes)
    """
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    # 0=Monday, 6=Sunday
    return now.weekday() < 5

def scheduled_eod_job():
    """
    Job EOD programado que respeta días de mercado
    """
    try:
        if eod_schedule_config['market_days_only'] and not is_market_day(eod_schedule_config['timezone']):
            print(f"📅 Saltando EOD job - No es día de mercado")
            return
        
        print(f"🕰️  Ejecutando EOD job programado...")
        result = run_eod_job()
        
        if result['status'] == 'SUCCESS':
            print(f"✅ EOD job programado completado exitosamente")
        else:
            print(f"⚠️  EOD job programado completado con warnings: {result}")
            
    except Exception as e:
        print(f"❌ Error en EOD job programado: {e}")

def start_scheduler():
    """
    Iniciar el scheduler de tareas automáticas
    """
    global scheduler_running
    
    if scheduler_running:
        print("⚠️  Scheduler ya está ejecutándose")
        return
    
    # Limpiar schedule anterior
    schedule.clear()
    
    if eod_schedule_config['enabled']:
        # Programar EOD job
        schedule.every().day.at(eod_schedule_config['time']).do(scheduled_eod_job)
        print(f"📅 EOD job programado para {eod_schedule_config['time']} {eod_schedule_config['timezone']}")
    
    scheduler_running = True
    print("🚀 Scheduler iniciado")

def stop_scheduler():
    """
    Detener el scheduler
    """
    global scheduler_running
    schedule.clear()
    scheduler_running = False
    print("⏹️  Scheduler detenido")

def run_pending_jobs():
    """
    Ejecutar jobs pendientes (llamar desde background thread)
    """
    while scheduler_running:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check cada minuto
        except Exception as e:
            print(f"❌ Error en scheduler: {e}")
            time.sleep(60)

@app.post("/scheduler/start")
async def start_scheduler_endpoint():
    """
    Iniciar scheduler automático
    """
    try:
        start_scheduler()
        
        # Iniciar thread del scheduler si no está corriendo
        if scheduler_running:
            scheduler_thread = threading.Thread(target=run_pending_jobs, daemon=True)
            scheduler_thread.start()
        
        return {
            "message": "Scheduler iniciado",
            "config": eod_schedule_config,
            "jobs": len(schedule.jobs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")

@app.post("/scheduler/stop")
async def stop_scheduler_endpoint():
    """
    Detener scheduler automático
    """
    try:
        stop_scheduler()
        return {"message": "Scheduler detenido"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")

@app.get("/scheduler/status")
async def get_scheduler_status():
    """
    Obtener status del scheduler
    """
    return {
        "running": scheduler_running,
        "config": eod_schedule_config,
        "scheduled_jobs": len(schedule.jobs),
        "next_run": schedule.next_run().isoformat() if schedule.jobs else None,
        "is_market_day": is_market_day(eod_schedule_config['timezone'])
    }

@app.post("/scheduler/configure")
async def configure_scheduler(
    enabled: bool = Query(True, description="Habilitar scheduler automático"),
    time: str = Query("18:00", description="Hora EOD (HH:MM)"),
    timezone: str = Query("America/New_York", description="Timezone"),
    market_days_only: bool = Query(True, description="Solo días de mercado")
):
    """
    Configurar horarios del scheduler
    """
    try:
        # Validar formato de hora
        datetime.strptime(time, '%H:%M')
        
        # Validar timezone
        pytz.timezone(timezone)
        
        # Actualizar configuración
        eod_schedule_config.update({
            'enabled': enabled,
            'time': time,
            'timezone': timezone,
            'market_days_only': market_days_only
        })
        
        # Reiniciar scheduler si está corriendo
        if scheduler_running:
            stop_scheduler()
            start_scheduler()
            
            # Reiniciar thread
            scheduler_thread = threading.Thread(target=run_pending_jobs, daemon=True)
            scheduler_thread.start()
        
        return {
            "message": "Configuración actualizada",
            "config": eod_schedule_config,
            "next_run": schedule.next_run().isoformat() if schedule.jobs else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error en configuración: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configurando scheduler: {str(e)}")

@app.get("/scheduler/test-eod")
async def test_eod_job():
    """
    Probar EOD job manualmente (sin esperar horario)
    """
    try:
        print("🧪 Ejecutando EOD job de prueba...")
        result = run_eod_job()
        return {
            "message": "EOD job de prueba completado",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en test EOD: {str(e)}")

@app.post("/price-updates/configure")
async def configure_price_updates(
    enabled: bool = Query(True, description="Habilitar actualización de precios"),
    interval_minutes: int = Query(5, description="Intervalo en minutos (1-60)")
):
    """
    Configurar intervalo de actualización de precios
    """
    try:
        if interval_minutes < 1 or interval_minutes > 60:
            raise HTTPException(status_code=400, detail="Intervalo debe estar entre 1 y 60 minutos")
        
        # Actualizar configuración
        old_config = price_update_config.copy()
        price_update_config.update({
            'enabled': enabled,
            'interval_minutes': interval_minutes
        })
        
        # Si cambió la configuración y está corriendo, reiniciar
        if old_config != price_update_config and price_update_config['running']:
            price_update_config['running'] = False  # Detener el actual
            time.sleep(2)  # Esperar que termine
            
            # Iniciar nuevo thread
            if enabled:
                price_thread = threading.Thread(target=actualizar_precios_background, daemon=True)
                price_thread.start()
        
        return {
            "message": "Configuración de precios actualizada",
            "config": price_update_config,
            "restart_required": old_config != price_update_config
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error configurando precios: {str(e)}")

@app.get("/price-updates/status")
async def get_price_updates_status():
    """
    Obtener status de actualización de precios
    """
    return {
        "config": price_update_config,
        "message": "Actualización de precios " + ("activa" if price_update_config['running'] else "inactiva")
    }

if __name__ == "__main__":
    print("Iniciando Trading Dashboard API...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )