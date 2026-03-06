# Setup Script para SOV Forecasting
# Ejecutar este script para configurar el entorno inicial

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   SOV - LATAM Forecasting Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "[1/5] Verificando Python..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python no encontrado. Por favor instala Python 3.11.9" -ForegroundColor Red
    exit 1
}
Write-Host "      ✓ $pythonVersion" -ForegroundColor Green

# Crear entorno virtual si no existe
Write-Host "[2/5] Configurando entorno virtual..." -ForegroundColor Yellow
if (-Not (Test-Path "venv_sov")) {
    python -m venv venv_sov
    Write-Host "      ✓ Entorno virtual creado: venv_sov" -ForegroundColor Green
} else {
    Write-Host "      ✓ Entorno virtual ya existe" -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "[3/5] Activando entorno virtual..." -ForegroundColor Yellow
try {
    & ".\venv_sov\Scripts\Activate.ps1" -ErrorAction Stop
    Write-Host "      ✓ Entorno virtual activado" -ForegroundColor Green
} catch {
    Write-Host "      ! Error al activar entorno virtual" -ForegroundColor Yellow
    Write-Host "      ! Si ves error de ejecucion de scripts, ejecuta:" -ForegroundColor Yellow
    Write-Host "        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Write-Host "      ! Luego vuelve a ejecutar este script" -ForegroundColor Yellow
    exit 1
}

# Instalar dependencias
Write-Host "[4/5] Instalando dependencias..." -ForegroundColor Yellow
if (-Not (Test-Path "requirements.txt")) {
    Write-Host "      ERROR: requirements.txt no encontrado" -ForegroundColor Red
    exit 1
}
Write-Host "      Esto puede tomar varios minutos..." -ForegroundColor Gray

# Usar pip del entorno virtual explicitamente
& ".\venv_sov\Scripts\pip.exe" install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR: Fallo al instalar dependencias" -ForegroundColor Red
    exit 1
}
Write-Host "      ✓ Dependencias instaladas" -ForegroundColor Green

# Verificar/Crear estructura de directorios
Write-Host "[5/5] Verificando estructura de directorios..." -ForegroundColor Yellow

$directories = @(
    "data\Params",
    "data\Params_fix",
    "data\Params_new",
    "data\examples",
    "historical_decisions"
)

foreach ($dir in $directories) {
    if (Test-Path $dir) {
        Write-Host "      ✓ $dir" -ForegroundColor Green
    } else {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        if (Test-Path $dir) {
            Write-Host "      ✓ $dir (creado)" -ForegroundColor Cyan
        } else {
            Write-Host "      ✗ $dir (error al crear)" -ForegroundColor Red
        }
    }
}

# Resumen final
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Configuracion Completada" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximos pasos:" -ForegroundColor Yellow
Write-Host "  1. Activar entorno: .\venv_sov\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Ejecutar tests:" -ForegroundColor White
Write-Host "     pytest -v" -ForegroundColor Gray
Write-Host "  3. Probar con datos de ejemplo:" -ForegroundColor White
Write-Host "     python scripts\merge_params.py Example" -ForegroundColor Gray
Write-Host "  4. Ejecutar Vector QA:" -ForegroundColor White
Write-Host "     python scripts\vecqa_to_post_qa.py --country Guatemala" -ForegroundColor Gray
Write-Host "  5. Ejecutar app Streamlit:" -ForegroundColor White
Write-Host "     streamlit run streamlit_app\streamlit_forecast_validator.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Ver README.md para mas informacion" -ForegroundColor Cyan
Write-Host ""
