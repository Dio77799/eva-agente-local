"""Importar primero en toda prueba: aísla a Eva en carpetas temporales."""
import json
import os
import tempfile
from pathlib import Path

TEMP = Path(tempfile.mkdtemp(prefix="eva-pruebas-"))
ESCRITORIO = TEMP / "escritorio"
ESCRITORIO.mkdir()
CONFIG = TEMP / "config.json"
CONFIG.write_text(json.dumps({
    "escritorio": str(ESCRITORIO),
    "raices_proyectos": [],
    "github_usuario": "usuario-prueba",
    "privados": ["clienteprivado"],
    "juegos": ["juegoprueba"],
    "kali": {"vm": "vm-prueba", "vboxmanage": "no-existe", "ovpn_dir": "~/Downloads", "ovpn": "lab.ovpn"},
    "ollama": {"url": "http://127.0.0.1:9", "modelo": "ninguno"},
}), encoding="utf-8")

os.environ["EVA_DATOS"] = str(TEMP / "data")
os.environ["EVA_CONFIG"] = str(CONFIG)
