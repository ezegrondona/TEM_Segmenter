# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: info_panel.py
#
# Panel derecho de información del proyecto.
# ==========================================================

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QGroupBox, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QSizePolicy,
                               QVBoxLayout, QWidget)


class InfoPanel(QWidget):

    # Señal emitida cuando el usuario pide borrar una segmentación
    # puntual desde la lista (botón ✕ de esa fila)
    delete_mask_requested = Signal(int)

    def __init__(self):

        super().__init__()

        self.setup_ui()

    # ======================================================
    # INTERFAZ
    # ======================================================

    def setup_ui(self):

        layout = QVBoxLayout()

        info_box = QGroupBox("Información")

        info_layout = QVBoxLayout()

        self.image_label = QLabel("Imagen:\n---")

        self.size_label = QLabel("Resolución:\n---")

        self.scale_label = QLabel("Escala:\nSin calibrar")

        self.status_label = QLabel("Estado:\nEsperando imagen")

        self.calibrate_button = QPushButton("📏 Calibrar")

        self.segment_button = QPushButton("▶ Segmentación Automática")

        self.manual_segment_button = QPushButton("✏️ Segmentación manual")

        self.load_project_button = QPushButton("📂 Cargar proyecto...")

        info_layout.addWidget(self.image_label)
        info_layout.addWidget(self.size_label)
        info_layout.addWidget(self.scale_label)
        info_layout.addWidget(self.status_label)

        info_layout.addSpacing(15)

        info_layout.addWidget(self.load_project_button)
        info_layout.addWidget(self.calibrate_button)
        info_layout.addWidget(self.segment_button)
        info_layout.addWidget(self.manual_segment_button)

        info_layout.addStretch()

        info_box.setLayout(info_layout)

        layout.addWidget(info_box)

        # --------------------------------------------------
        # Lista de segmentaciones aceptadas, con borrado
        # individual y deshacer (Ctrl+Z se conecta desde
        # MainWindow, pero usa el mismo mecanismo de borrado).
        # --------------------------------------------------

        masks_box = QGroupBox("Segmentaciones")

        masks_layout = QVBoxLayout()

        self.masks_hint_label = QLabel(
            "Clic en ✕ para borrar una segmentación.\n"
            "Ctrl+Z deshace la última aceptada."
        )
        self.masks_hint_label.setWordWrap(True)

        self.masks_list = QListWidget()
        self.measure_button = QPushButton("📊 Medir Segmentaciones")

        masks_layout.addWidget(self.masks_hint_label)
        masks_layout.addWidget(self.masks_list)
        masks_layout.addWidget(self.measure_button)

        masks_box.setLayout(masks_layout)

        layout.addWidget(masks_box)

        layout.addStretch()

        self.setLayout(layout)

    # ======================================================
    # ACTUALIZAR TODA LA INFORMACIÓN
    # ======================================================

    def update_info(self, info):

        self.image_label.setText(f"Imagen:\n{info['name']}")

        self.size_label.setText(f"Resolución:\n{info['width']} × {info['height']}")

        self.scale_label.setText(f"Escala:\n{info['scale']}")

        self.status_label.setText(f"Estado:\n{info['status']}")

    # ======================================================
    # ACTUALIZAR ESCALA
    # ======================================================

    def update_scale(self, text):

        self.scale_label.setText(f"Escala:\n{text}")

    # ======================================================
    # ACTUALIZAR ESTADO
    # ======================================================

    def update_status(self, text):

        self.status_label.setText(f"Estado:\n{text}")

    # ======================================================
    # LISTA DE SEGMENTACIONES (borrado individual)
    # ======================================================

    def set_masks_list(self, label_ids):
        """
        Repuebla la lista de segmentaciones aceptadas con los
        números de máscara recibidos (uno por fila, con botón
        de borrado individual).
        """

        self.masks_list.clear()

        for label_id in label_ids:

            item = QListWidgetItem()
            item.setData(Qt.UserRole, label_id)

            self.masks_list.addItem(item)

            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(4, 2, 4, 2)

            name_label = QLabel(f"Máscara {label_id}")
            name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

            delete_button = QPushButton("✕")
            delete_button.setFixedSize(20, 20)
            delete_button.setToolTip("Borrar esta segmentación")
            delete_button.clicked.connect(
                lambda _checked=False, lid=label_id: self.delete_mask_requested.emit(
                    lid
                )
            )

            row_layout.addWidget(name_label)
            row_layout.addWidget(delete_button)
            row_widget.setLayout(row_layout)

            item.setSizeHint(row_widget.sizeHint())
            self.masks_list.setItemWidget(item, row_widget)

    # ======================================================
    # LIMPIAR (cuando se cierra la imagen activa)
    # ======================================================

    def clear(self):

        self.image_label.setText("Imagen:\n---")
        self.size_label.setText("Resolución:\n---")
        self.scale_label.setText("Escala:\nSin calibrar")
        self.status_label.setText("Estado:\nEsperando imagen")

        self.masks_list.clear()
