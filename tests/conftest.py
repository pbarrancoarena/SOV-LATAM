"""
Configuración de pytest para tests de SOV Forecasting.
"""
import pytest
import pandas as pd
from pathlib import Path

# Configurar path base del proyecto
BASE_PATH = Path(__file__).parent.parent


@pytest.fixture
def project_root():
    """Path raíz del proyecto."""
    return BASE_PATH


@pytest.fixture
def data_examples_path():
    """Path al directorio de ejemplos."""
    return BASE_PATH / "data" / "examples"


@pytest.fixture
def sample_params_df():
    """
    DataFrame de ejemplo con parámetros Prophet.
    """
    return pd.DataFrame({
        'combination': ['COMBO_A', 'COMBO_B', 'COMBO_C'],
        'changepoint_prior_scale': [0.05, 0.1, 0.03],
        'seasonality_prior_scale': [1.0, 2.0, 0.5],
        'holidays_prior_scale': [0.1, 0.5, 0.05],
        'seasonality_mode': ['additive', 'multiplicative', 'additive'],
        'growth': ['linear', 'linear', 'linear'],
        'interval_width': [0.95, 0.90, 0.95],
        'changepoint_range': [0.9, 0.85, 0.95],
        'MAE': [1250.5, 1380.2, 890.3],
        'RMSE': [1680.3, 1850.7, 1150.8],
        'MAPE': [0.08, 0.09, 0.06],
        'range': [2500.0, 2800.0, 1800.0],
        'range_proportion': [0.15, 0.18, 0.12],
        'mean_range_proportion': [0.12, 0.15, 0.10],
        'RMSE_TEST': [1720.4, 1890.1, 1180.5],
        'RMSE_TO_STD': [0.45, 0.52, 0.38],
        'best': [True, False, True],
        'good': [True, True, True],
        'acceptable': [True, True, True],
        'fixed': [False, False, False]
    })


@pytest.fixture
def sample_params_fix_df():
    """
    DataFrame de ejemplo con parámetros ajustados (fix).
    """
    return pd.DataFrame({
        'combination': ['COMBO_A'],
        'changepoint_prior_scale': [0.03],
        'seasonality_prior_scale': [0.8],
        'holidays_prior_scale': [0.08],
        'seasonality_mode': ['additive'],
        'growth': ['linear'],
        'interval_width': [0.95],
        'changepoint_range': [0.92],
        'MAE': [1180.2],
        'RMSE': [1580.5],
        'MAPE': [0.075],
        'range': [2400.0],
        'range_proportion': [0.14],
        'mean_range_proportion': [0.11],
        'RMSE_TEST': [1620.8],
        'RMSE_TO_STD': [0.43],
        'best': [True],
        'good': [True],
        'acceptable': [True],
        'fixed': [True]
    })


@pytest.fixture
def sample_forecast_df():
    """
    DataFrame de ejemplo con forecast.
    """
    return pd.DataFrame({
        'date': pd.date_range('2025-01-01', periods=12, freq='MS'),
        'category': ['SPARKLING'] * 12,
        'value': [125000, 128500, 132000, 135500, 138000, 141000, 
                  143500, 145000, 142000, 139000, 136000, 138500],
        'yhat': [124850, 128320, 131980, 135420, 137850, 140980,
                 143320, 144850, 141980, 138920, 135880, 138320],
        'yhat_lower': [120200, 123600, 127100, 130400, 132800, 135800,
                       138100, 139700, 136900, 133900, 130900, 133200],
        'yhat_upper': [129500, 133000, 136900, 140500, 142900, 146200,
                       148600, 150000, 147100, 144000, 140900, 143500],
        'is_forecast': [False] * 12
    })
