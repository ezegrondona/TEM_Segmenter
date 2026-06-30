# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: project_panel.py
# ==========================================================

from pathlib import Path

from PySide6.QtCore import Signal, Qt

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QSizePolicy
)


class ProjectPanel(QWidget):

    # Señal emitida cuando cambia la imagen seleccionada
    image_selected = Signal(Path)

    # Señal emitida cuando el usuario cierra una imagen de la lista
    # (botón ✕ de esa fila)
    image_closed = Signal(Path)

    def __init__(self):

        super().__init__()

        self.images = []

        self.setup_ui()

    # ======================================================

    def setup_ui(self):

        layout = QVBoxLayout()

        project_box = QGroupBox("Proyecto")

        project_layout = QVBoxLayout()

        self.folder_label = QLabel("Imágenes abiertas")

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
    # CARPETA (solo etiqueta informativa)
    # ======================================================

    def set_folder(self, folder):

        folder = Path(folder)

        self.folder_label.setText(
            f"Carpeta abierta:\n{folder.name}"
        )

    # ======================================================
    # AGREGAR IMÁGENES (sin borrar las que ya estaban abiertas)
    # ======================================================

    def add_image(self, image_path):
        """
        Agrega UNA imagen a la lista. Si ya estaba abierta,
        simplemente la selecciona en vez de duplicarla.
        """

        image_path = Path(image_path)

        if image_path in self.images:
            self._select_image(image_path)
            return

        self.images.append(image_path)
        self._add_list_row(image_path)

        self.image_list.setCurrentRow(self.image_list.count() - 1)

    # ======================================================

    def add_images(self, image_paths):
        """
        Agrega VARIAS imágenes a la lista (abrir carpeta o
        multi-selección de archivos). Las que ya estuvieran
        abiertas se ignoran, no se duplican.
        """

        added_any = False

        for image_path in image_paths:

            image_path = Path(image_path)

            if image_path in self.images:
                continue

            self.images.append(image_path)
            self._add_list_row(image_path)
            added_any = True

        if added_any:
            self.image_list.setCurrentRow(self.image_list.count() - 1)

    # ======================================================
    # FILA DE LA LISTA (nombre + botón de cierre individual)
    # ======================================================

    def _add_list_row(self, image_path):

        item = QListWidgetItem()

        # Guardamos la ruta completa en el propio item, para no
        # depender de que el orden visual coincida con self.images.
        item.setData(Qt.UserRole, image_path)

        self.image_list.addItem(item)

        row_widget = QWidget()

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(4, 2, 4, 2)

        name_label = QLabel(image_path.name)
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        name_label.setToolTip(str(image_path))

        close_button = QPushButton("✕")
        close_button.setFixedSize(20, 20)
        close_button.setToolTip("Cerrar esta imagen")
        close_button.clicked.connect(
            lambda _checked=False, path=image_path: self._close_image(path)
        )

        row_layout.addWidget(name_label)
        row_layout.addWidget(close_button)

        row_widget.setLayout(row_layout)

        item.setSizeHint(row_widget.sizeHint())

        self.image_list.setItemWidget(item, row_widget)

    # ======================================================
    # CERRAR UNA IMAGEN (botón ✕)
    # ======================================================

    def _close_image(self, image_path):

        row = self._row_of(image_path)

        if row is None:
            return

        self.image_list.takeItem(row)
        self.images.remove(image_path)

        self.image_closed.emit(image_path)

        # Si queda alguna imagen abierta, seleccionar otra
        # para que el visor no quede sin nada cargado.
        if self.images:
            new_row = min(row, len(self.images) - 1)
            self.image_list.setCurrentRow(new_row)

    # ======================================================

    def _row_of(self, image_path):

        for row in range(self.image_list.count()):

            item = self.image_list.item(row)

            if item.data(Qt.UserRole) == image_path:
                return row

        return None

    # ======================================================

    def _select_image(self, image_path):

        row = self._row_of(image_path)

        if row is not None:
            self.image_list.setCurrentRow(row)

    # ======================================================
    # SELECCIÓN
    # ======================================================

    def on_selection_changed(self, row):

        if row < 0:
            return

        item = self.image_list.item(row)

        if item is None:
            return

        image_path = item.data(Qt.UserRole)

        if image_path is not None:
            self.image_selected.emit(image_path)
