# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: image_session.py
#
# Información temporal asociada a UNA imagen.
# ==========================================================

from pathlib import Path


class ImageSession:

    def __init__(self, filename):

        self.filename = Path(filename)

        # --------------------------------------------------
        # Información del proyecto
        # --------------------------------------------------

        self.calibration = None

        self.rois = []

        self.segmentations = []

        self.measurements = []

        self.masks = []

        self.notes = ""

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def name(self):

        return self.filename.name

    # ======================================================

    @property
    def stem(self):

        return self.filename.stem

    # ======================================================

    @property
    def data_folder(self):
        """
        Carpeta donde se guardarán los datos
        asociados a esta imagen.

        Ejemplo:

            imagen.tif

                ↓

            imagen/
        """

        return self.filename.parent / self.filename.stem

    # ======================================================
    # CALIBRACIÓN
    # ======================================================

    @property
    def calibrated(self):
        """
        Indica si la imagen posee una calibración válida.
        """

        return self.calibration is not None

    # ======================================================

    def set_calibration(
        self,
        pixels,
        distance,
        unit
    ):
        """
        Guarda la calibración de la imagen.
        """

        pixels = float(pixels)
        distance = float(distance)

        self.calibration = {

            "pixels": pixels,

            "distance": distance,

            "unit": unit,

            "pixel_size": distance / pixels

        }

    # ======================================================

    def clear_calibration(self):
        """
        Elimina la calibración.
        """

        self.calibration = None