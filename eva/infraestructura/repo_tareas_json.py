"""Implementa RepositorioTareas guardando en un archivo JSON (data/tareas.json).

Es el único punto que sabe que las tareas viven en JSON. Para cambiar a SQLite
bastaría con otra clase que cumpla el mismo puerto; el dominio no se entera.
"""
from ..comun import guardar_json, leer_json
from ..dominio.tarea import Tarea


class RepositorioTareasJSON:
    def __init__(self, nombre="tareas.json"):
        self.nombre = nombre

    def listar(self):
        return [Tarea.desde_dict(d) for d in leer_json(self.nombre, [])]

    def guardar(self, tareas):
        guardar_json(self.nombre, [t.a_dict() for t in tareas])
