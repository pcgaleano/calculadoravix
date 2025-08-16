#!/usr/bin/env python3
"""
Debug detallado del cálculo VIX_Fix
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import sqlite3

class VixFixDebug:
    def __init__(self, pd_period=22, bbl=20, mult=2.0, lb=50, ph=0.85, pl=1.01):
        self.pd_period = pd_period
        self.bbl = bbl
        self.mult = mult
        self.lb = lb
        self.ph = ph
        self.pl = pl
    
    def obtener_datos_bd(self, ticker):
        """Obtener datos de BD local"""
        conn = sqlite3.connect('backend/trading_dashboard.db')
        query = '''
            SELECT business_date, open_price, high_price, low_price, close_price, volume
            FROM market_data_eod 
            WHERE symbol = ? 
            ORDER BY business_date ASC
        '''
        df = pd.read_sql_query(query, conn, params=(ticker,))
        conn.close()
        
        if df.empty:
            return None
        
        df['business_date'] = pd.to_datetime(df['business_date'])
        df.set_index('business_date', inplace=True)
        
        df = df.rename(columns={
            'open_price': 'Open',
            'high_price': 'High', 
            'low_price': 'Low',
            'close_price': 'Close',
            'volume': 'Volume'
        })
        
        return df[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    def obtener_datos_yfinance(self, ticker, start_date):
        """Obtener datos de yfinance"""
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end='2025-08-17')
        return data
    
    def rolling_max(self, series, window):
        return series.rolling(window=window, min_periods=1).max()
    
    def rolling_min(self, series, window):
        return series.rolling(window=window, min_periods=1).min()
    
    def simple_moving_average(self, series, window):
        return series.rolling(window=window, min_periods=1).mean()
    
    def standard_deviation(self, series, window):
        return series.rolling(window=window, min_periods=1).std()
    
    def debug_vix_calculation(self, data, fuente):
        """Debug paso a paso del VIX_Fix"""
        print(f"\n=== DEBUG VIX_Fix ({fuente}) ===")
        print(f"Datos disponibles: {len(data)} registros")
        print(f"Rango: {data.index[0].strftime('%Y-%m-%d')} a {data.index[-1].strftime('%Y-%m-%d')}")
        
        # Últimos 5 días de datos
        print(f"\nÚltimos 5 días de precios:")
        for fecha, row in data.tail(5).iterrows():
            print(f"  {fecha.strftime('%Y-%m-%d')}: H={row['High']:.2f} L={row['Low']:.2f} C={row['Close']:.2f}")
        
        # Calcular WVF paso a paso
        print(f"\n1. Calculando WVF...")
        highest_close = self.rolling_max(data['Close'], self.pd_period)
        wvf = ((highest_close - data['Low']) / highest_close) * 100
        
        print(f"   Último highest_close ({self.pd_period} días): {highest_close.iloc[-1]:.2f}")
        print(f"   Último Low: {data['Low'].iloc[-1]:.2f}")
        print(f"   Último WVF: {wvf.iloc[-1]:.2f}")
        
        # Bollinger Bands para WVF
        print(f"\n2. Calculando Bollinger Bands...")
        midLine = self.simple_moving_average(wvf, self.bbl)
        sDev = self.mult * self.standard_deviation(wvf, self.bbl)
        lowerBand = midLine - sDev
        upperBand = midLine + sDev
        
        print(f"   WVF MidLine ({self.bbl} días): {midLine.iloc[-1]:.2f}")
        print(f"   WVF StdDev * {self.mult}: {sDev.iloc[-1]:.2f}")
        print(f"   UpperBand: {upperBand.iloc[-1]:.2f}")
        print(f"   LowerBand: {lowerBand.iloc[-1]:.2f}")
        
        # Percentiles
        print(f"\n3. Calculando Percentiles...")
        rangeHigh = self.rolling_max(wvf, self.lb) * self.ph
        rangeLow = self.rolling_min(wvf, self.lb) * self.pl
        
        print(f"   WVF Max ({self.lb} días): {self.rolling_max(wvf, self.lb).iloc[-1]:.2f}")
        print(f"   RangeHigh (Max * {self.ph}): {rangeHigh.iloc[-1]:.2f}")
        print(f"   WVF Min ({self.lb} días): {self.rolling_min(wvf, self.lb).iloc[-1]:.2f}")
        print(f"   RangeLow (Min * {self.pl}): {rangeLow.iloc[-1]:.2f}")
        
        # Condiciones de señal
        print(f"\n4. Evaluando condiciones para 2025-08-16...")
        wvf_actual = wvf.iloc[-1]
        upper_actual = upperBand.iloc[-1]
        range_high_actual = rangeHigh.iloc[-1]
        
        print(f"   WVF actual: {wvf_actual:.2f}")
        print(f"   UpperBand: {upper_actual:.2f}")
        print(f"   RangeHigh: {range_high_actual:.2f}")
        
        condicion1 = wvf_actual >= upper_actual
        condicion2 = wvf_actual >= range_high_actual
        es_verde = condicion1 or condicion2
        
        print(f"   WVF >= UpperBand: {wvf_actual:.2f} >= {upper_actual:.2f} = {condicion1}")
        print(f"   WVF >= RangeHigh: {wvf_actual:.2f} >= {range_high_actual:.2f} = {condicion2}")
        print(f"   SEÑAL VERDE: {es_verde}")
        
        return es_verde

def main():
    debug = VixFixDebug()
    
    # Obtener datos de BD local
    print("Obteniendo datos de BD local...")
    data_bd = debug.obtener_datos_bd('ETH-USD')
    
    if data_bd is not None:
        senal_bd = debug.debug_vix_calculation(data_bd, "BD Local")
    
    # Obtener datos de yfinance
    print("\nObteniendo datos de yfinance...")
    data_yf = debug.obtener_datos_yfinance('ETH-USD', '2025-05-01')
    
    if data_yf is not None:
        senal_yf = debug.debug_vix_calculation(data_yf, "yfinance")
    
    # Comparar resultados
    print(f"\n=== COMPARACIÓN ===")
    print(f"BD Local: {'VERDE' if senal_bd else 'NO VERDE'}")
    print(f"yfinance: {'VERDE' if senal_yf else 'NO VERDE'}")
    
    if senal_bd != senal_yf:
        print("⚠️ DISCREPANCIA DETECTADA!")
    else:
        print("✅ Resultados coinciden")

if __name__ == "__main__":
    main()