#!/usr/bin/env python3
"""
Script para ejecutar carga inicial masiva de 2 años de datos
"""
import sys
import os

# Cambiar al directorio backend
os.chdir('backend')
sys.path.append('.')

from main import run_initial_data_load

if __name__ == "__main__":
    print("Iniciando carga inicial masiva de 2 años de datos...")
    print("Esto puede tomar varios minutos...")
    
    result = run_initial_data_load(years_back=2, force_reload=False)
    
    print(f"\nResultado final:")
    print(f"Status: {result['status']}")
    print(f"Simbolos procesados: {result['symbols_processed']}")
    print(f"Exitosos: {result['symbols_successful']}")
    print(f"Fallidos: {result['symbols_failed']}")
    
    if 'duration_seconds' in result:
        print(f"Duracion: {result['duration_seconds']:.1f} segundos")
    
    if result['symbols_failed'] > 0:
        print(f"\nSimbolos con problemas:")
        for detail in result.get('details', []):
            if detail['status'] != 'SUCCESS':
                print(f"  - {detail['symbol']}: {detail.get('error', 'Unknown error')}")