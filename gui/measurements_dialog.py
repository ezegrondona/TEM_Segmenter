# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: measurements_dialog.py
#
# Ventana para mostrar y exportar los resultados de mediciones.
# ==========================================================

import csv

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QFileDialog, QHBoxLayout, QHeaderView,
                               QMessageBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout)


class MeasurementsDialog(QDialog):
    def __init__(self, measurements_data, image_name, parent=None):
        super().__init__(parent)
        self.measurements_data = measurements_data
        self.image_name = image_name

        self.setWindowTitle(f"Mediciones - {image_name}")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(900, 400)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Tabla
        self.table = QTableWidget()
        layout.addWidget(self.table)

        if not self.measurements_data:
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setItem(
                0, 0, QTableWidgetItem("No hay segmentaciones para medir.")
            )
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        else:
            # Obtener encabezados desde las claves del primer diccionario
            headers = list(self.measurements_data[0].keys())
            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(len(self.measurements_data))

            for row, data_row in enumerate(self.measurements_data):
                for col, header in enumerate(headers):
                    val = data_row[header]
                    item = QTableWidgetItem(str(val))
                    # Alinear a la derecha los números
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    # Hacer que no sea editable
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.table.setItem(row, col, item)

            self.table.resizeColumnsToContents()

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("Exportar a CSV...")
        self.btn_close = QPushButton("Cerrar")

        if not self.measurements_data:
            self.btn_export.setEnabled(False)

        self.btn_export.clicked.connect(self.export_csv)
        self.btn_close.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def export_csv(self):
        if not self.measurements_data:
            return

        import os

        name_base = os.path.splitext(self.image_name)[0]
        default_path = f"{name_base}_mediciones.csv"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Exportar Mediciones a CSV", default_path, "Archivos CSV (*.csv)"
        )

        if not filename:
            return

        try:
            headers = list(self.measurements_data[0].keys())
            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for row in self.measurements_data:
                    writer.writerow(row)

            QMessageBox.information(
                self,
                "Exportación exitosa",
                f"Las mediciones se han exportado a:\n{filename}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar a CSV:\n{str(e)}")
