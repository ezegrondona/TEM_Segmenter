# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: main_window.py
# ==========================================================

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, QThread, Signal as QtSignal
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QSplitter,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
    QDialog,
    QLabel,
    QProgressBar
)

from settings import PROGRAM_NAME, VERSION

from gui.project_panel import ProjectPanel
from gui.info_panel import InfoPanel
from gui.image_view import ImageView
from gui.calibration_dialog import CalibrationDialog

from core.image_loader import find_images
from core.image_info import get_image_info
from core.session import Session
from core import storage


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

        self.project_panel.image_selected.connect(
            self.load_image
        )

        self.info_panel.calibrate_button.clicked.connect(
            self.open_calibration
        )
        
        self.info_panel.segment_button.clicked.connect(
            self.toggle_segmentation
        )

        self.info_panel.manual_segment_button.clicked.connect(
            self.toggle_manual_segmentation
        )
        
        self.image_view.mask_accepted.connect(
            self.on_mask_accepted
        )
        
        self.info_panel.load_project_button.clicked.connect(
            self.load_project_data
        )

        self.calibration_dialog.start_measurement.connect(
            self.image_view.start_measurement
        )

        self.image_view.measurement_finished.connect(
            self.calibration_dialog.set_pixels
        )

        self.calibration_dialog.finished.connect(
            self.image_view.stop_measurement
        )

        self.calibration_dialog.calibration_saved.connect(
            self.save_calibration
        )

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

        open_image_action = QAction(
            "Abrir imagen...",
            self
        )
        open_image_action.setShortcut(QKeySequence("Ctrl+O"))

        open_image_action.triggered.connect(
            self.open_image
        )

        file_menu.addAction(open_image_action)

        # ----------------------------------------------
        # Abrir carpeta
        # ----------------------------------------------

        open_folder_action = QAction(
            "Abrir carpeta...",
            self
        )
        open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))

        open_folder_action.triggered.connect(
            self.open_folder
        )

        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        # ----------------------------------------------
        # Guardar
        # ----------------------------------------------

        save_action = QAction(
            "Guardar",
            self
        )
        save_action.setShortcut(QKeySequence("Ctrl+S"))

        save_action.triggered.connect(
            self.save_project
        )

        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # ----------------------------------------------
        # Exportar
        # ----------------------------------------------

        export_action = QAction(
            "Exportar...",
            self
        )

        export_action.triggered.connect(
            self.export_project
        )

        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # ----------------------------------------------
        # Salir
        # ----------------------------------------------

        exit_action = QAction(
            "Salir",
            self
        )

        exit_action.triggered.connect(
            self.close
        )

        file_menu.addAction(exit_action)

    # ======================================================
    # ABRIR IMAGEN
    # ======================================================

    def open_image(self):

        filename, _ = QFileDialog.getOpenFileName(

            self,

            "Abrir imagen",

            "",

            "Imágenes (*.tif *.tiff *.png *.jpg *.jpeg *.bmp)"

        )

        if not filename:
            return

        self.project_panel.set_single_image(filename)
        self.load_image(filename)

    # ======================================================
    # ABRIR CARPETA
    # ======================================================

    def open_folder(self):

        folder = QFileDialog.getExistingDirectory(

            self,

            "Seleccionar carpeta"

        )

        if not folder:
            return

        self.project_panel.set_folder(folder)

        self.images = find_images(folder)

        self.project_panel.set_image_list(self.images)

        if self.images:

            self.load_image(self.images[0])

    # ======================================================
    # CARGAR IMAGEN
    # ======================================================

    def load_image(self, filename):

        self.current_image = filename

        if getattr(self.image_view, "segmentation_mode", False):
            self.image_view.stop_segmentation()
            self.info_panel.segment_button.setText("▶ Segmentación Automática")

        self.image_view.load_image(filename)

        image_session = self.session.add_image(filename)

        if not image_session.calibrated:
            data = storage.load_calibration(filename)
            if data:
                image_session.set_calibration(
                    data["pixels"],
                    data["distance"],
                    data["unit"]
                )

        # --------------------------------------------------
        # Restaurar máscaras (desde la sesión en memoria, o
        # si no había nada en memoria, desde disco)
        # --------------------------------------------------

        if image_session.masks is None:
            loaded_masks = storage.load_masks(filename)
            if loaded_masks is not None:
                image_session.set_masks(loaded_masks)

        if image_session.masks is not None:
            self.image_view.load_accepted_masks(image_session.masks)

        info = get_image_info(filename)

        if image_session.calibrated:

            info["scale"] = (

                f'{image_session.calibration["pixel_size"]:.6f} '

                f'{image_session.calibration["unit"]}/px'

            )

            info["status"] = "Calibrada"

        self.info_panel.update_info(info)

    # ======================================================
    # CALIBRACIÓN
    # ======================================================

    def open_calibration(self):

        self.calibration_dialog.show()

        self.calibration_dialog.raise_()

        self.calibration_dialog.activateWindow()

    # ======================================================

    def save_calibration(

        self,

        pixels,

        distance,

        unit

    ):

        if self.current_image is None:
            return

        image_session = self.session.get_image(

            self.current_image

        )

        image_session.set_calibration(

            pixels,

            distance,

            unit

        )
        self.session.modified = True

        info = get_image_info(self.current_image)

        info["scale"] = (

            f'{image_session.calibration["pixel_size"]:.6f} '

            f'{unit}/px'

        )

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
        dlg.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )
        dlg.setFixedSize(340, 90)

        lbl = QLabel("  Procesando imagen para su segmentación...\n  Por favor, espere.", dlg)
        lbl.setAlignment(Qt.AlignCenter)

        bar = QProgressBar(dlg)
        bar.setRange(0, 0)          # modo indeterminado (animado)
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
            QMessageBox.critical(self, "Error", f"Error al inicializar la segmentación:\n{e}")
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

    # ======================================================
    # GUARDAR
    # ======================================================

    def save_project(self):

        if not self.session.has_unsaved_changes():
            QMessageBox.information(self, "Guardar", "No hay cambios para guardar.")
            return

        saved_count = 0
        for filename, image_session in self.session.images.items():
            image_saved = False

            if image_session.calibrated:
                storage.save_calibration(image_session)
                image_saved = True

            if image_session.has_masks:
                storage.save_masks(image_session)
                image_saved = True

            if image_saved:
                saved_count += 1

        self.session.modified = False

        if saved_count > 0:
            QMessageBox.information(self, "Guardar", f"Se guardaron datos de {saved_count} imágenes.")

    # ======================================================
    # EXPORTAR
    # ======================================================

    def export_project(self):

        print("Exportar proyecto")

    # ======================================================
    # CARGAR DATOS EXTERNOS
    # ======================================================

    def load_project_data(self):
        
        if self.current_image is None:
            QMessageBox.warning(self, "Cargar proyecto", "Primero debe abrir una imagen.")
            return
            
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de datos del proyecto"
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
                    data["pixels"],
                    data["distance"],
                    data["unit"]
                )
                self.session.modified = True
                
                info = get_image_info(self.current_image)
                info["scale"] = f'{image_session.calibration["pixel_size"]:.6f} {data["unit"]}/px'
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
            QMessageBox.information(self, "Cargar proyecto", "Datos cargados correctamente.")
        else:
            QMessageBox.information(self, "Cargar proyecto", "No se encontraron datos de calibración ni máscaras en la carpeta seleccionada.")

    # ======================================================
    # EVENTOS
    # ======================================================

    def closeEvent(self, event):
        
        if self.session.has_unsaved_changes():
            reply = QMessageBox.question(
                self, 'Guardar cambios',
                "Hay cambios sin guardar. ¿Desea guardarlos antes de salir?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
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