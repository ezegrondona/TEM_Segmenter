# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: image_view.py
# ==========================================================

import math
from pathlib import Path

import imageio.v3 as iio
import napari
import numpy as np
import tifffile
from napari.utils.colormaps import DirectLabelColormap
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget
from skimage.draw import polygon as sk_polygon

from core.tool_manager import Tool, ToolManager
from segmentation.predictor import Segmenter
from segmentation.preprocessing import preprocess_image

# Modos de interacción disponibles
MODE_NONE   = "none"
MODE_SAM    = "sam"     # Segmentación automática con clic
MODE_MANUAL = "manual"  # Dibujo manual de polígono


class ImageView(QWidget):

    measurement_finished = Signal(float)
    mask_accepted        = Signal(int)  # emite el número de máscara aceptada
    mask_removed         = Signal(int)  # emite el número de máscara borrada

    def __init__(self):

        super().__init__()

        self.viewer               = None
        self.image_layer          = None
        self.measure_layer        = None

        self.segmenter            = None
        self.temp_mask_layer      = None
        self.accepted_masks_layer = None

        self.interaction_mode = MODE_NONE

        # Estado de la barra espaciadora (pan temporal durante segmentación)
        self._space_held = False

        # Historial de máscaras aceptadas en esta sesión de imagen,
        # usado para Ctrl+Z. Se reinicia al cambiar de imagen.
        self._mask_history = []

        self.tool_manager = ToolManager()

        self.setup_ui()

    # ======================================================

    def setup_ui(self):

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.setFocusPolicy(Qt.StrongFocus)

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

        canvas = self.viewer.window._qt_viewer.canvas.native
        canvas.installEventFilter(self)

    # ======================================================

    def eventFilter(self, obj, event):

        if event.type() == QEvent.KeyPress:

            if event.key() == Qt.Key_Space:
                self._on_space_pressed()

            return False

        elif event.type() == QEvent.KeyRelease:

            if event.key() == Qt.Key_Space:
                self._on_space_released()

            return False

        return super().eventFilter(obj, event)

    # ======================================================
    # PROPIEDADES
    # ======================================================

    @property
    def segmentation_mode(self):
        return self.tool_manager.current_tool == Tool.SAM

    # ======================================================

    def clear(self):

        self.viewer.layers.clear()

        self.image_layer          = None
        self.measure_layer        = None
        self.temp_mask_layer      = None
        self.accepted_masks_layer = None

        self._mask_history = []

    # ======================================================
    # CARGA DE IMAGEN
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

    def stop_measurement(self):

        if self.measure_layer is None:
            return

        self.measure_layer.data = []
        self.measure_layer.mode = "pan_zoom"

    def on_measurement_changed(self, event):

        if len(self.measure_layer.data) == 0:
            return

        line = self.measure_layer.data[0]

        if len(line) != 2:
            return

        y1, x1 = line[0]
        y2, x2 = line[1]

        pixels = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        self.measurement_finished.emit(pixels)

        self.measure_layer.mode = "pan_zoom"

    # ======================================================
    # CAPAS DE SEGMENTACIÓN (crea si no existen)
    # ======================================================

    def _ensure_mask_layers(self):

        shape = self.image_layer.data.shape[:2]

        if self.temp_mask_layer is None:
            self.temp_mask_layer = self.viewer.add_labels(
                np.zeros(shape, dtype=int),
                name="Temp Mask",
                opacity=0.55,
                colormap=DirectLabelColormap(
                    color_dict={None: (1.0, 0.0, 0.0, 1.0)}
                )
            )

        if self.accepted_masks_layer is None:
            self.accepted_masks_layer = self.viewer.add_labels(
                np.zeros(shape, dtype=int),
                name="Segmentations",
                opacity=0.55,
                colormap=DirectLabelColormap(
                    color_dict={None: (0.0, 1.0, 0.0, 1.0)}
                )
            )

    # ======================================================
    # PERSISTENCIA DE MÁSCARAS
    # ======================================================

    def get_masks_data(self):
        """
        Devuelve una copia de la matriz de segmentaciones aceptadas,
        o None si no se aceptó ninguna todavía.
        """

        if self.accepted_masks_layer is None:
            return None

        return self.accepted_masks_layer.data.copy()

    def load_accepted_masks(self, masks_array):
        """
        Restaura segmentaciones previas en la capa de segmentaciones aceptadas.
        """

        if self.image_layer is None or masks_array is None:
            return

        self._ensure_mask_layers()

        expected_shape = self.accepted_masks_layer.data.shape

        if masks_array.shape != expected_shape:
            return

        self.accepted_masks_layer.data = masks_array.astype(int)

    # ======================================================
    # SEGMENTACIÓN AUTOMÁTICA (SAM)
    # ======================================================

    def start_segmentation(self):

        if self.image_layer is None:
            return

        processed_image = preprocess_image(self.image_layer.data)

        if self.segmenter is None:
            self.segmenter = Segmenter()

        self.segmenter.set_image(processed_image)

        self._ensure_mask_layers()

        self.interaction_mode = MODE_SAM
        self.tool_manager.activate(Tool.SAM)

        if self.on_mouse_click not in self.viewer.mouse_drag_callbacks:
            self.viewer.mouse_drag_callbacks.append(self.on_mouse_click)

        self.setFocus()

    def stop_segmentation(self):

        if self.viewer and self.on_mouse_click in self.viewer.mouse_drag_callbacks:
            self.viewer.mouse_drag_callbacks.remove(self.on_mouse_click)

        self.interaction_mode = MODE_NONE
        self.tool_manager.activate(Tool.NONE)

    def on_mouse_click(self, viewer, event):

        if self.tool_manager.current_tool != Tool.SAM:
            return

        if self._space_held:
            return

        if event.type == "mouse_press":

            coords = self.image_layer.world_to_data(event.position)
            y, x = int(coords[0]), int(coords[1])

            h, w = self.image_layer.data.shape[:2]

            if 0 <= y < h and 0 <= x < w:

                mask = self.segmenter.predict_point(x, y)

                if mask is not None:

                    temp_data = np.zeros((h, w), dtype=int)
                    temp_data[mask] = 1

                    self.temp_mask_layer.data = temp_data

                    self.setFocus()

    # ======================================================
    # SEGMENTACIÓN MANUAL
    # ======================================================

    def start_manual_segmentation(self):

        if self.image_layer is None:
            return

        self._ensure_mask_layers()

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

        self.manual_shapes_layer.mode = "add_polygon"

        self.interaction_mode = MODE_MANUAL
        self.tool_manager.activate(Tool.MANUAL)

        self.manual_shapes_layer.events.data.connect(self._on_manual_shape_added)

        self.setFocus()

    def stop_manual_segmentation(self):

        self.interaction_mode = MODE_NONE
        self.tool_manager.activate(Tool.NONE)

        if hasattr(self, "manual_shapes_layer") and self.manual_shapes_layer is not None:
            try:
                self.manual_shapes_layer.events.data.disconnect(self._on_manual_shape_added)
            except Exception:
                pass
            self.manual_shapes_layer.mode = "pan_zoom"

    def _on_manual_shape_added(self, event):
        """Convierte el polígono dibujado a una máscara en temp_mask_layer."""

        if self.tool_manager.current_tool != Tool.MANUAL:
            return
        if not hasattr(self, "manual_shapes_layer"):
            return
        if len(self.manual_shapes_layer.data) == 0:
            return

        shape_data = self.manual_shapes_layer.data[-1]
        h, w = self.image_layer.data.shape[:2]

        ys = shape_data[:, 0].astype(int)
        xs = shape_data[:, 1].astype(int)

        rr, cc = sk_polygon(ys, xs, shape=(h, w))

        temp_data = np.zeros((h, w), dtype=int)
        temp_data[rr, cc] = 1
        self.temp_mask_layer.data = temp_data

        self.setFocus()

    # ======================================================
    # TECLAS
    # ======================================================

    def keyPressEvent(self, event):

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._accept_temp_mask()

        elif event.key() == Qt.Key_Escape:
            self._cancel_temp_selection()

        elif event.key() == Qt.Key_Space:
            self._on_space_pressed()
            event.accept()

        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):

        if event.key() == Qt.Key_Space:
            self._on_space_released()
            event.accept()
        else:
            super().keyReleaseEvent(event)

    def _on_space_pressed(self):
        """
        Activa el modo mover imagen mientras se mantiene espacio.
        En modo manual, pone la capa en pan_zoom para que el arrastre
        no agregue vértices al polígono.
        """

        if self._space_held:
            return

        self._space_held = True
        self._set_pan_cursor(True)

        if (
            self.interaction_mode == MODE_MANUAL
            and getattr(self, "manual_shapes_layer", None) is not None
        ):
            self.manual_shapes_layer.mode = "pan_zoom"

    def _on_space_released(self):
        """
        Desactiva el modo mover imagen y, si había segmentación manual
        en curso, restaura el modo add_polygon.
        """

        self._space_held = False
        self._set_pan_cursor(False)

        if (
            self.interaction_mode == MODE_MANUAL
            and getattr(self, "manual_shapes_layer", None) is not None
        ):
            self.manual_shapes_layer.mode = "add_polygon"

    def _set_pan_cursor(self, enabled):

        try:
            canvas_widget = self.viewer.window._qt_viewer.canvas.native
            if enabled:
                canvas_widget.setCursor(Qt.OpenHandCursor)
            else:
                canvas_widget.unsetCursor()
        except Exception:
            pass

    def _cancel_temp_selection(self):
        """
        Cancela la selección actual (ESCAPE) sin aceptarla.
        """

        if self.temp_mask_layer is not None:
            self.temp_mask_layer.data = np.zeros_like(self.temp_mask_layer.data)

        if (
            self.tool_manager.current_tool == Tool.MANUAL
            and getattr(self, "manual_shapes_layer", None) is not None
        ):
            try:
                self.manual_shapes_layer.data = []
                self.manual_shapes_layer.mode = "pan_zoom"
                self.manual_shapes_layer.mode = "add_polygon"
            except Exception:
                pass

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

        if hasattr(self, "manual_shapes_layer") and self.manual_shapes_layer is not None:
            try:
                self.manual_shapes_layer.data = []
            except Exception:
                pass

        self._mask_history.append(new_label)

        self.mask_accepted.emit(new_label)

    # ======================================================
    # BORRAR / DESHACER MÁSCARAS
    # ======================================================

    def get_mask_labels(self):
        """Lista ordenada de los números de máscara actualmente aceptados."""

        if self.accepted_masks_layer is None:
            return []

        labels = np.unique(self.accepted_masks_layer.data)

        return sorted(int(label) for label in labels if label != 0)

    def remove_mask(self, label_id):
        """
        Borra una máscara específica (por número), dejando intactas las demás.
        Devuelve True si se borró algo.
        """

        if self.accepted_masks_layer is None:
            return False

        data = self.accepted_masks_layer.data

        if not np.any(data == label_id):
            return False

        new_data = data.copy()
        new_data[new_data == label_id] = 0
        self.accepted_masks_layer.data = new_data

        if label_id in self._mask_history:
            self._mask_history.remove(label_id)

        self.mask_removed.emit(label_id)

        return True

    def undo_last_mask(self):
        """
        Deshace la última máscara aceptada en esta imagen (Ctrl+Z).
        El historial se reinicia al cambiar de imagen.
        """

        if not self._mask_history:
            return None

        label_id = self._mask_history[-1]

        if self.remove_mask(label_id):
            return label_id

        return None
