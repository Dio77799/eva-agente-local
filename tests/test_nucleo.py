"""Pruebas del núcleo de Eva (sin red, sin Ollama, sin tocar datos reales)."""
import unittest
from pathlib import Path

from tests import base
from eva import contenido, escritorio, kali, llm, proyectos, tareas
from eva.comun import DATOS


class Aislamiento(unittest.TestCase):
    def test_usa_carpeta_temporal(self):
        self.assertEqual(Path(DATOS), base.TEMP / "data")


class Tareas(unittest.TestCase):
    def test_agregar_sin_duplicar_y_completar(self):
        t = tareas.agregar("Probar Eva", "github", 1)
        self.assertEqual(tareas.agregar("probar eva")["id"], t["id"])
        tareas.completar(t["id"])
        self.assertNotIn(t["id"], [x["id"] for x in tareas.listar()])

    def test_area_desconocida_cae_en_general(self):
        self.assertEqual(tareas.agregar("x", "../../etc")["area"], "general")


class Escritorio(unittest.TestCase):
    def test_clasifica_y_no_mueve_nada(self):
        e = base.ESCRITORIO
        for nombre in ("~$tarea.docx", "Instalador.exe", "backup-2026-01-01.txt", "juegoprueba.lnk"):
            (e / nombre).write_text("x")
        (e / "proyecto").mkdir()
        (e / "proyecto.zip").write_text("x")
        antes = sorted(p.name for p in e.iterdir())
        tipos = {h["item"]: h["tipo"] for h in escritorio.analizar()}
        self.assertEqual(tipos["~$tarea.docx"], "temporal")
        self.assertEqual(tipos["Instalador.exe"], "instalador")
        self.assertEqual(tipos["backup-2026-01-01.txt"], "respaldo")
        self.assertEqual(tipos["juegoprueba.lnk"], "juego")
        self.assertEqual(tipos["proyecto.zip"], "duplicado")
        self.assertEqual(sorted(p.name for p in e.iterdir()), antes)


class Privacidad(unittest.TestCase):
    def test_detecta_secretos_sin_revelarlos(self):
        p = base.TEMP / "proy"
        p.mkdir()
        (p / ".env").write_text("CLAVE=1")
        secreto = "sk-" + "a" * 30
        (p / "app.py").write_text(f'api_key = "{secreto}"')
        hallazgos = proyectos.escanear_sensibles(p)
        self.assertEqual({h[0] for h in hallazgos}, {".env", "app.py"})
        self.assertNotIn(secreto, str(hallazgos))

    def test_lista_de_privados(self):
        self.assertTrue(proyectos.es_privado("App-ClientePrivado-v2"))
        self.assertFalse(proyectos.es_privado("portafolio"))


class Contenido(unittest.TestCase):
    def test_sanitizar(self):
        texto = ("flag 3f2a9b8c7d6e5f4a3b2c1d0e9f8a7b6c ip 10.10.11.5 correo a@b.com "
                 "password=Sup3r! en C:\\Users\\juan\\x y /home/kali/x")
        limpio = contenido.sanitizar(texto)
        for fuga in ("3f2a9b8c", "10.10.11.5", "a@b.com", "Sup3r!", "juan", "/home/kali"):
            self.assertNotIn(fuga, limpio)

    def test_no_publica_maquina_activa(self):
        notas = kali.nueva_maquina("Activa")
        with self.assertRaises(ValueError):
            contenido.borrador_htb(notas)

    def test_nombre_de_maquina_no_sale_de_data(self):
        notas = kali.nueva_maquina("../../fuera")
        self.assertTrue(notas.resolve().is_relative_to(Path(DATOS).resolve()))


class HerramientasChat(unittest.TestCase):
    """Regresión: el chat confundía escritorio/GitHub con áreas de tareas."""

    def test_tiene_herramientas_por_tema(self):
        funciones, esquemas = llm._herramientas()
        for nombre in ("analizar_escritorio", "auditar_github", "proyectos_publicables", "maquinas_htb"):
            self.assertIn(nombre, funciones)
        self.assertEqual(len(esquemas), len(funciones))

    def test_ninguna_herramienta_destructiva(self):
        funciones, _ = llm._herramientas()
        for prohibida in ("encender", "apagar", "borrar", "mover", "publicar", "snapshot"):
            self.assertFalse(any(prohibida in n for n in funciones), prohibida)

    def test_analizar_escritorio_desde_chat(self):
        funciones, _ = llm._herramientas()
        self.assertIn("instalador", funciones["analizar_escritorio"]())


if __name__ == "__main__":
    unittest.main()
