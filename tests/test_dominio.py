"""Dominio y aplicación de tareas: se prueban SIN IO (repositorio en memoria).

Esta es la ventaja de separar en capas: las reglas y los casos de uso se verifican
sin tocar archivos, red ni la hora real.
"""
import unittest

from eva.aplicacion.servicio_tareas import ServicioTareas
from eva.dominio.tarea import Area, Prioridad, Tarea


class RepoMemoria:
    """Repositorio falso que cumple el puerto RepositorioTareas, en memoria."""
    def __init__(self):
        self._items = []

    def listar(self):
        return list(self._items)

    def guardar(self, tareas):
        self._items = list(tareas)


class Entidad(unittest.TestCase):
    def test_titulo_vacio_falla(self):
        with self.assertRaises(ValueError):
            Tarea(id=1, titulo="   ")

    def test_area_desconocida_cae_en_general(self):
        self.assertEqual(Tarea(id=1, titulo="x", area="zzz").area, Area.GENERAL)

    def test_prioridad_invalida_cae_en_media(self):
        self.assertEqual(Tarea(id=1, titulo="x", prioridad=99).prioridad, Prioridad.MEDIA)

    def test_completar_fija_estado_y_fecha(self):
        t = Tarea(id=1, titulo="x")
        self.assertTrue(t.pendiente)
        t.completar("2026-10-31")
        self.assertFalse(t.pendiente)
        self.assertEqual(t.hecha, "2026-10-31")

    def test_roundtrip_dict(self):
        d = Tarea(id=3, titulo="Hola", area="github", prioridad=1).a_dict()
        self.assertEqual(Tarea.desde_dict(d).a_dict(), d)


class CasosDeUso(unittest.TestCase):
    def setUp(self):
        self.srv = ServicioTareas(RepoMemoria(), reloj=lambda: "T0")

    def test_agregar_asigna_id_y_fecha(self):
        t = self.srv.agregar("Probar", "htb", 1)
        self.assertEqual(t.id, 1)
        self.assertEqual(t.creada, "T0")
        self.assertEqual(t.area, Area.HTB)

    def test_no_duplica_pendiente(self):
        a = self.srv.agregar("misma")
        b = self.srv.agregar("MISMA")
        self.assertEqual(a.id, b.id)
        self.assertEqual(len(self.srv.listar(todas=True)), 1)

    def test_listar_filtra_area_y_oculta_hechas(self):
        self.srv.agregar("g1", "github")
        t2 = self.srv.agregar("e1", "escritorio")
        self.srv.completar(t2.id)
        self.assertEqual([t.titulo for t in self.srv.listar(area="github")], ["g1"])
        self.assertEqual(self.srv.listar(area="escritorio"), [])  # hecha, oculta
        self.assertEqual(len(self.srv.listar(area="escritorio", todas=True)), 1)

    def test_completar_inexistente_devuelve_none(self):
        self.assertIsNone(self.srv.completar(999))

    def test_area_vacia_no_filtra_y_area_inexistente_no_coincide(self):
        self.srv.agregar("g", "general")
        self.srv.agregar("h", "htb")
        self.assertEqual(len(self.srv.listar(area="")), 2)   # "" = sin filtro
        self.assertEqual(len(self.srv.listar(area=None)), 2)  # None = sin filtro
        self.assertEqual(self.srv.listar(area="noexiste"), [])  # inexistente: nada


if __name__ == "__main__":
    unittest.main()
