@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ===================================================
echo   TEM Segmenter - Inicializando...
echo ===================================================

:: 1. Verificar que Python este instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se detecto Python instalado o no esta en el PATH de Windows.
    echo.
    echo El programa necesita Python 3.9 o superior.
    echo IMPORTANTE: Durante la instalacion, marcar "Add python.exe to PATH".
    echo.
    echo Abriendo la pagina de descarga...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. Verificar que Git este instalado (necesario para instalar MobileSAM)
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se detecto Git instalado. Git es necesario para descargar el
    echo modelo de inteligencia artificial en la primera ejecucion.
    echo.
    echo Abriendo la pagina de descarga de Git...
    start https://git-scm.com/download/win
    pause
    exit /b 1
)

:: 3. Crear entorno virtual (solo la primera vez)
if not exist "venv\Scripts\python.exe" (
    echo.
    echo [1/3] Creando entorno virtual aislado (ocurre solo la primera vez)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual. Verifica tus permisos.
        pause
        exit /b 1
    )
)

:: 4. Instalar dependencias si faltan
call venv\Scripts\activate.bat

python -c "import PySide6, napari, torch, mobile_sam" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [2/3] Instalando dependencias por primera vez...
    echo Esto descargara archivos desde internet. Puede tardar varios minutos.
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Problema al instalar dependencias. Verifica tu conexion a internet.
        pause
        exit /b 1
    )
    echo [INFO] Instalacion completada.
)

:: 5. Iniciar la aplicacion (sin ventana de consola)
echo.
echo [3/3] Iniciando aplicacion...
start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0main.py"
