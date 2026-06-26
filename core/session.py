# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: session.py
#
# Sesión temporal del programa.
# ==========================================================

from core.image_session import ImageSession


class Session:

    def __init__(self):

        self.images = {}

        self.modified = False

    # ======================================================

    def add_image(self, filename):

        filename = str(filename)

        if filename not in self.images:

            self.images[filename] = ImageSession(filename)

        return self.images[filename]

    # ======================================================

    def get_image(self, filename):

        return self.images.get(str(filename))

    # ======================================================

    def clear(self):

        self.images.clear()

        self.modified = False

    # ======================================================

    def has_unsaved_changes(self):

        return self.modified