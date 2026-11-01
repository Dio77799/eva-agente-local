"""Pruebas de KELLY (ánimo): reglas locales, sin red, sin guardar texto."""
import json
import unittest

from tests import base
from eva import kelly
from eva.comun import DATOS


class Lectura(unittest.TestCase):
    def test_detecta_cada_animo(self):
        self.assertEqual(kelly.leer("esto no funciona otra vez"), "frustrado")
        self.assertEqual(kelly.leer("dímelo rápido y breve"), "con prisa")
        self.assertEqual(kelly.leer("no entiendo cómo hago eso"), "con dudas")
        self.assertEqual(kelly.leer("¡genial, gracias!"), "contento")
        self.assertEqual(kelly.leer("lista mis tareas"), "neutral")

    def test_mayusculas_y_frustracion_pesan_mas(self):
        self.assertEqual(kelly.leer("POR QUE NO RESPONDES NADA"), "frustrado")
        self.assertEqual(kelly.leer("gracias pero sigue sin funcionar"), "frustrado")

    def test_no_confunde_palabras_dentro_de_otras(self):
        # solo palabras completas: "mal" no debe saltar dentro de "normal"
        self.assertEqual(kelly.leer("todo normal"), "neutral")

    def test_frases_tecnicas_no_son_frustracion(self):
        # Falsos positivos que encontró el reviewer: en un asistente de desarrollo son normales.
        for frase in ("ayúdame a corregir este error 404", "hazlo otra vez con otro nombre",
                      "no se puede abrir el archivo", "estoy listo, empecemos", "NMAP ME DA ESTO"):
            self.assertEqual(kelly.leer(frase), "neutral", frase)

    def test_entrada_vacia_o_rara(self):
        self.assertEqual(kelly.leer(None), "neutral")
        self.assertEqual(kelly.leer(""), "neutral")

    def test_neutral_no_cambia_el_prompt(self):
        self.assertEqual(kelly.tono("neutral"), "")
        self.assertTrue(kelly.tono("con prisa"))


class Registro(unittest.TestCase):
    def test_ajustar_usa_el_ultimo_mensaje_del_usuario_y_no_guarda_texto(self):
        hist = [{"role": "user", "content": "no funciona"},
                {"role": "assistant", "content": "revisa esto"},
                {"role": "user", "content": "SECRETO-123 gracias, genial"}]
        animo, linea = kelly.ajustar(hist)
        self.assertEqual(animo, "contento")
        self.assertTrue(linea)
        crudo = (DATOS / "kelly.json").read_text(encoding="utf-8")
        self.assertNotIn("SECRETO", crudo)
        self.assertEqual(json.loads(crudo)["ultimo"], "contento")

    def test_conteos_corruptos_no_rompen_chat_ni_oficina(self):
        # Hallazgo del reviewer: un conteo no numérico tumbaba el chat en cada mensaje.
        from eva import servidor
        for malo in ('{"ultimo":"x","conteos":{"neutral":"abc","otro":null}}',
                     '{"ultimo":"x","conteos":[1,2]}', '{"ultimo":5}', '[1]'):
            (DATOS / "kelly.json").write_text(malo, encoding="utf-8")
            self.assertEqual(kelly.ajustar([{"role": "user", "content": "hola"}])[0], "neutral")
            (DATOS / "kelly.json").write_text(malo, encoding="utf-8")
            self.assertIn("KELLY", servidor.frag_oficina())

    def test_archivo_corrupto_no_rompe(self):
        (DATOS / "kelly.json").write_text("{roto", encoding="utf-8")
        self.assertEqual(kelly.estado(), {})
        kelly.registrar("neutral")
        self.assertEqual(kelly.estado()["conteos"], {"neutral": 1})


if __name__ == "__main__":
    unittest.main()
