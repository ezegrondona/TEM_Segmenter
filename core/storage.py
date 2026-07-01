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
import roifile
import tifffile
from skimage import measure


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
        "pixel_size": image_session.calibration["pixel_size"],
    }

    with open(calibration_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_calibration(data_folder):
    """
    Carga la calibración desde una carpeta de datos.
    Retorna un diccionario o None si no existe o falla.
    """

    calibration_file = Path(data_folder) / "calibration.json"

    if not calibration_file.exists():
        return None

    try:
        with open(calibration_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar calibración: {e}")
        return None


# ==========================================================
# MÁSCARAS / SEGMENTACIONES
# ==========================================================


def save_masks(image_session):
    """
    Guarda la matriz combinada de segmentaciones aceptadas como TIFF.
    Se necesita para poder recargar el proyecto y seguir editando.
    """

    if not image_session.has_masks:
        return

    data_folder = image_session.data_folder
    data_folder.mkdir(parents=True, exist_ok=True)

    masks_file = data_folder / "masks.tif"

    tifffile.imwrite(masks_file, image_session.masks.astype(np.uint32))


def load_masks(data_folder):
    """
    Carga la matriz de segmentaciones desde una carpeta de datos.
    Retorna un array de numpy o None si no existe o falla.
    """

    masks_file = Path(data_folder) / "masks.tif"

    if not masks_file.exists():
        return None

    try:
        return tifffile.imread(masks_file)
    except Exception as e:
        print(f"Error al cargar máscaras: {e}")
        return None


# ==========================================================
# ROIs INDIVIDUALES ESTILO FIJI/IMAGEJ (RoiSet.zip)
# ==========================================================


def save_rois(image_session):
    """
    Convierte cada segmentación aceptada en un ROI individual tipo
    ImageJ (FREEHAND) y los guarda en RoiSet.zip.

    Se abre en Fiji arrastrando el .zip a la barra, o desde el
    ROI Manager con "More >> Open...". Cada ROI puede seleccionarse
    o eliminarse de forma individual desde el ROI Manager.

    Los ROIs se guardan en coordenadas de píxel (sin calibración).
    """

    if not image_session.has_masks:
        return

    masks = image_session.masks
    labels = np.unique(masks)

    rois = []

    for label_id in labels:

        if label_id == 0:
            continue

        binary = masks == label_id

        contours = measure.find_contours(binary.astype(float), level=0.5)

        if not contours:
            continue

        # Si hay más de un contorno (regiones desconectadas),
        # se usa el más largo.
        contour = max(contours, key=len)

        # find_contours devuelve (fila, columna) = (y, x);
        # ImageJ espera (x, y).
        points = np.column_stack([contour[:, 1], contour[:, 0]])

        roi = roifile.ImagejRoi.frompoints(points, name=f"Mask_{int(label_id):03d}")

        rois.append(roi)

    if not rois:
        return

    data_folder = image_session.data_folder
    data_folder.mkdir(parents=True, exist_ok=True)

    roiset_file = data_folder / "RoiSet.zip"

    # mode="w" sobrescribe el zip anterior en vez de ir acumulando ROIs viejos.
    roifile.roiwrite(roiset_file, rois, mode="w")
