"""Casos de uso de tareas. Recibe el repositorio y el reloj inyectados (DI),
así se prueba con un repo en memoria y sin depender de la hora real."""
from ..dominio.tarea import Tarea


class ServicioTareas:
    def __init__(self, repo, reloj):
        self.repo = repo          # cualquier RepositorioTareas (JSON, memoria, SQLite...)
        self.reloj = reloj        # función -> str (marca de tiempo)

    def agregar(self, titulo, area="general", prioridad=2, notas=""):
        tareas = self.repo.listar()
        titulo = str(titulo).strip()
        for t in tareas:  # no duplicar una pendiente con el mismo título
            if t.pendiente and t.titulo.lower() == titulo.lower():
                return t
        nueva = Tarea(id=max((t.id for t in tareas), default=0) + 1,
                      titulo=titulo, area=area, prioridad=prioridad,
                      creada=self.reloj(), notas=notas)
        tareas.append(nueva)
        self.repo.guardar(tareas)
        return nueva

    def listar(self, area=None, todas=False):
        tareas = self.repo.listar()
        if area:  # None o "" = sin filtro; un área inexistente no coincide con ninguna
            objetivo = str(area)
            tareas = [t for t in tareas if t.area.value == objetivo]
        if not todas:
            tareas = [t for t in tareas if t.pendiente]
        return sorted(tareas, key=lambda t: (not t.pendiente, int(t.prioridad), t.id))

    def completar(self, id_tarea, cuando=None):
        tareas = self.repo.listar()
        for t in tareas:
            if t.id == int(id_tarea):
                t.completar(cuando or self.reloj())
                self.repo.guardar(tareas)
                return t
        return None
