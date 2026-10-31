"""Fachada de tareas: mantiene la API que usa el resto de Eva (CLI, chat, web) y
delega en las capas dominio/aplicación/infraestructura (piloto DDD-lite).

Quien llame a `tareas.agregar/listar/completar/formato` no cambia: sigue recibiendo
los mismos dicts. Debajo, la lógica vive ahora en capas separadas y probadas solas.
"""
from .aplicacion.servicio_tareas import ServicioTareas
from .comun import ahora, bitacora
from .dominio.tarea import Area, Prioridad
from .infraestructura.repo_tareas_json import RepositorioTareasJSON

AREAS = tuple(a.value for a in Area)
PRIORIDAD = {int(p): p.name.lower() for p in Prioridad}


def _servicio():
    return ServicioTareas(RepositorioTareasJSON(), ahora)


def agregar(titulo, area="general", prioridad=2, notas=""):
    servicio = _servicio()
    antes = {t.id for t in servicio.repo.listar()}
    t = servicio.agregar(titulo, area, prioridad, notas)
    if t.id not in antes:  # si era un duplicado, no se registra de nuevo
        bitacora("tarea_agregada", id=t.id, titulo=t.titulo, area=t.area.value)
    return t.a_dict()


def listar(area=None, todas=False):
    return [t.a_dict() for t in _servicio().listar(area, todas)]


def completar(id_tarea):
    t = _servicio().completar(id_tarea, ahora())
    if t:
        bitacora("tarea_completada", id=t.id, titulo=t.titulo)
    return t.a_dict() if t else None


def formato(t):
    marca = "x" if t["estado"] == "hecha" else " "
    return f"[{marca}] #{t['id']:<3} ({PRIORIDAD.get(t['prioridad'], '?'):5}) [{t['area']}] {t['titulo']}"
