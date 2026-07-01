# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: image_info.py
#
# Obtiene información básica de una imagen.
# ==========================================================

from pathlib import Path

import imageio.v3 as iio
import tifffile


def get_image_info(filename):

    filename = Path(filename)

    extension = filename.suffix.lower()

    if extension in (".tif", ".tiff"):

        image = tifffile.imread(filename)

    else:

        image = iio.imread(filename)

    height = image.shape[0]
    width = image.shape[1]

    info = {
        "name": filename.name,
        "width": width,
        "height": height,
        "scale": "Sin calibrar",
        "status": "Imagen cargada",
    }

    return info
