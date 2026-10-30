"""Utilidades compartidas: configuración, rutas de datos y bitácora."""
import json
import os
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# EVA_DATOS / EVA_CONFIG permiten a las pruebas usar carpetas temporales
DATOS = Path(os.environ.get("EVA_DATOS", RAIZ / "data"))
DATOS.mkdir(parents=True, exist_ok=True)


def config():
    """Lee config.json (personal, no se publica) o config.example.json."""
    candidatos = [os.environ["EVA_CONFIG"]] if os.environ.get("EVA_CONFIG") else []
    for nombre in candidatos + ["config.json", "config.example.json"]:
        ruta = RAIZ / nombre
        if ruta.exists():
            cfg = json.loads(ruta.read_text(encoding="utf-8"))
            cfg["_origen"] = nombre
            return cfg
    raise FileNotFoundError("Falta config.json (copia config.example.json)")


def expandir(ruta):
    return Path(os.path.expandvars(os.path.expanduser(ruta)))


def leer_json(nombre, defecto):
    ruta = DATOS / nombre
    if not ruta.exists():
        return defecto
    return json.loads(ruta.read_text(encoding="utf-8"))


def guardar_json(nombre, datos):
    (DATOS / nombre).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")


def ahora():
    return datetime.now().isoformat(timespec="seconds")


def bitacora(accion, **detalle):
    """Trazabilidad: cada acción de Eva queda en data/bitacora.jsonl."""
    linea = {"cuando": ahora(), "accion": accion, **detalle}
    with open(DATOS / "bitacora.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")
