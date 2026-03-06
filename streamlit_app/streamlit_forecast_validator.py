import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import logging
import random
from prophet import Prophet
from datetime import datetime
import os
from pathlib import Path

# Silence prophet logging
logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").disabled = True
logging.getLogger("pystan").disabled = True

# Suprimir warnings
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIG Y PATHS
# ============================================================================
BASE_PATH = Path(__file__).parent.parent
DATA_PATH = BASE_PATH / "data"
PARAMS_PATH = DATA_PATH / "Params"
PARAMS_FIX_PATH = DATA_PATH / "Params_fix"
ANALYSIS_PATH = BASE_PATH / "historical_decisions" / "analysis_combinations.json"

# Años permitidos para visualización
ALLOWED_YEARS = [2024, 2025, 2026]
YEAR_COLORS = {2024: '#1f77b4', 2025: '#ff7f0e', 2026: '#d62728'}

# Variable mapping
VARIABLE_MAPPING = {
    'volumen_ko': 'volume_uc_KO_ACTUAL',
    'volumen_noko': 'volume_uc_NOKO_ACTUAL',
    'precio_ko': 'price_lc_KO_ACTUAL',
    'precio_noko': 'price_lc_NOKO_ACTUAL'
}

VARIABLE_BASE_MAPPING = {
    'volumen_ko': 'volume_uc_KO',
    'volumen_noko': 'volume_uc_NOKO',
    'precio_ko': 'price_lc_KO',
    'precio_noko': 'price_lc_NOKO'
}

REVERSE_MAPPING = {v: k for k, v in VARIABLE_BASE_MAPPING.items()}

# ============================================================================
# RANDOM SEED (Reproducibilidad)
# ============================================================================
def set_random_seed(seed):
    """Fija todos los seeds para reproducibilidad en entrenamientos"""
    np.random.seed(seed)
    random.seed(seed)
    os.environ['STAN_SEED'] = str(seed)

# ============================================================================
# FUNCIONES HELPER
# ============================================================================

@st.cache_data
def load_analysis_combinations():
    """Carga las combinaciones desde el JSON"""
    with open(ANALYSIS_PATH, 'r') as f:
        combinations = json.load(f)
    return combinations

@st.cache_data
def load_country_data(country):
    """Carga los datos históricos del país"""
    filepath = DATA_PATH / f"{country}_forecast_baseline_intervalo_conf.csv"
    if not filepath.exists():
        st.error(f"Archivo no encontrado: {filepath}")
        return None
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

@st.cache_data
def load_params(country, variable_base):
    """Carga los parámetros para una variable específica"""
    filepath = PARAMS_PATH / country / f"{country}_params_{variable_base}.csv"
    if not filepath.exists():
        st.warning(f"Archivo de parámetros no encontrado: {filepath}")
        return None
    df = pd.read_csv(filepath)
    return df

def get_best_params(df_params, combination, expanded_combos=None):
    """Obtiene los mejores parámetros para una combinación.
    
    Si la combinación no se encuentra exactamente y hay expanded_combos,
    intenta obtener parámetros promediados de las combinaciones específicas.
    Si no encuentra ningún parámetro, devuelve valores por defecto razonables.
    """
    mask = df_params['combination'] == combination
    
    # Si encuentra la combinación exacta, retornarla
    if mask.any():
        df_sorted = df_params[mask].sort_values(by=['best', 'MAPE'], ascending=[False, True])
        best_row = df_sorted.iloc[0]
        
        params = {
            'changepoint_prior_scale': best_row['changepoint_prior_scale'],
            'seasonality_prior_scale': best_row['seasonality_prior_scale'],
            'holidays_prior_scale': best_row['holidays_prior_scale'],
            'seasonality_mode': best_row['seasonality_mode'],
            'growth': best_row['growth'],
            'interval_width': best_row['interval_width']
        }
        return params, best_row, 'exact'
    
    # Si no encuentra exacta pero hay combinaciones expandidas, usar la primera disponible
    if expanded_combos and len(expanded_combos) > 0:
        # Buscar parámetros para las combinaciones específicas expandidas
        specific_combos = [c['combo_key'] for c in expanded_combos]
        mask_expanded = df_params['combination'].isin(specific_combos)
        
        if mask_expanded.any():
            # Obtener el promedio de parámetros de las combinaciones específicas
            df_expanded = df_params[mask_expanded]
            
            # Calcular promedios numéricos
            avg_changepoint = df_expanded['changepoint_prior_scale'].mean()
            avg_seasonality = df_expanded['seasonality_prior_scale'].mean()
            avg_holidays = df_expanded['holidays_prior_scale'].mean()
            avg_interval = df_expanded['interval_width'].mean() if 'interval_width' in df_expanded.columns else 0.95
            
            # Usar mode para seasonality_mode (elegir el más frecuente)
            seasonality_mode = df_expanded['seasonality_mode'].mode()[0] if len(df_expanded['seasonality_mode'].mode()) > 0 else 'additive'
            growth = df_expanded['growth'].mode()[0] if 'growth' in df_expanded.columns and len(df_expanded['growth'].mode()) > 0 else 'linear'
            
            params = {
                'changepoint_prior_scale': avg_changepoint,
                'seasonality_prior_scale': avg_seasonality,
                'holidays_prior_scale': avg_holidays,
                'seasonality_mode': seasonality_mode,
                'growth': growth,
                'interval_width': avg_interval
            }
            
            # Crear un objeto similar a best_row con los promedios
            best_row = df_expanded.iloc[0].copy()
            best_row['changepoint_prior_scale'] = avg_changepoint
            best_row['seasonality_prior_scale'] = avg_seasonality
            best_row['holidays_prior_scale'] = avg_holidays
            
            return params, best_row, 'averaged'
    
    # Si no encuentra parámetros, intentar buscar cualquier parámetro del mismo país/variable
    # y usar el promedio general como referencia
    if len(df_params) > 0:
        avg_changepoint = df_params['changepoint_prior_scale'].mean()
        avg_seasonality = df_params['seasonality_prior_scale'].mean()
        avg_holidays = df_params['holidays_prior_scale'].mean()
        avg_interval = df_params['interval_width'].mean() if 'interval_width' in df_params.columns else 0.95
        
        seasonality_mode = df_params['seasonality_mode'].mode()[0] if len(df_params['seasonality_mode'].mode()) > 0 else 'additive'
        growth = df_params['growth'].mode()[0] if 'growth' in df_params.columns and len(df_params['growth'].mode()) > 0 else 'linear'
        
        params = {
            'changepoint_prior_scale': avg_changepoint,
            'seasonality_prior_scale': avg_seasonality,
            'holidays_prior_scale': avg_holidays,
            'seasonality_mode': seasonality_mode,
            'growth': growth,
            'interval_width': avg_interval
        }
        
        # Crear un objeto best_row genérico
        best_row = pd.Series({
            'changepoint_prior_scale': avg_changepoint,
            'seasonality_prior_scale': avg_seasonality,
            'holidays_prior_scale': avg_holidays,
            'seasonality_mode': seasonality_mode,
            'growth': growth,
            'interval_width': avg_interval,
            'combination': combination
        })
        
        return params, best_row, 'general_average'
    
    # Última opción: valores por defecto razonables
    default_params = {
        'changepoint_prior_scale': 0.05,
        'seasonality_prior_scale': 0.1,
        'holidays_prior_scale': 0.01,
        'seasonality_mode': 'additive',
        'growth': 'linear',
        'interval_width': 0.95
    }
    
    default_row = pd.Series({
        'changepoint_prior_scale': 0.05,
        'seasonality_prior_scale': 0.1,
        'holidays_prior_scale': 0.01,
        'seasonality_mode': 'additive',
        'growth': 'linear',
        'interval_width': 0.95,
        'combination': combination
    })
    
    return default_params, default_row, 'default'

