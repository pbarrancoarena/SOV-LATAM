# Tests para SOV Forecasting

Este directorio contiene tests unitarios y de integración para el sistema de forecasting.

## Estructura

```
tests/
├── test_merge_params.py      # Tests para script de merge
├── test_utils.py              # Tests para utilidades de Streamlit
├── fixtures/                  # Datos de prueba
│   └── sample_params.csv
└── conftest.py               # Configuración de pytest
```

## Ejecutar Tests

```bash
# Todos los tests
pytest

# Con verbose
pytest -v

# Test específico
pytest tests/test_merge_params.py

# Con coverage
pytest --cov=scripts --cov=streamlit_app

# Solo tests que fallen
pytest --lf
```

## Escribir Tests

### Estructura de Test

```python
import pytest
from scripts.merge_params import merge_params

def test_merge_basic():
    """Test básico de merge."""
    # Arrange
    country = "Example"
    
    # Act
    result = merge_params(country)
    
    # Assert
    assert result is not None
```

### Fixtures

Usar fixtures para datos de prueba:

```python
@pytest.fixture
def sample_params_df():
    """DataFrame de ejemplo con parámetros."""
    return pd.DataFrame({
        'combination': ['COMBO_A', 'COMBO_B'],
        'changepoint_prior_scale': [0.05, 0.1],
        # ...
    })
```

## Coverage

Meta: mantener >80% de cobertura para código crítico.

```bash
# Generar reporte HTML
pytest --cov=scripts --cov=streamlit_app --cov-report=html

# Ver reporte
# Abrir htmlcov/index.html
```

## CI/CD

Los tests se ejecutan automáticamente en:
- Pull requests
- Commits a main
- Releases

## Agregar Nuevos Tests

1. Crear archivo `test_*.py` en `tests/`
2. Seguir convenciones de naming
3. Documentar con docstrings
4. Verificar que pasan: `pytest -v`
