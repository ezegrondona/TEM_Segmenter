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
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from core.tool_manager import Tool, ToolManager

# Modos de interacción disponibles
MODE_NONE = "none"
MODE_SAM = "sam"  # Segmentación automática con clic
MODE_MANUAL = "manual"  # Dibujo manual de polígono


class ImageView(QWidget):

    measurement_finished = Signal(float)
    mask_accepted = Signal(int)  # emite el número de máscara aceptada
    mask_removed = Signal(int)  # emite el número de máscara borrada

    def __init__(self):

        super().__init__()

        self.viewer = None
        self.image_layer = None
        self.measure_layer = None

        self.segmenter = None
        self.temp_mask_layer = None
        self.accepted_masks_layer = None

        # Modo activo
        self.interaction_mode = MODE_NONE

        # Estado de la barra espaciadora (pan temporal durante segmentación)
        self._space_held = False

        # Orden en que se fueron aceptando las máscaras de ESTA imagen,
        # usado para poder deshacer (Ctrl+Z) la última aceptada. Se
        # reinicia cada vez que se carga una imagen nueva (ver clear()).
        self._mask_history = []

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
        canvas = self.viewer.window._qt_viewer.canvas.native
        canvas.installEventFilter(self)

    def eventFilter(self, obj, event):

        from PySide6.QtCore import QEvent

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
    # Propiedades de conveniencia
    # ======================================================

    @property
    def segmentation_mode(self):
        return self.tool_manager.current_tool == Tool.SAM

    # ======================================================

    def clear(self):

        self.viewer.layers.clear()

        self.image_layer = None
        self.measure_layer = None
        self.temp_mask_layer = None
        self.accepted_masks_layer = None

        self._mask_history = []

    # ======================================================

    def load_image(self, filename):

        filename = Path(filename)

        self.clear()

        if filename.suffix.lower() in (".tif", ".tiff"):
            image = tifffile.imread(filename)
        else:
            image = iio.imread(filename)

        self.image_layer = self.viewer.add_image(image, name=filename.name)

        self.measure_layer = self.viewer.add_shapes(
            name="Calibration",
            shape_type="line",
            edge_color="yellow",
            edge_width=3,
            face_color="transparent",
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

        pixels = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

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
                colormap=DirectLabelColormap(color_dict={None: (1.0, 0.0, 0.0, 1.0)}),
            )

        if self.accepted_masks_layer is None:
            self.accepted_masks_layer = self.viewer.add_labels(
                np.zeros(shape, dtype=int),
                name="Segmentations",
                opacity=0.55,
                # Mismo mecanismo: todas las máscaras aprobadas se ven
                # verdes, sin importar cuántas distintas haya (cada una
                # mantiene su propio número de etiqueta internamente).
                colormap=DirectLabelColormap(color_dict={None: (0.0, 1.0, 0.0, 1.0)}),
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

        print(
            "Modo segmentación activo. Haga clic en una estructura y presione ENTER para aceptar."
        )

    # ======================================================

    def stop_segmentation(self):
        if self.viewer and self.on_mouse_click in self.viewer.mouse_drag_callbacks:
            self.viewer.mouse_drag_callbacks.remove(self.on_mouse_click)

        self.interaction_mode = MODE_NONE
        self.tool_manager.activate(Tool.NONE)

        print("Modo segmentación finalizado.")

    # ======================================================

    def on_mouse_click(self, viewer, event):

        if self.tool_manager.current_tool != Tool.SAM:
            return

        if self._space_held:
            return

        if event.type == "mouse_press":

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
        existing = [
            layer for layer in self.viewer.layers if layer.name == manual_layer_name
        ]

        if existing:
            self.manual_shapes_layer = existing[0]
        else:
            self.manual_shapes_layer = self.viewer.add_shapes(
                name=manual_layer_name,
                shape_type="polygon",
                edge_color="cyan",
                face_color="transparent",
                edge_width=2,
            )

        # Activar modo dibujo de polígono
        self.manual_shapes_layer.mode = "add_polygon"

        self.interaction_mode = MODE_MANUAL
        self.tool_manager.activate(Tool.MANUAL)

        # Conectar evento de datos para detectar cuando termina el polígono
        self.manual_shapes_layer.events.data.connect(self._on_manual_shape_added)

        self.setFocus()
        print(
            "Modo manual activo. Dibuje el contorno haciendo clics y ciérrelo con doble clic."
        )

    # ======================================================

    def stop_manual_segmentation(self):
        self.interaction_mode = MODE_NONE
        self.tool_manager.activate(Tool.NONE)

        if (
            hasattr(self, "manual_shapes_layer")
            and self.manual_shapes_layer is not None
        ):
            try:
                self.manual_shapes_layer.events.data.disconnect(
                    self._on_manual_shape_added
                )
            except Exception:
                pass
            self.manual_shapes_layer.mode = "pan_zoom"

        print("Modo manual finalizado.")

    # ======================================================

    def _on_manual_shape_added(self, event):
        """Convierte el polígono dibujado a una máscara en temp_mask_layer."""
        if self.tool_manager.current_tool != Tool.MANUAL:
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
            self._on_space_pressed()
            event.accept()

        else:
            super().keyPressEvent(event)

    # ======================================================

    def keyReleaseEvent(self, event):
        """Detecta cuando se suelta la barra espaciadora para volver a segmentar."""

        if event.key() == Qt.Key_Space:
            self._on_space_released()
            event.accept()
        else:
            super().keyReleaseEvent(event)

    # ======================================================

    def _on_space_pressed(self):
        """
        Activa el modo "mover imagen" temporal mientras se mantiene
        presionada la barra espaciadora.

        En modo manual, la capa de shapes está en modo "add_polygon",
        que captura el arrastre del mouse como nuevos vértices del
        polígono en lugar de dejar que la cámara haga paneo. Por eso,
        mientras se mantiene espacio, esa capa se cambia a "pan_zoom"
        (se restaura en _on_space_released al soltar la tecla).
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

    # ======================================================

    def _on_space_released(self):
        """
        Desactiva el modo "mover imagen" y, si había una segmentación
        manual en curso, restaura el modo "add_polygon" de la capa de
        shapes para poder seguir dibujando el polígono.
        """

        self._space_held = False
        self._set_pan_cursor(False)

        if (
            self.interaction_mode == MODE_MANUAL
            and getattr(self, "manual_shapes_layer", None) is not None
        ):
            self.manual_shapes_layer.mode = "add_polygon"

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

        if (
            self.tool_manager.current_tool == Tool.MANUAL
            and getattr(self, "manual_shapes_layer", None) is not None
        ):
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
        new_label = current_max + 1

        accepted_data = self.accepted_masks_layer.data.copy()
        accepted_data[self.temp_mask_layer.data > 0] = new_label
        self.accepted_masks_layer.data = accepted_data

        self.temp_mask_layer.data = np.zeros_like(self.temp_mask_layer.data)

        # Limpiar shapes manuales después de aceptar
        if (
            hasattr(self, "manual_shapes_layer")
            and self.manual_shapes_layer is not None
        ):
            try:
                self.manual_shapes_layer.data = []
            except Exception:
                pass

        self._mask_history.append(new_label)

        self.mask_accepted.emit(new_label)
        print(f"Máscara {new_label} aceptada.")

    # ======================================================
    # BORRAR / DESHACER MÁSCARAS YA ACEPTADAS
    # ======================================================

    def get_mask_labels(self):
        """
        Devuelve la lista ordenada de los números de máscara
        actualmente aceptados en la imagen mostrada (para poblar
        el panel de "Segmentaciones" del lado derecho).
        """

        if self.accepted_masks_layer is None:
            return []

        labels = np.unique(self.accepted_masks_layer.data)

        return sorted(int(label) for label in labels if label != 0)

    # ======================================================

    def remove_mask(self, label_id):
        """
        Borra UNA máscara aceptada específica (por su número),
        dejando intactas las demás. Devuelve True si se borró
        algo, False si esa máscara no existía.
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
        print(f"Máscara {label_id} borrada.")

        return True

    # ======================================================

    def undo_last_mask(self):
        """
        Deshace (borra) la última máscara aceptada en esta imagen
        desde que se cargó (Ctrl+Z). Devuelve el número de máscara
        deshecha, o None si no hay nada para deshacer.

        Nota: el historial se reinicia cada vez que se cambia de
        imagen, así que esto deshace acciones de la sesión de
        trabajo actual sobre esta imagen, no de corridas anteriores
        del programa.
        """

        if not self._mask_history:
            return None

        label_id = self._mask_history[-1]

        if self.remove_mask(label_id):
            return label_id

        return None
