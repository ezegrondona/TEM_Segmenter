# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: project_panel.py
# ==========================================================

from pathlib import Path

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QGroupBox
)


class ProjectPanel(QWidget):

    # Señal emitida cuando cambia la imagen seleccionada
    image_selected = Signal(Path)

    def __init__(self):

        super().__init__()

        self.images = []

        self.setup_ui()

    # ======================================================

    def setup_ui(self):

        layout = QVBoxLayout()

        project_box = QGroupBox("Proyecto")

        project_layout = QVBoxLayout()

        self.folder_label = QLabel("Carpeta: (sin seleccionar)")

        self.image_list = QListWidget()

        self.image_list.currentRowChanged.connect(
            self.on_selection_changed
        )

        project_layout.addWidget(self.folder_label)
        project_layout.addWidget(self.image_list)

        project_box.setLayout(project_layout)

        layout.addWidget(project_box)

        self.setLayout(layout)

    # ======================================================

    def set_folder(self, folder):

        folder = Path(folder)

        self.folder_label.setText(
            f"Carpeta:\n{folder.name}"
        )

    # ======================================================

    def set_single_image(self, image_path):

        image_path = Path(image_path)

        self.folder_label.setText(
            f"Imagen:\n{image_path.name}"
        )

        self.images = [image_path]

        self.image_list.clear()

        self.image_list.addItem(image_path.name)

        self.image_list.setCurrentRow(0)

    # ======================================================

    def set_image_list(self, images):

        self.images = images

        self.image_list.clear()

        if not images:

            self.image_list.addItem(
                "No se encontraron imágenes."
            )

            return

        for image in images:

            self.image_list.addItem(image.name)

        self.image_list.setCurrentRow(0)

    # ======================================================

    def on_selection_changed(self, row):

        if row < 0:

            return

        if row >= len(self.images):

            return

        self.image_selected.emit(self.images[row])