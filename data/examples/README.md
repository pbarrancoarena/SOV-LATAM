# Datos de Ejemplo

Este directorio contiene datos sintéticos de ejemplo para demostración y pruebas del sistema de forecasting.

## ⚠️ Importante

**Estos datos son completamente sintéticos y generados para propósitos de demostración únicamente.** No representan datos reales de ningún país, embotellador o marca.

## Archivos Disponibles

### Parámetros de Ejemplo

**`Example_params_volume_uc_KO.csv`**
- Parámetros de ejemplo para forecasting de volumen Coca-Cola
- Estructura típica de salida de entrenamiento baseline
- Incluye múltiples combinaciones y sus hiperparámetros Prophet

**`Example_params_volume_uc_KO_fix.csv`**
- Ejemplo de parámetros ajustados manualmente (Params_fix)
- Muestra cómo se estructuran los ajustes de QA
- Incluye la columna `fixed=True`

### Forecasts de Ejemplo

**`Example_forecast_baseline_category.csv`**
- Pronóstico agregado a nivel categoría
- Incluye valor histórico y proyectado con intervalos de confianza

**`Example_forecast_baseline_post_qa.csv`**
- Pronóstico post-QA a nivel combinación detallada
- Muestra estructura completa de output

## Uso

### Para Probar merge_params.py

```bash
# Copiar ejemplos a estructura temporal
mkdir -p data/Params/Example data/Params_fix/Example
cp data/examples/Example_params_volume_uc_KO.csv data/Params/Example/
cp data/examples/Example_params_volume_uc_KO_fix.csv data/Params_fix/Example/Example_params_volume_uc_KO.csv

# Ejecutar merge
python scripts/merge_params.py Example

# Verificar output en data/Params_new/Example/
```

### Para Probar Streamlit Apps

```bash
# Copiar forecasts de ejemplo
cp data/examples/Example_forecast_*.csv data/

# Ejecutar app
streamlit run streamlit_app/streamlit_forecast_validator.py
```

## Estructura de Combinaciones

Las combinaciones en los ejemplos siguen el formato:
```
Bottler_Category_SubCategory_MS_SS_Refillability
```

Ejemplo: `ACME_SPARKLING_CSD_KB_SB_REFILLABLE`

Donde:
- **Bottler**: Embotellador (ej: ACME, GLOBAL)
- **Category**: Categoría principal (ej: SPARKLING, STILL)
- **SubCategory**: Subcategoría (ej: CSD, JUICE)
- **MS**: Market Segment (ej: KB - Knowledge Based, TB - Traditional)
- **SS**: Segment Specification (ej: SB - Small Business)
- **Refillability**: REFILLABLE o NONREFILLABLE

## Columnas de Parámetros

### Hiperparámetros Prophet
- `changepoint_prior_scale`: Flexibilidad de cambios de tendencia (0.001 - 0.5)
- `seasonality_prior_scale`: Fuerza de estacionalidad (0.01 - 10)
- `holidays_prior_scale`: Impacto de días festivos (0.01 - 10)
- `seasonality_mode`: 'additive' o 'multiplicative'
- `growth`: 'linear' o 'logistic'
- `interval_width`: Ancho del intervalo de confianza (0.80 - 0.95)
- `changepoint_range`: Proporción de datos para detectar cambios (0.8 - 0.99)

### Métricas de Error
- `MAE`: Mean Absolute Error
- `RMSE`: Root Mean Square Error
- `MAPE`: Mean Absolute Percentage Error
- `RMSE_TO_STD`: RMSE normalizado por desviación estándar

### Flags
- `best`: Parámetro tiene mejor performance
- `good`: Performance aceptable
- `acceptable`: Performance mínima aceptable
- `fixed`: Parámetro ajustado manualmente (en Params_fix)