def get_data_for_combination(df_country, bottler, category, sub_category, ms_ss, refillability):
    """Filtra los datos para una combinación específica.
    Si algún parámetro es 'All', incluye todos los valores de ese campo (wildcard).
    """
    mask = pd.Series([True] * len(df_country), index=df_country.index)
    
    # Aplicar filtros solo si el valor NO es "All"
    if bottler != "All":
        mask &= (df_country['Bottler'] == bottler)
    if category != "All":
        mask &= (df_country['Category'] == category)
    if sub_category != "All":
        mask &= (df_country['Sub_Category'] == sub_category)
    if ms_ss != "All":
        mask &= (df_country['MS_SS'] == ms_ss)
    if refillability != "All":
        mask &= (df_country['Refillability'] == refillability)
    
    return df_country[mask].sort_values('Date').reset_index(drop=True)

def get_expanded_combinations(df_country, bottler, category, sub_category, ms_ss, refillability):
    """Expande una combinación con 'All' a todas las combinaciones específicas subyacentes.
    Retorna lista de diccionarios con todas las combinaciones específicas.
    """
    # Primero filtrar los datos según la combinación (respetando "All")
    df_filtered = get_data_for_combination(df_country, bottler, category, sub_category, ms_ss, refillability)
    
    if df_filtered.empty:
        return []
    
    # Obtener valores únicos para cada dimensión
    unique_bottlers = [bottler] if bottler != "All" else df_filtered['Bottler'].unique().tolist()
    unique_categories = [category] if category != "All" else df_filtered['Category'].unique().tolist()
    unique_subcats = [sub_category] if sub_category != "All" else df_filtered['Sub_Category'].unique().tolist()
    unique_ms_ss = [ms_ss] if ms_ss != "All" else df_filtered['MS_SS'].unique().tolist()
    unique_refills = [refillability] if refillability != "All" else df_filtered['Refillability'].unique().tolist()
    
    # Generar todas las combinaciones específicas
    combinations = []
    for b in unique_bottlers:
        for c in unique_categories:
            for sc in unique_subcats:
                for m in unique_ms_ss:
                    for r in unique_refills:
                        combo_key = f"{b}_{c}_{sc}_{m}_{r}"
                        combinations.append({
                            'Bottler': b,
                            'Category': c,
                            'Sub_Category': sc,
                            'MS_SS': m,
                            'Refillability': r,
                            'combo_key': combo_key
                        })
    
    return combinations

def prepare_prophet_data(df_combination, variable_actual):
    """Prepara datos para Prophet.
    Si el dataframe tiene múltiples combinaciones, las agrega por fecha.
    """
    # Verificar si la variable existe
    if variable_actual not in df_combination.columns:
        return pd.DataFrame(columns=['ds', 'y'])
    
    # Agregar por fecha sumando los valores
    df_agg = df_combination.groupby('Date')[variable_actual].sum().reset_index()
    df_agg.columns = ['ds', 'y']
    df_agg = df_agg[df_agg['y'] > 0].dropna()
    return df_agg

def train_prophet_model(df_prophet, params, random_seed=None, outlier_holidays=None):
    """Entrena un modelo de Prophet con seed fijo para reproducibilidad
    
    Args:
        df_prophet: DataFrame con columnas 'ds' y 'y'
        params: Diccionario de parámetros de Prophet
        random_seed: Seed para reproducibilidad
        outlier_holidays: Lista de fechas (date objects) que son outliers/holidays especiales
                         Se removerán del entrenamiento para limpiar el modelo
    """
    if len(df_prophet) < 3:
        return None
    
    # Fijar seed si se proporciona
    if random_seed is not None:
        set_random_seed(random_seed)
    
    try:
        # Si hay outlier holidays, remover esos puntos del entrenamiento
        df_train = df_prophet.copy()
        if outlier_holidays and len(outlier_holidays) > 0:
            # Convertir fechas a datetime para comparación
            outlier_dates = []
            for date_obj in outlier_holidays:
                if isinstance(date_obj, pd.Timestamp):
                    outlier_dates.append(date_obj.date())
                else:
                    outlier_dates.append(pd.to_datetime(date_obj).date())
            
            # Filtrar: mantener solo las fechas que NO están en outliers
            df_train['date_only'] = df_train['ds'].dt.date
            df_train = df_train[~df_train['date_only'].isin(outlier_dates)].copy()
            df_train = df_train.drop('date_only', axis=1)
            
            if len(df_train) < 3:
                # Si quedan muy pocos puntos, usar todos de todas formas
                df_train = df_prophet.copy()
        
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            m = Prophet(
                changepoint_prior_scale=params['changepoint_prior_scale'],
                seasonality_prior_scale=params['seasonality_prior_scale'],
                holidays_prior_scale=params['holidays_prior_scale'],
                seasonality_mode=params['seasonality_mode'],
                growth=params['growth'],
                interval_width=params['interval_width']
            )
            m.add_country_holidays(country_name='US')
            m.fit(df_train)
        return m
    except Exception as e:
        error_msg = str(e)[:80]
        st.error(f"❌ Error: {error_msg}")
        return None

def make_forecast(m, periods=12, include_intervals=True):
    """Genera pronóstico
    
    Args:
        m: Modelo Prophet entrenado
        periods: Número de períodos a pronosticar
        include_intervals: Si True, incluye yhat_lower y yhat_upper
    """
    if m is None:
        return None
    
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            future = m.make_future_dataframe(periods=periods, freq='MS')
            forecast = m.predict(future)
        
        if include_intervals:
            return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        else:
            return forecast[['ds', 'yhat']]
    except Exception as e:
        return None

