"""
Script para mergear Params y Params_fix por país
Uso: python merge_params.py <country>
Ejemplo: python merge_params.py Peru
"""

import pandas as pd
import os
import sys
import numpy as np
from pathlib import Path

# Configuración de rutas
BASE_PATH = Path(__file__).parent.parent
DATA_PATH = BASE_PATH / "data"
PARAMS_PATH = DATA_PATH / "Params"
PARAMS_FIX_PATH = DATA_PATH / "Params_fix"
PARAMS_NEW_PATH = DATA_PATH / "Params_new"

# Variables a procesar
VARIABLES = ['volume_uc_KO', 'volume_uc_NOKO', 'price_lc_KO', 'price_lc_NOKO']


def merge_params(country, deduplicate=False):
    """
    Mergea parámetros de baseline (Params) con parámetros tuneados (Params_fix).
    
    Args:
        country (str): País a procesar (ej: 'Peru', 'Argentina')
        deduplicate (bool): Si True, deduplica Params baseline por combinación.
                           Si False (default), mantiene todos los duplicados originales
                           en Params y solo reemplaza las combos que están en Params_fix.
    """
    
    # Crear directorio de salida
    country_new_path = PARAMS_NEW_PATH / country
    country_new_path.mkdir(parents=True, exist_ok=True)
    
    # Definir todas las columnas esperadas
    EXPECTED_COLUMNS = [
        'combination', 'changepoint_prior_scale', 'seasonality_prior_scale',
        'holidays_prior_scale', 'seasonality_mode', 'growth', 'interval_width',
        'changepoint_range', 'MAE', 'RMSE', 'MAPE', 'range', 'range_proportion',
        'mean_range_proportion', 'RMSE_TEST', 'RMSE_TO_STD', 'best', 'good', 'acceptable', 'fixed'
    ]
    
    mode = "CON DEDUPLICACIÓN" if deduplicate else "SIN DEDUPLICACIÓN (preservando duplicados)"
    print(f"\n{'='*70}")
    print(f"MERGEANDO PARÁMETROS PARA: {country}")
    print(f"MODO: {mode}")
    print(f"{'='*70}\n")
    
    # Diccionario para almacenar resultados
    results = {}
    
    for variable in VARIABLES:
        print(f"Procesando {variable}...")
        
        # Rutas de archivos
        params_file = PARAMS_PATH / country / f"{country}_params_{variable}.csv"
        params_fix_file = PARAMS_FIX_PATH / country / f"{country}_params_{variable}.csv"
        output_file = country_new_path / f"{country}_params_{variable}.csv"
        
        try:
            # 1. Leer parámetros baseline
            if not params_file.exists():
                print(f"  ⚠ ADVERTENCIA: No existe {params_file.name}")
                results[variable] = {'status': 'skip', 'fixed': 0, 'total': 0}
                continue
            
            df_params = pd.read_csv(params_file)
            total_baseline = len(df_params)
            
            # Asegurar que todas las columnas esperadas existan
            for col in EXPECTED_COLUMNS:
                if col not in df_params.columns:
                    if col in ['MAE', 'RMSE', 'MAPE', 'range', 'range_proportion', 'mean_range_proportion', 'RMSE_TEST', 'RMSE_TO_STD']:
                        df_params[col] = np.nan
                    elif col in ['best', 'good', 'acceptable', 'fixed']:
                        df_params[col] = False
                    elif col == 'changepoint_range':
                        df_params[col] = 0.99
            
            # Deduplicar si está habilitado (mantener solo el mejor por combinación)
            if deduplicate:
                df_params = df_params.sort_values(
                    by=['combination', 'best', 'good', 'acceptable', 'mean_range_proportion'] 
                        if 'mean_range_proportion' in df_params.columns 
                        else ['combination', 'best', 'good', 'acceptable'],
                    ascending=[True, False, False, False, True] if 'mean_range_proportion' in df_params.columns else [True, False, False, False]
                )
                df_params = df_params.drop_duplicates(subset=['combination'], keep='first')
            
            # 2. Intentar leer y aplicar params_fix
            fixed_count = 0
            if params_fix_file.exists():
                df_params_fix = pd.read_csv(params_fix_file)
                fixed_count = len(df_params_fix)
                
                # Asegurar que todas las columnas esperadas existan en params_fix
                for col in EXPECTED_COLUMNS:
                    if col not in df_params_fix.columns:
                        if col in ['MAE', 'RMSE', 'MAPE', 'range', 'range_proportion', 'mean_range_proportion', 'RMSE_TEST', 'RMSE_TO_STD']:
                            df_params_fix[col] = np.nan
                        elif col in ['best', 'good', 'acceptable', 'fixed']:
                            df_params_fix[col] = False
                        elif col == 'changepoint_range':
                            df_params_fix[col] = 0.99
                
                # Marcar como True los parámetros que se van a usar (fueron tuneados y guardados intencionalmente)
                df_params_fix['best'] = True
                df_params_fix['good'] = True
                df_params_fix['acceptable'] = True
                df_params_fix['fixed'] = True  # Marcar como fijo porque viene de Params_fix
                
                # 3. Eliminar del baseline las combinaciones que están en fix
                df_params = df_params[~df_params['combination'].isin(df_params_fix['combination'])]
                
                # 4. Concatenar: params_fix van primero (para que se lean primero)
                df_params = pd.concat([df_params_fix, df_params], ignore_index=True)
                
                print(f"  ✓ {fixed_count} combinaciones sobrescritas con parámetros tuneados")
            else:
                print(f"  ℹ No encontrado params_fix, usando solo baseline")
            
            # 5. Guardar resultado (mantener solo las columnas esperadas en el orden correcto)
            df_params = df_params[EXPECTED_COLUMNS]
            df_params.to_csv(output_file, index=False)
            print(f"  ✓ Guardado: {output_file.name}")
            
            results[variable] = {
                'status': 'success',
                'fixed': fixed_count,
                'total': len(df_params),
                'baseline': total_baseline
            }
            
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            results[variable] = {'status': 'error', 'error': str(e)}
    
    # Imprimir resumen
    print_summary(country, results)


