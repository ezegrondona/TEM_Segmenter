# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: image_session.py
#
# Información temporal asociada a UNA imagen.
# ==========================================================

from pathlib import Path

import numpy as np


class ImageSession:

    def __init__(self, filename):

        self.filename = Path(filename)

        self.calibration = None

        self.masks = None

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def name(self):

        return self.filename.name

    @property
    def data_folder(self):
        """
        Carpeta donde se guardarán los datos asociados a esta imagen.

        Ejemplo:
            imagen.tif → imagen/
        """

        return self.filename.parent / self.filename.stem

    # ======================================================
    # CALIBRACIÓN
    # ======================================================

    @property
    def calibrated(self):
        """Indica si la imagen posee una calibración válida."""

        return self.calibration is not None

    def set_calibration(self, pixels, distance, unit):
        """Guarda la calibración de la imagen."""

        pixels = float(pixels)
        distance = float(distance)

        self.calibration = {
            "pixels": pixels,
            "distance": distance,
            "unit": unit,
            "pixel_size": distance / pixels,
        }

    def clear_calibration(self):
        """Elimina la calibración."""

        self.calibration = None

    # ======================================================
    # MÁSCARAS / SEGMENTACIONES
    # ======================================================

    @property
    def has_masks(self):
        """
        Indica si la imagen tiene al menos una segmentación
        aceptada en memoria.
        """

        return self.masks is not None and np.any(self.masks > 0)

    def set_masks(self, masks_array):
        """
        Guarda en memoria la matriz combinada de todas las
        segmentaciones aceptadas para esta imagen.
        """

        self.masks = masks_array

    def clear_masks(self):
        """Elimina las máscaras en memoria."""

        self.masks = None
