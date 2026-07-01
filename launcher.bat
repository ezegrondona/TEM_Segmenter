@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ===================================================
echo   TEM Segmenter - Inicializando...
echo ===================================================

:: 1. Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se detecto Python instalado o no esta en el PATH de Windows.
    echo.
    echo El programa necesita que instales Python 3.9 o superior.
    echo ATENCION: Durante la instalacion de Python, asegurate de marcar
    echo la casilla "Add python.exe to PATH".
    echo.
    echo Abriendo la pagina oficial de descarga de Python...
    start https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 2. Crear entorno virtual (solo la primera vez)
if not exist "venv\Scripts\python.exe" (
    echo.
    echo [1/3] Creando entorno virtual aislado (esto ocurre solo la primera vez)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual. Verifica tus permisos.
        pause
        exit /b 1
    )
)

:: 3. Activar e Instalar dependencias
call venv\Scripts\activate.bat

python -c "import PySide6, napari, torch, mobile_sam" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [2/3] Instalando dependencias necesarias por primera vez...
    echo Esto descargara los paquetes desde internet. Puede tardar varios minutos dependiendo de tu conexion.
    python -m pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Hubo un problema al descargar las dependencias. Verifica tu conexion a internet.
        pause
        exit /b 1
    )
    echo [INFO] Instalacion completada con exito.
)

:: 4. Iniciar la aplicacion
echo.
echo [3/3] Iniciando aplicacion...
start "" pythonw main.py