def print_summary(country, results):
    """Imprime un resumen de los resultados del merge."""
    
    print(f"\n{'='*70}")
    print(f"RESUMEN PARA {country.upper()}")
    print(f"{'='*70}\n")
    
    total_fixed = 0
    for variable, result in results.items():
        status = result.get('status')
        
        if status == 'success':
            fixed = result['fixed']
            total = result['total']
            baseline = result['baseline']
            
            print(f"{variable:20} | Baseline: {baseline:4d} | Fixed: {fixed:3d} | Total: {total:4d}")
            total_fixed += fixed
        
        elif status == 'skip':
            print(f"{variable:20} | ⚠ SALTADO - No existe baseline")
        
        elif status == 'error':
            print(f"{variable:20} | ✗ ERROR: {result['error']}")
    
    print(f"\n{'─'*70}")
    print(f"TOTAL DE COMBINACIONES SOBRESCRITAS: {total_fixed}")
    print(f"{'─'*70}\n")
    
    print(f"✓ Archivos guardados en: {PARAMS_NEW_PATH / country}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python merge_params.py <country> [--deduplicate]")
        print("\nOpciones:")
        print("  <country>          País a procesar (ej: Peru, Argentina, Chile)")
        print("  --deduplicate      Deduplica baseline. Mantiene solo el mejor parámetro")
        print("                     por cada combinación en Params")
        print("\nEjemplos:")
        print("  python merge_params.py Peru")
        print("  python merge_params.py Peru --deduplicate")
        sys.exit(1)
    
    country = sys.argv[1]
    deduplicate = '--deduplicate' in sys.argv
    
    merge_params(country, deduplicate=deduplicate)