def calculate_metrics(y_true, y_pred):
    """Calcula métricas de error"""
    mask = ~(np.isnan(y_true) | np.isnan(y_pred)) & (y_true > 0)
    if not mask.any():
        return {'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan}
    
    y_t = y_true[mask]
    y_p = y_pred[mask]
    
    mae = np.mean(np.abs(y_t - y_p))
    rmse = np.sqrt(np.mean((y_t - y_p) ** 2))
    mape = np.mean(np.abs((y_t - y_p) / y_t)) * 100
    
    return {'MAE': mae, 'RMSE': rmse, 'MAPE': mape}

def get_forecast_variations(df_params_best, changepoint_range=(0.001, 0.1), seasonality_range=(0.001, 0.5)):
    """Genera dos variaciones de parámetros"""
    base_changepoint = df_params_best['changepoint_prior_scale']
    base_seasonality = df_params_best['seasonality_prior_scale']
    
    # Variación 1: Aumentar changepoint_prior_scale
    var1_changepoint = min(base_changepoint * 10, changepoint_range[1])
    var1_params = df_params_best.copy()
    var1_params['changepoint_prior_scale'] = var1_changepoint
    
    # Variación 2: Aumentar seasonality_prior_scale
    var2_seasonality = min(base_seasonality * 10, seasonality_range[1])
    var2_params = df_params_best.copy()
    var2_params['seasonality_prior_scale'] = var2_seasonality
    
    return var1_params, var2_params

def ensure_params_fix_folder(country):
    """Crea la carpeta Params_fix si no existe"""
    country_params_fix = PARAMS_FIX_PATH / country
    country_params_fix.mkdir(parents=True, exist_ok=True)
    return country_params_fix

def calculate_model_error(m, df_prophet):
    """Calcula el RMSE/MAPE del modelo en los datos históricos"""
    if m is None:
        return float('inf')
    
    try:
        forecast = m.predict(df_prophet[['ds']])
        y_true = df_prophet['y'].values
        y_pred = forecast['yhat'].values
        
        mask = ~(np.isnan(y_true) | np.isnan(y_pred)) & (y_true > 0)
        if not mask.any():
            return float('inf')
        
        rmse = np.sqrt(np.mean((y_true[mask] - y_pred[mask]) ** 2))
        return rmse
    except:
        return float('inf')

def suggest_best_fit(df_prophet, best_params, slider_params, random_seed=None, outlier_holidays=None):
    """Sugiere cuál es el mejor fit entre el modelo base y el ajustado"""
    m_base = train_prophet_model(df_prophet, best_params, random_seed=random_seed, outlier_holidays=outlier_holidays)
    m_slider = train_prophet_model(df_prophet, slider_params, random_seed=random_seed, outlier_holidays=outlier_holidays)
    
    error_base = calculate_model_error(m_base, df_prophet)
    error_slider = calculate_model_error(m_slider, df_prophet)
    
    return error_base, error_slider

def plot_years_overlay(df_combination, variable_actual, variable_base, m_slider=None, outlier_holidays=None):
    """Crea una gráfica con los 3 años sobrepuestos por mes.
    Muestra actuals para todos los años y pronóstico solo para 2026.
    Similar a la visualización de streamlit_dashboard.py
    """
    # Preparar datos: agregar por año y mes
    df_plot = df_combination.copy()
    df_plot['Year'] = pd.to_datetime(df_plot['Date']).dt.year
    df_plot['Month'] = pd.to_datetime(df_plot['Date']).dt.month
    
    # Filtrar solo los últimos 3 años permitidos
    df_plot = df_plot[df_plot['Year'].isin(ALLOWED_YEARS)]
    
    # Verificar si la variable existe
    if variable_actual not in df_plot.columns:
        return None
    
    # Agregar actuals por año y mes
    df_agg = df_plot.groupby(['Year', 'Month'])[variable_actual].sum().reset_index()
    
    if df_agg.empty:
        return None
    
    # Generar pronóstico si se proporciona el modelo
    df_forecast_agg = None
    if m_slider is not None:
        try:
            # Crear rango de fechas para TODO 2026 (enero a diciembre) con frecuencia mensual
            # Esto asegura que tenemos pronóstico para los 12 meses
            dates_2026 = pd.date_range(start='2026-01-01', end='2026-12-31', freq='MS')
            df_dates_2026 = pd.DataFrame({'ds': dates_2026})
            
            # Realizar predicción para 2026
            forecast = m_slider.predict(df_dates_2026)
            
            # Procesar pronóstico
            df_forecast = forecast[['ds', 'yhat']].copy()
            df_forecast['Year'] = pd.to_datetime(df_forecast['ds']).dt.year
            df_forecast['Month'] = pd.to_datetime(df_forecast['ds']).dt.month
            
            # Agregar pronóstico por año y mes
            df_forecast_agg = df_forecast.groupby(['Year', 'Month'])['yhat'].sum().reset_index()
            df_forecast_agg.columns = ['Year', 'Month', 'forecast']
        except Exception as e:
            df_forecast_agg = None
    
    # Crear figura
    fig = go.Figure()
    
    # Agregar trazas para actuals de cada año
    for year in sorted(df_agg['Year'].unique()):
        year_data = df_agg[df_agg['Year'] == year].sort_values('Month')
        
        fig.add_trace(go.Scatter(
            x=year_data['Month'],
            y=year_data[variable_actual],
            mode='lines+markers',
            name=f'{year} (Actual)',
            line=dict(color=YEAR_COLORS.get(year, '#000000'), width=2.5),
            marker=dict(size=6),
            hovertemplate='<b>%{fullData.name}</b><br>Month: %{x}<br>Value: %{y:,.0f}<extra></extra>'
        ))
    
    # Agregar pronóstico SOLO para 2026 (último año)
    if df_forecast_agg is not None:
        year_forecast_2026 = df_forecast_agg[df_forecast_agg['Year'] == 2026].sort_values('Month')
        
        if not year_forecast_2026.empty:
            fig.add_trace(go.Scatter(
                x=year_forecast_2026['Month'],
                y=year_forecast_2026['forecast'],
                mode='lines+markers',
                name='2026 (Pronóstico)',
                line=dict(color=YEAR_COLORS.get(2026, '#d62728'), width=3, dash='dash'),
                marker=dict(size=7, symbol='diamond'),
                hovertemplate='<b>%{fullData.name}</b><br>Month: %{x}<br>Value: %{y:,.0f}<extra></extra>'
            ))
    
    # Labels de meses
    month_labels = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 
                    'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    # Resaltar meses con outliers cuando aplica.
    if outlier_holidays and len(outlier_holidays) > 0:
        outlier_months = sorted({pd.to_datetime(d).month for d in outlier_holidays})
        y_max = df_agg[variable_actual].max() if not df_agg.empty else 0
        if df_forecast_agg is not None and 'forecast' in df_forecast_agg.columns and not df_forecast_agg.empty:
            y_max = max(y_max, df_forecast_agg['forecast'].max())

        if y_max > 0 and outlier_months:
            fig.add_trace(go.Scatter(
                x=outlier_months,
                y=[y_max * 1.03] * len(outlier_months),
                mode='markers',
                name='Meses con Outliers',
                marker=dict(color='crimson', size=10, symbol='x'),
                hovertemplate='<b>Mes con outlier</b><br>Month: %{x}<extra></extra>'
            ))

    fig.update_layout(
        title=f"Comparación Histórica por Año - {variable_base}",
        xaxis=dict(
            title="Mes",
            tickmode='array',
            tickvals=list(range(1, 13)),
            ticktext=month_labels
        ),
        yaxis_title="Valor",
        hovermode='x unified',
        height=500,
        template='plotly_white',
        showlegend=True,
        legend=dict(orientation='v', yanchor='top', y=0.99, xanchor='left', x=0.01)
    )
    
    return fig

def plot_model_components(m_slider, df_prophet, variable_base):
    """Crea gráficas de referencia del modelo mostrando:
    - Tendencia con changepoints
    - Intervalo de confianza
    - Componentes estacionales
    """
    if m_slider is None:
        return None, None, None
    
    try:
        # Crear pronóstico para rango completo incluyendo histórico
        forecast = m_slider.predict(df_prophet[['ds']])
        
        if forecast is None or forecast.empty:
            return None, None, None
        
        # Gráfica 1: Tendencia con Changepoints
        try:
            fig_trend = go.Figure()
            
            # Agregar datos históricos
            fig_trend.add_trace(go.Scatter(
                x=df_prophet['ds'],
                y=df_prophet['y'],
                mode='markers',
                name='Datos Históricos',
                marker=dict(color='lightgray', size=4),
                opacity=0.6
            ))
            
            # Agregar tendencia (componente trend del pronóstico)
            if 'trend' in forecast.columns:
                fig_trend.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast['trend'],
                    mode='lines',
                    name='Tendencia',
                    line=dict(color='blue', width=2)
                ))
            
            # Agregar changepoints como líneas verticales
            if hasattr(m_slider, 'changepoints') and m_slider.changepoints is not None and len(m_slider.changepoints) > 0:
                for cp in m_slider.changepoints:
                    try:
                        fig_trend.add_vline(
                            x=cp,
                            line_dash='dash',
                            line_color='red',
                            opacity=0.5,
                            annotation_text='CP',
                            annotation_position='top',
                        )
                    except:
                        pass  # Ignorar si un changepoint específico falla
            
            fig_trend.update_layout(
                title=f"Tendencia y Changepoints - {variable_base}",
                xaxis_title="Fecha",
                yaxis_title="Valor",
                hovermode='x unified',
                height=400,
                template='plotly_white',
                showlegend=True
            )
        except Exception as e:
            fig_trend = None
        
        # Gráfica 2: Intervalo de Confianza
        try:
            fig_interval = go.Figure()
            
            # Agregar datos históricos
            fig_interval.add_trace(go.Scatter(
                x=df_prophet['ds'],
                y=df_prophet['y'],
                mode='markers',
                name='Datos Históricos',
                marker=dict(color='black', size=4)
            ))
            
            # Agregar pronóstico con intervalo
            if 'yhat' in forecast.columns:
                fig_interval.add_trace(go.Scatter(
                    x=forecast['ds'],
                    y=forecast['yhat'],
                    mode='lines',
                    name='Pronóstico',
                    line=dict(color='blue', width=2)
                ))
            
            # Agregar intervalo de confianza como banda sombreada
            if 'yhat_upper' in forecast.columns and 'yhat_lower' in forecast.columns:
                upper = forecast['yhat_upper'].values.tolist()
                lower = forecast['yhat_lower'].values.tolist()
                dates = forecast['ds'].values.tolist()
                
                fig_interval.add_trace(go.Scatter(
                    x=dates + dates[::-1],
                    y=upper + lower[::-1],
                    fill='toself',
                    fillcolor='rgba(0, 100, 200, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Intervalo de Confianza (95%)',
                    hovertemplate='<extra></extra>'
                ))
            
            fig_interval.update_layout(
                title=f"Intervalo de Confianza - {variable_base}",
                xaxis_title="Fecha",
                yaxis_title="Valor",
                hovermode='x unified',
                height=400,
                template='plotly_white',
                showlegend=True
            )
        except Exception as e:
            fig_interval = None
        
        # Gráfica 3: Componentes (si existen)
        fig_components = None
        try:
            components_to_plot = []
            
            # Obtener componentes principales
            if 'yearly' in forecast.columns:
                components_to_plot.append(('yearly', 'Seasonality Yearly', 'blue'))
            if 'weekly' in forecast.columns:
                components_to_plot.append(('weekly', 'Seasonality Weekly', 'green'))
            
            if components_to_plot:
                fig_components = go.Figure()
                
                for col, name, color in components_to_plot:
                    if col in forecast.columns:
                        fig_components.add_trace(go.Scatter(
                            x=forecast['ds'],
                            y=forecast[col],
                            mode='lines',
                            name=name,
                            line=dict(color=color, width=2)
                        ))
                
                fig_components.update_layout(
                    title=f"Componentes Estacionales - {variable_base}",
                    xaxis_title="Fecha",
                    yaxis_title="Impacto",
                    hovermode='x unified',
                    height=400,
                    template='plotly_white',
                    showlegend=True
                )
        except Exception as e:
            fig_components = None
        
        return fig_trend, fig_interval, fig_components
        
    except Exception as e:
        error_msg = f"Error en plot_model_components: {str(e)}"
        return None, None, None

