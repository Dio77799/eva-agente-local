"""Analiza el escritorio y propone cómo ordenarlo. Nunca mueve ni borra nada."""
import re
from pathlib import Path

from .comun import bitacora, config, expandir
from . import tareas

COMPRIMIDOS = {".zip", ".rar", ".7z"}
DOCUMENTOS = {".pdf", ".docx", ".doc", ".pptx", ".xlsx", ".txt", ".pkt"}
PATRON_RESPALDO = re.compile(r"respaldo|backup|copia|\d{1,2}-\d{1,2}-\d{4}|\d{4}-\d{2}-\d{2}", re.I)


def analizar(ruta=None):
    cfg = config()
    ruta = expandir(ruta or cfg["escritorio"])
    juegos = [j.lower() for j in cfg.get("juegos", [])]
    carpetas = {p.name.lower() for p in ruta.iterdir() if p.is_dir()}
    hallazgos = []

    for p in sorted(ruta.iterdir(), key=lambda x: x.name.lower()):
        nombre, ext = p.name, p.suffix.lower()
        if nombre in ("desktop.ini", ".git", ".gitignore", "Eva"):
            continue
        if nombre.startswith("~$"):
            tipo, sug = "temporal", "Archivo temporal de Office: se puede borrar"
        elif any(j in nombre.lower() for j in juegos):
            tipo, sug = "juego", "Mover a una carpeta 'Juegos' fuera del escritorio"
        elif ext == ".exe" or ext == ".apk":
            tipo, sug = "instalador", "Mover a Descargas/instaladores o borrar si ya está instalado"
        elif ext in COMPRIMIDOS and p.stem.lower() in carpetas:
            tipo, sug = "duplicado", f"Ya existe la carpeta '{p.stem}': el comprimido sobra o va a respaldos"
        elif PATRON_RESPALDO.search(nombre):
            tipo, sug = "respaldo", "Mover a una carpeta 'Respaldos' (o subirlo a Drive y borrarlo)"
        elif ext == ".lnk":
            tipo, sug = "acceso", "Acceso directo: agrupar en una carpeta 'Accesos' o anclar a la barra"
        elif p.is_dir() and (p / ".git").exists():
            tipo, sug = "proyecto", "Proyecto con git: revisar con `eva proyectos`"
        elif ext in DOCUMENTOS:
            tipo, sug = "documento", "Mover a Documentos (escuela/trabajo)"
        elif p.is_dir():
            tipo, sug = "carpeta", "Revisar: ¿proyecto, escuela o personal?"
        else:
            tipo, sug = "otro", "Revisar manualmente"
        hallazgos.append({"item": nombre, "tipo": tipo, "sugerencia": sug})

    bitacora("escritorio_analizado", ruta=str(ruta), elementos=len(hallazgos))
    return hallazgos


def crear_tareas(hallazgos):
    """Convierte el análisis en una tarea por tipo (no una por archivo)."""
    por_tipo = {}
    for h in hallazgos:
        if h["tipo"] not in ("proyecto", "carpeta", "otro"):
            por_tipo.setdefault(h["tipo"], []).append(h["item"])
    creadas = []
    for tipo, items in por_tipo.items():
        titulo = f"Escritorio: ordenar {len(items)} elemento(s) tipo '{tipo}'"
        creadas.append(tareas.agregar(titulo, "escritorio", 3, notas=", ".join(items)))
    return creadas
