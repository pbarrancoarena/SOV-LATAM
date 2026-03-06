# Flujo de Información - Proceso de Forecasting LATAM

## Descripción General

Este diagrama muestra el flujo completo del proceso de forecasting para países de LATAM (Guatemala, Perú, Ecuador, Chile, Chile W/ Blues, Brasil, Argentina). El proceso consta de tres etapas principales:

1. **Entrenamiento**: Utiliza datos históricos de Nielsen para generar parámetros óptimos por categoría y combinación
2. **Forecasting**: Genera pronósticos tanto a nivel categoría como por combinaciones individuales
3. **Validación y Consolidación**: Valida y consolida los resultados en archivos finales por país y región

## Diagrama de Flujo

```mermaid
graph TB
    %% Datos de entrada
    PAISES[<b>Países LATAM</b><br/><br/>Guatemala - Perú - Ecuador<br/>Chile - Chile W/ Blues<br/>Brasil - Argentina]
  
    NIELSEN[(<b>BASE DE DATOS</b><br/>Datos Nielsen<br/>36 observaciones)]
  
    %% Etapa 1: Entrenamiento
    subgraph STAGE1[<b>ETAPA 1: ENTRENAMIENTO</b>]
        TRAINING[<b>PROCESO: Optimización de parámetros</b><br/>nb_sdc_baseline_training<br/>_LATAM_SellOut<br/>]
        PARAMS[/<b>ARCHIVOS</b><br/>Parámetros<br/>Por categoría y combinación\]
    end
  
    %% Etapa 2: Forecasting
    subgraph STAGE2[<b>ETAPA 2: FORECASTING DUAL</b>]
        FORECAST_CAT[<b>PROCESO 1: Forecast por Categoría</b><br/>nb_sdc_baseline_forecast<br/>_LATAM_Category<br/><br/>]
        OUTPUT_CAT[/<b>CSV OUTPUT</b><br/>Country_forecast_baseline<br/>_category.csv\]
      
        FORECAST_COMB[<b>PROCESO 2: Forecast por Combinación</b><br/>nb_sdc_baseline_forecast<br/>_LATAM_Combination<br/><br/>]
        OUTPUT_COMB[/<b>CSV OUTPUT</b><br/>Country_forecast_baseline<br/>_intervalo_conf.csv\]
    end
  
    %% Etapa 3: Validación
    subgraph STAGE3[<b>ETAPA 3: VALIDACIÓN Y CONSOLIDACIÓN</b>]
        QA_PROCESS[<b>PROCESO QA</b><br/>nb_sdc_baseline_forecast<br/>_LATAM_VecQA<br/>o vecqa_to_post_qa.py<br/><br/>]
        OUTPUT_QA[/<b>CSV OUTPUT</b><br/>Country_forecast_baseline<br/>_post_qa.csv\]
        FINAL[[<b>RESULTADO FINAL</b><br/><br/>Resultados_LATAM<br/>mes_timestamp.xlsx<br/><br/>]]
    end
  
    %% Conexiones principales
    PAISES -.->|define scope| NIELSEN
    NIELSEN ==>|datos históricos| TRAINING
    TRAINING ==>|genera| PARAMS
  
    %% Hacia forecasting - Branch 1
    NIELSEN ==>|input datos| FORECAST_CAT
    PARAMS ==>|input params| FORECAST_CAT
    FORECAST_CAT ==>|genera| OUTPUT_CAT
  
    %% Hacia forecasting - Branch 2
    NIELSEN ==>|input datos| FORECAST_COMB
    PARAMS ==>|input params| FORECAST_COMB
    FORECAST_COMB ==>|genera| OUTPUT_COMB
  
    %% Hacia validación
    OUTPUT_CAT ==>|valida| QA_PROCESS
    OUTPUT_COMB ==>|valida| QA_PROCESS
    QA_PROCESS ==>|genera por país| OUTPUT_QA
  
    %% Consolidación final
    OUTPUT_QA ==>|todos los países| FINAL
  
    %% Estilos mejorados con efecto HTML
    classDef sourceStyle fill:#667eea,stroke:#764ba2,stroke-width:4px,color:#fff,font-size:12px
    classDef dbStyle fill:#2d3748,stroke:#4299e1,stroke-width:4px,color:#fff,font-size:12px
    classDef processStyle fill:#f093fb,stroke:#f5576c,stroke-width:3px,color:#fff,font-size:11px
    classDef paramStyle fill:#4facfe,stroke:#00f2fe,stroke-width:3px,color:#fff,font-size:11px
    classDef outputStyle fill:#43e97b,stroke:#38f9d7,stroke-width:3px,color:#2d3748,font-size:11px
    classDef qaStyle fill:#fa709a,stroke:#fee140,stroke-width:3px,color:#fff,font-size:11px
    classDef finalStyle fill:#30cfd0,stroke:#330867,stroke-width:5px,color:#fff,font-size:13px
  
    class PAISES sourceStyle
    class NIELSEN dbStyle
    class TRAINING,FORECAST_CAT,FORECAST_COMB processStyle
    class PARAMS paramStyle
    class OUTPUT_CAT,OUTPUT_COMB,OUTPUT_QA outputStyle
    class QA_PROCESS qaStyle
    class FINAL finalStyle
```

## Detalle de Etapas

### 1. Entrenamiento (Training)

- **Input**: Datos Nielsen (36 observaciones históricas por país)
- **Proceso**: `nb_sdc_baseline_training_LATAM_SellOut`
- **Output**: Archivos de parámetros óptimos almacenados en `data/Params/{Country}/`
  - Parámetros por categoría (KO/NOKO)
  - Parámetros por métrica (price_lc, volume_uc)

### 2. Forecasting

Se ejecutan dos procesos paralelos con los mismos inputs (Nielsen + Params):

#### 2.1. Forecast por Categoría

- **Proceso**: `nb_sdc_baseline_forecast_LATAM_Category`
- **Output**: `{Country}_forecast_baseline_category.csv`
- Genera pronósticos agregados a nivel de categoría

#### 2.2. Forecast por Combinación

- **Proceso**: `nb_sdc_baseline_forecast_LATAM_Combination`
- **Output**: `{Country}_forecast_baseline_intervalo_conf.csv`
- Genera pronósticos detallados por todas las combinaciones posibles
- Incluye intervalos de confianza

### 3. Validación y Consolidación

#### 3.1. Validación QA (por país)

- **Input**: Ambos archivos de forecast (categoría + combinación)
- **Proceso**: `nb_sdc_baseline_forecast_LATAM_VecQA` (notebook) o `scripts/vecqa_to_post_qa.py` (script CLI)
- **Output**: `{Country}_forecast_baseline_post_qa.csv`
- Valida y reconcilia los pronósticos de ambas metodologías
- El script CLI permite automatizar este proceso sin necesidad de ejecutar el notebook manualmente

#### 3.2. Consolidación Regional

- **Input**: Archivos post-QA de todos los países
- **Output**: `Resultados_LATAM_{mes}_{timestamp}.xlsx`
- Archivo final que consolida resultados de todos los países LATAM

## Archivos de Salida

### Por País (en `data/`)

- `{Country}_forecast_baseline_category.csv` - Pronóstico por categoría
- `{Country}_forecast_baseline_intervalo_conf.csv` - Pronóstico por combinación
- `{Country}_forecast_baseline_post_qa.csv` - Pronóstico validado final

### Consolidado Regional (en `target_model/`)

- `Resultados_LATAM_{mes}_{timestamp}.xlsx` - Resultados consolidados de todos los países
