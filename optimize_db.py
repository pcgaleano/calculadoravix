#!/usr/bin/env python3
"""
Optimización de SQLite para producción
"""

import sqlite3
import os

def optimize_sqlite_production(db_path):
    """Optimizar SQLite para producción"""
    
    print(f"🔧 Optimizando base de datos: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # WAL Mode para mejor concurrencia
    cursor.execute("PRAGMA journal_mode=WAL;")
    print("✅ WAL mode activado")
    
    # Optimizaciones de performance
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA cache_size=10000;")
    cursor.execute("PRAGMA temp_store=memory;")
    cursor.execute("PRAGMA mmap_size=268435456;")  # 256MB
    
    # Análisis de tablas para optimizar queries
    cursor.execute("ANALYZE;")
    print("✅ Análisis de tablas completado")
    
    # Vacuum para compactar
    cursor.execute("VACUUM;")
    print("✅ Base de datos compactada")
    
    # Crear índices adicionales si no existen
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticker_date ON market_data(ticker, date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_ticker ON market_data(date, ticker);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticker_quality ON market_data(ticker, quality_score);")
        print("✅ Índices optimizados")
    except Exception as e:
        print(f"⚠️ Error creando índices: {e}")
    
    conn.commit()
    conn.close()
    
    # Verificar tamaño
    size_mb = os.path.getsize(db_path) / (1024 * 1024)
    print(f"📊 Tamaño de DB: {size_mb:.2f} MB")

if __name__ == "__main__":
    db_path = "backend/trading_dashboard.db"
    if os.path.exists(db_path):
        optimize_sqlite_production(db_path)
    else:
        print(f"❌ No se encontró la base de datos: {db_path}")