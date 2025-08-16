#!/usr/bin/env python3
"""
Analizador Simple de Ticker - Análisis completo de trading con VIX_Fix
Uso: python analizar_ticker.py TICKER FECHA_INICIO FECHA_FIN
"""

import sys
import argparse
from trade_analyzer import TradeAnalyzer

def main():
    """Función principal simplificada"""
    parser = argparse.ArgumentParser(
        description='Análisis completo de trading para un ticker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python analizar_ticker.py GGAL.BA 2025-01-01 2025-08-04
  python analizar_ticker.py CARC.BA 2025-01-01 2025-08-04  
  python analizar_ticker.py BTC-USD 2025-01-01 2025-08-04
        """
    )
    
    parser.add_argument('ticker', help='Símbolo del ticker (ej: GGAL.BA, CARC.BA, BTC-USD)')
    parser.add_argument('fecha_inicio', help='Fecha de inicio (YYYY-MM-DD)')
    parser.add_argument('fecha_fin', help='Fecha de fin (YYYY-MM-DD)')
    parser.add_argument('--target', type=float, default=0.04, help='Target de profit (default: 0.04 = 4%)')
    parser.add_argument('--max-dias', type=int, default=30, help='Máximo días por trade (default: 30)')
    
    args = parser.parse_args()
    
    try:
        # Crear analizador
        analyzer = TradeAnalyzer(
            profit_target=args.target,
            max_hold_days=args.max_dias
        )
        
        print(f"Analizando {args.ticker} desde {args.fecha_inicio} hasta {args.fecha_fin}")
        print(f"Target: {args.target:.1%} | Máximo días: {args.max_dias}")
        
        # Analizar trades
        resultados = analyzer.analizar_trades(args.ticker, args.fecha_inicio, args.fecha_fin)
        analyzer.mostrar_resultados_trades(resultados, args.ticker)
        
        return resultados
        
    except ValueError as e:
        print(f"Error en las fechas: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperación cancelada")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()