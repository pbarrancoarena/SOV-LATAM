"""
Tests para scripts/merge_params.py

Ejecutar: pytest tests/test_merge_params.py -v
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Agregar path del proyecto para imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_sample_params_fixture(sample_params_df):
    """Test que verifica la fixture de parámetros."""
    assert len(sample_params_df) == 3
    assert 'combination' in sample_params_df.columns
    assert 'changepoint_prior_scale' in sample_params_df.columns
    assert sample_params_df['best'].sum() == 2


def test_sample_params_fix_fixture(sample_params_fix_df):
    """Test que verifica la fixture de parámetros fix."""
    assert len(sample_params_fix_df) == 1
    assert sample_params_fix_df.iloc[0]['combination'] == 'COMBO_A'
    assert sample_params_fix_df.iloc[0]['fixed'] == True


def test_merge_logic_basic(sample_params_df, sample_params_fix_df):
    """
    Test de lógica básica de merge:
    - Params_fix debe sobrescribir Params
    - La combinación COMBO_A debe venir de params_fix
    """
    # Simular merge: eliminar COMBO_A de params y agregar params_fix
    params_merged = sample_params_df[
        ~sample_params_df['combination'].isin(sample_params_fix_df['combination'])
    ]
    params_merged = pd.concat([sample_params_fix_df, params_merged], ignore_index=True)
    
    # Verificaciones
    assert len(params_merged) == 3  # 1 fix + 2 originales
    combo_a = params_merged[params_merged['combination'] == 'COMBO_A'].iloc[0]
    assert combo_a['fixed'] == True
    assert combo_a['changepoint_prior_scale'] == 0.03  # Valor de fix, no original (0.05)


def test_deduplication_logic(sample_params_df):
    """
    Test de lógica de deduplicación:
    - Debe mantener solo una fila por combinación
    - Debe mantener la fila marcada como 'best'
    """
    # Agregar duplicados
    df_with_dupes = pd.concat([
        sample_params_df,
        pd.DataFrame({
            'combination': ['COMBO_A'],
            'changepoint_prior_scale': [0.2],
            'seasonality_prior_scale': [3.0],
            'holidays_prior_scale': [1.0],
            'seasonality_mode': ['multiplicative'],
            'growth': ['linear'],
            'interval_width': [0.85],
            'changepoint_range': [0.8],
            'MAE': [2000.0],
            'RMSE': [2500.0],
            'MAPE': [0.15],
            'range': [3500.0],
            'range_proportion': [0.25],
            'mean_range_proportion': [0.22],
            'RMSE_TEST': [2600.0],
            'RMSE_TO_STD': [0.75],
            'best': [False],
            'good': [False],
            'acceptable': [True],
            'fixed': [False]
        })
    ], ignore_index=True)
    
    # Deduplicar manteniendo el mejor
    df_deduped = df_with_dupes.sort_values(
        by=['combination', 'best', 'good', 'acceptable', 'mean_range_proportion'],
        ascending=[True, False, False, False, True]
    ).drop_duplicates(subset=['combination'], keep='first')
    
    assert len(df_deduped) == 3  # 3 combinaciones únicas
    combo_a = df_deduped[df_deduped['combination'] == 'COMBO_A'].iloc[0]
    assert combo_a['best'] == True
    assert combo_a['changepoint_prior_scale'] == 0.05  # El mejor, no el duplicado


def test_column_presence(sample_params_df):
    """Test que verifica la presencia de columnas esperadas."""
    expected_columns = [
        'combination', 'changepoint_prior_scale', 'seasonality_prior_scale',
        'holidays_prior_scale', 'seasonality_mode', 'growth', 'interval_width',
        'changepoint_range', 'MAE', 'RMSE', 'MAPE', 'best', 'good', 'acceptable', 'fixed'
    ]
    
    for col in expected_columns:
        assert col in sample_params_df.columns, f"Columna {col} faltante"


def test_data_types(sample_params_df):
    """Test que verifica tipos de datos correctos."""
    # Strings
    assert sample_params_df['combination'].dtype == object
    assert sample_params_df['seasonality_mode'].dtype == object
    
    # Floats
    assert pd.api.types.is_numeric_dtype(sample_params_df['changepoint_prior_scale'])
    assert pd.api.types.is_numeric_dtype(sample_params_df['MAE'])
    
    # Booleans
    assert sample_params_df['best'].dtype == bool
    assert sample_params_df['fixed'].dtype == bool


def test_hyperparameter_ranges(sample_params_df):
    """Test que verifica rangos válidos de hiperparámetros."""
    # changepoint_prior_scale: 0.001 - 0.5
    assert (sample_params_df['changepoint_prior_scale'] >= 0.001).all()
    assert (sample_params_df['changepoint_prior_scale'] <= 0.5).all()
    
    # interval_width: 0.80 - 0.95
    assert (sample_params_df['interval_width'] >= 0.80).all()
    assert (sample_params_df['interval_width'] <= 0.95).all()
    
    # changepoint_range: 0.8 - 0.99
    assert (sample_params_df['changepoint_range'] >= 0.8).all()
    assert (sample_params_df['changepoint_range'] <= 0.99).all()


def test_metrics_validity(sample_params_df):
    """Test que verifica que las métricas sean válidas."""
    # MAE, RMSE deben ser positivos
    assert (sample_params_df['MAE'] > 0).all()
    assert (sample_params_df['RMSE'] > 0).all()
    
    # MAPE debe estar entre 0 y 1 (proporción)
    assert (sample_params_df['MAPE'] >= 0).all()
    assert (sample_params_df['MAPE'] <= 1).all()
    
    # RMSE >= MAE (propiedad matemática)
    assert (sample_params_df['RMSE'] >= sample_params_df['MAE']).all()


def test_fixed_flag_consistency(sample_params_fix_df):
    """Test que verifica que params_fix tenga flag fixed=True."""
    assert (sample_params_fix_df['fixed'] == True).all()


def test_example_files_exist(data_examples_path):
    """Test que verifica que existen archivos de ejemplo."""
    expected_files = [
        'Example_params_volume_uc_KO.csv',
        'Example_params_volume_uc_KO_fix.csv',
        'Example_forecast_baseline_category.csv'
    ]
    
    for filename in expected_files:
        filepath = data_examples_path / filename
        assert filepath.exists(), f"Archivo de ejemplo {filename} no encontrado"


def test_load_example_params(data_examples_path):
    """Test de carga real de archivo de ejemplo."""
    filepath = data_examples_path / 'Example_params_volume_uc_KO.csv'
    
    if not filepath.exists():
        pytest.skip("Archivo de ejemplo no encontrado")
    
    df = pd.read_csv(filepath)
    
    # Verificaciones básicas
    assert len(df) > 0
    assert 'combination' in df.columns
    assert 'changepoint_prior_scale' in df.columns
    assert 'fixed' in df.columns
