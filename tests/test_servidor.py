"""El panel es interactivo (chat + acciones) pero seguro: token, whitelist y escapado."""
import inspect
import unittest

from tests import base
from eva import servidor, tareas


class Shell(unittest.TestCase):
    def test_shell_tiene_sidebar_token_y_secciones(self):
        html = servidor.shell()
        self.assertIn("<title>Eva", html)
        self.assertIn('class="side"', html)
        self.assertIn(f'TOKEN="{servidor.TOKEN}"', html)  # la página lleva el token
        for sec in servidor.SECCIONES:
            self.assertIn(f'data-sec="{sec}"', html)

    def test_secciones_y_acciones_esperadas(self):
        self.assertEqual(set(servidor.SECCIONES),
                         {"eva", "oficina", "perfiles", "cv", "portafolio", "contenido", "tareas",
                          "escritorio", "github", "kali", "contador", "seguridad", "libreria",
                          "mejoras", "despliegue", "aprende"})
        self.assertEqual(set(servidor.ACCIONES), {"chat", "tarea_agregar", "tarea_completar"})

    def test_shell_tiene_selector_de_tema(self):
        html = servidor.shell()
        for t in ("verde", "azul", "morado", "dinamico"):
            self.assertIn(f'data-tema="{t}"', html)

    def test_cv_tiene_descarga_y_portafolio(self):
        html = servidor.frag_cv()
        self.assertIn("/descargar/cv", html)
        self.assertIn("portafolio", html.lower())

    def test_ruta_descargar_cv_en_el_handler(self):
        import inspect
        self.assertIn("/descargar/cv", inspect.getsource(servidor._Handler.do_GET))

    def test_todas_las_secciones_en_el_menu(self):
        html = servidor.shell()
        for sec in servidor.SECCIONES:
            self.assertIn(f'data-sec="{sec}"', html)


class Fragmentos(unittest.TestCase):
    def test_eva_tiene_chat(self):
        html = servidor.frag_eva()
        self.assertIn("Terminal de Eva", html)
        self.assertIn('id="chatform"', html)

    def test_tareas_form_y_escapa_html(self):
        tareas.agregar("<script>alert(1)</script>", "general", 2)
        html = servidor.frag_tareas()
        self.assertIn('id="ftarea"', html)        # formulario para crear
        self.assertIn('class="done"', html)        # botón completar
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_perfiles_sin_archivo_no_rompe(self):
        html = servidor.frag_perfiles()            # no hay tracker en la carpeta temporal
        self.assertIn("tracker", html.lower())

    def test_oficina_usa_apodos_de_los_agentes(self):
        html = servidor.frag_oficina()
        self.assertIn("Oficina de agentes", html)
        for apodo in ("MICHAEL", "DWIGHT", "JIM", "ANGELA", "OSCAR", "KELLY"):
            self.assertIn(apodo, html)

    def test_estado_personalidad_en_diseno(self):
        estados, _ = servidor._estado_agentes("## Plan\nx\n")
        self.assertEqual(estados["personalidad"][0], "design")
        self.assertEqual(estados["seguridad"][0], "ok")  # Hank siempre vigilando

    def test_contador_registra_y_convierte(self):
        from eva import contador
        base = contador.resumen()["consultas"]
        wh = contador.registrar(36)   # 36 s a 40 W = 0.4 Wh
        self.assertGreater(wh, 0)
        self.assertEqual(contador.resumen()["consultas"], base + 1)
        self.assertAlmostEqual(contador.convertir(1), 4.0)  # 1 kWh * 4 L/kWh (config de prueba)

    def test_seguridad_audita_y_da_veredicto(self):
        from eva import seguridad
        checks = seguridad.auditar()
        self.assertTrue(checks)
        self.assertIn(seguridad.veredicto(checks), ("seguro", "atencion", "alerta"))
        # El auditor confirma que el núcleo no usa dependencias de terceros.
        dep = next(c for c in checks if "terceros" in c[0].lower())
        self.assertEqual(dep[1], "ok")

    def test_frag_contador_y_seguridad_no_rompen(self):
        self.assertIn("Contador", servidor.frag_contador())
        self.assertIn("Auditoría", servidor.frag_seguridad())

    def test_libreria_muestra_historico(self):
        html = servidor.frag_libreria()
        self.assertIn("Histórico", html)
        self.assertIn("Arquitectura", html)  # docs/historia/01-arquitectura.md

    def test_estado_agentes_segun_handoff(self):
        # Un handoff con Plan y Cambios llenos -> planner/developer LISTO, qa EN TURNO.
        texto = "## Plan\nhacer x\n## Amenazas\nninguna\n## Cambios\ncommit y\n## Pruebas\n## Revisión\n"
        estados, terminado = servidor._estado_agentes(texto)
        self.assertEqual(estados["planner"][0], "ok")
        self.assertEqual(estados["developer"][0], "ok")
        self.assertEqual(estados["qa"][0], "work")
        self.assertEqual(estados["reviewer"][0], "off")
        self.assertFalse(terminado)

    def test_placeholder_no_cuenta_como_aporte(self):
        # "(pendiente reviewer)" no debe marcar al reviewer como LISTO.
        texto = "## Plan\nx\n## Cambios\ny\n## Pruebas\nz\n## Revisión\n(pendiente reviewer)\n"
        estados, terminado = servidor._estado_agentes(texto)
        self.assertEqual(estados["reviewer"][0], "work")
        self.assertFalse(terminado)

    def test_markdown_min_escapa(self):
        html = servidor._markdown_min("## Título\n- <b>x</b>\n| a | b |")
        self.assertIn("<h2>Título</h2>", html)
        self.assertNotIn("<b>x</b>", html)
        self.assertIn("&lt;b&gt;", html)


class Acciones(unittest.TestCase):
    def test_tarea_agregar_y_completar(self):
        r = servidor._accion_tarea_agregar({"titulo": "Desde la web", "area": "github", "prioridad": "1"})
        self.assertTrue(r["ok"])
        creada = next(t for t in tareas.listar() if t["titulo"] == "Desde la web")
        self.assertTrue(servidor._accion_tarea_completar({"id": creada["id"]})["ok"])
        self.assertNotIn(creada["id"], [t["id"] for t in tareas.listar()])

    def test_tarea_agregar_sin_titulo_da_error(self):
        self.assertIn("error", servidor._accion_tarea_agregar({"titulo": "   "}))


class Seguridad(unittest.TestCase):
    def test_solo_escucha_en_localhost(self):
        self.assertIn("127.0.0.1", inspect.getsource(servidor.iniciar))
        self.assertNotIn("0.0.0.0", inspect.getsource(servidor.iniciar))

    def test_post_valida_token_y_host(self):
        # El handler exige token y Host local antes de ejecutar una acción.
        fuente = inspect.getsource(servidor._Handler.do_POST)
        self.assertIn("X-Eva-Token", fuente)
        self.assertIn("_local", fuente)

    def test_token_no_trivial(self):
        self.assertGreaterEqual(len(servidor.TOKEN), 16)


if __name__ == "__main__":
    unittest.main()
