# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: preprocessing.py
#
# Funciones para analizar y mejorar el contraste de 
# imágenes TEM antes de la segmentación.
# ==========================================================

import cv2
import numpy as np

def analyze_contrast(image):
    """
    Analiza el contraste de una imagen en escala de grises usando la desviación estándar.
    Devuelve True si el contraste es bajo, False si es adecuado.
    """
    if len(image.shape) > 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
    std_dev = np.std(image)
    
    # Umbral de desviación estándar (35.0 es un buen punto de partida para imágenes TEM)
    return std_dev < 35.0

def apply_clahe(image, clip_limit=2.0, tile_grid_size=(8, 8)):
    """
    Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization).
    Mejora el contraste local sin amplificar el ruido.
    """
    if len(image.shape) > 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    return clahe.apply(image)

def preprocess_image(image):
    """
    Analiza la imagen y le aplica CLAHE únicamente si tiene bajo contraste.
    Retorna la imagen preprocesada (o la original si no hacía falta).
    """
    if analyze_contrast(image):
        print("Bajo contraste detectado. Aplicando CLAHE...")
        return apply_clahe(image)
    
    print("Contraste adecuado. No se aplica preprocesamiento.")
    
    # Si es a color pero necesitamos blanco y negro, la convertimos igual
    if len(image.shape) > 2:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
    return image
