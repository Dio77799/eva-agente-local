"""Gestor de tareas sencillo guardado en data/tareas.json."""
from .comun import ahora, bitacora, guardar_json, leer_json

AREAS = ("general", "escritorio", "github", "htb", "contenido", "estudio")
PRIORIDAD = {1: "alta", 2: "media", 3: "baja"}


def _cargar():
    return leer_json("tareas.json", [])


def agregar(titulo, area="general", prioridad=2, notas=""):
    tareas = _cargar()
    # Evita duplicados exactos pendientes (útil cuando otros módulos crean tareas)
    for t in tareas:
        if t["titulo"].lower() == titulo.lower() and t["estado"] == "pendiente":
            return t
    nueva = {
        "id": max((t["id"] for t in tareas), default=0) + 1,
        "titulo": titulo,
        "area": area if area in AREAS else "general",
        "prioridad": int(prioridad),
        "estado": "pendiente",
        "creada": ahora(),
        "hecha": None,
        "notas": notas,
    }
    tareas.append(nueva)
    guardar_json("tareas.json", tareas)
    bitacora("tarea_agregada", id=nueva["id"], titulo=titulo, area=nueva["area"])
    return nueva


def listar(area=None, todas=False):
    tareas = _cargar()
    if area:
        tareas = [t for t in tareas if t["area"] == area]
    if not todas:
        tareas = [t for t in tareas if t["estado"] == "pendiente"]
    return sorted(tareas, key=lambda t: (t["estado"] != "pendiente", t["prioridad"], t["id"]))


def completar(id_tarea):
    tareas = _cargar()
    for t in tareas:
        if t["id"] == int(id_tarea):
            t["estado"], t["hecha"] = "hecha", ahora()
            guardar_json("tareas.json", tareas)
            bitacora("tarea_completada", id=t["id"], titulo=t["titulo"])
            return t
    return None


def formato(t):
    marca = "x" if t["estado"] == "hecha" else " "
    return f"[{marca}] #{t['id']:<3} ({PRIORIDAD.get(t['prioridad'], '?'):5}) [{t['area']}] {t['titulo']}"
