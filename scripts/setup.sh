#!/bin/bash
# Setup Script para SOV Forecasting (Linux/Mac)
# Ejecutar: bash scripts/setup.sh

echo "============================================"
echo "   SOV - LATAM Forecasting Setup"
echo "============================================"
echo ""

# Verificar Python
echo "[1/5] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no encontrado. Por favor instala Python 3.11.9"
    exit 1
fi
python_version=$(python3 --version)
echo "      ✓ $python_version"

# Crear entorno virtual
echo "[2/5] Configurando entorno virtual..."
if [ ! -d "venv_sov" ]; then
    python3 -m venv venv_sov
    echo "      ✓ Entorno virtual creado: venv_sov"
else
    echo "      ✓ Entorno virtual ya existe"
fi

# Activar entorno virtual
echo "[3/5] Activando entorno virtual..."
if source venv_sov/bin/activate; then
    echo "      ✓ Entorno virtual activado"
else
    echo "      ERROR: No se pudo activar el entorno virtual"
    exit 1
fi

# Instalar dependencias
echo "[4/5] Instalando dependencias..."
if [ ! -f "requirements.txt" ]; then
    echo "      ERROR: requirements.txt no encontrado"
    exit 1
fi
echo "      Esto puede tomar varios minutos..."

if pip install -r requirements.txt --quiet; then
    echo "      ✓ Dependencias instaladas"
else
    echo "      ERROR: Fallo al instalar dependencias"
    exit 1
fi

# Verificar/Crear estructura
echo "[5/5] Verificando estructura de directorios..."
directories=("data/Params" "data/Params_fix" "data/Params_new" "data/examples" "historical_decisions")
for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        echo "      ✓ $dir"
    else
        mkdir -p "$dir"
        if [ -d "$dir" ]; then
            echo "      ✓ $dir (creado)"
        else
            echo "      ✗ $dir (error al crear)"
        fi
    fi
done

# Resumen
echo ""
echo "============================================"
echo "   Configuracion Completada"
echo "============================================"
echo ""
echo "Proximos pasos:"
echo "  1. Activar entorno: source venv_sov/bin/activate"
echo "  2. Ejecutar tests:"
echo "     pytest -v"
echo "  3. Probar con datos de ejemplo:"
echo "     python scripts/merge_params.py Example"
echo "  4. Ejecutar Vector QA:"
echo "     python scripts/vecqa_to_post_qa.py --country Guatemala"
echo "  5. Ejecutar app Streamlit:"
echo "     streamlit run streamlit_app/streamlit_forecast_validator.py"
echo ""
echo "Ver README.md para mas informacion"
echo ""
