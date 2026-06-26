# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: image_view.py
# ==========================================================

from pathlib import Path
import math

import imageio.v3 as iio
import napari
import numpy as np
import tifffile

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

# Modos de interacción disponibles
MODE_NONE      = "none"
MODE_SAM       = "sam"       # Segmentación automática con clic
MODE_MANUAL    = "manual"    # Dibujo manual de polígono


class ImageView(QWidget):

    measurement_finished = Signal(float)
    mask_accepted        = Signal(int)     # emite el número de máscara aceptada

    def __init__(self):

        super().__init__()

        self.viewer               = None
        self.image_layer          = None
        self.measure_layer        = None

        self.segmenter            = None
        self.temp_mask_layer      = None
        self.accepted_masks_layer = None

        # Modo activo
        self.interaction_mode = MODE_NONE

        self.setup_ui()

    # ======================================================

    def setup_ui(self):

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.viewer = napari.Viewer(show=False)

        qt = self.viewer.window._qt_window

        qt.menuBar().hide()
        qt.statusBar().hide()

        try:
            self.viewer.window._qt_viewer.dockLayerList.hide()
            self.viewer.window._qt_viewer.dockLayerControls.hide()
            self.viewer.window._qt_viewer.dockConsole.hide()
            self.viewer.window._qt_viewer.activity_dialog.hide()
        except Exception:
            pass

        layout.addWidget(qt)
        self.setLayout(layout)

    # ======================================================
    # Propiedades de conveniencia
    # ======================================================

    @property
    def segmentation_mode(self):
        return self.interaction_mode == MODE_SAM

    # ======================================================

    def clear(self):

        self.viewer.layers.clear()

        self.image_layer          = None
        self.measure_layer        = None
        self.temp_mask_layer      = None
        self.accepted_masks_layer = None

    # ======================================================

    def load_image(self, filename):

        filename = Path(filename)

        self.clear()

        if filename.suffix.lower() in (".tif", ".tiff"):
            image = tifffile.imread(filename)
        else:
            image = iio.imread(filename)

        self.image_layer = self.viewer.add_image(
            image,
            name=filename.name
        )

        self.measure_layer = self.viewer.add_shapes(
            name="Calibration",
            shape_type="line",
            edge_color="yellow",
            edge_width=3,
            face_color="transparent"
        )

        self.measure_layer.events.data.connect(self.on_measurement_changed)

        self.viewer.reset_view()

    # ======================================================
    # CALIBRACIÓN
    # ======================================================

    def start_measurement(self):

        if self.measure_layer is None:
            return

        self.measure_layer.data = []
        self.measure_layer.mode = "add_line"

    # ======================================================

    def stop_measurement(self):

        if self.measure_layer is None:
            return

        self.measure_layer.data = []
        self.measure_layer.mode = "pan_zoom"

    # ======================================================

    def on_measurement_changed(self, event):

        if len(self.measure_layer.data) == 0:
            return

        line = self.measure_layer.data[0]

        if len(line) != 2:
            return

        y1, x1 = line[0]
        y2, x2 = line[1]

        pixels = math.sqrt(
            (x2 - x1) ** 2 +
            (y2 - y1) ** 2
        )

        self.measurement_finished.emit(pixels)

        # Volver al modo normal para que no siga dibujando
        self.measure_layer.mode = "pan_zoom"

    # ======================================================
    # CAPAS COMPARTIDAS (crea si no existen)
    # ======================================================

    def _ensure_mask_layers(self):
        shape = self.image_layer.data.shape[:2]

        if self.temp_mask_layer is None:
            self.temp_mask_layer = self.viewer.add_labels(
                np.zeros(shape, dtype=int),
                name="Temp Mask",
                opacity=0.55
            )

        if self.accepted_masks_layer is None:
            self.accepted_masks_layer = self.viewer.add_labels(
                np.zeros(shape, dtype=int),
                name="Segmentations",
                opacity=0.55
            )

    # ======================================================
    # SEGMENTACIÓN AUTOMÁTICA (SAM)
    # ======================================================

    def start_segmentation(self):

        if self.image_layer is None:
            return

        print("Preparando modo segmentación...")
        from segmentation.preprocessing import preprocess_image
        processed_image = preprocess_image(self.image_layer.data)

        if self.segmenter is None:
            from segmentation.predictor import Segmenter
            self.segmenter = Segmenter()

        self.segmenter.set_image(processed_image)

        self._ensure_mask_layers()

        self.interaction_mode = MODE_SAM

        if self.on_mouse_click not in self.viewer.mouse_drag_callbacks:
            self.viewer.mouse_drag_callbacks.append(self.on_mouse_click)

        # Dar foco al widget para recibir KeyPressEvent de Qt
        self.setFocus()

        print("Modo segmentación activo. Haga clic en una estructura y presione ENTER para aceptar.")

    # ======================================================

    def stop_segmentation(self):
        if self.viewer and self.on_mouse_click in self.viewer.mouse_drag_callbacks:
            self.viewer.mouse_drag_callbacks.remove(self.on_mouse_click)

        self.interaction_mode = MODE_NONE
        print("Modo segmentación finalizado.")

    # ======================================================

    def on_mouse_click(self, viewer, event):

        if self.interaction_mode != MODE_SAM:
            return

        if event.type == 'mouse_press':
            # Convertir coordenadas world → píxeles de imagen
            coords = self.image_layer.world_to_data(event.position)
            y, x = int(coords[0]), int(coords[1])

            h, w = self.image_layer.data.shape[:2]
            if 0 <= y < h and 0 <= x < w:
                print(f"Clic detectado en ({x}, {y})")

                mask = self.segmenter.predict_point(x, y)

                if mask is not None:
                    temp_data = np.zeros((h, w), dtype=int)
                    temp_data[mask] = 1
                    self.temp_mask_layer.data = temp_data
                    print("Máscara temporal generada. Presione ENTER para aceptar.")

                    # Dar foco al widget para que keyPressEvent funcione
                    self.setFocus()

    # ======================================================
    # SEGMENTACIÓN MANUAL (Shapes de napari)
    # ======================================================

    def start_manual_segmentation(self):

        if self.image_layer is None:
            return

        self._ensure_mask_layers()

        # Si ya existe la capa de shapes manual, reutizarla
        manual_layer_name = "Manual ROI"
        existing = [l for l in self.viewer.layers if l.name == manual_layer_name]

        if existing:
            self.manual_shapes_layer = existing[0]
        else:
            self.manual_shapes_layer = self.viewer.add_shapes(
                name=manual_layer_name,
                shape_type="polygon",
                edge_color="cyan",
                face_color="transparent",
                edge_width=2
            )

        # Activar modo dibujo de polígono
        self.manual_shapes_layer.mode = "add_polygon"

        self.interaction_mode = MODE_MANUAL

        # Conectar evento de datos para detectar cuando termina el polígono
        self.manual_shapes_layer.events.data.connect(self._on_manual_shape_added)

        self.setFocus()
        print("Modo manual activo. Dibuje el contorno haciendo clics y ciérrelo con doble clic.")

    # ======================================================

    def stop_manual_segmentation(self):
        self.interaction_mode = MODE_NONE

        if hasattr(self, "manual_shapes_layer") and self.manual_shapes_layer is not None:
            try:
                self.manual_shapes_layer.events.data.disconnect(self._on_manual_shape_added)
            except Exception:
                pass
            self.manual_shapes_layer.mode = "pan_zoom"

        print("Modo manual finalizado.")

    # ======================================================

    def _on_manual_shape_added(self, event):
        """Convierte el polígono dibujado a una máscara en temp_mask_layer."""
        if self.interaction_mode != MODE_MANUAL:
            return
        if not hasattr(self, "manual_shapes_layer"):
            return
        if len(self.manual_shapes_layer.data) == 0:
            return

        from skimage.draw import polygon as sk_polygon

        shape_data = self.manual_shapes_layer.data[-1]  # último polígono
        h, w = self.image_layer.data.shape[:2]

        ys = shape_data[:, 0].astype(int)
        xs = shape_data[:, 1].astype(int)

        rr, cc = sk_polygon(ys, xs, shape=(h, w))

        temp_data = np.zeros((h, w), dtype=int)
        temp_data[rr, cc] = 1
        self.temp_mask_layer.data = temp_data

        print("Contorno manual generado. Presione ENTER para aceptar.")
        self.setFocus()

    # ======================================================
    # ACEPTAR MÁSCARA (Enter → Qt keyPressEvent)
    # ======================================================

    def keyPressEvent(self, event):
        """Qt intercepta la tecla Enter directamente, sin depender de Napari."""

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._accept_temp_mask()
        else:
            super().keyPressEvent(event)

    # ======================================================

    def _accept_temp_mask(self):

        if self.temp_mask_layer is None or self.accepted_masks_layer is None:
            return

        if not np.any(self.temp_mask_layer.data > 0):
            return

        current_max = int(np.max(self.accepted_masks_layer.data))
        new_label   = current_max + 1

        accepted_data = self.accepted_masks_layer.data.copy()
        accepted_data[self.temp_mask_layer.data > 0] = new_label
        self.accepted_masks_layer.data = accepted_data

        self.temp_mask_layer.data = np.zeros_like(self.temp_mask_layer.data)

        # Limpiar shapes manuales después de aceptar
        if hasattr(self, "manual_shapes_layer") and self.manual_shapes_layer is not None:
            try:
                self.manual_shapes_layer.data = []
            except Exception:
                pass

        self.mask_accepted.emit(new_label)
        print(f"Máscara {new_label} aceptada.")