"""Inventario de proyectos locales y repos de GitHub, con filtro de privacidad.

Regla de oro: un proyecto es candidato a publicarse solo si su nombre no está en
la lista de privados y no se detectan archivos/datos sensibles dentro.
"""
import json
import re
import subprocess
from pathlib import Path

from .comun import bitacora, config, expandir

MARCADORES = ("package.json", "pubspec.yaml", "requirements.txt", "pyproject.toml",
              "index.html", "pom.xml", "composer.json", "Cargo.toml")
IGNORAR = {"node_modules", ".git", "venv", ".venv", "__pycache__", "build", "dist",
           ".dart_tool", "bin", "obj", "vendor", ".next"}
ARCHIVOS_SENSIBLES = re.compile(
    r"(^\.env(\..+)?$|\.pem$|\.key$|\.p12$|\.pfx$|id_rsa|\.sql$|\.db$|\.sqlite3?$|"
    r"credentials|secrets?\.|\.ovpn$|\.kdbx$)", re.I)
CONTENIDO_SENSIBLE = re.compile(
    r"(password\s*[=:]\s*['\"][^'\"]{3,}|api[_-]?key\s*[=:]\s*['\"][^'\"]{8,}|"
    r"sk-[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|mongodb(\+srv)?://[^\s'\"]+:[^\s'\"]+@)", re.I)
EXT_TEXTO = {".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".php", ".cs", ".java", ".dart",
             ".yml", ".yaml", ".env", ".ini", ".cfg", ".toml", ".xml", ".html", ".txt", ".md"}


def es_privado(nombre):
    nombre = nombre.lower()
    return any(p in nombre for p in config().get("privados", []))


def _es_proyecto(p):
    return (p / ".git").exists() or any((p / m).exists() for m in MARCADORES) \
        or any(p.glob("*.csproj")) or any(p.glob("*.sln"))


def encontrar():
    raices = [expandir(r) for r in config().get("raices_proyectos", [])]
    excluir = {e.lower() for e in config().get("excluir", [])}
    vistos, proyectos = {r.resolve() for r in raices if r.exists()}, []
    for raiz in raices:
        if not raiz.exists():
            continue
        for p in raiz.iterdir():
            try:
                if p.is_dir() and not p.name.startswith(".") and p.name.lower() not in excluir \
                        and p.resolve() not in vistos and _es_proyecto(p):
                    vistos.add(p.resolve())
                    proyectos.append(p)
            except OSError:
                continue
    return proyectos


def _archivos(ruta, max_archivos):
    """En repos git: solo lo que se subiría (respeta .gitignore). Si no, recorre la carpeta."""
    ruta = Path(ruta)
    if (ruta / ".git").exists():
        listado = _git(ruta, "ls-files", "-co", "--exclude-standard")
        return [ruta / r for r in listado.splitlines()[:max_archivos]]
    archivos, pila = [], [ruta]
    while pila and len(archivos) < max_archivos:
        try:
            hijos = list(pila.pop().iterdir())
        except OSError:
            continue
        for h in hijos:
            if h.is_dir():
                if h.name not in IGNORAR:
                    pila.append(h)
            else:
                archivos.append(h)
    return archivos


def escanear_sensibles(ruta, max_archivos=3000):
    """Devuelve rutas relativas + motivo. Nunca devuelve el valor del secreto."""
    hallazgos = []
    for h in _archivos(ruta, max_archivos):
        rel = str(h.relative_to(ruta))
        if any(parte in IGNORAR for parte in h.parts):
            continue
        if ARCHIVOS_SENSIBLES.search(h.name) and not h.name.endswith(".example"):
            hallazgos.append((rel, "archivo sensible por nombre"))
        elif h.suffix.lower() in EXT_TEXTO and "test" not in rel.lower():
            try:
                if h.stat().st_size < 200_000 and CONTENIDO_SENSIBLE.search(
                        h.read_text(encoding="utf-8", errors="ignore")):
                    hallazgos.append((rel, "posible credencial en el código"))
            except OSError:
                pass
    return hallazgos


def _git(ruta, *args):
    r = subprocess.run(["git", "-C", str(ruta), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="ignore")
    return r.stdout.strip() if r.returncode == 0 else ""


def estado_git(ruta):
    if not (Path(ruta) / ".git").exists():
        return {"git": False}
    cambios = _git(ruta, "status", "--porcelain")
    return {
        "git": True,
        "remoto": _git(ruta, "remote", "get-url", "origin"),
        "rama": _git(ruta, "branch", "--show-current"),
        "cambios_sin_commit": len(cambios.splitlines()) if cambios else 0,
        "ultimo_commit": _git(ruta, "log", "-1", "--format=%cs"),
    }


def repos_github():
    usuario = config().get("github_usuario", "")
    r = subprocess.run(
        ["gh", "repo", "list", usuario, "--limit", "100", "--json",
         "name,visibility,description,repositoryTopics,homepageUrl,updatedAt,isFork"],
        capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError("gh no respondió (¿`gh auth login`?): " + r.stderr.strip())
    repos = json.loads(r.stdout)
    for repo in repos:
        faltas = []
        if not repo.get("description"):
            faltas.append("sin descripción")
        if not repo.get("repositoryTopics"):
            faltas.append("sin topics")
        if repo["visibility"] == "PUBLIC" and es_privado(repo["name"]):
            faltas.append("¡PÚBLICO pero está en tu lista de privados!")
        repo["mejoras"] = faltas
    return repos


def informe(con_escaneo=True):
    """Clasifica proyectos locales: privado / con datos sensibles / candidato."""
    resultado = []
    for p in encontrar():
        item = {"nombre": p.name, "ruta": str(p), **estado_git(p)}
        if es_privado(p.name):
            item["veredicto"] = "privado (lista de privados)"
        else:
            sens = escanear_sensibles(p) if con_escaneo else []
            item["sensibles"] = sens[:10]
            if sens:
                item["veredicto"] = f"NO publicar aún: {len(sens)} hallazgo(s) sensible(s)"
            elif "github.com" in item.get("remoto", ""):
                item["veredicto"] = "ya en GitHub: mejorar README/demo"
            else:
                item["veredicto"] = "CANDIDATO a publicar"
        resultado.append(item)
    bitacora("proyectos_informe", total=len(resultado),
             candidatos=sum(r["veredicto"].startswith("CANDIDATO") for r in resultado))
    return resultado
