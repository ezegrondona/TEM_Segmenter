# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: export_dialog.py
#
# Diálogo de opciones para la exportación de imagen.
# ==========================================================

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QDialog, QGroupBox,
                               QHBoxLayout, QPushButton, QRadioButton,
                               QVBoxLayout)


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones de Exportación")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(300, 200)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Checkbox principal
        self.embed_rois_checkbox = QCheckBox("Incrustar ROIs en la imagen")
        self.embed_rois_checkbox.setChecked(True)
        self.embed_rois_checkbox.toggled.connect(self._toggle_options)
        layout.addWidget(self.embed_rois_checkbox)

        # Grupo de opciones de estilo
        self.style_group = QGroupBox("Estilo de ROIs")
        style_layout = QVBoxLayout(self.style_group)

        self.radio_contour = QRadioButton("Solo contornos")
        self.radio_solid = QRadioButton("Relleno sólido (semitransparente)")
        self.radio_contour.setChecked(True)

        self.style_button_group = QButtonGroup(self)
        self.style_button_group.addButton(self.radio_contour, 0)
        self.style_button_group.addButton(self.radio_solid, 1)

        style_layout.addWidget(self.radio_contour)
        style_layout.addWidget(self.radio_solid)

        layout.addWidget(self.style_group)

        # Botones
        button_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_export = QPushButton("Exportar...")

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_export.clicked.connect(self.accept)

        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_export)

        layout.addStretch()
        layout.addLayout(button_layout)

    def _toggle_options(self, checked):
        self.style_group.setEnabled(checked)

    def get_settings(self):
        return {
            "embed_rois": self.embed_rois_checkbox.isChecked(),
            "style": "contour" if self.radio_contour.isChecked() else "solid",
        }
