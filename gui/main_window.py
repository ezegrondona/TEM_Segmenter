# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: main_window.py
# ==========================================================

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (QDialog, QFileDialog, QLabel, QMainWindow,
                               QMessageBox, QProgressBar, QSplitter,
                               QVBoxLayout, QWidget)

from core import storage
from core.image_info import get_image_info
from core.image_loader import find_images
from core.session import Session
from gui.calibration_dialog import CalibrationDialog
from gui.export_dialog import ExportDialog
from gui.image_view import ImageView
from gui.info_panel import InfoPanel
from gui.project_panel import ProjectPanel
from settings import PROGRAM_NAME, VERSION


class MainWindow(QMainWindow):

    # ======================================================
    # CONSTRUCTOR
    # ======================================================

    def __init__(self):

        super().__init__()

        self.images = []

        self.current_image = None

        # Sesión temporal
        self.session = Session()

        self.setup_ui()

        self.create_menu()

        # Ventana de calibración
        self.calibration_dialog = CalibrationDialog(self)

        # --------------------------------------------------
        # Conexiones
        # --------------------------------------------------

        self.project_panel.image_selected.connect(self.load_image)

        self.project_panel.image_closed.connect(self.on_image_closed)

        self.info_panel.calibrate_button.clicked.connect(self.open_calibration)

        self.info_panel.segment_button.clicked.connect(self.toggle_segmentation)

        self.info_panel.manual_segment_button.clicked.connect(
            self.toggle_manual_segmentation
        )

        self.image_view.mask_accepted.connect(self.on_mask_accepted)

        self.image_view.mask_removed.connect(self.on_mask_removed)

        self.info_panel.delete_mask_requested.connect(self.on_delete_mask_requested)

        self.info_panel.load_project_button.clicked.connect(self.load_project_data)

        self.calibration_dialog.start_measurement.connect(
            self.image_view.start_measurement
        )

        self.image_view.measurement_finished.connect(self.calibration_dialog.set_pixels)

        self.calibration_dialog.finished.connect(self.image_view.stop_measurement)

        self.calibration_dialog.calibration_saved.connect(self.save_calibration)

        # --------------------------------------------------
        # Atajo de teclado: Ctrl+Z deshace la última
        # segmentación aceptada en la imagen actual.
        # --------------------------------------------------

        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo_last_segmentation)

    # ======================================================
    # INTERFAZ
    # ======================================================

    def setup_ui(self):

        self.setWindowTitle(f"{PROGRAM_NAME} - v{VERSION}")

        self.resize(1400, 850)

        central = QWidget()

        layout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        self.project_panel = ProjectPanel()

        self.image_view = ImageView()

        self.info_panel = InfoPanel()

        splitter.addWidget(self.project_panel)
        splitter.addWidget(self.image_view)
        splitter.addWidget(self.info_panel)

        splitter.setSizes([260, 1000, 260])

        splitter.setChildrenCollapsible(False)

        layout.addWidget(splitter)

        central.setLayout(layout)

        self.setCentralWidget(central)

    # ======================================================
    # MENÚ
    # ======================================================

    def create_menu(self):

        menu = self.menuBar()

        file_menu = menu.addMenu("Archivo")

        # ----------------------------------------------
        # Abrir imagen
        # ----------------------------------------------

        open_image_action = QAction("Abrir imagen...", self)
        open_image_action.setShortcut(QKeySequence("Ctrl+O"))

        open_image_action.triggered.connect(self.open_image)

        file_menu.addAction(open_image_action)

        # ----------------------------------------------
        # Abrir carpeta
        # ----------------------------------------------

        open_folder_action = QAction("Abrir carpeta...", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))

        open_folder_action.triggered.connect(self.open_folder)

        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        # ----------------------------------------------
        # Guardar
        # ----------------------------------------------

        save_action = QAction("Guardar", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))

        save_action.triggered.connect(self.save_project)

        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # ----------------------------------------------
        # Exportar
        # ----------------------------------------------

        export_action = QAction("Exportar...", self)

        export_action.triggered.connect(self.export_project)

        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # ----------------------------------------------
        # Salir
        # ----------------------------------------------

        exit_action = QAction("Salir", self)

        exit_action.triggered.connect(self.close)

        file_menu.addAction(exit_action)

    # ======================================================
    # ABRIR IMAGEN
    # ======================================================

    def open_image(self):

        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Abrir imagen(es)",
            "",
            "Imágenes (*.tif *.tiff *.png *.jpg *.jpeg *.bmp)",
        )

        if not filenames:
            return

        # add_images() ya selecciona la última imagen agregada, lo
        # que dispara la señal image_selected -> load_image() sola.
        # Llamarla de nuevo acá duplicaba la carga (y, antes del fix
        # en session.py, generaba dos entradas para la misma imagen).
        self.project_panel.add_images(filenames)

    # ======================================================
    # ABRIR CARPETA
    # ======================================================

    def open_folder(self):

        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")

        if not folder:
            return

        self.project_panel.set_folder(folder)

        found_images = find_images(folder)

        if not found_images:
            QMessageBox.information(
                self, "Abrir carpeta", "No se encontraron imágenes en esa carpeta."
            )
            return

        self.project_panel.add_images(found_images)

        # add_images() ya seleccionó la última imagen agregada; acá
        # elegimos explícitamente la primera, lo que dispara
        # image_selected -> load_image() una sola vez.
        self.project_panel.select_image(found_images[0])

    # ======================================================
    # CARGAR IMAGEN
    # ======================================================

    def load_image(self, filename):

        self.current_image = filename

        if getattr(self.image_view, "segmentation_mode", False):
            self.image_view.stop_segmentation()
            self.info_panel.segment_button.setText("▶ Segmentación Automática")

        if self.image_view.interaction_mode == "manual":
            self.image_view.stop_manual_segmentation()
            self.info_panel.manual_segment_button.setText("✏️ Segmentación manual")

        self.image_view.load_image(filename)

        image_session = self.session.add_image(filename)

        # --------------------------------------------------
        # NOTA: ya no se lee nada de disco automáticamente acá.
        # Calibración y máscaras solo se restauran si ya estaban
        # en la sesión en memoria (porque esta misma imagen se
        # trabajó antes en esta corrida del programa). Para
        # traer datos guardados en una corrida anterior hay que
        # usar explícitamente "Cargar proyecto...".
        # --------------------------------------------------

        if image_session.masks is not None:
            self.image_view.load_accepted_masks(image_session.masks)

        self.refresh_masks_panel()

        info = get_image_info(filename)

        if image_session.calibrated:

            info["scale"] = (
                f'{image_session.calibration["pixel_size"]:.6f} '
                f'{image_session.calibration["unit"]}/px'
            )

            info["status"] = "Calibrada"

        self.info_panel.update_info(info)

    # ======================================================
    # CERRAR IMAGEN (botón ✕ del panel izquierdo)
    # ======================================================

    def on_image_closed(self, filename):
        """
        Se llama cuando el usuario cierra una imagen desde la lista
        del panel izquierdo. Limpia el visor y borra los datos en
        memoria de esa imagen para que, si se vuelve a abrir, empiece
        limpia y el usuario deba cargar el proyecto manualmente.
        """

        self.session.remove_image(filename)

        if str(self.current_image) != str(filename):
            return

        if getattr(self.image_view, "segmentation_mode", False):
            self.image_view.stop_segmentation()
            self.info_panel.segment_button.setText("▶ Segmentación Automática")

        if self.image_view.interaction_mode == "manual":
            self.image_view.stop_manual_segmentation()
            self.info_panel.manual_segment_button.setText("✏️ Segmentación manual")

        self.image_view.clear()
        self.current_image = None
        self.info_panel.clear()

    # ======================================================
    # CALIBRACIÓN
    # ======================================================

    def open_calibration(self):

        self.calibration_dialog.show()

        self.calibration_dialog.raise_()

        self.calibration_dialog.activateWindow()

    # ======================================================

    def save_calibration(self, pixels, distance, unit):

        if self.current_image is None:
            return

        image_session = self.session.get_image(self.current_image)

        image_session.set_calibration(pixels, distance, unit)
        self.session.modified = True

        info = get_image_info(self.current_image)

        info["scale"] = f'{image_session.calibration["pixel_size"]:.6f} ' f"{unit}/px"

        info["status"] = "Calibrada"

        self.info_panel.update_info(info)

    # ======================================================
    # SEGMENTACIÓN
    # ======================================================

    def toggle_segmentation(self):
        if self.current_image is None:
            QMessageBox.warning(self, "Segmentación", "Primero debe abrir una imagen.")
            return

        if not getattr(self.image_view, "segmentation_mode", False):
            # Detener modo manual si estaba activo
            if self.image_view.interaction_mode == "manual":
                self.image_view.stop_manual_segmentation()
                self.info_panel.manual_segment_button.setText("✏️ Segmentación manual")

            # Mostrar diálogo de procesamiento en hilo separado
            self._run_segmentation_start()
        else:
            self.image_view.stop_segmentation()
            self.info_panel.segment_button.setText("▶ Segmentación Automática")

    # ======================================================

    def _run_segmentation_start(self):
        """Muestra el diálogo 'Procesando...' mientras SAM inicializa."""

        dlg = QDialog(self)
        dlg.setWindowTitle("Segmentación")
        dlg.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        dlg.setFixedSize(340, 90)

        lbl = QLabel(
            "  Procesando imagen para su segmentación...\n  Por favor, espere.", dlg
        )
        lbl.setAlignment(Qt.AlignCenter)

        bar = QProgressBar(dlg)
        bar.setRange(0, 0)  # modo indeterminado (animado)
        bar.setTextVisible(False)

        lay = QVBoxLayout(dlg)
        lay.addWidget(lbl)
        lay.addWidget(bar)
        dlg.setLayout(lay)

        # Ejecutar la inicialización de SAM de forma bloqueante
        # pero mostrando el diálogo antes (procesEvents)
        dlg.show()
        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

        try:
            self.image_view.start_segmentation()
        except Exception as e:
            dlg.close()
            QMessageBox.critical(
                self, "Error", f"Error al inicializar la segmentación:\n{e}"
            )
            return

        dlg.close()
        self.info_panel.segment_button.setText("⏹ Detener Segmentación Automática")

    # ======================================================

    def toggle_manual_segmentation(self):
        if self.current_image is None:
            QMessageBox.warning(self, "Segmentación", "Primero debe abrir una imagen.")
            return

        if self.image_view.interaction_mode != "manual":
            # Detener SAM si estaba activo
            if self.image_view.segmentation_mode:
                self.image_view.stop_segmentation()
                self.info_panel.segment_button.setText("▶ Segmentación Automática")

            self.image_view.start_manual_segmentation()
            self.info_panel.manual_segment_button.setText("⏹ Detener Seg. Manual")
        else:
            self.image_view.stop_manual_segmentation()
            self.info_panel.manual_segment_button.setText("✏️ Segmentación manual")

    # ======================================================

    def on_mask_accepted(self, label_id):
        """Callback cuando el usuario acepta una máscara (Enter)."""
        self.session.modified = True

        if self.current_image is not None:
            image_session = self.session.get_image(self.current_image)
            if image_session is not None:
                image_session.set_masks(self.image_view.get_masks_data())

        self.info_panel.update_status(f"Segmentaciones: {label_id}")
        self.refresh_masks_panel()

    # ======================================================

    def on_mask_removed(self, label_id):
        """Callback cuando se borra una máscara (botón ✕ o Ctrl+Z)."""
        self.session.modified = True

        if self.current_image is not None:
            image_session = self.session.get_image(self.current_image)
            if image_session is not None:
                image_session.set_masks(self.image_view.get_masks_data())

        self.info_panel.update_status(f"Segmentación {label_id} borrada")
        self.refresh_masks_panel()

    # ======================================================

    def on_delete_mask_requested(self, label_id):
        """El usuario tocó el botón ✕ de una fila en el panel de Segmentaciones."""
        self.image_view.remove_mask(label_id)

    # ======================================================

    def undo_last_segmentation(self):
        """Ctrl+Z: deshace la última segmentación aceptada en la imagen actual."""

        if self.current_image is None:
            return

        self.image_view.undo_last_mask()

    # ======================================================

    def refresh_masks_panel(self):
        """Repuebla la lista de segmentaciones del panel derecho con las
        máscaras actualmente aceptadas en la imagen mostrada."""

        labels = self.image_view.get_mask_labels()
        self.info_panel.set_masks_list(labels)

    # ======================================================
    # GUARDAR
    # ======================================================

    def save_project(self):

        if not self.session.has_unsaved_changes():
            QMessageBox.information(self, "Guardar", "No hay cambios para guardar.")
            return

        saved_count = 0
        errors = []

        for filename, image_session in self.session.images.items():
            image_saved = False

            if image_session.calibrated:
                try:
                    storage.save_calibration(image_session)
                    image_saved = True
                except Exception as e:
                    errors.append(f"{image_session.name} (calibración): {e}")

            if image_session.has_masks:
                try:
                    storage.save_masks(image_session)
                    image_saved = True
                except Exception as e:
                    errors.append(f"{image_session.name} (máscaras): {e}")

                try:
                    storage.save_rois(image_session)
                except Exception as e:
                    errors.append(f"{image_session.name} (ROIs Fiji): {e}")

            if image_saved:
                saved_count += 1

        self.session.modified = False

        if saved_count > 0:
            QMessageBox.information(
                self, "Guardar", f"Se guardaron datos de {saved_count} imágenes."
            )

        if errors:
            QMessageBox.warning(
                self,
                "Guardar (con errores)",
                "Algunos datos no se pudieron guardar:\n\n" + "\n".join(errors),
            )

    # ======================================================
    # EXPORTAR
    # ======================================================

    # ======================================================
    # CARGAR DATOS EXTERNOS
    # ======================================================

    def load_project_data(self):

        if self.current_image is None:
            QMessageBox.warning(
                self, "Cargar proyecto", "Primero debe abrir una imagen."
            )
            return

        folder = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de datos del proyecto"
        )

        if not folder:
            return

        from pathlib import Path

        folder_path = Path(folder)

        calibration_file = folder_path / "calibration.json"
        masks_file = folder_path / "masks.tif"

        image_session = self.session.get_image(self.current_image)

        loaded_something = False

        if calibration_file.exists():
            import json

            try:
                with open(calibration_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                image_session.set_calibration(
                    data["pixels"], data["distance"], data["unit"]
                )
                self.session.modified = True

                info = get_image_info(self.current_image)
                info["scale"] = (
                    f'{image_session.calibration["pixel_size"]:.6f} {data["unit"]}/px'
                )
                info["status"] = "Calibrada (Importada)"
                self.info_panel.update_info(info)

                loaded_something = True

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar calibración: {e}")

        if masks_file.exists():
            try:
                import tifffile

                masks_array = tifffile.imread(masks_file)

                image_session.set_masks(masks_array)
                self.image_view.load_accepted_masks(masks_array)
                self.session.modified = True

                loaded_something = True

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cargar máscaras: {e}")

        if loaded_something:
            QMessageBox.information(
                self, "Cargar proyecto", "Datos cargados correctamente."
            )
        else:
            QMessageBox.information(
                self,
                "Cargar proyecto",
                "No se encontraron datos de calibración ni máscaras en la carpeta seleccionada.",
            )

    # ======================================================
    # EXPORTAR IMAGEN
    # ======================================================

    def export_project(self):
        if self.current_image is None:
            QMessageBox.warning(self, "Exportar", "Primero debe abrir una imagen.")
            return

        dialog = ExportDialog(self)
        if dialog.exec() == QDialog.Accepted:
            settings = dialog.get_settings()

            import os

            name_base = os.path.splitext(os.path.basename(self.current_image))[0]
            default_path = os.path.join(
                os.path.dirname(self.current_image), f"{name_base}_exportado.tif"
            )

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar imagen",
                default_path,
                "Imágenes TIFF (*.tif *.tiff);;Imágenes PNG (*.png);;Imágenes JPEG (*.jpg *.jpeg)",
            )

            if not filename:
                return

            dlg = QDialog(self)
            dlg.setWindowTitle("Exportando")
            dlg.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
            dlg.setFixedSize(300, 80)
            lbl = QLabel("  Generando imagen exportada...", dlg)
            lbl.setAlignment(Qt.AlignCenter)
            bar = QProgressBar(dlg)
            bar.setRange(0, 0)
            bar.setTextVisible(False)
            lay = QVBoxLayout(dlg)
            lay.addWidget(lbl)
            lay.addWidget(bar)
            dlg.show()
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()

            try:
                import imageio.v3 as iio
                import numpy as np

                img = iio.imread(self.current_image)

                if settings["embed_rois"]:
                    image_session = self.session.get_image(self.current_image)
                    masks = image_session.masks

                    if masks is not None and np.any(masks > 0):
                        if img.ndim == 2:
                            img_rgb = np.stack((img,) * 3, axis=-1)
                        elif img.shape[2] == 4:
                            img_rgb = img[..., :3]
                        else:
                            img_rgb = img.copy()

                        if img_rgb.dtype != np.uint8:
                            # Normalize float images to 0-255 if needed
                            if img_rgb.max() > 1.0 and img_rgb.dtype.kind in "fu":
                                img_rgb = (
                                    (img_rgb - img_rgb.min())
                                    / (img_rgb.max() - img_rgb.min())
                                    * 255
                                )
                            elif img_rgb.dtype.kind == "f":
                                img_rgb = img_rgb * 255
                            else:
                                img_rgb = (
                                    (img_rgb - img_rgb.min())
                                    / (img_rgb.max() - img_rgb.min())
                                    * 255
                                )
                            img_rgb = img_rgb.astype(np.uint8)

                        if settings["style"] == "contour":
                            from skimage.segmentation import mark_boundaries

                            result = mark_boundaries(
                                img_rgb, masks, color=(0, 1, 0), mode="outer"
                            )
                            img_out = (result * 255).astype(np.uint8)
                        else:
                            img_out = img_rgb.copy().astype(float)
                            mask_bool = masks > 0
                            alpha = 0.3
                            img_out[mask_bool, 0] = img_out[mask_bool, 0] * (1 - alpha)
                            img_out[mask_bool, 1] = (
                                img_out[mask_bool, 1] * (1 - alpha) + 255 * alpha
                            )
                            img_out[mask_bool, 2] = img_out[mask_bool, 2] * (1 - alpha)
                            img_out = img_out.astype(np.uint8)
                    else:
                        img_out = img
                else:
                    img_out = img

                iio.imwrite(filename, img_out)
                dlg.close()
                QMessageBox.information(
                    self, "Exportar", f"Imagen exportada exitosamente a:\n{filename}"
                )

            except Exception as e:
                dlg.close()
                QMessageBox.critical(
                    self, "Error", f"Error al exportar la imagen:\n{str(e)}"
                )

    # ======================================================
    # EVENTOS
    # ======================================================

    def closeEvent(self, event):

        if self.session.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Guardar cambios",
                "Hay cambios sin guardar. ¿Desea guardarlos antes de salir?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )

            if reply == QMessageBox.Save:
                self.save_project()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
