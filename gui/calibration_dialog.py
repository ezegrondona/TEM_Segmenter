# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: calibration_dialog.py
#
# Ventana de calibración
# ==========================================================

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLineEdit,
    QComboBox,
    QMessageBox
)

from PySide6.QtCore import Signal, Qt


class CalibrationDialog(QDialog):

    # ------------------------------------------------------
    # Señales
    # ------------------------------------------------------

    # Comenzar medición sobre la imagen
    start_measurement = Signal()

    # Guardar calibración
    calibration_saved = Signal(float, float, str)

    def __init__(self, parent=None):

        super().__init__(parent)

        self.pixels = None

        self.setup_ui()

    # ======================================================

    def setup_ui(self):

        self.setWindowTitle("Calibración")

        self.setMinimumWidth(380)

        layout = QVBoxLayout()

        # --------------------------------------------------
        # Medición
        # --------------------------------------------------

        measurement_box = QGroupBox("Medición")

        measurement_layout = QVBoxLayout()

        self.measure_button = QPushButton(
            "✏ Medir sobre la imagen"
        )

        self.pixel_label = QLabel("---")

        self.pixel_label.setAlignment(Qt.AlignCenter)

        self.pixel_label.setStyleSheet("""
            font-size:18px;
            font-weight:bold;
            color:#D32F2F;
        """)

        measurement_layout.addWidget(self.measure_button)
        measurement_layout.addWidget(self.pixel_label)

        measurement_box.setLayout(measurement_layout)

        # --------------------------------------------------
        # Distancia conocida
        # --------------------------------------------------

        distance_box = QGroupBox("Distancia conocida")

        distance_layout = QVBoxLayout()

        self.distance_edit = QLineEdit()

        self.distance_edit.setPlaceholderText(
            "Ej: 2"
        )

        distance_layout.addWidget(self.distance_edit)

        distance_box.setLayout(distance_layout)

        # --------------------------------------------------
        # Unidad
        # --------------------------------------------------

        unit_box = QGroupBox("Unidad")

        unit_layout = QVBoxLayout()

        self.unit_combo = QComboBox()

        self.unit_combo.addItems([
            "nm",
            "µm",
            "mm"
        ])

        unit_layout.addWidget(self.unit_combo)

        unit_box.setLayout(unit_layout)

        # --------------------------------------------------
        # Botones
        # --------------------------------------------------

        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Guardar")

        self.cancel_button = QPushButton("Cancelar")

        button_layout.addStretch()

        button_layout.addWidget(self.save_button)

        button_layout.addWidget(self.cancel_button)

        # --------------------------------------------------

        layout.addWidget(measurement_box)
        layout.addWidget(distance_box)
        layout.addWidget(unit_box)

        layout.addStretch()

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # --------------------------------------------------
        # Conexiones
        # --------------------------------------------------

        self.measure_button.clicked.connect(
            self.start_measurement.emit
        )

        self.cancel_button.clicked.connect(
            self.reject
        )

        self.save_button.clicked.connect(
            self.save_calibration
        )

    # ======================================================

    def set_pixels(self, pixels):

        self.pixels = pixels

        self.pixel_label.setText(
            f"{pixels:.2f} px"
        )

    # ======================================================

    def save_calibration(self):

        if self.pixels is None:

            QMessageBox.warning(
                self,
                "Calibración",
                "Primero debe medir la barra de escala."
            )

            return

        text = self.distance_edit.text().strip()

        if not text:

            QMessageBox.warning(
                self,
                "Calibración",
                "Ingrese la distancia conocida."
            )

            return

        try:

            distance = float(
                text.replace(",", ".")
            )

        except ValueError:

            QMessageBox.warning(
                self,
                "Calibración",
                "La distancia debe ser un número."
            )

            return

        unit = self.unit_combo.currentText()

        self.calibration_saved.emit(

            self.pixels,

            distance,

            unit

        )

        self.accept()