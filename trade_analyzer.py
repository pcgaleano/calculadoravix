#!/usr/bin/env python3
"""
Trade Analyzer - Analiza el performance de trades basados en VIX_Fix
Calcula cuántos días toma alcanzar el target de profit (4%)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import sys
from vix_fix_strategy import VixFixStrategy

class TradeAnalyzer:
    def __init__(self, profit_target=0.04, max_hold_days=30, use_local_db=True):
        """
        Inicializa el analizador de trades
        
        Args:
            profit_target (float): Target de profit (default 4% = 0.04)
            max_hold_days (int): Máximo días para mantener un trade
            use_local_db (bool): Usar base de datos local SQLite (default True)
        """
        self.profit_target = profit_target
        self.max_hold_days = max_hold_days
        self.use_local_db = use_local_db
        self.vix_strategy = VixFixStrategy()
    
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
                print(f"⚠️  No se encontró trading_dashboard.db en ninguna de estas ubicaciones:")
                for path in possible_paths:
                    print(f"   - {os.path.abspath(path)}")
                return None
            
            conn = sqlite3.connect(db_path)
            
            query = '''
                SELECT business_date, open_price, high_price, low_price, close_price, volume,
                       data_quality_score
                FROM market_data_eod 
                WHERE symbol = ? AND business_date >= ? AND business_date <= ?
                ORDER BY business_date ASC
            '''
            
            # Leer datos como DataFrame
            df = pd.read_sql_query(query, conn, params=(ticker, fecha_inicio, fecha_fin))
            conn.close()
            
            if df.empty:
                print(f"⚠️  No hay datos locales para {ticker} ({fecha_inicio} a {fecha_fin})")
                return None
            
            # Convertir a formato pandas igual que yfinance
            df['business_date'] = pd.to_datetime(df['business_date'])
            df.set_index('business_date', inplace=True)
            
            # Renombrar columnas para compatibilidad con código existente
            df = df.rename(columns={
                'open_price': 'Open',
                'high_price': 'High', 
                'low_price': 'Low',
                'close_price': 'Close',
                'volume': 'Volume'
            })
            
            # Solo quedarnos con OHLCV
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            
            print(f"✅ Datos locales para {ticker}: {len(df)} registros desde BD")
            return df
            
        except Exception as e:
            print(f"❌ Error obteniendo datos locales para {ticker}: {e}")
            return None
    
    def obtener_datos_desde_yfinance(self, ticker, fecha_inicio, fecha_fin):
        """
        Fallback: obtener datos desde yfinance (método original)
        """
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(start=fecha_inicio, end=fecha_fin)
            
            if data.empty:
                print(f"⚠️  No hay datos en yfinance para {ticker}")
                return None
            
            print(f"📡 Datos desde yfinance para {ticker}: {len(data)} registros")
            return data
            
        except Exception as e:
            print(f"❌ Error obteniendo datos de yfinance para {ticker}: {e}")
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
            
            print(f"🔄 Fallback a yfinance para {ticker}")
        
        # Fallback a yfinance
        return self.obtener_datos_desde_yfinance(ticker, fecha_inicio, fecha_fin)
    
    def analizar_trades(self, ticker, fecha_inicio, fecha_fin):
        """
        Analiza todos los trades basados en señales VIX_Fix
        
        Args:
            ticker (str): Símbolo del ticker
            fecha_inicio (str): Fecha de inicio
            fecha_fin (str): Fecha de fin
            
        Returns:
            pandas.DataFrame: DataFrame con resultados de cada trade
        """
        try:
            # Obtener señales de compra
            fechas_compra = self.vix_strategy.obtener_fechas_compra(ticker, fecha_inicio, fecha_fin)
            
            if fechas_compra is None or fechas_compra.empty:
                print("No se encontraron señales de compra")
                return None
            
            # Obtener datos completos para análisis de salidas
            # Necesitamos datos hasta más allá del último trade para ver las salidas
            fecha_fin_extendida = (pd.to_datetime(fecha_fin) + pd.Timedelta(days=self.max_hold_days + 10)).strftime('%Y-%m-%d')
            
            # Obtener datos completos con warm-up
            max_lookback = max(self.vix_strategy.pd_period, self.vix_strategy.bbl, self.vix_strategy.lb)
            warm_up_days = max_lookback + 50
            fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_inicio_extendida = fecha_inicio_dt - pd.Timedelta(days=warm_up_days)
            fecha_inicio_str_extendida = fecha_inicio_extendida.strftime('%Y-%m-%d')
            
            # Usar nuevo método híbrido para obtener datos
            data_completa = self.obtener_datos_ticker(ticker, fecha_inicio_str_extendida, fecha_fin_extendida)
            
            if data_completa.empty:
                print(f"No se pudieron obtener datos completos para {ticker}")
                return None
            
            print(f"Analizando {len(fechas_compra)} trades...")
            
            # Analizar cada trade
            resultados_trades = []
            
            for i, (fecha_compra, row_compra) in enumerate(fechas_compra.iterrows(), 1):
                resultado = self.analizar_trade_individual(
                    data_completa, fecha_compra, row_compra['Close'], i
                )
                if resultado:
                    resultados_trades.append(resultado)
            
            if not resultados_trades:
                print("No se pudieron analizar los trades")
                return None
            
            df_resultados = pd.DataFrame(resultados_trades)
            return df_resultados
            
        except Exception as e:
            print(f"Error al analizar trades: {e}")
            return None
    
    def analizar_trade_individual(self, data_completa, fecha_compra, precio_compra, trade_num):
        """
        Analiza un trade individual desde la compra hasta la venta o cierre
        
        Args:
            data_completa (pandas.DataFrame): Datos completos del ticker
            fecha_compra (datetime): Fecha de compra
            precio_compra (float): Precio de compra
            trade_num (int): Número del trade
            
        Returns:
            dict: Resultado del trade
        """
        try:
            # Precio target (4% profit)
            precio_target = precio_compra * (1 + self.profit_target)
            
            # Obtener datos posteriores a la fecha de compra
            datos_posteriores = data_completa[data_completa.index > fecha_compra].copy()
            
            if datos_posteriores.empty:
                return {
                    'trade_num': trade_num,
                    'fecha_compra': fecha_compra,
                    'precio_compra': precio_compra,
                    'precio_target': precio_target,
                    'resultado': 'SIN_DATOS',
                    'dias_trade': 0,
                    'precio_venta': precio_compra,
                    'profit_pct': 0.0,
                    'fecha_venta': fecha_compra
                }
            
            # Buscar el primer día que alcanza el target
            dias_para_target = None
            fecha_venta = None
            precio_venta = None
            
            for i, (fecha, row) in enumerate(datos_posteriores.iterrows(), 1):
                # Verificar si el máximo del día alcanza el target
                if row['High'] >= precio_target:
                    dias_para_target = i
                    fecha_venta = fecha
                    precio_venta = precio_target  # Asumimos que vendemos exactamente al target
                    break
                
                # Si llegamos al máximo de días sin alcanzar target
                if i >= self.max_hold_days:
                    dias_para_target = i
                    fecha_venta = fecha
                    precio_venta = row['Close']  # Vendemos al cierre
                    break
            
            # Si no encontramos salida, usar el último dato disponible
            if dias_para_target is None:
                dias_para_target = len(datos_posteriores)
                fecha_venta = datos_posteriores.index[-1]
                precio_venta = datos_posteriores['Close'].iloc[-1]
            
            # Calcular profit
            profit_pct = (precio_venta - precio_compra) / precio_compra
            
            # Determinar resultado correctamente
            if profit_pct >= self.profit_target:
                resultado = 'TARGET_ALCANZADO'
            elif dias_para_target >= self.max_hold_days:
                resultado = 'MAX_DIAS'
            else:
                resultado = 'FIN_DATOS'  # Para casos que terminaron por falta de datos
            
            return {
                'trade_num': trade_num,
                'fecha_compra': fecha_compra,
                'precio_compra': precio_compra,
                'precio_target': precio_target,
                'fecha_venta': fecha_venta,
                'precio_venta': precio_venta,
                'dias_trade': dias_para_target,
                'profit_pct': profit_pct,
                'resultado': resultado
            }
            
        except Exception as e:
            print(f"Error analizando trade {trade_num}: {e}")
            return None
    
    def mostrar_resultados_trades(self, df_resultados, ticker):
        """
        Muestra los resultados del análisis de trades
        
        Args:
            df_resultados (pandas.DataFrame): Resultados de los trades
            ticker (str): Símbolo del ticker
        """
        if df_resultados is None or df_resultados.empty:
            print("No hay resultados para mostrar")
            return
        
        print(f"\n{'='*100}")
        print(f"ANÁLISIS DE TRADES - {ticker.upper()}")
        print(f"Target de Profit: {self.profit_target:.1%} | Máximo días por trade: {self.max_hold_days}")
        print(f"{'='*100}")
        
        # Estadísticas generales
        total_trades = len(df_resultados)
        trades_exitosos = len(df_resultados[df_resultados['resultado'] == 'TARGET_ALCANZADO'])
        trades_max_dias = len(df_resultados[df_resultados['resultado'] == 'MAX_DIAS'])
        trades_fin_datos = len(df_resultados[df_resultados['resultado'] == 'FIN_DATOS'])
        
        tasa_exito = (trades_exitosos / total_trades) * 100 if total_trades > 0 else 0
        
        # Estadísticas de días
        dias_min_total = df_resultados['dias_trade'].min()
        dias_max_total = df_resultados['dias_trade'].max()
        dias_promedio_total = df_resultados['dias_trade'].mean()
        
        print(f"\nRESUMEN EJECUTIVO:")
        print(f"{'-'*50}")
        print(f"Total de trades: {total_trades}")
        print(f"Trades exitosos (alcanzaron {self.profit_target:.1%}): {trades_exitosos} ({tasa_exito:.1f}%)")
        print(f"Trades cerrados por tiempo maximo: {trades_max_dias}")
        print(f"Trades cerrados por fin de datos: {trades_fin_datos}")
        
        print(f"\nESTADISTICAS GENERALES DE TIEMPO:")
        print(f"{'-'*50}")
        print(f"Dias promedio de todos los trades: {dias_promedio_total:.1f}")
        print(f"Minimo dias (cualquier trade): {dias_min_total}")
        print(f"MAXIMO DIAS (cualquier trade): {dias_max_total}")
        
        if trades_exitosos > 0:
            df_exitosos = df_resultados[df_resultados['resultado'] == 'TARGET_ALCANZADO']
            dias_promedio_exito = df_exitosos['dias_trade'].mean()
            dias_min_exito = df_exitosos['dias_trade'].min()
            dias_max_exito = df_exitosos['dias_trade'].max()
            
            print(f"\nESTADISTICAS DE TRADES EXITOSOS:")
            print(f"{'-'*50}")
            print(f"Dias promedio para alcanzar {self.profit_target:.1%}: {dias_promedio_exito:.1f}")
            print(f"Minimo dias (trades exitosos): {dias_min_exito}")
            print(f"Maximo dias (trades exitosos): {dias_max_exito}")
        
        # Profit promedio de todos los trades
        profit_promedio = df_resultados['profit_pct'].mean()
        profit_min = df_resultados['profit_pct'].min()
        profit_max = df_resultados['profit_pct'].max()
        
        print(f"\nESTADISTICAS DE PROFIT:")
        print(f"{'-'*50}")
        print(f"Profit promedio: {profit_promedio:.2%}")
        print(f"Profit minimo: {profit_min:.2%}")
        print(f"Profit maximo: {profit_max:.2%}")
        
        print(f"\nDETALLE DE CADA TRADE:")
        print(f"{'-'*100}")
        print(f"{'#':<3} {'Compra':<12} {'Precio Compra':<12} {'Venta':<12} {'Precio Venta':<12} {'Dias':<5} {'Profit':<8} {'Estado':<20}")
        print(f"{'-'*100}")
        
        for _, trade in df_resultados.iterrows():
            fecha_compra_str = trade['fecha_compra'].strftime('%Y-%m-%d')
            fecha_venta_str = trade['fecha_venta'].strftime('%Y-%m-%d')
            
            print(f"{trade['trade_num']:<3} "
                  f"{fecha_compra_str:<12} "
                  f"${trade['precio_compra']:<11.2f} "
                  f"{fecha_venta_str:<12} "
                  f"${trade['precio_venta']:<11.2f} "
                  f"{trade['dias_trade']:<5} "
                  f"{trade['profit_pct']:<7.2%} "
                  f"{trade['resultado']:<20}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Analizar trades basados en VIX_Fix con target de profit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python trade_analyzer.py --inicio 2025-01-01 --fin 2025-08-04
  python trade_analyzer.py -i 2025-01-01 -f 2025-08-04 --target 0.03 --max-dias 20
        """
    )
    
    parser.add_argument('--ticker', '-t', default='GGAL.BA', help='Símbolo del ticker')
    parser.add_argument('--inicio', '-i', required=True, help='Fecha de inicio (YYYY-MM-DD)')
    parser.add_argument('--fin', '-f', required=True, help='Fecha de fin (YYYY-MM-DD)')
    parser.add_argument('--target', type=float, default=0.04, help='Target de profit (default: 0.04 = 4%)')
    parser.add_argument('--max-dias', type=int, default=30, help='Máximo días por trade (default: 30)')
    
    args = parser.parse_args()
    
    try:
        # Validar fechas
        datetime.strptime(args.inicio, '%Y-%m-%d')
        datetime.strptime(args.fin, '%Y-%m-%d')
        
        # Crear analizador
        analyzer = TradeAnalyzer(
            profit_target=args.target,
            max_hold_days=args.max_dias
        )
        
        print(f"Analizando trades de {args.ticker} desde {args.inicio} hasta {args.fin}")
        print(f"Target: {args.target:.1%} | Máximo días: {args.max_dias}")
        
        # Analizar trades
        resultados = analyzer.analizar_trades(args.ticker, args.inicio, args.fin)
        analyzer.mostrar_resultados_trades(resultados, args.ticker)
        
    except ValueError as e:
        print(f"Error en las fechas: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperación cancelada")
        sys.exit(0)

if __name__ == "__main__":
    main()