def save_parameters_to_fix(country, variable_base, combo_key, slider_params, expanded_combos=None):
    """Guarda los parámetros ajustados en Params_fix.
    
    Args:
        country: País
        variable_base: Variable base
        combo_key: Clave de combinación (puede contener 'All')
        slider_params: Parámetros ajustados
        expanded_combos: Lista de combinaciones específicas expandidas (opcional)
    
    Si expanded_combos se proporciona, guarda los parámetros para cada combinación específica.
    Esto permite que hiperparámetros con 'All' impacten todas las combinaciones subyacentes.
    """
    country_params_fix = ensure_params_fix_folder(country)
    filepath = country_params_fix / f"{country}_params_{variable_base}.csv"
    
    # Determinar qué combinaciones actualizar
    combos_to_update = [combo_key]
    if expanded_combos and len(expanded_combos) > 0:
        # Si hay combinaciones expandidas, actualizar cada una
        combos_to_update = [c['combo_key'] for c in expanded_combos]
    
    # Si el archivo existe, cargar. Si no, crear desde cero
    if filepath.exists():
        df_params = pd.read_csv(filepath)
        
        # Actualizar o agregar cada combinación
        for combo in combos_to_update:
            mask = df_params['combination'] == combo
            if mask.any():
                df_params.loc[mask, :] = [
                    combo,
                    slider_params['changepoint_prior_scale'],
                    slider_params['seasonality_prior_scale'],
                    slider_params['holidays_prior_scale'],
                    slider_params['seasonality_mode'],
                    slider_params['growth'],
                    slider_params['interval_width'],
                    np.nan, np.nan, np.nan, np.nan, np.nan, False, False, False
                ]
            else:
                new_row = {
                    'combination': combo,
                    'changepoint_prior_scale': slider_params['changepoint_prior_scale'],
                    'seasonality_prior_scale': slider_params['seasonality_prior_scale'],
                    'holidays_prior_scale': slider_params['holidays_prior_scale'],
                    'seasonality_mode': slider_params['seasonality_mode'],
                    'growth': slider_params['growth'],
                    'interval_width': slider_params['interval_width'],
                    'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan, 
                    'range': np.nan, 'range_proportion': np.nan,
                    'best': False, 'good': False, 'acceptable': False
                }
                df_params = pd.concat([df_params, pd.DataFrame([new_row])], ignore_index=True)
    else:
        # Crear archivo nuevo con todas las combinaciones
        rows = []
        for combo in combos_to_update:
            rows.append({
                'combination': combo,
                'changepoint_prior_scale': slider_params['changepoint_prior_scale'],
                'seasonality_prior_scale': slider_params['seasonality_prior_scale'],
                'holidays_prior_scale': slider_params['holidays_prior_scale'],
                'seasonality_mode': slider_params['seasonality_mode'],
                'growth': slider_params['growth'],
                'interval_width': slider_params['interval_width'],
                'MAE': np.nan, 'RMSE': np.nan, 'MAPE': np.nan,
                'range': np.nan, 'range_proportion': np.nan,
                'best': False, 'good': False, 'acceptable': False
            })
        df_params = pd.DataFrame(rows)
    
    df_params.to_csv(filepath, index=False)
    return filepath, len(combos_to_update)

