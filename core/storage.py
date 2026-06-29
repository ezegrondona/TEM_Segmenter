# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: storage.py
#
# Funciones para guardar y cargar datos del proyecto.
# ==========================================================

import json
from pathlib import Path

import numpy as np
import tifffile


# ==========================================================
# CALIBRACIÓN
# ==========================================================

def save_calibration(image_session):
    """
    Guarda la calibración de una imagen en su carpeta de datos.
    Crea la carpeta si no existe.
    """

    if not image_session.calibrated:
        return

    data_folder = image_session.data_folder
    data_folder.mkdir(parents=True, exist_ok=True)

    calibration_file = data_folder / "calibration.json"

    data = {
        "pixels": image_session.calibration["pixels"],
        "distance": image_session.calibration["distance"],
        "unit": image_session.calibration["unit"],
        "pixel_size": image_session.calibration["pixel_size"]
    }

    with open(calibration_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ==========================================================

def load_calibration(image_path):
    """
    Carga la calibración de una imagen desde su carpeta de datos.
    Retorna un diccionario con los datos o None si no existe.
    """

    image_path = Path(image_path)
    data_folder = image_path.parent / image_path.stem
    calibration_file = data_folder / "calibration.json"

    if not calibration_file.exists():
        return None

    try:
        with open(calibration_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error al cargar calibración: {e}")
        return None


# ==========================================================
# MÁSCARAS / SEGMENTACIONES
# ==========================================================

def save_masks(image_session):
    """
    Guarda la matriz combinada de segmentaciones aceptadas de una
    imagen en su carpeta de datos, como TIFF de enteros sin signo.
    Se guarda como TIFF (y no como JSON) para que sea directamente
    compatible con Fiji/ImageJ.
    """

    if not image_session.has_masks:
        return

    data_folder = image_session.data_folder
    data_folder.mkdir(parents=True, exist_ok=True)

    masks_file = data_folder / "masks.tif"

    tifffile.imwrite(
        masks_file,
        image_session.masks.astype(np.uint32)
    )


# ==========================================================

def load_masks(image_path):
    """
    Carga la matriz de segmentaciones guardada para una imagen,
    si existe. Retorna un array de numpy o None si no existe o
    si ocurre un error al leerlo.
    """

    image_path = Path(image_path)
    data_folder = image_path.parent / image_path.stem
    masks_file = data_folder / "masks.tif"

    if not masks_file.exists():
        return None

    try:
        return tifffile.imread(masks_file)
    except Exception as e:
        print(f"Error al cargar máscaras: {e}")
        return None
