# Estructura de Datos

Este directorio contiene los parametros de Prophet y archivos de forecast. La estructura esta diseñada para separar parametros baseline, ajustes manuales y outputs consolidados.

## Subdirectorios

### `Params/`
**Parametros baseline** generados automaticamente durante el entrenamiento.

- Contiene multiples ensayos por combinacion (puede haber duplicados)
- Incluye metricas de error: MAE, RMSE, MAPE, etc.
- Organizado por pais: `Params/<country>/<country>_params_<variable>.csv`

Variables:
- `volume_uc_KO.csv` - Volumen Coca-Cola
- `volume_uc_NOKO.csv` - Volumen No Coca-Cola  
- `price_lc_KO.csv` - Precio Coca-Cola
- `price_lc_NOKO.csv` - Precio No Coca-Cola

### `Params_fix/`
**Parametros ajustados manualmente** para combinaciones problematicas identificadas en QA.

- Contiene UNA sola fila por combinacion (la mejor tuneada)
- Se usa para sobrescribir parametros baseline que tienen mal desempeño
- Misma estructura de archivos que `Params/`

### `Params_new/`
**Output consolidado** del script `merge_params.py`.

- Resultado del merge entre `Params/` y `Params_fix/`
- Prioriza parametros de `Params_fix/` sobre `Params/`
- Incluye columna `fixed=True` para identificar parametros tuneados manualmente
- Este directorio es el que se usa para generar forecasts

## Archivos CSV (ignorados por Git)

Los archivos `.csv` con datos de forecast estan en `.gitignore` por contener informacion sensible.

Patrones de archivos:

- `<Country>_forecast_baseline_intervalo_conf.csv`  
  Baseline forecast a nivel combinacion con intervalos de confianza (entrada para QA)
  
- `<Country>_forecast_baseline_category.csv`  
  Baseline forecast agregado a nivel categoria (entrada para QA)
  
- `<Country>_forecast_baseline_post_qa.csv`  
  Forecast final despues de aplicar Vector QA (salida del pipeline)

## Workflow

```
1. Entrenamiento → Params/
2. QA Manual → Identificar combos problematicas
3. Tuning Manual → Params_fix/
4. Consolidacion → python scripts/merge_params.py <country>
5. Output → Params_new/
6. Forecasting → Genera archivos *_intervalo_conf.csv y *_category.csv
7. Vector QA → python scripts/vecqa_to_post_qa.py --country <country>
8. Output Final → <Country>_forecast_baseline_post_qa.csv
```

## Estructura de Combinaciones

Las combinaciones se identifican por:
```
Bottler_Category_SubCategory_MS_SS_Refillability
```

Ejemplo: `FEMSA_SPARKLING_CSD_KB_SB_REFILLABLE`
