# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: image_view.py
# ==========================================================

from pathlib import Path
import math

import imageio.v3 as iio
import napari
from napari.utils.colormaps import DirectLabelColormap
import numpy as np
import tifffile

from PySide6.QtCore import Signal, Qt
from core.tool_manager import ToolManager, Tool
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

        # Estado de la barra espaciadora (pan temporal durante segmentación)
        self._space_held = False
        
        # Administrador de herramientas
        self.tool_manager = ToolManager()

        self.setup_ui()

    # ======================================================

    def setup_ui(self):

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Asegura que este widget pueda recibir foco de teclado
        # (necesario para ENTER, ESCAPE y la barra espaciadora).
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
                opacity=0.55,
                # En napari >= 0.5 el kwarg 'color' fue eliminado del
                # constructor de Labels; ahora el color fijo se define
                # con un DirectLabelColormap. La clave "None" actúa como
                # color por defecto para cualquier etiqueta no nula
                # -> todo lo seleccionado se ve rojo.
                colormap=DirectLabelColormap(
                    color_dict={None: (1.0, 0.0, 0.0, 1.0)}
                )
            )

        if self.accepted_masks_layer is None:
            self.accepted_masks_layer = self.viewer.add_labels(
                np.zeros(shape, dtype=int),
                name="Segmentations",
                opacity=0.55,
                # Mismo mecanismo: todas las máscaras aprobadas se ven
                # verdes, sin importar cuántas distintas haya (cada una
                # mantiene su propio número de etiqueta internamente).
                colormap=DirectLabelColormap(
                    color_dict={None: (0.0, 1.0, 0.0, 1.0)}
                )
            )

    # ======================================================
    # PERSISTENCIA DE MÁSCARAS (lectura/restauración externa)
    # ======================================================

    def get_masks_data(self):
        """
        Devuelve una copia de la matriz de segmentaciones aceptadas
        actual, o None si todavía no existe la capa (no se aceptó
        ninguna segmentación en esta imagen).
        """

        if self.accepted_masks_layer is None:
            return None

        return self.accepted_masks_layer.data.copy()

    # ======================================================

    def load_accepted_masks(self, masks_array):
        """
        Restaura segmentaciones previamente guardadas (desde disco
        o desde la sesión en memoria) en la capa de segmentaciones
        aceptadas, creándola si todavía no existe.
        """

        if self.image_layer is None or masks_array is None:
            return

        self._ensure_mask_layers()

        expected_shape = self.accepted_masks_layer.data.shape

        if masks_array.shape != expected_shape:
            print(
                f"Aviso: las máscaras guardadas ({masks_array.shape}) no "
                f"coinciden con el tamaño de la imagen actual ({expected_shape}). "
                "Se ignoran para evitar datos corruptos."
            )
            return

        self.accepted_masks_layer.data = masks_array.astype(int)

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
        self.tool_manager.activate(Tool.SAM)

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
        self.tool_manager.activate(Tool.NONE)
    
        print("Modo segmentación finalizado.")

    # ======================================================

    def on_mouse_click(self, viewer, event):

        if self.interaction_mode != MODE_SAM:
            return

        # Si se mantiene presionada la barra espaciadora, el clic se
        # destina a mover la imagen (pan), no a segmentar.
        if self._space_held:
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
        self.tool_manager.activate(Tool.MANUAL)

        # Conectar evento de datos para detectar cuando termina el polígono
        self.manual_shapes_layer.events.data.connect(self._on_manual_shape_added)

        self.setFocus()
        print("Modo manual activo. Dibuje el contorno haciendo clics y ciérrelo con doble clic.")

    # ======================================================

    def stop_manual_segmentation(self):
        self.interaction_mode = MODE_NONE
        self.tool_manager.activate(Tool.NONE)

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
        """Qt intercepta las teclas directamente, sin depender de Napari."""

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._accept_temp_mask()

        elif event.key() == Qt.Key_Escape:
            self._cancel_temp_selection()

        elif event.key() == Qt.Key_Space:
            # Evita repetir la acción mientras la tecla queda presionada
            if not self._space_held:
                self._space_held = True
                self._set_pan_cursor(True)
            event.accept()

        else:
            super().keyPressEvent(event)

    # ======================================================

    def keyReleaseEvent(self, event):
        """Detecta cuando se suelta la barra espaciadora para volver a segmentar."""

        if event.key() == Qt.Key_Space:
            self._space_held = False
            self.tool_manager = ToolManager()
            self._set_pan_cursor(False)
            event.accept()
        else:
            super().keyReleaseEvent(event)

    # ======================================================

    def _set_pan_cursor(self, enabled):
        """
        Cambia el cursor a 'manito' mientras se mantiene presionada la
        barra espaciadora, para indicar que el modo activo es mover
        la imagen y no segmentar.
        """
        try:
            canvas_widget = self.viewer.window._qt_viewer.canvas.native
            if enabled:
                canvas_widget.setCursor(Qt.OpenHandCursor)
            else:
                canvas_widget.unsetCursor()
        except Exception:
            pass

    # ======================================================

    def _cancel_temp_selection(self):
        """
        Cancela la selección actual sin aceptarla (tecla ESCAPE).
        Funciona tanto si el clic fue de SAM como si fue un polígono
        manual: borra la máscara temporal y, si corresponde, el
        polígono que se estuviera dibujando, para poder repetir la
        selección desde cero.
        """

        if self.temp_mask_layer is not None:
            self.temp_mask_layer.data = np.zeros_like(self.temp_mask_layer.data)

        if self.interaction_mode == MODE_MANUAL and getattr(self, "manual_shapes_layer", None) is not None:
            try:
                self.manual_shapes_layer.data = []
                # Se reinicia el modo para descartar cualquier vértice
                # que estuviera "en curso" (todavía no confirmado).
                self.manual_shapes_layer.mode = "pan_zoom"
                self.manual_shapes_layer.mode = "add_polygon"
            except Exception:
                pass

        print("Selección cancelada (ESCAPE).")

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