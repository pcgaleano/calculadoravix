#!/usr/bin/env python3
"""
Script inteligente para poblar últimos 3 meses con verificación de duplicados
y actualización solo cuando sea necesario
"""
import requests
import sqlite3
import time
from datetime import datetime, timedelta
import os

# Configuración
BASE_URL = "http://127.0.0.1:8000/run-eod-job"
DB_PATH = "backend/trading_dashboard.db"
MESES_ATRAS = 3

def conectar_bd():
    """Conectar a la base de datos"""
    return sqlite3.connect(DB_PATH)

def obtener_fechas_existentes():
    """Obtener todas las fechas que ya existen en la BD"""
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT business_date FROM market_data_eod ORDER BY business_date")
    fechas = {row[0] for row in cursor.fetchall()}
    
    conn.close()
    return fechas

def obtener_simbolos_por_fecha(fecha):
    """Obtener símbolos que existen para una fecha específica"""
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("SELECT symbol FROM market_data_eod WHERE business_date = ?", (fecha,))
    simbolos = {row[0] for row in cursor.fetchall()}
    
    conn.close()
    return simbolos

def obtener_total_simbolos_esperados():
    """Obtener total de símbolos únicos en la BD"""
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(DISTINCT symbol) FROM market_data_eod")
    total = cursor.fetchone()[0]
    
    conn.close()
    return total if total > 0 else 58  # Default esperado

def verificar_fecha_completa(fecha):
    """Verificar si una fecha tiene todos los símbolos esperados"""
    simbolos_fecha = obtener_simbolos_por_fecha(fecha)
    total_esperado = obtener_total_simbolos_esperados()
    
    # Si tenemos al menos 50+ símbolos, consideramos la fecha completa
    return len(simbolos_fecha) >= max(50, total_esperado * 0.8)

def poblar_fecha(fecha_str, forzar=False):
    """Poblar una fecha específica"""
    try:
        url = f"{BASE_URL}?business_date={fecha_str}"
        response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            processed = data.get('symbols_processed', 0)
            failed = data.get('symbols_failed', 0)
            
            if status == 'SUCCESS':
                print(f"  NUEVO {fecha_str}: {processed} simbolos procesados")
                return True
            elif status == 'PARTIAL':
                print(f"  PARCIAL {fecha_str}: {processed} OK, {failed} fallos")
                return True
            else:
                print(f"  FALLO {fecha_str}: {status}")
                return False
        else:
            print(f"  ERROR {fecha_str}: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ERROR {fecha_str}: {e}")
        return False

def generar_fechas_ultimos_meses():
    """Generar lista de fechas de los últimos N meses (solo días hábiles)"""
    hoy = datetime.now()
    fecha_inicio = hoy - timedelta(days=MESES_ATRAS * 30)  # Aproximadamente 3 meses
    
    fechas = []
    fecha_actual = fecha_inicio
    
    while fecha_actual <= hoy:
        # Solo días de semana (Lun-Vie)
        if fecha_actual.weekday() < 5:
            fechas.append(fecha_actual.strftime('%Y-%m-%d'))
        fecha_actual += timedelta(days=1)
    
    return sorted(fechas)

def main():
    print("Iniciando carga inteligente de ultimos 3 meses...")
    print(f"Base de datos: {DB_PATH}")
    
    # Verificar que la BD existe
    if not os.path.exists(DB_PATH):
        print(f"ERROR: No se encuentra la base de datos en {DB_PATH}")
        return
    
    # Obtener fechas existentes
    fechas_existentes = obtener_fechas_existentes()
    print(f"Fechas ya en BD: {len(fechas_existentes)}")
    
    # Generar fechas objetivo
    fechas_objetivo = generar_fechas_ultimos_meses()
    print(f"Fechas objetivo (ultimos 3 meses): {len(fechas_objetivo)}")
    print(f"Rango: {fechas_objetivo[0]} a {fechas_objetivo[-1]}")
    
    # Procesar fechas
    nuevas = 0
    actualizadas = 0
    omitidas = 0
    
    for fecha in fechas_objetivo:
        if fecha in fechas_existentes:
            # Verificar si la fecha está completa
            if verificar_fecha_completa(fecha):
                print(f"OMITIR {fecha}: Ya completa")
                omitidas += 1
            else:
                print(f"ACTUALIZAR {fecha}: Datos incompletos")
                if poblar_fecha(fecha, forzar=True):
                    actualizadas += 1
        else:
            print(f"NUEVA {fecha}: No existe")
            if poblar_fecha(fecha):
                nuevas += 1
        
        # Pausa para no sobrecargar
        time.sleep(0.3)
    
    # Resumen final
    print(f"\nResumen final:")
    print(f"  Fechas nuevas agregadas: {nuevas}")
    print(f"  Fechas actualizadas: {actualizadas}")
    print(f"  Fechas omitidas (ya completas): {omitidas}")
    print(f"  Total procesadas: {nuevas + actualizadas}")
    
    # Verificar estado final
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_data_eod WHERE symbol = 'ETH-USD'")
    eth_records = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT business_date) FROM market_data_eod")
    total_dates = cursor.fetchone()[0]
    conn.close()
    
    print(f"\nEstado final de la BD:")
    print(f"  Registros ETH-USD: {eth_records}")
    print(f"  Fechas unicas totales: {total_dates}")
    print(f"  Status: {'SUFICIENTE' if eth_records >= 50 else 'INSUFICIENTE'} para VIX_Fix")

if __name__ == "__main__":
    main()