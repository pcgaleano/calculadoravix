#!/usr/bin/env python3
"""
VIX_Fix Strategy - Implementación en Python del indicador Pine Script
Detecta condiciones de compra (verde) basado en el algoritmo VIX_Fix
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import sys

class VixFixStrategy:
    def __init__(self, pd_period=22, bbl=20, mult=2.0, lb=50, ph=0.85, pl=1.01, use_local_db=True):
        """
        Inicializa los parámetros del VIX_Fix
        
        Args:
            pd_period (int): LookBack Period Standard Deviation High
            bbl (int): Bollinger Band Length  
            mult (float): Bollinger Band Standard Deviation Up
            lb (int): Look Back Period Percentile High
            ph (float): Highest Percentile
            pl (float): Lowest Percentile
            use_local_db (bool): Usar base de datos local SQLite (default True)
        """
        self.pd_period = pd_period
        self.bbl = bbl
        self.mult = mult
        self.lb = lb
        self.use_local_db = use_local_db
        self.ph = ph
        self.pl = pl
    
    def obtener_datos_desde_bd(self, ticker, fecha_inicio, fecha_fin):
        """
        Obtener datos OHLCV desde base de datos local SQLite
        """
        try:
            import sqlite3
            import os
            
            # Encontrar path correcto de la BD dinámicamente
            possible_paths = [
                'backend/trading_dashboard.db',           # Desde root del proyecto
                'trading_dashboard.db',                   # Desde directorio backend
                '../trading_dashboard.db',                # Desde subdirectorio
                os.path.join(os.path.dirname(__file__), 'backend', 'trading_dashboard.db'),  # Relativo al script
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'trading_dashboard.db')  # Backup
            ]
            
            db_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            
            if db_path is None:
                return None
            
            conn = sqlite3.connect(db_path)
            
            query = '''
                SELECT business_date, open_price, high_price, low_price, close_price, volume
                FROM market_data_eod 
                WHERE symbol = ? AND business_date >= ? AND business_date <= ?
                ORDER BY business_date ASC
            '''
            
            # Leer datos como DataFrame
            df = pd.read_sql_query(query, conn, params=(ticker, fecha_inicio, fecha_fin))
            conn.close()
            
            if df.empty:
                return None
            
            # Convertir a formato pandas igual que yfinance
            df['business_date'] = pd.to_datetime(df['business_date'])
            df.set_index('business_date', inplace=True)
            
            # Renombrar columnas para compatibilidad
            df = df.rename(columns={
                'open_price': 'Open',
                'high_price': 'High', 
                'low_price': 'Low',
                'close_price': 'Close',
                'volume': 'Volume'
            })
            
            return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
        except Exception as e:
            return None
    
    def obtener_datos_ticker(self, ticker, fecha_inicio, fecha_fin):
        """
        Obtener datos con estrategia híbrida: BD local primero, yfinance como fallback
        """
        if self.use_local_db:
            # Intentar BD local primero
            data = self.obtener_datos_desde_bd(ticker, fecha_inicio, fecha_fin)
            
            if data is not None and len(data) > 0:
                return data
        
        # Fallback a yfinance
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(start=fecha_inicio, end=fecha_fin)
            return data
        except Exception as e:
            return None
    
    def rolling_max(self, series, window):
        """Equivalente a highest() en Pine Script"""
        return series.rolling(window=window, min_periods=1).max()
    
    def rolling_min(self, series, window):
        """Equivalente a lowest() en Pine Script"""
        return series.rolling(window=window, min_periods=1).min()
    
    def simple_moving_average(self, series, window):
        """Equivalente a sma() en Pine Script"""
        return series.rolling(window=window, min_periods=1).mean()
    
    def standard_deviation(self, series, window):
        """Equivalente a stdev() en Pine Script"""
        return series.rolling(window=window, min_periods=1).std()
    
    def calculate_vix_fix(self, data):
        """
        Calcula el indicador VIX_Fix basado en los datos OHLC
        
        Args:
            data (pandas.DataFrame): DataFrame con columnas Open, High, Low, Close
            
        Returns:
            pandas.DataFrame: DataFrame con todas las señales calculadas
        """
        df = data.copy()
        
        # Calcular WVF (Williams VIX Fix)
        highest_close = self.rolling_max(df['Close'], self.pd_period)
        wvf = ((highest_close - df['Low']) / highest_close) * 100
        df['wvf'] = wvf
        
        # Calcular Bollinger Bands para WVF
        midLine = self.simple_moving_average(wvf, self.bbl)
        sDev = self.mult * self.standard_deviation(wvf, self.bbl)
        lowerBand = midLine - sDev
        upperBand = midLine + sDev
        
        df['midLine'] = midLine
        df['lowerBand'] = lowerBand
        df['upperBand'] = upperBand
        
        # Calcular rangos percentiles
        rangeHigh = self.rolling_max(wvf, self.lb) * self.ph
        rangeLow = self.rolling_min(wvf, self.lb) * self.pl
        
        df['rangeHigh'] = rangeHigh
        df['rangeLow'] = rangeLow
        
        # Determinar color/condición según la lógica original
        # Verde (lime): wvf >= upperBand or wvf >= rangeHigh
        # Rojo (red): wvf <= lowerBand or wvf <= rangeLow
        # Gris (gray): el resto
        
        df['es_verde'] = (wvf >= upperBand) | (wvf >= rangeHigh)
        df['es_rojo'] = (wvf <= lowerBand) | (wvf <= rangeLow)
        df['es_gris'] = ~df['es_verde'] & ~df['es_rojo']
        
        # Agregar información adicional
        df['color'] = 'gris'
        df.loc[df['es_verde'], 'color'] = 'verde'
        df.loc[df['es_rojo'], 'color'] = 'rojo'
        
        return df
    
    def obtener_fechas_compra(self, ticker, fecha_inicio, fecha_fin):
        """
        Obtiene las fechas donde se cumple la condición de compra (verde)
        
        Args:
            ticker (str): Símbolo del ticker
            fecha_inicio (str): Fecha de inicio
            fecha_fin (str): Fecha de fin
            
        Returns:
            pandas.DataFrame: DataFrame con las fechas de compra y datos relevantes
        """
        try:
            # Calcular cuántos días adicionales necesitamos para el warm-up
            # Necesitamos el máximo entre pd_period, bbl, y lb para que los cálculos sean correctos
            max_lookback = max(self.pd_period, self.bbl, self.lb)
            warm_up_days = max_lookback + 50  # Agregamos 50 días extra para asegurar suficientes datos
            
            # Calcular fecha de inicio extendida
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_inicio_extendida = fecha_inicio_dt - pd.Timedelta(days=warm_up_days)
            fecha_inicio_str_extendida = fecha_inicio_extendida.strftime('%Y-%m-%d')
            
            print(f"Obteniendo datos desde {fecha_inicio_str_extendida} (warm-up) hasta {fecha_fin}")
            print(f"Período de análisis: {fecha_inicio} hasta {fecha_fin}")
            
            # Obtener datos del ticker con período extendido usando método híbrido
            data = self.obtener_datos_ticker(ticker, fecha_inicio_str_extendida, fecha_fin)
            
            if data.empty:
                print(f"No se encontraron datos para {ticker}")
                return None
            
            print(f"Datos obtenidos: {len(data)} registros desde {data.index[0].strftime('%Y-%m-%d')}")
            
            # Calcular VIX_Fix con todos los datos
            df_vix = self.calculate_vix_fix(data)
            
            # Filtrar solo las fechas del período solicitado
            fecha_inicio_filter = pd.to_datetime(fecha_inicio).tz_localize(df_vix.index.tz)
            fecha_fin_filter = pd.to_datetime(fecha_fin).tz_localize(df_vix.index.tz)
            
            df_vix_periodo = df_vix[
                (df_vix.index >= fecha_inicio_filter) & 
                (df_vix.index <= fecha_fin_filter)
            ].copy()
            
            # Filtrar solo las fechas verdes (condición de compra) en el período solicitado
            fechas_compra = df_vix_periodo[df_vix_periodo['es_verde']].copy()
            
            return fechas_compra
            
        except Exception as e:
            print(f"Error al procesar datos: {e}")
            return None
    
    def mostrar_resultados(self, fechas_compra, ticker):
        """
        Muestra los resultados de manera legible
        
        Args:
            fechas_compra (pandas.DataFrame): DataFrame con fechas de compra
            ticker (str): Símbolo del ticker
        """
        if fechas_compra is None or fechas_compra.empty:
            print(f"No se encontraron condiciones de compra para {ticker}")
            return
        
        print(f"\n{'='*80}")
        print(f"SEÑALES DE COMPRA (VERDE) PARA {ticker.upper()}")
        print(f"{'='*80}")
        print(f"Total de señales encontradas: {len(fechas_compra)}")
        print(f"Período: {fechas_compra.index[0].strftime('%Y-%m-%d')} a {fechas_compra.index[-1].strftime('%Y-%m-%d')}")
        
        # Mostrar estadísticas
        if len(fechas_compra) > 0:
            precio_promedio = fechas_compra['Close'].mean()
            precio_min = fechas_compra['Close'].min()
            precio_max = fechas_compra['Close'].max()
            
            print(f"\nESTADÍSTICAS DE PRECIOS EN SEÑALES:")
            print(f"Precio promedio: ${precio_promedio:.2f}")
            print(f"Precio mínimo: ${precio_min:.2f}")
            print(f"Precio máximo: ${precio_max:.2f}")
        
        print(f"\nLISTA COMPLETA DE FECHAS DE COMPRA:")
        print("-" * 80)
        
        # Lista numerada de fechas
        for i, (fecha, row) in enumerate(fechas_compra.iterrows(), 1):
            print(f"{i:2d}. {fecha.strftime('%Y-%m-%d')} ({fecha.strftime('%A')}) - Precio: ${row['Close']:,.2f}")
        
        print(f"\nDETALLE TÉCNICO DE CADA SEÑAL:")
        print("-" * 80)
        
        # Mostrar las fechas con información relevante
        for i, (fecha, row) in enumerate(fechas_compra.iterrows(), 1):
            upper_str = f"{row['upperBand']:5.1f}" if not pd.isna(row['upperBand']) else " N/A "
            range_str = f"{row['rangeHigh']:5.1f}" if not pd.isna(row['rangeHigh']) else " N/A "
            
            # Determinar qué condición se cumplió
            condicion = ""
            if not pd.isna(row['upperBand']) and row['wvf'] >= row['upperBand']:
                condicion += "UpperBand "
            if not pd.isna(row['rangeHigh']) and row['wvf'] >= row['rangeHigh']:
                condicion += "RangeHigh "
            
            print(f"{i:2d}. {fecha.strftime('%Y-%m-%d')} | "
                  f"Close: ${row['Close']:7.2f} | "
                  f"VIX_Fix: {row['wvf']:5.1f} | "
                  f"UpperBand: {upper_str} | "
                  f"RangeHigh: {range_str} | "
                  f"Trigger: {condicion.strip()}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Detectar señales de compra usando VIX_Fix Strategy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python vix_fix_strategy.py --inicio 2024-01-01 --fin 2024-12-31
  python vix_fix_strategy.py -i 2024-06-01 -f 2024-06-30 --ticker GGAL.BA
        """
    )
    
    parser.add_argument('--ticker', '-t', default='GGAL.BA', help='Símbolo del ticker')
    parser.add_argument('--inicio', '-i', required=True, help='Fecha de inicio (YYYY-MM-DD)')
    parser.add_argument('--fin', '-f', required=True, help='Fecha de fin (YYYY-MM-DD)')
    
    # Parámetros del VIX_Fix
    parser.add_argument('--pd', type=int, default=22, help='LookBack Period Standard Deviation High')
    parser.add_argument('--bbl', type=int, default=20, help='Bollinger Band Length')
    parser.add_argument('--mult', type=float, default=2.0, help='Bollinger Band Standard Deviation Up')
    parser.add_argument('--lb', type=int, default=50, help='Look Back Period Percentile High')
    parser.add_argument('--ph', type=float, default=0.85, help='Highest Percentile')
    parser.add_argument('--pl', type=float, default=1.01, help='Lowest Percentile')
    
    args = parser.parse_args()
    
    try:
        # Validar fechas
        datetime.strptime(args.inicio, '%Y-%m-%d')
        datetime.strptime(args.fin, '%Y-%m-%d')
        
        # Crear instancia de la estrategia
        strategy = VixFixStrategy(
            pd_period=args.pd,
            bbl=args.bbl,
            mult=args.mult,
            lb=args.lb,
            ph=args.ph,
            pl=args.pl
        )
        
        print(f"Analizando {args.ticker} desde {args.inicio} hasta {args.fin}...")
        print(f"Parámetros VIX_Fix: pd={args.pd}, bbl={args.bbl}, mult={args.mult}, lb={args.lb}, ph={args.ph}, pl={args.pl}")
        
        # Obtener fechas de compra
        fechas_compra = strategy.obtener_fechas_compra(args.ticker, args.inicio, args.fin)
        strategy.mostrar_resultados(fechas_compra, args.ticker)
        
    except ValueError as e:
        print(f"Error en las fechas: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperación cancelada")
        sys.exit(0)

if __name__ == "__main__":
    main()