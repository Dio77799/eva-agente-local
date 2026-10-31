"""El panel web es solo lectura y escapa el contenido dinámico."""
import unittest

from tests import base
from eva import servidor, tareas


class Pagina(unittest.TestCase):
    def test_pagina_se_genera_y_tiene_secciones(self):
        tareas.agregar("Probar el panel", "general", 1)
        html = servidor.pagina()
        self.assertIn("<title>Eva", html)
        for seccion in ("Pendientes", "Escritorio", "GitHub"):
            self.assertIn(seccion, html)
        self.assertIn("Probar el panel", html)

    def test_escapa_html_de_una_tarea(self):
        # Un título con HTML no debe inyectarse en la página.
        tareas.agregar("<script>alert(1)</script>", "general", 2)
        html = servidor.pagina()
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_solo_escucha_en_localhost(self):
        import inspect
        fuente = inspect.getsource(servidor.iniciar)
        self.assertIn("127.0.0.1", fuente)
        self.assertNotIn("0.0.0.0", fuente)


if __name__ == "__main__":
    unittest.main()
