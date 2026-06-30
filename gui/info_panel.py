# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: info_panel.py
#
# Panel derecho de información del proyecto.
# ==========================================================

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QGroupBox
)


class InfoPanel(QWidget):

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

        layout.addStretch()

        self.setLayout(layout)

    # ======================================================
    # ACTUALIZAR TODA LA INFORMACIÓN
    # ======================================================

    def update_info(self, info):

        self.image_label.setText(
            f"Imagen:\n{info['name']}"
        )

        self.size_label.setText(
            f"Resolución:\n{info['width']} × {info['height']}"
        )

        self.scale_label.setText(
            f"Escala:\n{info['scale']}"
        )

        self.status_label.setText(
            f"Estado:\n{info['status']}"
        )

    # ======================================================
    # ACTUALIZAR ESCALA
    # ======================================================

    def update_scale(self, text):

        self.scale_label.setText(
            f"Escala:\n{text}"
        )

    # ======================================================
    # ACTUALIZAR ESTADO
    # ======================================================

    def update_status(self, text):

        self.status_label.setText(
            f"Estado:\n{text}"
        )

    # ======================================================
    # LIMPIAR (cuando se cierra la imagen activa)
    # ======================================================

    def clear(self):

        self.image_label.setText("Imagen:\n---")
        self.size_label.setText("Resolución:\n---")
        self.scale_label.setText("Escala:\nSin calibrar")
        self.status_label.setText("Estado:\nEsperando imagen")