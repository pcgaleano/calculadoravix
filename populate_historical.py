#!/usr/bin/env python3
"""
Script para poblar datos históricos masivamente
"""
import requests
import time
from datetime import datetime, timedelta

# Configuración
BASE_URL = "http://127.0.0.1:8000/run-eod-job"
FECHA_INICIO = datetime(2025, 4, 16)  # Necesitamos desde abril
FECHA_FIN = datetime(2025, 8, 16)

def poblar_fecha(fecha_str):
    """Poblar una fecha específica"""
    try:
        url = f"{BASE_URL}?business_date={fecha_str}"
        response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            processed = data.get('symbols_processed', 0)
            failed = data.get('symbols_failed', 0)
            print(f"OK {fecha_str}: {status} - Procesados: {processed}, Fallos: {failed}")
            return True
        else:
            print(f"ERROR {fecha_str}: Error HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERROR {fecha_str}: Error - {e}")
        return False

def main():
    print("Iniciando poblacion masiva de datos historicos...")
    print(f"Rango: {FECHA_INICIO.strftime('%Y-%m-%d')} a {FECHA_FIN.strftime('%Y-%m-%d')}")
    
    fecha_actual = FECHA_FIN
    total_fechas = 0
    exitosas = 0
    
    while fecha_actual >= FECHA_INICIO:
        # Solo procesar días de semana (Lun-Vie)
        if fecha_actual.weekday() < 5:
            fecha_str = fecha_actual.strftime('%Y-%m-%d')
            total_fechas += 1
            
            if poblar_fecha(fecha_str):
                exitosas += 1
            
            # Pausa pequeña para no sobrecargar
            time.sleep(0.5)
        
        fecha_actual -= timedelta(days=1)
    
    print(f"\nResumen:")
    print(f"   Total fechas procesadas: {total_fechas}")
    print(f"   Exitosas: {exitosas}")
    print(f"   Fallidas: {total_fechas - exitosas}")
    print(f"   Tasa de exito: {(exitosas/total_fechas)*100:.1f}%")

if __name__ == "__main__":
    main()