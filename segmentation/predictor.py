# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: predictor.py
#
# Interfaz con MobileSAM para la predicción de máscaras
# basada en clics del usuario.
# ==========================================================

import urllib.request

import cv2
import numpy as np
import torch
from mobile_sam import SamPredictor, sam_model_registry

from settings import MODEL_FILE, MODEL_FOLDER, MODEL_URL


class Segmenter:
    def __init__(self):
        self.predictor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.image_set = False

    def check_and_download_model(self):
        """
        Verifica si existe el archivo del modelo.
        Si no existe, lo descarga.
        """
        if not MODEL_FILE.exists():
            print(f"Modelo no encontrado en {MODEL_FILE}. Descargando...")
            MODEL_FOLDER.mkdir(parents=True, exist_ok=True)

            try:
                urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)
                print("Descarga completada con éxito.")
            except Exception as e:
                print(f"Error al descargar el modelo: {e}")
                return False
        return True

    def initialize(self):
        """
        Carga el modelo en memoria.
        """
        if not self.check_and_download_model():
            raise RuntimeError("No se pudo obtener el modelo MobileSAM.")

        print(f"Inicializando MobileSAM en {self.device}...")

        # MobileSAM usa el tipo de modelo "vit_t"
        model_type = "vit_t"

        sam = sam_model_registry[model_type](checkpoint=str(MODEL_FILE))
        sam.to(device=self.device)
        sam.eval()

        self.predictor = SamPredictor(sam)
        print("MobileSAM inicializado.")

    def set_image(self, image):
        """
        Pasa la imagen a MobileSAM para calcular los embeddings.
        Esto puede tardar unos segundos, pero se hace una sola vez por imagen.
        """
        if self.predictor is None:
            self.initialize()

        # SAM espera RGB, ImageIO/tifffile devuelven 2D para grises.
        if len(image.shape) == 2:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif len(image.shape) == 3 and image.shape[2] == 4:
            # RGBA a RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        else:
            image_rgb = image

        print("Calculando embeddings de la imagen (esto puede tardar)...")
        self.predictor.set_image(image_rgb)
        self.image_set = True
        print("Embeddings calculados. Listo para predecir.")

    def predict_point(self, x, y):
        """
        Devuelve una máscara a partir de un clic (punto positivo).
        """
        if not self.image_set:
            return None

        # MobileSAM espera (x, y) donde x es columna y y es fila
        input_point = np.array([[x, y]])
        input_label = np.array([1])  # 1 indica punto positivo (foreground)

        masks, scores, logits = self.predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=False,  # Pedimos solo la mejor máscara
        )

        return masks[0]
