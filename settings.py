# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: settings.py
#
# Configuración global del proyecto.
# ==========================================================

from pathlib import Path


# ==========================================================
# INFORMACIÓN GENERAL DEL PROYECTO
# ==========================================================

PROGRAM_NAME = "TEM Segmenter"

VERSION = "1.0"

AUTHOR = "Dr. Ezequiel Grondona"


# ==========================================================
# CARPETA PRINCIPAL DEL PROYECTO
# ==========================================================

PROJECT_ROOT = Path(__file__).parent


# ==========================================================
# MODELO MobileSAM
# ==========================================================

RESOURCES_FOLDER = PROJECT_ROOT / "resources"

MODEL_FOLDER = RESOURCES_FOLDER / "models"

MODEL_FILE = MODEL_FOLDER / "mobile_sam.pt"

# URL oficial para descargar los pesos de MobileSAM
MODEL_URL = (
    "https://github.com/ChaoningZhang/MobileSAM/raw/master/weights/mobile_sam.pt"
)
