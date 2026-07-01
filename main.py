# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: main.py
#
# Descripción:
# Punto de entrada principal de la aplicación.
#
# Autor:
# Dr. Ezequiel + Aether
# ==========================================================

# ==========================================================
# IMPORTACIONES
# ==========================================================

import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow

# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================


def main():
    """
    Inicia la aplicación.
    """

    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())


# ==========================================================
# INICIO DEL PROGRAMA
# ==========================================================

if __name__ == "__main__":
    main()
