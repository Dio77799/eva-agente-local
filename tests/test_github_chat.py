"""auditar_github del chat agrupa los repos en públicos y privados (sin red ni gh real)."""
import json
import subprocess
import unittest
from unittest import mock

from tests import base  # noqa: F401  (aísla a Eva en carpetas temporales)
from eva import llm

REPOS = [
    {"name": "usuario-prueba", "visibility": "PUBLIC", "description": "",
     "repositoryTopics": []},
    {"name": "proyecto-completo", "visibility": "PUBLIC", "description": "Algo",
     "repositoryTopics": [{"name": "python"}]},
    {"name": "secreto-interno", "visibility": "PRIVATE", "description": "x",
     "repositoryTopics": [{"name": "x"}]},
    {"name": "clienteprivado", "visibility": "PUBLIC", "description": "x",
     "repositoryTopics": [{"name": "x"}]},
]


def _gh_falso(*args, **kwargs):
    return subprocess.CompletedProcess(args, 0, stdout=json.dumps(REPOS), stderr="")


class AuditarGithubAgrupado(unittest.TestCase):
    def setUp(self):
        parche = mock.patch("eva.proyectos.subprocess.run", side_effect=_gh_falso)
        parche.start()
        self.addCleanup(parche.stop)
        self.auditar = llm._herramientas()[0]["auditar_github"]

    def test_agrupa_publicos_y_privados(self):
        salida = self.auditar()
        pub, priv = salida.index("PÚBLICOS (3):"), salida.index("PRIVADOS (1):")
        self.assertLess(pub, salida.index("usuario-prueba"))
        self.assertLess(salida.index("usuario-prueba"), priv)
        self.assertGreater(salida.index("secreto-interno"), priv)
        self.assertNotIn("PUBLIC ", salida)

    def test_filtra_por_visibilidad(self):
        privados = self.auditar(visibilidad="Privado")
        self.assertIn("secreto-interno", privados)
        self.assertNotIn("PÚBLICOS", privados)
        self.assertNotIn("usuario-prueba", privados)
        self.assertNotIn("secreto-interno", self.auditar(visibilidad="público"))
