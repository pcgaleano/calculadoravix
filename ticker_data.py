#!/usr/bin/env python3
"""
Aplicación de consola para obtener datos de ticker GGAL en un rango de fechas
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import argparse
import sys

def obtener_datos_ticker(ticker, fecha_inicio, fecha_fin):
    """
    Obtiene datos históricos de un ticker en un rango de fechas
    
    Args:
        ticker (str): Símbolo del ticker (ej: 'GGAL.BA')
        fecha_inicio (str): Fecha de inicio en formato YYYY-MM-DD
        fecha_fin (str): Fecha de fin en formato YYYY-MM-DD
    
    Returns:
        pandas.DataFrame: Datos históricos del ticker
    """
    try:
        # Crear objeto ticker
        stock = yf.Ticker(ticker)
        
        # Obtener datos históricos
        datos = stock.history(start=fecha_inicio, end=fecha_fin)
        
        if datos.empty:
            print(f"No se encontraron datos para {ticker} en el rango especificado")
            return None
            
        return datos
        
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return None

def mostrar_datos(datos, ticker):
    """
    Muestra los datos en formato legible
    
    Args:
        datos (pandas.DataFrame): Datos del ticker
        ticker (str): Símbolo del ticker
    """
    if datos is None:
        return
        
    print(f"\n{'='*60}")
    print(f"DATOS HISTÓRICOS DE {ticker.upper()}")
    print(f"{'='*60}")
    print(f"Período: {datos.index[0].strftime('%Y-%m-%d')} a {datos.index[-1].strftime('%Y-%m-%d')}")
    print(f"Total de días: {len(datos)}")
    print(f"{'='*60}")
    
    # Mostrar resumen estadístico
    print("\nRESUMEN ESTADÍSTICO:")
    print("-" * 40)
    print(f"Precio más alto: ${datos['High'].max():.2f}")
    print(f"Precio más bajo: ${datos['Low'].min():.2f}")
    print(f"Precio promedio: ${datos['Close'].mean():.2f}")
    print(f"Volumen promedio: {datos['Volume'].mean():,.0f}")
    
    # Mostrar últimos 10 registros
    print(f"\nÚLTIMOS {min(10, len(datos))} REGISTROS:")
    print("-" * 80)
    print(datos[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10).to_string())

def validar_fecha(fecha_str):
    """
    Valida que la fecha esté en formato YYYY-MM-DD
    
    Args:
        fecha_str (str): Fecha en formato string
        
    Returns:
        datetime: Objeto datetime si es válida
        
    Raises:
        ValueError: Si la fecha no es válida
    """
    try:
        return datetime.strptime(fecha_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Fecha inválida: {fecha_str}. Use formato YYYY-MM-DD")

def main():
    """Función principal de la aplicación"""
    parser = argparse.ArgumentParser(
        description='Obtener datos históricos de ticker GGAL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python ticker_data.py --inicio 2024-01-01 --fin 2024-12-31
  python ticker_data.py -i 2024-06-01 -f 2024-06-30 --ticker GGAL.BA
        """
    )
    
    parser.add_argument(
        '--ticker', '-t',
        default='GGAL.BA',
        help='Símbolo del ticker (default: GGAL.BA)'
    )
    
    parser.add_argument(
        '--inicio', '-i',
        required=True,
        help='Fecha de inicio (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--fin', '-f',
        required=True,
        help='Fecha de fin (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    try:
        # Validar fechas
        fecha_inicio = validar_fecha(args.inicio)
        fecha_fin = validar_fecha(args.fin)
        
        if fecha_inicio >= fecha_fin:
            print("Error: La fecha de inicio debe ser anterior a la fecha de fin")
            sys.exit(1)
            
        if fecha_fin > datetime.now():
            print("Advertencia: La fecha de fin es futura, se ajustará a hoy")
            
        # Obtener y mostrar datos
        print(f"Obteniendo datos de {args.ticker} desde {args.inicio} hasta {args.fin}...")
        datos = obtener_datos_ticker(args.ticker, args.inicio, args.fin)
        mostrar_datos(datos, args.ticker)
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario")
        sys.exit(0)

if __name__ == "__main__":
    main()