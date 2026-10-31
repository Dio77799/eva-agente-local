"""Hank: auditoría de seguridad del propio sistema Eva.

Evalúa que no haya amenazas, fugas de información ni herramientas de terceros que
puedan afectar. Solo LEE el código local y el estado de git; no se conecta a nada.
Devuelve una lista de (nombre, estado, detalle) con estado ok | warn | alerta.
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

from . import llm, proyectos

RAIZ = Path(__file__).resolve().parent.parent
NUCLEO = [RAIZ / "eva.py", *sorted(p for p in (RAIZ / "eva").rglob("*.py") if "__pycache__" not in p.parts)]
EXTERNO = re.compile(r"https?://(?!(?:localhost|127\.0\.0\.1))", re.I)
PELIGRO = {"eval", "exec", "system", "popen"}
HERRAMIENTAS_OK = {"agregar_tarea", "listar_tareas", "completar_tarea", "estado_kali", "guia_vpn_htb",
                   "resumen_del_dia", "analizar_escritorio", "auditar_github", "proyectos_publicables", "maquinas_htb"}
DESTRUCTIVAS = ("encender", "apagar", "borrar", "eliminar", "mover", "publicar", "push", "snapshot", "delete", "remove")


def _git_ignorado(ruta):
    r = subprocess.run(["git", "-C", str(RAIZ), "check-ignore", "-q", ruta], capture_output=True)
    return r.returncode == 0


def auditar():
    checks = []

    # 1. Dependencias de terceros (algo que no sea librería estándar puede afectarnos).
    terceros = []
    for f in NUCLEO:
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            mods = []
            if isinstance(n, ast.Import):
                mods = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.level == 0:
                mods = [(n.module or "").split(".")[0]]
            for m in mods:
                if m and m not in sys.stdlib_module_names and m != "eva":
                    terceros.append(f"{f.name}:{m}")
    checks.append(("Dependencias de terceros", "ok" if not terceros else "alerta",
                   "Solo librería estándar de Python." if not terceros else "Externos: " + ", ".join(terceros)))

    # 2. Ejecución peligrosa.
    peligros = []
    for f in NUCLEO:
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call):
                nom = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
                if nom in PELIGRO:
                    peligros.append(f"{f.name}:{n.lineno} {nom}()")
                for kw in n.keywords:
                    if kw.arg == "shell" and getattr(kw.value, "value", False) is True:
                        peligros.append(f"{f.name}:{n.lineno} shell=True")
    checks.append(("Ejecución peligrosa (eval/exec/shell)", "ok" if not peligros else "alerta",
                   "Ninguna." if not peligros else ", ".join(peligros)))

    # 3. Conexiones solo locales (sin fuga a terceros).
    externas = []
    for f in NUCLEO:
        if f.name == "seguridad.py":
            continue  # este archivo define el patrón; evitar el falso positivo
        for i, ln in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if EXTERNO.search(ln) and "example" not in ln.lower():
                externas.append(f"{f.name}:{i}")
    checks.append(("Conexiones solo locales (sin fuga)", "ok" if not externas else "warn",
                   "Solo Ollama local y gh." if not externas else "URLs externas: " + ", ".join(externas)))

    # 4. Sin secretos/credenciales en el código.
    sens = proyectos.escanear_sensibles(RAIZ)
    checks.append(("Sin secretos/credenciales en el código", "ok" if not sens else "alerta",
                   "Limpio." if not sens else f"{len(sens)} hallazgo(s): " + ", ".join(r for r, _ in sens[:5])))

    # 5. Datos personales fuera de git (privacidad).
    noign = [p for p in ("config.json", "data/x") if not _git_ignorado(p)]
    checks.append(("Datos personales fuera de git", "ok" if not noign else "alerta",
                   "config.json y data/ ignorados." if not noign else "NO ignorado: " + ", ".join(noign)))

    # 6. Herramientas del chat solo de lectura / bajo impacto.
    try:
        funciones, _ = llm._herramientas()
        mal = [n for n in funciones if n not in HERRAMIENTAS_OK or any(p in n for p in DESTRUCTIVAS)]
        checks.append(("Herramientas del chat de bajo impacto", "ok" if not mal else "alerta",
                       "Solo lectura / bajo impacto." if not mal else "Revisar: " + ", ".join(sorted(set(mal)))))
    except Exception:
        checks.append(("Herramientas del chat de bajo impacto", "warn", "No pude inspeccionarlas."))

    # 7. Panel web solo local + token.
    from . import servidor
    src = Path(servidor.__file__).read_text(encoding="utf-8")
    ok_panel = "_local" in src and "TOKEN" in src and "127.0.0.1" in src and "0.0.0.0" not in src
    checks.append(("Panel web solo local + token", "ok" if ok_panel else "alerta",
                   "Escucha solo 127.0.0.1, con token anti-CSRF." if ok_panel else "Revisar el panel."))
    return checks


def veredicto(checks):
    if any(c[1] == "alerta" for c in checks):
        return "alerta"
    if any(c[1] == "warn" for c in checks):
        return "atencion"
    return "seguro"
