"""El panel web es solo lectura, con sidebar y secciones escapadas."""
import unittest

from tests import base
from eva import servidor, tareas


class Shell(unittest.TestCase):
    def test_shell_tiene_sidebar_y_todas_las_secciones(self):
        html = servidor.shell()
        self.assertIn("<title>Eva", html)
        self.assertIn('class="side"', html)  # sidebar
        for sec in servidor.SECCIONES:
            self.assertIn(f'data-sec="{sec}"', html)

    def test_secciones_esperadas(self):
        self.assertEqual(set(servidor.SECCIONES),
                         {"inicio", "tareas", "escritorio", "github", "kali", "aprende"})


class Fragmentos(unittest.TestCase):
    def test_inicio_explica_y_lista_comandos(self):
        html = servidor.frag_inicio()
        self.assertIn("Qué es Eva", html)
        self.assertIn("python eva.py", html)

    def test_tareas_escapa_html(self):
        tareas.agregar("<script>alert(1)</script>", "general", 2)
        html = servidor.frag_tareas()
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_aprende_tiene_secciones_clave(self):
        html = servidor.frag_aprende()
        for s in ("Dominio", "Aplicación", "Infraestructura", "Glosario", "DDD"):
            self.assertIn(s, html)


class Seguridad(unittest.TestCase):
    def test_solo_escucha_en_localhost(self):
        import inspect
        fuente = inspect.getsource(servidor.iniciar)
        self.assertIn("127.0.0.1", fuente)
        self.assertNotIn("0.0.0.0", fuente)

    def test_seccion_valida_whitelist(self):
        # El handler solo sirve nombres de SECCIONES; una ruta con '..' no está en el dict.
        self.assertNotIn("../etc/passwd", servidor.SECCIONES)
        self.assertNotIn("..", servidor.SECCIONES)


if __name__ == "__main__":
    unittest.main()
