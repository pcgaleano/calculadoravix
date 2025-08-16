#!/usr/bin/env python3
"""
Script para poblar base de datos directamente usando yfinance
(sin depender del backend API)
"""
import yfinance as yf
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

# Configuración
DB_PATH = "backend/trading_dashboard.db"
MESES_ATRAS = 3

# Lista de símbolos principales
SYMBOLS = [
    # Cryptos
    "BTC-USD", "ETH-USD", "USDT-USD", "BNB-USD", "XRP-USD", "USDC-USD", "ADA-USD",
    "DOGE-USD", "MATIC-USD", "SOL-USD", "DOT-USD", "AVAX-USD", "SHIB-USD", "TRX-USD",
    "UNI-USD", "ATOM-USD", "ETC-USD", "LTC-USD", "BCH-USD", "LINK-USD",
    
    # US Stocks principales
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "SPY", "QQQ",
    "IWM", "EEM", "GLD", "SLV", "VIX",
    
    # Argentinas (ADR y directas)
    "GGAL", "PAM", "YPF", "BMA", "SUPV", "TEO", "CRESY", "IRS", "TGS",
    
    # Argentinas .BA
    "GGAL.BA", "PAMP.BA", "YPFD.BA", "ALUA.BA", "TECO2.BA", "MIRG.BA", 
    "CEPU.BA", "BMA.BA", "SUPV.BA", "LOMA.BA"
]

def conectar_bd():
    """Conectar a la base de datos"""
    return sqlite3.connect(DB_PATH)

def verificar_tabla_existe():
    """Verificar que la tabla market_data_eod existe"""
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='market_data_eod'
    """)
    
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def crear_tabla_si_no_existe():
    """Crear tabla market_data_eod si no existe"""
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data_eod (
            symbol TEXT NOT NULL,
            business_date DATE NOT NULL,
            open_price DECIMAL(12,4) NOT NULL,
            high_price DECIMAL(12,4) NOT NULL,
            low_price DECIMAL(12,4) NOT NULL,
            close_price DECIMAL(12,4) NOT NULL,
            volume BIGINT DEFAULT 0,
            data_quality_score INTEGER DEFAULT 100,
            anomaly_flags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (symbol, business_date)
        )
    """)
    
    conn.commit()
    conn.close()

def obtener_fechas_existentes(symbol):
    """Obtener fechas que ya existen para un símbolo"""
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT business_date FROM market_data_eod WHERE symbol = ?", 
        (symbol,)
    )
    fechas = {row[0] for row in cursor.fetchall()}
    
    conn.close()
    return fechas

def insertar_datos_simbolo(symbol, fecha_inicio, fecha_fin):
    """Descargar e insertar datos para un símbolo específico"""
    try:
        print(f"  Descargando {symbol}...")
        
        # Obtener fechas existentes
        fechas_existentes = obtener_fechas_existentes(symbol)
        
        # Descargar datos de yfinance
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=fecha_inicio, end=fecha_fin)
        
        if data.empty:
            print(f"    Sin datos para {symbol}")
            return 0
        
        # Preparar datos para inserción
        registros_nuevos = 0
        registros_actualizados = 0
        
        conn = conectar_bd()
        cursor = conn.cursor()
        
        for fecha, row in data.iterrows():
            fecha_str = fecha.strftime('%Y-%m-%d')
            
            # Validar datos
            if pd.isna(row['Open']) or pd.isna(row['Close']):
                continue
                
            # Verificar si ya existe
            if fecha_str in fechas_existentes:
                # Actualizar registro existente
                cursor.execute("""
                    UPDATE market_data_eod 
                    SET open_price = ?, high_price = ?, low_price = ?, close_price = ?, 
                        volume = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE symbol = ? AND business_date = ?
                """, (
                    float(row['Open']), float(row['High']), float(row['Low']), 
                    float(row['Close']), int(row['Volume']), symbol, fecha_str
                ))
                registros_actualizados += 1
            else:
                # Insertar nuevo registro
                cursor.execute("""
                    INSERT OR REPLACE INTO market_data_eod 
                    (symbol, business_date, open_price, high_price, low_price, close_price, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, fecha_str, float(row['Open']), float(row['High']), 
                    float(row['Low']), float(row['Close']), int(row['Volume'])
                ))
                registros_nuevos += 1
        
        conn.commit()
        conn.close()
        
        print(f"    {symbol}: {registros_nuevos} nuevos, {registros_actualizados} actualizados")
        return registros_nuevos + registros_actualizados
        
    except Exception as e:
        print(f"    ERROR {symbol}: {e}")
        return 0

def generar_fechas_objetivo():
    """Generar fechas de los últimos N meses"""
    hoy = datetime.now()
    fecha_inicio = hoy - timedelta(days=MESES_ATRAS * 30)
    
    return fecha_inicio.strftime('%Y-%m-%d'), hoy.strftime('%Y-%m-%d')

def main():
    print("Poblando base de datos directamente con yfinance...")
    print(f"Base de datos: {DB_PATH}")
    
    # Verificar BD
    if not os.path.exists(DB_PATH):
        print(f"ERROR: No se encuentra {DB_PATH}")
        return
    
    # Crear tabla si no existe
    crear_tabla_si_no_existe()
    
    # Calcular fechas
    fecha_inicio, fecha_fin = generar_fechas_objetivo()
    print(f"Período: {fecha_inicio} a {fecha_fin}")
    print(f"Símbolos a procesar: {len(SYMBOLS)}")
    
    # Procesar cada símbolo
    total_procesados = 0
    exitosos = 0
    
    for i, symbol in enumerate(SYMBOLS, 1):
        print(f"[{i}/{len(SYMBOLS)}] Procesando {symbol}")
        
        registros = insertar_datos_simbolo(symbol, fecha_inicio, fecha_fin)
        total_procesados += registros
        
        if registros > 0:
            exitosos += 1
    
    # Resumen final
    print(f"\nResumen:")
    print(f"  Símbolos exitosos: {exitosos}/{len(SYMBOLS)}")
    print(f"  Total registros procesados: {total_procesados}")
    
    # Estado final de ETH-USD
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_data_eod WHERE symbol = 'ETH-USD'")
    eth_records = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT business_date) FROM market_data_eod")
    total_dates = cursor.fetchone()[0]
    cursor.execute("SELECT MIN(business_date), MAX(business_date) FROM market_data_eod")
    date_range = cursor.fetchone()
    conn.close()
    
    print(f"\nEstado final:")
    print(f"  ETH-USD registros: {eth_records}")
    print(f"  Fechas únicas: {total_dates}")
    print(f"  Rango: {date_range[0]} a {date_range[1]}")
    print(f"  VIX_Fix: {'SUFICIENTE' if eth_records >= 50 else 'INSUFICIENTE'} ({eth_records}/50+)")

if __name__ == "__main__":
    main()