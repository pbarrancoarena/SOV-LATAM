# Share of Value (SOV) - Forecasting LATAM

Repositorio para entrenamiento, consolidacion de parametros y validacion de pronosticos de Share of Value (SOV) en paises LATAM.

## Alcance

Este proyecto cubre:

- Generacion y consolidacion de parametros Prophet por pais/categoria.
- Validacion de resultados mediante aplicaciones Streamlit.
- Trazabilidad de decisiones de forecast.

## Estructura del Proyecto

```text
SOV/
├── data/
│   ├── Params/            # Parametros baseline
│   ├── Params_fix/        # Ajustes manuales QA
│   ├── Params_new/        # Salida consolidada del merge
│   └── *.csv              # Archivos de datos locales (ignorados por git)
├── scripts/
│   └── merge_params.py    # Merge de Params + Params_fix
├── streamlit_app/
│   ├── streamlit_dashboard.py
│   ├── streamlit_forecast_validator.py
│   ├── streamlit_qa_category.py
│   └── utils.py
├── tests/                 # Tests unitarios
│   ├── test_merge_params.py
│   ├── test_utils.py
│   └── conftest.py
├── documentation/         # KT y documentacion funcional/tecnica
├── historical_decisions/  # Historial de decisiones y logs
├── notebooks_azure/       # Notebooks de trabajo (ignorado)
├── notebooks_local/       # Notebooks de trabajo (ignorado)
├── target_model/          # Outputs/model artifacts (ignorado)
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.11.9 recomendado
- Dependencias en `requirements.txt`

## Instalacion

### Opcion 1: Setup Automatico (Recomendado)

```bash
# Windows
.\scripts\setup.ps1

# Linux/Mac
bash scripts/setup.sh
```

### Opcion 2: Manual

```bash
python -m venv venv_sov
# Windows
.\venv_sov\Scripts\activate
# Linux/Mac
source venv_sov/bin/activate

# Instalación de dependencias
pip install -r requirements.txt
```

## Datos de Ejemplo

El directorio `data/examples/` contiene datos sintéticos para probar el sistema:

```bash
# Probar merge de parámetros con datos de ejemplo
python scripts/merge_params.py Example

# Los ejemplos incluyen:
# - Example_params_volume_uc_KO.csv (parámetros baseline)
# - Example_params_volume_uc_KO_fix.csv (parámetros ajustados)
# - Example_forecast_baseline_*.csv (forecasts de ejemplo)
```

Ver [data/examples/README.md](data/examples/README.md) para más detalles.

## Scripts Principales

### `scripts/merge_params.py`

Consolida parametros baseline (`data/Params/`) con ajustes manuales (`data/Params_fix/`) y genera salida en `data/Params_new/<country>/`.

Uso:

```bash
python scripts/merge_params.py <country> [--deduplicate]
```

Ejemplos:

```bash
python scripts/merge_params.py Peru
python scripts/merge_params.py Peru --deduplicate
```

Comportamiento:

- Modo default: mantiene duplicados de baseline y solo reemplaza combinaciones presentes en `Params_fix`.
- Modo `--deduplicate`: conserva una sola fila por combinacion (la mejor) y luego aplica reemplazos de `Params_fix`.
- Marca `fixed=True` para parametros que vienen de `Params_fix`.

### `scripts/vecqa_to_post_qa.py`

Aplica el pipeline de Vector QA para reconstruir series temporales a nivel categoria y desagregar entre combinaciones. Toma los archivos de forecast baseline y genera el archivo post-QA.

Uso:

```bash
python scripts/vecqa_to_post_qa.py --country <country> [OPTIONS]
```

Ejemplos:

```bash
# Uso basico (con reconciliacion por defecto)
python scripts/vecqa_to_post_qa.py --country Guatemala

# Sin reconciliacion
python scripts/vecqa_to_post_qa.py --country Peru --no-reconciliation

