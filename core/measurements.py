# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: measurements.py
#
# Cálculo de métricas estilo FIJI.
# ==========================================================

import math

import numpy as np
from skimage.measure import regionprops


def calculate_measurements(masks, intensity_image, calibration=None):
    """
    Calcula métricas geométricas y de intensidad para cada ROI (etiqueta) en 'masks'.
    Retorna una lista de diccionarios, donde cada diccionario representa un ROI.
    """
    if masks is None or not np.any(masks > 0):
        return []

    # skimage regionprops necesita una imagen de intensidad (idealmente grayscale)
    # Si la imagen es RGB, la pasamos a escala de grises para el mean gray value.
    if intensity_image.ndim == 3:
        # Ponderación estándar (luminance)
        intensity_gray = (
            0.299 * intensity_image[..., 0]
            + 0.587 * intensity_image[..., 1]
            + 0.114 * intensity_image[..., 2]
        )
    else:
        intensity_gray = intensity_image

    props = regionprops(masks, intensity_image=intensity_gray)

    results = []

    # Parámetros de calibración
    pixel_size = 1.0
    unit = "px"
    if calibration is not None:
        pixel_size = calibration.get("pixel_size", 1.0)
        unit = calibration.get("unit", "px")

    area_factor = pixel_size**2

    for p in props:
        roi_id = p.label

        # --------------------------------------------------
        # Área e Intensidad
        # --------------------------------------------------
        area_px = p.area
        area = area_px * area_factor

        mean_val = p.intensity_mean
        min_val = p.intensity_min
        max_val = p.intensity_max

        # --------------------------------------------------
        # Perímetro y Feret
        # --------------------------------------------------
        perim_px = p.perimeter
        perimeter = perim_px * pixel_size

        feret_max_px = p.feret_diameter_max
        feret_max = feret_max_px * pixel_size

        # --------------------------------------------------
        # Descriptores de Forma (Shape Descriptors estilo FIJI)
        # --------------------------------------------------
        # Circularity = 4pi * (area / perimeter^2). 1.0 es círculo perfecto.
        # Si perim_px es 0, circularity no está definida.
        circularity = 0.0
        if perim_px > 0:
            circularity = 4 * math.pi * (area_px / (perim_px**2))

        # Aspect Ratio = major_axis / minor_axis
        aspect_ratio = 0.0
        if p.axis_minor_length > 0:
            aspect_ratio = p.axis_major_length / p.axis_minor_length

        # Roundness = 4 * area / (pi * major_axis^2)
        roundness = 0.0
        if p.axis_major_length > 0:
            roundness = 4 * area_px / (math.pi * (p.axis_major_length**2))

        # Solidity = area / convex_area
        solidity = 0.0
        if p.area_convex > 0:
            solidity = area_px / p.area_convex

        results.append(
            {
                "ROI": roi_id,
                f"Area ({unit}²)": round(area, 4),
                "Mean": round(mean_val, 4),
                "Min": round(min_val, 4),
                "Max": round(max_val, 4),
                f"Perimeter ({unit})": round(perimeter, 4),
                "Circularity": round(circularity, 4),
                "Aspect Ratio": round(aspect_ratio, 4),
                "Roundness": round(roundness, 4),
                "Solidity": round(solidity, 4),
                f"Feret Max ({unit})": round(feret_max, 4),
            }
        )

    return results