def update_forecast_baseline(country, variable_base, df_combination, slider_params, 
                             bottler, category, sub_category, ms_ss, refillability,
                             random_seed=None, outlier_holidays=None, expanded_combos=None):
    """Actualiza el archivo de forecast baseline con nuevos pronósticos.
    
    Args:
        country: País
        variable_base: Variable base (ej: 'volume_uc_KO', 'price_lc_NOKO')
        df_combination: DataFrame con los datos filtrados para la combinación
        slider_params: Parámetros ajustados del modelo
        bottler, category, sub_category, ms_ss, refillability: Filtros de combinación
        random_seed: Seed para reproducibilidad
        outlier_holidays: Lista de fechas outliers
        expanded_combos: Lista de combinaciones específicas (si hay 'All')
    
    Returns:
        filepath: Ruta del archivo actualizado
        num_rows_updated: Número de filas actualizadas
    """
    # Archivo de forecast baseline
    forecast_file = DATA_PATH / f"{country}_forecast_baseline_intervalo_conf.csv"
    
    if not forecast_file.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {forecast_file}")
    
    # Cargar archivo de forecast
    df_forecast = pd.read_csv(forecast_file)
    df_forecast['Date'] = pd.to_datetime(df_forecast['Date'], errors='coerce')
    if 'ds' not in df_forecast.columns:
        raise ValueError("Columna 'ds' no encontrada en el archivo de forecast")
    df_forecast['ds'] = pd.to_datetime(df_forecast['ds'], errors='coerce')
    
    # Columnas a actualizar según variable_base
    forecast_col = f"{variable_base}_FORECAST"
    lower_col = f"{variable_base}_lower"
    upper_col = f"{variable_base}_upper"
    
    # Verificar que las columnas existen
    if forecast_col not in df_forecast.columns:
        raise ValueError(f"Columna {forecast_col} no encontrada en el archivo de forecast")
    
    # Obtener variable actual correspondiente
    variable_actual = None
    for key, val in VARIABLE_BASE_MAPPING.items():
        if val == variable_base:
            variable_actual = VARIABLE_MAPPING[key]
            break
    
    if variable_actual is None:
        raise ValueError(f"No se encontró variable_actual para {variable_base}")
    
    # Determinar qué combinaciones actualizar
    combos_to_process = []
    if expanded_combos and len(expanded_combos) > 0:
        # Hay 'All' - procesar cada combinación específica
        combos_to_process = expanded_combos
    else:
        # Combinación específica única
        combos_to_process = [{
            'Bottler': bottler,
            'Category': category,
            'Sub_Category': sub_category,
            'MS_SS': ms_ss,
            'Refillability': refillability
        }]
    
    total_rows_updated = 0
    
    # Procesar cada combinación
    for combo_dict in combos_to_process:
        # Filtrar datos históricos para esta combinación específica
        df_combo_specific = get_data_for_combination(
            df_combination,
            combo_dict.get('Bottler', bottler),
            combo_dict.get('Category', category),
            combo_dict.get('Sub_Category', sub_category),
            combo_dict.get('MS_SS', ms_ss),
            combo_dict.get('Refillability', refillability)
        )
        
        if df_combo_specific.empty:
            continue
        
        # Preparar datos para Prophet
        df_prophet = prepare_prophet_data(df_combo_specific, variable_actual)
        
        if len(df_prophet) < 3:
            continue
        
        # Entrenar modelo con nuevos parámetros
        m_new = train_prophet_model(df_prophet, slider_params, 
                                    random_seed=random_seed, 
                                    outlier_holidays=outlier_holidays)
        
        if m_new is None:
            continue
        
        # Generar pronóstico con intervalos de confianza
        forecast_new = make_forecast(m_new, periods=12, include_intervals=True)
        
        if forecast_new is None:
            continue
        
        # Verificar que las columnas de intervalos existen
        required_cols = ['ds', 'yhat', 'yhat_lower', 'yhat_upper']
        if not all(col in forecast_new.columns for col in required_cols):
            # Si no hay intervalos, saltear esta combinación
            continue
        
        # Crear máscara para identificar filas a actualizar en df_forecast
        mask = pd.Series([True] * len(df_forecast), index=df_forecast.index)
        mask &= (df_forecast['Bottler'] == combo_dict.get('Bottler', bottler))
        mask &= (df_forecast['Category'] == combo_dict.get('Category', category))
        mask &= (df_forecast['Sub_Category'] == combo_dict.get('Sub_Category', sub_category))
        mask &= (df_forecast['MS_SS'] == combo_dict.get('MS_SS', ms_ss))
        mask &= (df_forecast['Refillability'] == combo_dict.get('Refillability', refillability))
        
        # Actualizar pronósticos para fechas futuras.
        # En los archivos baseline suele venir como 'Forecasted' y en ocasiones como 'Forecast'.
        type_norm = df_forecast['Type'].fillna('').astype(str).str.strip().str.lower()
        mask_forecast = mask & type_norm.isin(['forecasted', 'forecast'])
        
        # Merge forecast con df_forecast usando fecha clave.
        # Para filas forecasted, 'Date' suele venir vacío y la fecha real está en 'ds'.
        forecast_new_renamed = forecast_new[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        forecast_new_renamed.columns = ['match_date', 'new_forecast', 'new_lower', 'new_upper']
        forecast_new_renamed['match_date'] = pd.to_datetime(forecast_new_renamed['match_date'], errors='coerce')

        # Preferir Date; si está vacío, usar ds.
        df_forecast['match_date'] = df_forecast['Date'].where(df_forecast['Date'].notna(), df_forecast['ds'])
        
        # Actualizar valores
        for idx in df_forecast[mask_forecast].index:
            date_val = df_forecast.loc[idx, 'match_date']
            forecast_row = forecast_new_renamed[forecast_new_renamed['match_date'] == date_val]
            
            if not forecast_row.empty:
                df_forecast.loc[idx, forecast_col] = forecast_row['new_forecast'].values[0]
                df_forecast.loc[idx, lower_col] = forecast_row['new_lower'].values[0]
                df_forecast.loc[idx, upper_col] = forecast_row['new_upper'].values[0]
                total_rows_updated += 1
    
    # Guardar archivo actualizado
    df_forecast.to_csv(forecast_file, index=False)
    
    return forecast_file, total_rows_updated

# ============================================================================
# STREAMLIT APP
# ============================================================================

st.set_page_config(page_title="Forecast Validator", layout="wide")
st.title("📊 Validador de Pronósticos - Reentrenamiento en Tiempo Real")

# Inicializar session_state para sliders
if 'changepoint_slider' not in st.session_state:
    st.session_state.changepoint_slider = 0.05
if 'seasonality_slider' not in st.session_state:
    st.session_state.seasonality_slider = 0.1
if 'holidays_slider' not in st.session_state:
    st.session_state.holidays_slider = 0.01
if 'seasonality_mode_radio' not in st.session_state:
    st.session_state.seasonality_mode_radio = 'additive'
if 'show_suggestion' not in st.session_state:
    st.session_state.show_suggestion = False
if 'use_outlier_holidays' not in st.session_state:
    st.session_state.use_outlier_holidays = False
if 'outlier_holidays_dates' not in st.session_state:
    st.session_state.outlier_holidays_dates = []

# Sidebar para selecciones
st.sidebar.header("⚙️ Configuración")

# Cargar combinaciones
combinations = load_analysis_combinations()

if not combinations:
    st.warning("No hay combinaciones en analysis_combinations.json")
    st.stop()

# Selector de país (filtro superior)
st.sidebar.subheader("📊 Filtro de País")

# Obtener países únicos de las combinaciones
available_countries = sorted(set(c['country'] for c in combinations))

# Inicializar session_state para país seleccionado
if 'selected_country_filter' not in st.session_state:
    st.session_state.selected_country_filter = available_countries[0]

selected_country = st.sidebar.selectbox(
    "País a analizar:",
    options=available_countries,
    index=available_countries.index(st.session_state.selected_country_filter),
    help="Filtra las combinaciones por país para análisis más eficiente"
)

st.session_state.selected_country_filter = selected_country

# Filtrar combinaciones por país seleccionado
filtered_combinations = [c for c in combinations if c['country'] == selected_country]

if not filtered_combinations:
    st.error(f"No hay combinaciones disponibles para {selected_country}")
    st.stop()

# Selector de combinación
st.sidebar.subheader("📊 Seleccionar Combinación")

def _combo_label(combo, is_latest=False):
    base = (
        f"{combo['country']} - {combo['Bottler']} - {combo['Category']} - "
        f"{combo['Sub_Category']} - {combo['MS_SS']} - {combo['Refillability']}"
    )
    ts = str(combo.get('timestamp', ''))[:19].replace('T', ' ')
    suffix = " (última)" if is_latest else ""
    return f"{base}{suffix} | {ts}"

# Mostrar más reciente primero, manteniendo el índice real de la lista filtrada
combo_options = list(range(len(filtered_combinations) - 1, -1, -1))
latest_idx = len(filtered_combinations) - 1

selected_combo_idx = st.sidebar.selectbox(
    f"Elige la combinación a analizar ({len(filtered_combinations)} disponibles):",
    options=combo_options,
    index=0,
    format_func=lambda i: _combo_label(filtered_combinations[i], is_latest=(i == latest_idx)),
    help="Selecciona una combinación guardada usando toda la granularidad"
)

# Información de la combinación seleccionada
current_combo = filtered_combinations[selected_combo_idx]
country = current_combo['country']
bottler = current_combo['Bottler']
category = current_combo['Category']
sub_category = current_combo['Sub_Category']
ms_ss = current_combo['MS_SS']
refillability = current_combo['Refillability']

# Obtener variables guardadas o usar default
default_variables = [
    v for v in current_combo.get('variables_to_analyze', ['volumen_ko', 'volumen_noko'])
    if v in VARIABLE_MAPPING
]
if not default_variables:
    default_variables = ['volumen_ko', 'volumen_noko']

# Sincronizar variables con la combinación seleccionada
combo_uid = (
    f"{country}|{bottler}|{category}|{sub_category}|{ms_ss}|{refillability}|"
    f"{current_combo.get('timestamp', '')}"
)
if st.session_state.get('current_combo_uid') != combo_uid:
    st.session_state.current_combo_uid = combo_uid
    st.session_state.variables_to_train_selector = default_variables

st.sidebar.divider()
st.sidebar.info(f"""
**Combinación Seleccionada:**
- Country: {country}
- Bottler: {bottler}
- Category: {category}
- Sub-Category: {sub_category}
- MS_SS: {ms_ss}
- Refillability: {refillability}
""")

# Seleccionar variables a entrenar
st.sidebar.subheader("Variables a Entrenar")
variables_to_train = st.sidebar.multiselect(
    "Selecciona las variables:",
    options=list(VARIABLE_MAPPING.keys()),
    key="variables_to_train_selector",
    help="Puedes seleccionar una o múltiples variables. Las variables predeterminadas provienen de la combinación guardada."
)

if not variables_to_train:
    st.warning("Selecciona al menos una variable")
    st.stop()

# Sliders para hiperparámetros
st.sidebar.subheader("🎚️ Hiperparámetros Ajustables")

# Opciones logarítmicas
changepoint_options = [0.001, 0.01, 0.05, 0.1, 0.5]
seasonality_options = [0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0]
holidays_options = [0.01, 0.1, 1, 5, 10]

slider_changepoint = st.sidebar.select_slider(
    "Changepoint Prior Scale",
    options=changepoint_options,
    value=st.session_state.changepoint_slider,
    help="Controla la flexibilidad del modelo para detectar cambios de tendencia",
    key="changepoint_slider_input"
)
st.session_state.changepoint_slider = slider_changepoint

slider_seasonality = st.sidebar.select_slider(
    "Seasonality Prior Scale",
    options=seasonality_options,
    value=st.session_state.seasonality_slider,
    help="Controla la fuerza del componente estacional",
    key="seasonality_slider_input"
)
st.session_state.seasonality_slider = slider_seasonality

slider_holidays = st.sidebar.select_slider(
    "Holidays Prior Scale",
    options=holidays_options,
    value=st.session_state.holidays_slider if st.session_state.holidays_slider in holidays_options else holidays_options[0],
    help="Controla el impacto de los días festivos",
    key="holidays_slider_input"
)
st.session_state.holidays_slider = slider_holidays

slider_seasonality_mode = st.sidebar.radio(
    "Seasonality Mode",
    options=['additive', 'multiplicative'],
    index=0 if st.session_state.seasonality_mode_radio == 'additive' else 1,
    help="Aditivo: efecto constante | Multiplicativo: efecto proporcional",
    key="seasonality_mode_input"
)
st.session_state.seasonality_mode_radio = slider_seasonality_mode

# Outlier Holidays - Date Range Selector
st.sidebar.subheader("📅 Outlier Holidays")

use_outlier_holidays = st.sidebar.checkbox(
    "Incluir outlier holidays",
    value=st.session_state.use_outlier_holidays,
    help="Marcar fechas especiales (promociones, eventos) que afectan la demanda",
    key="use_outlier_holidays_checkbox"
)
st.session_state.use_outlier_holidays = use_outlier_holidays

outlier_holidays = []
if use_outlier_holidays:
    st.sidebar.caption("Selecciona rango de fechas para outliers")
    
    outlier_date_range = st.sidebar.date_input(
        "Rango de fechas (inicio y fin)",
        value=[pd.Timestamp("2024-01-01"), pd.Timestamp("2026-12-31")],
        format="YYYY-MM-DD",
        help="Selecciona el período que contiene los outliers/eventos especiales",
        key="outlier_date_range_selector"
    )
    
    # Convertir el rango a lista de fechas
    if outlier_date_range and len(outlier_date_range) == 2:
        start_date = pd.to_datetime(outlier_date_range[0])
        end_date = pd.to_datetime(outlier_date_range[1])
        outlier_holidays = pd.date_range(start=start_date, end=end_date, freq='D').tolist()
        st.sidebar.success(f"✅ {len(outlier_holidays)} días en el rango seleccionado")
    else:
        outlier_holidays = []

# Botones de control
st.sidebar.divider()
st.sidebar.subheader("⚙️ Controles")

col_btn1, col_btn2 = st.sidebar.columns(2)

with col_btn1:
    if st.button("🔄 Restablecer", help="Volver a parámetros originales", width='stretch'):
        st.session_state.changepoint_slider = 0.05
        st.session_state.seasonality_slider = 0.1
        st.session_state.holidays_slider = 0.01
        st.session_state.seasonality_mode_radio = 'additive'
        st.success("✅ Parámetros restablecidos")
        st.rerun()

with col_btn2:
    if st.button("💡 Sugerir Mejor Fit", help="Analizar y sugerir parámetros óptimos", width='stretch'):
        st.session_state.show_suggestion = True

st.sidebar.divider()

# Mostrar información sobre la combinación
combo_key = f"{bottler}_{category}_{sub_category}_{ms_ss}_{refillability}"

# Detectar si hay valores "All" en la combinación
has_all = any(v == "All" for v in [bottler, category, sub_category, ms_ss, refillability])

st.markdown(f"""
### 🎯 Combinación: `{combo_key}`
**País:** {country} | **Total Variables:** {len(variables_to_train)}
""")

if has_all:
    st.info("ℹ️ Esta combinación contiene campos con valor 'All' - se agregarán todos los valores disponibles de esos campos.")

# Cargar datos
with st.spinner("Cargando datos..."):
    df_country = load_country_data(country)
    if df_country is None:
        st.stop()
    
    # Calcular random seed basado en año máximo de los datos (para reproducibilidad)
    valid_dates = pd.to_datetime(df_country['Date'], errors='coerce')
    valid_dates = valid_dates[valid_dates.notna()]
    random_seed = int(max(valid_dates).year) if len(valid_dates) > 0 else 2026
    
    # Obtener datos filtrados (respetando "All" como wildcard)
    df_combination = get_data_for_combination(
        df_country, bottler, category, sub_category, ms_ss, refillability
    )
    
    if df_combination.empty:
        st.error("No hay datos para esta combinación")
        st.stop()
    
    # Si hay "All", obtener las combinaciones específicas expandidas
    expanded_combos = None
    if has_all:
        expanded_combos = get_expanded_combinations(
            df_country, bottler, category, sub_category, ms_ss, refillability
        )
        st.success(f"✅ Datos cargados: {len(df_combination)} registros | {len(expanded_combos)} combinaciones específicas detectadas")
        
        with st.expander(f"🔍 Ver {len(expanded_combos)} combinaciones expandidas"):
            for i, combo in enumerate(expanded_combos[:20], 1):  # Mostrar máximo 20
                st.caption(f"{i}. `{combo['combo_key']}`")
            if len(expanded_combos) > 20:
                st.caption(f"... y {len(expanded_combos) - 20} más")
    else:
        st.success(f"✅ Datos cargados: {len(df_combination)} registros")
    
    # Mostrar info del seed usado
    st.info(f"🔐 Random Seed para reproducibilidad: `{random_seed}` (basado en año máximo: {random_seed})")

# Crear tabs para cada variable
tabs = st.tabs([f"📈 {var.upper()}" for var in variables_to_train])

for tab_idx, (tab, variable_display) in enumerate(zip(tabs, variables_to_train)):
    with tab:
        variable_actual = VARIABLE_MAPPING[variable_display]
        variable_base = VARIABLE_BASE_MAPPING[variable_display]
        
        # Cargar parámetros
        df_params = load_params(country, variable_base)
        if df_params is None:
            st.error(f"No hay parámetros para {variable_base}")
            continue
        
        # Preparar datos para Prophet
        df_prophet = prepare_prophet_data(df_combination, variable_actual)
        
        if len(df_prophet) < 3:
            st.error(f"Datos insuficientes para {variable_base} ({len(df_prophet)} puntos)")
            continue
        
        st.subheader(f"Variable: {variable_base}")
        
        col1_info, col2_info = st.columns(2)
        with col1_info:
            st.metric("Puntos de datos disponibles", len(df_prophet))
        with col2_info:
            st.metric("Rango de fechas", f"{df_prophet['ds'].min().date()} a {df_prophet['ds'].max().date()}")
        
        # Entrenar modelos
        st.subheader("🤖 Entrenamiento en Tiempo Real")
        
        with st.spinner(f"Entrenando modelo con parámetros ajustados para {variable_base}..."):
            # Modelo original (parámetros del archivo)
            result = get_best_params(df_params, combo_key, expanded_combos=expanded_combos)
            
            if result is None or len(result) != 3:
                st.error(f"❌ Error al obtener parámetros para {combo_key}")
                continue
            
            best_params, best_row, param_type = result
            
            # Mostrar información sobre el origen de los parámetros
            if param_type == 'exact':
                st.success(f"✅ Parámetros encontrados para la combinación exacta")
            elif param_type == 'averaged':
                num_found = len([c for c in (expanded_combos or []) if df_params['combination'].eq(c['combo_key']).any()]) if expanded_combos else 0
                st.info(f"📊 Usando promedio de {num_found} combinaciones específicas")
            elif param_type == 'general_average':
                st.warning(f"⚠️ No se encontraron parámetros específicos. Usando promedio general de {len(df_params)} combinaciones del país/variable")
            elif param_type == 'default':
                st.warning(f"⚠️ No se encontraron parámetros. Usando valores por defecto de Prophet. Ajusta los sliders según sea necesario.")
            
            m_original = train_prophet_model(df_prophet, best_params, random_seed=random_seed, outlier_holidays=outlier_holidays)
            
            # Modelo con sliders (usuario ajustado)
            slider_params = {
                'changepoint_prior_scale': slider_changepoint,
                'seasonality_prior_scale': slider_seasonality,
                'holidays_prior_scale': slider_holidays,
                'seasonality_mode': slider_seasonality_mode,
                'growth': best_params['growth'],
                'interval_width': best_params['interval_width']
            }
            
            m_slider = train_prophet_model(df_prophet, slider_params, random_seed=random_seed, outlier_holidays=outlier_holidays)
        
        # Generar pronósticos
        if m_original is None:
            st.warning(f"⚠️ No fue posible entrenar el modelo. Verifica que los datos sean válidos.")
            continue
        
        forecast_original = make_forecast(m_original, periods=12)
        forecast_slider = make_forecast(m_slider, periods=12) if m_slider else None
        
        # Verificar que los pronósticos se generaron correctamente
        if forecast_original is None:
            st.warning(f"⚠️ No fue posible generar pronóstico para el modelo base.")
            continue
        
        # Preparar datos para visualización
        df_historical = df_prophet.copy()
        df_historical.columns = ['ds', 'actual']
        
        # Combinar con pronósticos
        df_viz = df_historical.copy()
        if forecast_original is not None:
            df_viz = df_viz.merge(forecast_original, on='ds', how='outer', suffixes=('_actual', '_original'))
            df_viz.rename(columns={'yhat': 'original'}, inplace=True)
        
        if forecast_slider is not None:
            df_viz = df_viz.merge(forecast_slider[['ds', 'yhat']], on='ds', how='outer')
            df_viz.rename(columns={'yhat': 'slider'}, inplace=True)
        else:
            df_viz['slider'] = np.nan
        
        df_viz.sort_values('ds', inplace=True)
        
        # Gráfica principal
        fig = go.Figure()
        
        # Datos históricos
        fig.add_trace(go.Scatter(
            x=df_historical['ds'],
            y=df_historical['actual'],
            mode='lines+markers',
            name='Datos Históricos',
            line=dict(color='black', width=2),
            marker=dict(size=4)
        ))
        
        # Pronóstico original
        if forecast_original is not None:
            fig.add_trace(go.Scatter(
                x=forecast_original['ds'],
                y=forecast_original['yhat'],
                mode='lines',
                name='Parámetros Base (Archivo)',
                line=dict(color='blue', width=2)
            ))
        
        # Pronóstico con sliders (ajustado por usuario)
        if forecast_slider is not None:
            fig.add_trace(go.Scatter(
                x=forecast_slider['ds'],
                y=forecast_slider['yhat'],
                mode='lines',
                name='Parámetros Ajustados (Sliders)',
                line=dict(color='red', width=2, dash='dash')
            ))

        # Marcar outliers seleccionados en la visual principal.
        if outlier_holidays and len(outlier_holidays) > 0:
            selected_outlier_dates = set(pd.to_datetime(outlier_holidays).normalize())
            df_outlier_points = df_historical[df_historical['ds'].dt.normalize().isin(selected_outlier_dates)].copy()

            if not df_outlier_points.empty:
                fig.add_trace(go.Scatter(
                    x=df_outlier_points['ds'],
                    y=df_outlier_points['actual'],
                    mode='markers',
                    name='Outliers Seleccionados',
                    marker=dict(color='crimson', size=10, symbol='diamond-open'),
                    hovertemplate='<b>Outlier</b><br>Fecha: %{x|%Y-%m-%d}<br>Valor: %{y:,.0f}<extra></extra>'
                ))
        
        fig.update_layout(
            title=f"Comparativo de Pronósticos - {variable_base}",
            xaxis_title="Fecha",
            yaxis_title="Valor",
            hovermode='x unified',
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Sección expandible: Gráficas de Referencia del Modelo
        with st.expander("📊 Gráficas de Referencia del Modelo", expanded=False):
            st.markdown("**Análisis detallado de los componentes del modelo Prophet**")
            
            # Verificar si el modelo fue entrenado correctamente
            if m_slider is None:
                st.error("❌ El modelo no fue entrenado correctamente. Verifica los datos de entrada.")
            else:
                try:
                    # Intentar predecir para verificar que el modelo es válido
                    test_forecast = m_slider.predict(df_prophet[['ds']])
                    
                    if test_forecast is None or test_forecast.empty:
                        st.error("❌ El modelo no genera pronósticos válidos.")
                    else:
                        # Generar gráficas
                        fig_trend, fig_interval, fig_components = plot_model_components(m_slider, df_prophet, variable_base)
                        
                        # Mostrar gráficas individual
                        gráficas_mostradas = 0
                        
                        if fig_trend is not None:
                            st.plotly_chart(fig_trend, width='stretch')
                            gráficas_mostradas += 1
                        else:
                            st.warning("⚠️ No fue posible generar gráfica de Tendencia y Changepoints")
                        
                        if fig_interval is not None:
                            st.plotly_chart(fig_interval, width='stretch')
                            gráficas_mostradas += 1
                        else:
                            st.warning("⚠️ No fue posible generar gráfica de Intervalo de Confianza")
                        
                        if fig_components is not None:
                            st.plotly_chart(fig_components, width='stretch')
                            gráficas_mostradas += 1
                        
                        # Si las gráficas se generaron, mostrar interpretación
                        if gráficas_mostradas > 0:
                            # Información adicional sobre los parámetros
                            st.divider()
                            st.subheader("📌 Interpretar las Gráficas")
                            
                            col_interp1, col_interp2 = st.columns(2)
                            
                            with col_interp1:
                                st.markdown("""
                                **Tendencia y Changepoints:**
                                - Línea azul: tendencia del modelo
                                - Líneas rojas punteadas: puntos donde Prophet detecta cambios de dirección
                                - Útil para entender flexibilidad (`changepoint_prior_scale`)
                                """)
                            
                            with col_interp2:
                                st.markdown(f"""
                                **Intervalo de Confianza:**
                                - Área sombreada: rango de pronóstico (basado en `interval_width: {slider_params['interval_width']}`)
                                - Valores superiores/inferiores = límites del intervalo
                                - Mayor ancho = mayor incertidumbre
                                """)
                        else:
                            st.error("❌ No fue posible generar las gráficas del modelo. Verifica que los datos y parámetros sean válidos.")
                
                except Exception as e:
                    st.error(f"❌ Error al procesar gráficas: {str(e)}")
        
        # Mostrar gráfica de años sobrepuestos
        st.subheader("📊 Comparación Histórica por Año")
        fig_years = plot_years_overlay(
            df_combination,
            variable_actual,
            variable_base,
            m_slider=m_slider,
            outlier_holidays=outlier_holidays
        )
        if fig_years is not None:
            st.plotly_chart(fig_years, width='stretch')
        else:
            st.warning(f"No hay datos disponibles para visualizar años sobrepuestos en {variable_base}")
        
        # Sección de análisis y sugerencias
        if st.session_state.get('show_suggestion', False):
            with st.spinner("Analizando parámetros para encontrar el mejor fit..."):
                error_base, error_slider = suggest_best_fit(df_prophet, best_params, slider_params, random_seed=random_seed, outlier_holidays=outlier_holidays)
            
            st.divider()
            st.subheader("🎯 Análisis de Mejor Fit")
            
            col_err1, col_err2 = st.columns(2)
            with col_err1:
                st.metric("RMSE - Parámetros Base", f"{error_base:.2f}", delta="Referencia")
            with col_err2:
                if error_slider < error_base:
                    delta_text = f"↓ {error_base - error_slider:.2f}"
                    delta_color = "green"
                else:
                    delta_text = f"↑ {error_slider - error_base:.2f}"
                    delta_color = "red"
                st.metric("RMSE - Parámetros Ajustados", f"{error_slider:.2f}", delta=delta_text)
            
            if error_slider < error_base:
                st.success(f"✅ Los parámetros ajustados son **{((error_base-error_slider)/error_base*100):.1f}% mejores**")
            else:
                st.warning(f"⚠️ Los parámetros base son mejores. Diferencia: {((error_slider-error_base)/error_base*100):.1f}%")
            
            st.session_state.show_suggestion = False
        
        # Mostrar parámetros
        st.subheader("📋 Comparación de Parámetros")
        
        param_cols = st.columns(2)
        
        with param_cols[0]:
            st.write("**Parámetros Base (Archivo)**")
            for key, val in best_params.items():
                st.caption(f"{key}: `{val}`")
        
        with param_cols[1]:
            st.write("**Parámetros Ajustados (Sliders)**")
            for key, val in slider_params.items():
                st.caption(f"{key}: `{val}`")
        
        # Mostrar diferencias
        st.divider()
        st.subheader("📊 Diferencias entre Modelos")
        
        diff_changepoint = abs(best_params['changepoint_prior_scale'] - slider_params['changepoint_prior_scale'])
        diff_seasonality = abs(best_params['seasonality_prior_scale'] - slider_params['seasonality_prior_scale'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Δ Changepoint", f"{diff_changepoint:.4f}")
        with col2:
            st.metric("Δ Seasonality", f"{diff_seasonality:.4f}")
        with col3:
            if best_params['seasonality_mode'] == slider_params['seasonality_mode']:
                st.metric("Seasonality Mode", "Igual")
            else:
                st.metric("Seasonality Mode", f"{best_params['seasonality_mode']} → {slider_params['seasonality_mode']}")
        
        # Botón para guardar parámetros
        st.divider()
        st.subheader("💾 Guardar Parámetros Ajustados")
        
        if has_all and expanded_combos:
            st.warning(f"⚠️ Esta combinación contiene 'All'. Los parámetros se aplicarán a las {len(expanded_combos)} combinaciones específicas detectadas.")
        
        col_save1, col_save2 = st.columns(2)
        
        with col_save1:
            if st.button(
                "💾 Guardar Params",
                help="Guardar estos parámetros en la carpeta Params_fix",
                use_container_width=True,
                type="primary",
                key=f"save_params_{variable_base}"
            ):
                try:
                    filepath, num_combos = save_parameters_to_fix(
                        country, 
                        variable_base, 
                        combo_key, 
                        slider_params,
                        expanded_combos=expanded_combos if (has_all and expanded_combos) else None
                    )
                    st.success(f"✅ Parámetros guardados en:\n`{filepath}`")
                    st.info(f"📊 Total de combinaciones actualizadas: **{num_combos}**")
                    if has_all and expanded_combos:
                        st.info("💡 Los hiperparámetros se han aplicado a todas las combinaciones específicas subyacentes")
                except Exception as e:
                    st.error(f"❌ Error al guardar: {str(e)}")
        
        with col_save2:
            if st.button(
                "📊 Actualizar Forecast",
                help="Actualizar el archivo de forecast baseline con los nuevos pronósticos",
                use_container_width=True,
                type="secondary",
                key=f"update_forecast_{variable_base}"
            ):
                try:
                    with st.spinner(f"Actualizando forecast para {variable_base}..."):
                        filepath_forecast, num_rows = update_forecast_baseline(
                            country=country,
                            variable_base=variable_base,
                            df_combination=df_combination,
                            slider_params=slider_params,
                            bottler=bottler,
                            category=category,
                            sub_category=sub_category,
                            ms_ss=ms_ss,
                            refillability=refillability,
                            random_seed=random_seed,
                            outlier_holidays=outlier_holidays,
                            expanded_combos=expanded_combos if (has_all and expanded_combos) else None
                        )
                    st.success(f"✅ Forecast actualizado en:\n`{filepath_forecast}`")
                    st.info(f"📊 Total de filas actualizadas: **{num_rows}**")
                    if has_all and expanded_combos:
                        st.info("💡 Los pronósticos se han actualizado para todas las combinaciones específicas subyacentes")
                except FileNotFoundError as e:
                    st.error(f"❌ Archivo no encontrado: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error al actualizar forecast: {str(e)}")

st.markdown("---")
st.caption("Aplicación generada automáticamente para validar pronósticos de Prophet")
