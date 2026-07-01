# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: image_loader.py
#
# Búsqueda de imágenes del proyecto.
# ==========================================================

from pathlib import Path

SUPPORTED_EXTENSIONS = (
    ".tif",
    ".tiff",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
)


def find_images(folder):

    folder = Path(folder)

    images = []

    for file in folder.iterdir():

        if not file.is_file():
            continue

        if file.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(file)

    images.sort(key=lambda p: p.name.lower())

    return images
