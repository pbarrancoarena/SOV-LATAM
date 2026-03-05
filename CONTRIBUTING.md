# Contribuyendo a SOV Forecasting

Gracias por tu interés en contribuir al proyecto de forecasting SOV LATAM!

## Cómo Contribuir

### Reportar Bugs

Si encuentras un bug, por favor abre un issue incluyendo:

1. **Descripción del problema**: Qué esperabas vs qué ocurrió
2. **Pasos para reproducir**: Cómo replicar el error
3. **Entorno**: Sistema operativo, versión de Python (3.11.9 recomendado), versión de dependencias
4. **Logs/Screenshots**: Si aplica

### Sugerir Mejoras

Para sugerir nuevas características:

1. Abre un issue describiendo la funcionalidad
2. Explica el caso de uso y beneficio
3. Propón una implementación si tienes ideas

### Pull Requests

1. **Fork el repositorio**
2. **Crea una rama**: `git checkout -b feature/nueva-funcionalidad`
3. **Haz tus cambios**
4. **Asegúrate de que todo funciona**
5. **Commit**: `git commit -m "feat: descripción clara"`
6. **Push**: `git push origin feature/nueva-funcionalidad`
7. **Abre un Pull Request**

## Guías de Estilo

### Python

- Seguir PEP 8
- Usar nombres descriptivos de variables
- Documentar funciones con docstrings
- Máximo 100 caracteres por línea

Ejemplo:

```python
def calculate_metrics(df, metric_type='MAE'):
    """
    Calcula métricas de error para forecast.
  
    Args:
        df (pd.DataFrame): DataFrame con columnas 'value' y 'yhat'
        metric_type (str): Tipo de métrica ('MAE', 'RMSE', 'MAPE')
  
    Returns:
        float: Valor de la métrica calculada
    """
    # Implementación
    pass
```

### Commits

Usar conventional commits:

- `feat:` Nueva funcionalidad
- `fix:` Corrección de bug
- `docs:` Cambios en documentación
- `style:` Cambios de formato (no afectan código)
- `refactor:` Refactorización de código
- `test:` Agregar o modificar tests
- `chore:` Tareas de mantenimiento

Ejemplos:

```
feat: agregar soporte para Mexico
fix: corregir cálculo de MAPE en utils
docs: actualizar README con nuevos ejemplos
```

## Workflow de Desarrollo

### 1. Setup

```bash
# Clonar y configurar
git clone <repo-url>
cd SOV
.\scripts\setup.ps1  # o bash scripts/setup.sh

# O instalación manual
pip install -r requirements.txt
```

### 2. Desarrollo

```bash
# Crear rama
git checkout -b feature/mi-feature

# Hacer cambios
# ...

# Verificar que funciona
python scripts/merge_params.py Example
streamlit run streamlit_app/streamlit_forecast_validator.py
```

### 3. Testing

Siempre ejecuta los tests antes de hacer un PR:

```bash
# Ejecutar todos los tests
pytest -v

# Con coverage
pytest --cov=scripts --cov=streamlit_app

# Solo tests modificados
pytest tests/test_merge_params.py -v
```

Ver [tests/README.md](tests/README.md) para guía de cómo escribir nuevos tests.

### 4. Commit y Push

```bash
git add .
git commit -m "feat: descripción de cambios"
git push origin feature/mi-feature
```

mpliar cobertura de

### 5. Pull Request

- Describir claramente los cambios
- Referenciar issues relacionados (#123)
- Incluir screenshots si es relevante

## Áreas de Contribución

### Prioridades Actuales

1. **Testing**: Agregar tests unitarios
2. **Documentación**: Mejorar KT en `documentation/`
3. **Validación**: Nuevos checks de QA
4. **Visualización**: Mejorar dashboards Streamlit
5. **Performance**: Optimización de merge_params.py

### Ideas de Proyectos

- [ ] **Integración de Outlier Holidays**: Incorporar parámetros de holidays en entrenamiento Prophet (local y Azure)
- [ ] Sistema de alertas automáticas para anomalías
- [ ] Export a Excel formateado desde Streamlit
- [ ] API REST para forecasts
- [ ] Dockerización del proyecto
- [ ] CI/CD con GitHub Actions
- [ ] Comparación de múltiples modelos (Prophet vs otros)

## Código de Conducta

- Ser respetuoso y profesional
- Dar feedback constructivo
- Aceptar críticas constructivas
- Enfocarse en lo mejor para el proyecto

## Preguntas

Si tienes dudas, puedes:

- Abrir un issue con la etiqueta "question"
- Revisar la documentación en `documentation/`
- Consultar ejemplos en `data/examples/`
