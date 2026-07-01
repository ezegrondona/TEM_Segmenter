# ==========================================================
# TEM SEGMENTER
# ----------------------------------------------------------
# Archivo: session.py
#
# Sesión temporal del programa.
# ==========================================================

from pathlib import Path

from core.image_session import ImageSession


class Session:

    def __init__(self):

        self.images = {}

        self.modified = False

    # ======================================================

    def add_image(self, filename):

        filename = self._key(filename)

        if filename not in self.images:

            self.images[filename] = ImageSession(filename)

        return self.images[filename]

    # ======================================================

    def get_image(self, filename):

        return self.images.get(self._key(filename))

    # ======================================================

    def clear(self):

        self.images.clear()

        self.modified = False

    # ======================================================

    def remove_image(self, filename):

        filename = self._key(filename)

        if filename in self.images:
            del self.images[filename]

    # ======================================================

    def has_unsaved_changes(self):

        return self.modified

    # ======================================================
    # CLAVE NORMALIZADA
    # ======================================================

    def _key(self, filename):
        """
        Convierte siempre el nombre de archivo a la representación
        canónica de Path antes de usarlo como clave del diccionario.

        Esto es necesario porque la MISMA imagen puede llegar acá
        representada de formas distintas según su origen: QFileDialog
        en Windows devuelve rutas con '/', mientras que el panel de
        imágenes las guarda como objetos Path (que se convierten a
        string con '\\'). Sin esta normalización, una misma imagen
        terminaba creando DOS entradas distintas en self.images, y
        al volver a ella el programa buscaba en la entrada vacía,
        dando la sensación de que la calibración y las máscaras
        habían desaparecido.
        """

        return str(Path(filename))