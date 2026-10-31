"""Seguridad: los errores no filtran datos al modelo (NORMAS §3.9)."""
import unittest
from unittest import mock

from tests import base  # noqa: F401  (aísla datos en carpetas temporales)
from eva import llm, proyectos


class FugasEnErrores(unittest.TestCase):
    def test_repos_github_no_filtra_stderr(self):
        # Simula a `gh` fallando con un stderr que trae una ruta y una pista de token.
        falso = mock.Mock(returncode=1, stdout="",
                          stderr="auth error en /home/usuario/.config/gh con ghp_PISTAFALSA")
        with mock.patch("eva.proyectos.subprocess.run", return_value=falso), \
                mock.patch("sys.stderr"):  # el detalle va a consola; no nos interesa aquí
            with self.assertRaises(RuntimeError) as ctx:
                proyectos.repos_github()
        mensaje = str(ctx.exception)
        self.assertNotIn("ghp_PISTAFALSA", mensaje)
        self.assertNotIn("/home/usuario", mensaje)

    def test_ejecutar_no_filtra_excepcion(self):
        def explota():
            raise RuntimeError("detalle con ruta /home/usuario/secreto y token ghp_PISTA")
        salida = llm._ejecutar({"x": explota}, "x", {})
        self.assertNotIn("secreto", salida)
        self.assertNotIn("ghp_PISTA", salida)
        self.assertIn("no se pudo", salida.lower())

    def test_ejecutar_herramienta_inexistente(self):
        self.assertIn("no existe", llm._ejecutar({}, "fantasma", {}).lower())

    def test_ejecutar_args_malos_no_rompen(self):
        # Un argumento que la función no acepta se maneja como error seguro.
        salida = llm._ejecutar({"x": lambda: "ok"}, "x", {"sobra": 1})
        self.assertIn("no se pudo", salida.lower())


if __name__ == "__main__":
    unittest.main()
