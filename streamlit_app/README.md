# Aplicaciones Streamlit

Este directorio contiene aplicaciones interactivas desarrolladas con Streamlit para visualización y validación de forecasts.

## Aplicaciones Disponibles

### 1. `streamlit_dashboard.py`
**Dashboard principal de KPIs**

Panel de control general con métricas clave de performance del sistema de forecasting.

```bash
streamlit run streamlit_app/streamlit_dashboard.py
```

**Características:**
- Resumen de KPIs por país y categoría
- Métricas de error agregadas (MAE, RMSE, MAPE)
- Visualización de tendencias temporales
- Comparación entre países

---

### 2. `streamlit_forecast_validator.py`
**Validador de forecasts vs histórico**

Herramienta para validar visualmente forecasts contra datos históricos a nivel de combinación.

```bash
streamlit run streamlit_app/streamlit_forecast_validator.py
```

**Características:**
- Comparación gráfica histórico vs forecast
- Intervalos de confianza visualizados
- Filtros por país, categoría, combinación
- Detección visual de anomalías
- Métricas de error por combinación

**Uso típico:**
1. Seleccionar país
2. Elegir combinación específica
3. Revisar ajuste del modelo
4. Identificar puntos que requieren ajuste manual

---

### 3. `streamlit_qa_category.py`
**QA a nivel categoría**

Análisis de calidad agregado por categoría para detección temprana de problemas.

```bash
streamlit run streamlit_app/streamlit_qa_category.py
```

**Características:**
- Análisis agregado por categoría
- Detección de combinaciones problemáticas
- Rankings de error (peores combinaciones)
- Recomendaciones de ajuste
- Export de combinaciones para Params_fix

**Workflow:**
1. Ejecutar esta app después de generar forecasts baseline
2. Identificar categorías/combinaciones con errores altos
3. Marcar combinaciones para tuning manual
4. Generar lista para crear Params_fix

---

### 4. `utils.py`
**Utilidades compartidas**

Módulo con funciones reutilizables para lectura de datos y procesamiento.

**Funciones principales:**
- `load_forecast_data()`: Carga datos de forecast
- `load_params()`: Carga parámetros
- `calculate_metrics()`: Calcula métricas de error
- `filter_combinations()`: Filtrado de combinaciones

---

## Estructura de Datos Esperada

Las apps esperan encontrar datos en:

```
data/
├── <Country>_forecast_baseline_category.csv
├── <Country>_forecast_baseline_post_qa.csv
├── Params/<Country>/<Country>_params_<variable>.csv
└── Params_new/<Country>/<Country>_params_<variable>.csv
```

### Formato de CSVs de Forecast

**Category Level:**
```csv
date,category,value,yhat,yhat_lower,yhat_upper,is_forecast
2025-01-01,SPARKLING,125000.0,124850.5,120200.0,129500.0,False
2026-01-01,SPARKLING,,141250.8,135800.0,146700.0,True
```

**Combination Level:**
```csv
date,combination,bottler,category,value,yhat,yhat_lower,yhat_upper,is_forecast
2025-01-01,ACME_SPARKLING_CSD,ACME,SPARKLING,15000.0,14950.5,14200.0,15700.0,False
```

---

## Uso con Datos de Ejemplo

Para probar las apps con datos sintéticos:

```bash
# 1. Copiar ejemplos al directorio data/
cp data/examples/Example_forecast_*.csv data/

# 2. Ejecutar cualquier app
streamlit run streamlit_app/streamlit_forecast_validator.py

# 3. Seleccionar "Example" como país
```

---

## Configuración

### Puerto personalizado
```bash
streamlit run streamlit_app/streamlit_dashboard.py --server.port 8502
```

### Modo headless (sin abrir browser)
```bash
streamlit run streamlit_app/streamlit_dashboard.py --server.headless true
```

### Configuración de tema
Crear `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#F63366"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

---

## Troubleshooting

**Error: No se encuentra el archivo CSV**
- Verificar que existen forecasts en `data/`
- Usar datos de ejemplo: `cp data/examples/*.csv data/`

**App muy lenta**
- Reducir rango de fechas en filtros
- Usar datos agregados (category level) en lugar de combination level
- Verificar tamaño de CSVs

**Gráficos no se visualizan**
- Actualizar plotly: `pip install --upgrade plotly`
- Limpiar cache de Streamlit: `streamlit cache clear`

---

## Desarrollo

Para modificar o extender las apps:

1. **Agregar nueva métrica:**
   - Editar `utils.py` → agregar función de cálculo
   - Editar app correspondiente → visualizar métrica

2. **Agregar nuevo filtro:**
   - Usar `st.selectbox()` o `st.multiselect()`
   - Aplicar filtro al dataframe antes de graficar

3. **Recargar automáticamente:**
   ```bash
   streamlit run streamlit_app/your_app.py --server.runOnSave true
   ```

---

## Referencias

- [Documentación Streamlit](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
- [Altair](https://altair-viz.github.io/)