# Con undo QA para categorias especificas
python scripts/vecqa_to_post_qa.py --country Chile --undo-qa --undo-qa-categories "Water,Juices"

# Mantener forecast original para ciertas categorias
python scripts/vecqa_to_post_qa.py --country Brazil --keep-comb-forecast --keep-comb-forecast-categories "Juices"
```

Opciones:

- `--country`: (Requerido) Nombre del pais
- `--data-dir`: Directorio con archivos CSV de entrada (default: `data/`)
- `--output-file`: Ruta del archivo de salida (default: `data/{country}_forecast_baseline_post_qa.csv`)
- `--no-reconciliation`: Deshabilita reconciliacion optima de forecast
- `--undo-qa`: Deshace QA para categorias seleccionadas
- `--undo-qa-categories`: Categorias separadas por comas para undo QA
- `--keep-comb-forecast`: Mantiene forecast original a nivel combinacion
- `--keep-comb-forecast-categories`: Categorias separadas por comas para mantener forecast

Entradas:
- `{country}_forecast_baseline_intervalo_conf.csv`
- `{country}_forecast_baseline_category.csv`

Salida:
- `{country}_forecast_baseline_post_qa.csv`

## Aplicaciones Streamlit

- `streamlit_app/streamlit_dashboard.py`: dashboard general de KPIs.
- `streamlit_app/streamlit_forecast_validator.py`: validacion forecast vs historico.
- `streamlit_app/streamlit_qa_category.py`: QA por categoria.
- `streamlit_app/utils.py`: utilidades compartidas.

Ver [streamlit_app/README.md](streamlit_app/README.md) para documentacion detallada de cada aplicacion.

Ejemplo:

```bash
streamlit run streamlit_app/streamlit_forecast_validator.py
```

## Politica de Git y Datos Sensibles

Este repositorio esta preparado para no versionar datos pesados/sensibles ni entornos locales.

Segun `.gitignore`:

- Se ignoran notebooks de trabajo: `notebooks_azure/`, `notebooks_local/`
- Se ignoran artefactos de modelo: `target_model/`
- Se ignoran CSV bajo `data/`: `data/**/*.csv`
- Debe ignorarse el entorno virtual local: `venv_sov/`

Importante:

- Si algun archivo ya fue trackeado antes de agregarlo al `.gitignore`, hay que quitarlo del index de git con `git rm --cached`.

## Workflow Recomendado

1. Entrenamiento baseline y generacion de parametros en `data/Params/`.
2. QA para detectar combinaciones problematicas.
3. Ajuste manual en `data/Params_fix/`.
4. Consolidacion con `scripts/merge_params.py`.
5. Validacion en Streamlit.
6. Registro de decisiones en `historical_decisions/`.

## Tests

El proyecto incluye tests unitarios para verificar la lógica de consolidación de parámetros y utilidades.

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con verbose
pytest -v

# Ejecutar tests específicos
pytest tests/test_merge_params.py

# Con coverage
pytest --cov=scripts --cov=streamlit_app
```

Ver [tests/README.md](tests/README.md) para más detalles sobre los tests y cómo escribir nuevos.

## Paises Trabajados

- Peru
- Argentina
- Chile
- Chile_wo_Blues
- Ecuador
- Brazil
- Guatemala

## Documentacion Relacionada

Ver `documentation/` para KT funcional y especificaciones de inputs/outputs.

## Trabajos Futuros Sugeridos

- **Integración de Outlier Holidays**: Incorporar parámetros de outlier holidays en el entrenamiento de modelos Prophet, tanto en el pipeline local como en la plataforma de entrenamiento de Azure.
- Alertas automáticas para anomalías en forecasts
- Export formateado a Excel desde Streamlit
- API REST para consumir forecasts
- Dockerización del proyecto
- CI/CD con GitHub Actions

## Contribuciones

Las contribuciones son bienvenidas! Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de estilo y workflow.

## Licencia

Este proyecto esta bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para mas detalles.
