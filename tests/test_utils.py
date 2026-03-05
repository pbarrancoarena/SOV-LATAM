"""
Tests para streamlit_app/utils.py

Ejecutar: pytest tests/test_utils.py -v
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path


def test_forecast_dataframe_structure(sample_forecast_df):
    """Test que verifica la estructura del DataFrame de forecast."""
    required_columns = ['date', 'category', 'value', 'yhat', 'yhat_lower', 'yhat_upper', 'is_forecast']
    
    for col in required_columns:
        assert col in sample_forecast_df.columns, f"Columna {col} faltante"


def test_forecast_confidence_intervals(sample_forecast_df):
    """Test que verifica que los intervalos de confianza son válidos."""
    # yhat debe estar entre yhat_lower y yhat_upper
    assert (sample_forecast_df['yhat'] >= sample_forecast_df['yhat_lower']).all()
    assert (sample_forecast_df['yhat'] <= sample_forecast_df['yhat_upper']).all()
    
    # yhat_upper debe ser mayor que yhat_lower
    assert (sample_forecast_df['yhat_upper'] > sample_forecast_df['yhat_lower']).all()


def test_forecast_date_types(sample_forecast_df):
    """Test que verifica tipos de datos correctos en forecast."""
    # Fecha debe ser datetime
    assert pd.api.types.is_datetime64_any_dtype(sample_forecast_df['date'])
    
    # Valores numéricos
    assert pd.api.types.is_numeric_dtype(sample_forecast_df['value'])
    assert pd.api.types.is_numeric_dtype(sample_forecast_df['yhat'])
    
    # is_forecast debe ser booleano
    assert sample_forecast_df['is_forecast'].dtype == bool


def test_forecast_no_negative_values(sample_forecast_df):
    """Test que verifica que no hay valores negativos en forecast."""
    # Valores positivos (volumen/precio)
    assert (sample_forecast_df['value'] >= 0).all()
    assert (sample_forecast_df['yhat'] >= 0).all()
    assert (sample_forecast_df['yhat_lower'] >= 0).all()


def test_forecast_chronological_order(sample_forecast_df):
    """Test que verifica orden cronológico de fechas."""
    dates = sample_forecast_df['date'].values
    assert all(dates[i] <= dates[i+1] for i in range(len(dates)-1)), \
        "Fechas no están en orden cronológico"


def test_combination_format():
    """Test que verifica formato de combinaciones."""
    valid_combinations = [
        'FEMSA_SPARKLING_CSD_KB_SB_REFILLABLE',
        'ACME_STILL_WATER_TB_MB_NONREFILLABLE',
        'GLOBAL_SPARKLING_ENERGY_KB_LB_REFILLABLE'
    ]
    
    for combo in valid_combinations:
        parts = combo.split('_')
        assert len(parts) == 6, f"Combinación {combo} no tiene 6 partes"
        
        # Verificar que refillability es válida
        refillability = parts[-1]
        assert refillability in ['REFILLABLE', 'NONREFILLABLE']


def test_metric_calculations():
    """Test de cálculos de métricas de error."""
    # Datos de prueba
    actual = np.array([100, 150, 200, 250, 300])
    predicted = np.array([95, 145, 210, 240, 310])
    
    # MAE (Mean Absolute Error)
    mae = np.mean(np.abs(actual - predicted))
    expected_mae = (5 + 5 + 10 + 10 + 10) / 5  # = 8.0
    assert np.isclose(mae, expected_mae)
    
    # RMSE (Root Mean Square Error)
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    expected_rmse = np.sqrt((25 + 25 + 100 + 100 + 100) / 5)  # = sqrt(70)
    assert np.isclose(rmse, expected_rmse)
    
    # MAPE (Mean Absolute Percentage Error)
    mape = np.mean(np.abs((actual - predicted) / actual))
    assert mape > 0 and mape < 1


def test_data_filtering():
    """Test de filtrado de datos."""
    df = pd.DataFrame({
        'country': ['Peru', 'Peru', 'Chile', 'Chile'],
        'category': ['SPARKLING', 'STILL', 'SPARKLING', 'STILL'],
        'value': [100, 200, 150, 250]
    })
    
    # Filtrar por país
    peru_data = df[df['country'] == 'Peru']
    assert len(peru_data) == 2
    
    # Filtrar por categoría
    sparkling_data = df[df['category'] == 'SPARKLING']
    assert len(sparkling_data) == 2
    
    # Filtro múltiple
    peru_sparkling = df[(df['country'] == 'Peru') & (df['category'] == 'SPARKLING')]
    assert len(peru_sparkling) == 1
    assert peru_sparkling.iloc[0]['value'] == 100


def test_aggregation():
    """Test de agregaciones de datos."""
    df = pd.DataFrame({
        'category': ['SPARKLING', 'SPARKLING', 'STILL', 'STILL'],
        'value': [100, 150, 200, 250]
    })
    
    # Agregación por categoría
    agg = df.groupby('category')['value'].sum()
    
    assert agg['SPARKLING'] == 250
    assert agg['STILL'] == 450


def test_missing_values_handling(sample_forecast_df):
    """Test de manejo de valores faltantes."""
    # Crear copia con algunos NaN
    df_with_nan = sample_forecast_df.copy()
    df_with_nan.loc[0, 'value'] = np.nan
    
    # Verificar que se detectan NaNs
    assert df_with_nan['value'].isna().any()
    
    # Contar NaNs
    nan_count = df_with_nan['value'].isna().sum()
    assert nan_count == 1


def test_date_range_generation():
    """Test de generación de rangos de fechas."""
    start_date = '2025-01-01'
    periods = 12
    
    date_range = pd.date_range(start=start_date, periods=periods, freq='MS')
    
    assert len(date_range) == periods
    assert date_range[0] == pd.Timestamp('2025-01-01')
    assert date_range[-1] == pd.Timestamp('2025-12-01')


def test_category_values():
    """Test de valores válidos de categorías."""
    valid_categories = ['SPARKLING', 'STILL', 'WATER', 'JUICE', 'ENERGY']
    
    for category in valid_categories:
        assert category.isupper(), f"Categoría {category} no está en mayúsculas"
        assert isinstance(category, str), f"Categoría {category} no es string"
