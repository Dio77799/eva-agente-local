"""Convierte notas (HTB, proyectos) en borradores de publicación, sin datos sensibles."""
import re
from pathlib import Path

from .comun import DATOS, bitacora
from . import llm

BORRADORES = DATOS / "borradores"

LIMPIEZA = [
    (re.compile(r"\b[0-9a-f]{32}\b", re.I), "<FLAG_OCULTA>"),            # flags HTB / hashes md5
    (re.compile(r"\b\d{1,3}(\.\d{1,3}){3}\b"), "<IP>"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "<EMAIL>"),
    (re.compile(r"[A-Z]:\\Users\\[^\\\s]+", re.I), r"C:\\Users\\<usuario>"),
    (re.compile(r"/home/[^/\s]+"), "/home/<usuario>"),
    (re.compile(r"(password|pass|pwd)\s*[:=]\s*\S+", re.I), r"\1: <OCULTO>"),
]


def sanitizar(texto):
    for patron, reemplazo in LIMPIEZA:
        texto = patron.sub(reemplazo, texto)
    return texto


def borrador_htb(archivo_notas, usar_llm=False):
    notas = Path(archivo_notas).read_text(encoding="utf-8")
    if re.search(r"Estado HTB:\s*activa", notas, re.I):
        raise ValueError("La máquina sigue ACTIVA en HTB: sus reglas prohíben publicar "
                         "write-ups hasta que se retire. Cambia el estado cuando ocurra.")
    limpio = sanitizar(notas)
    if usar_llm:
        limpio = llm.generar(
            "Convierte estas notas de una máquina retirada de Hack The Box en un post "
            "educativo en español para LinkedIn/blog: intro breve, metodología, lo que "
            "aprendí y recomendaciones defensivas. No incluyas flags, IPs ni contraseñas.\n\n"
            + limpio) or limpio
        limpio = sanitizar(limpio)  # segunda pasada por si el modelo reintrodujo algo
    BORRADORES.mkdir(exist_ok=True)
    destino = BORRADORES / f"post-{Path(archivo_notas).stem}.md"
    destino.write_text(limpio, encoding="utf-8")
    bitacora("borrador_creado", origen=str(archivo_notas), destino=str(destino), llm=usar_llm)
    return destino
