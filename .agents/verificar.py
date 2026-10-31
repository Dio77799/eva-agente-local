"""Comprobaciones mecánicas de todo cambio en Eva. Salida 0 = todo bien.

Uso: python .agents/verificar.py
"""
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

NUCLEO = [RAIZ / "eva.py", *sorted(p for p in (RAIZ / "eva").rglob("*.py")
                                   if "__pycache__" not in p.parts)]
PERSONALES = ["config.json", "data/x", ".agents/handoffs/x", ".agents/bitacora/x", ".agents/PENDIENTES.md"]
fallos = []


def comprobar(nombre, problemas):
    estado = "OK   " if not problemas else "FALLA"
    print(f"[{estado}] {nombre}")
    for p in problemas[:10]:
        print(f"         - {p}")
    if problemas:
        fallos.append(nombre)


def git(*args):
    r = subprocess.run(["git", "-C", str(RAIZ), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    return r.returncode, r.stdout


def publicables():
    """Lo que se subiría a GitHub: rastreado + nuevo no ignorado."""
    _, salida = git("ls-files", "-co", "--exclude-standard")
    return [RAIZ / r for r in salida.splitlines() if (RAIZ / r).is_file()]


# 1. Sintaxis
problemas = []
for f in RAIZ.rglob("*.py"):
    if "__pycache__" in f.parts:
        continue
    try:
        ast.parse(f.read_text(encoding="utf-8"), str(f))
    except SyntaxError as e:
        problemas.append(f"{f.relative_to(RAIZ)}:{e.lineno} {e.msg}")
comprobar("Sintaxis de Python", problemas)

# 2. Núcleo sin dependencias externas y sin llamadas peligrosas
problemas = []
for f in NUCLEO:
    arbol = ast.parse(f.read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos = [a.name.split(".")[0] for a in nodo.names]
        elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0:
            modulos = [nodo.module.split(".")[0]]
        else:
            modulos = []
        for m in modulos:
            if m not in sys.stdlib_module_names and m != "eva":
                problemas.append(f"{f.name}:{nodo.lineno} importa '{m}' (no es librería estándar)")
        if isinstance(nodo, ast.Call):
            nombre = getattr(nodo.func, "id", None) or getattr(nodo.func, "attr", None)
            if nombre in ("eval", "exec", "system", "popen"):
                problemas.append(f"{f.name}:{nodo.lineno} usa {nombre}()")
            for kw in nodo.keywords:
                if kw.arg == "shell" and getattr(kw.value, "value", False) is True:
                    problemas.append(f"{f.name}:{nodo.lineno} usa shell=True")
comprobar("Núcleo: solo stdlib, sin eval/exec/os.system/shell=True", problemas)

# 3. Datos personales ignorados por git y nunca rastreados
codigo, _ = git("rev-parse", "--is-inside-work-tree")
if codigo != 0:
    comprobar("Datos personales fuera de git", ["Eva no tiene repositorio git propio (git init)"])
else:
    problemas = [f"{p} NO está ignorado" for p in PERSONALES if git("check-ignore", "-q", p)[0] != 0]
    _, rastreados = git("ls-files")
    problemas += [f"{r} está rastreado por git" for r in rastreados.splitlines()
                  if r == "config.json" or r.startswith(("data/", ".agents/handoffs", ".agents/bitacora"))]
    comprobar("Datos personales fuera de git", problemas)

# 4. Sin secretos en lo publicable (reutiliza el escáner de Eva)
from eva import proyectos  # noqa: E402

hallazgos = [f"{r} ({m})" for r, m in proyectos.escanear_sensibles(RAIZ)]
comprobar("Sin secretos en lo publicable", hallazgos)

# 5. Sin datos personales en lo publicable
problemas = []
cfg_personal = RAIZ / "config.json"
if cfg_personal.exists():
    cfg = json.loads(cfg_personal.read_text(encoding="utf-8"))
    ejemplo = (RAIZ / "config.example.json").read_text(encoding="utf-8").lower()
    marcas = {cfg.get("github_usuario", "")} | set(cfg.get("privados", []))
    marcas |= {Path(cfg.get("escritorio", "")).parent.name}  # nombre de usuario de Windows
    marcas = {m for m in marcas if len(m) >= 3 and m.lower() not in ejemplo}
    patron = re.compile(r"\b(" + "|".join(re.escape(m) for m in marcas) + r")\b", re.I)
    correo = re.compile(r"[\w.+-]+@(gmail|hotmail|outlook|yahoo)\.\w+", re.I)
    for f in publicables():
        if f.suffix.lower() not in {".py", ".md", ".json", ".txt", ".bat", ".yml", ".yaml", ".toml"}:
            continue
        for n, linea in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            m = patron.search(linea) or correo.search(linea)
            if m:
                problemas.append(f"{f.relative_to(RAIZ)}:{n} contiene '{m.group(0)}'")
comprobar("Sin datos personales en lo publicable", problemas)

# 6. Pruebas
r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                   cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="ignore")
ultima = (r.stderr.strip().splitlines() or ["sin salida"])[-1]
comprobar(f"Pruebas unittest ({ultima})", [] if r.returncode == 0 else r.stderr.splitlines()[-15:])

print("\nRESULTADO:", "todo en orden" if not fallos else f"{len(fallos)} comprobación(es) fallan")
sys.exit(1 if fallos else 0)
