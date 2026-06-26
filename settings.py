# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: settings.py
#
# Descripción:
# Configuración global del proyecto.
#
# Todas las constantes importantes del programa se almacenan
# aquí para evitar repetir información en múltiples archivos.
#
# Autor:
# Dr. Ezequiel + Aether
# ==========================================================

from pathlib import Path


# ==========================================================
# INFORMACIÓN GENERAL DEL PROYECTO
# ==========================================================

PROGRAM_NAME = "TEM Segmenter"

VERSION = "0.1.0"

AUTHOR = "Dr. Ezequiel + Aether"


# ==========================================================
# CARPETA PRINCIPAL DEL PROYECTO
# ==========================================================

PROJECT_ROOT = Path(__file__).parent


# ==========================================================
# CARPETAS DEL PROYECTO
# ==========================================================

GUI_FOLDER = PROJECT_ROOT / "gui"

IO_FOLDER = PROJECT_ROOT / "io"

SEGMENTATION_FOLDER = PROJECT_ROOT / "segmentation"

MEASUREMENTS_FOLDER = PROJECT_ROOT / "measurements"

RESOURCES_FOLDER = PROJECT_ROOT / "resources"


# ==========================================================
# FUTURA CARPETA DEL MODELO MobileSAM
# ==========================================================

MODEL_FOLDER = RESOURCES_FOLDER / "models"

MODEL_FILE = MODEL_FOLDER / "mobile_sam.pt"

# URL oficial para descargar los pesos de MobileSAM
MODEL_URL = "https://github.com/ChaoningZhang/MobileSAM/raw/master/weights/mobile_sam.pt"