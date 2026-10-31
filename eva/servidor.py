"""Panel web local de Eva: interactivo (tipo asistente) con estética de terminal retro.

Sirve en 127.0.0.1 con la stdlib. Look CRT/fósforo (diseño propio, sin marcas de terceros),
barra lateral + contenido que cambia sin recargar. Permite HABLAR con Eva (chat con sus
herramientas), hacer acciones de bajo impacto (crear/completar tareas) y ver la OFICINA DE
AGENTES con el estado de cada uno. Acciones por POST /accion/<nombre> con un token que solo
conoce esta página (anti-CSRF) y validando Host local; todo lo dinámico se escapa.
"""
import html
import http.server
import json
import re
import secrets
from pathlib import Path

from . import __version__, escritorio, kali, tareas
from .comun import DATOS

TOKEN = secrets.token_urlsafe(18)
AGENTES_DIR = Path(__file__).resolve().parent.parent / ".agents"

# Equipo visible en la Oficina. (clave, nombre, rol corto)
ROLES = [
    ("eva", "EVA", "Orquestadora: reparte el trabajo y decide merge/push."),
    ("planner", "PLANNER", "Convierte el pedido en plan + amenazas."),
    ("developer", "DEVELOPER", "Programa en una rama, con pruebas."),
    ("qa", "QA", "Pruebas que fallan al revertir + ataques."),
    ("reviewer", "REVIEWER", "Pasada final de solo lectura: veredicto."),
]
# Sección del handoff que marca que cada agente ya aportó.
APORTE = {"planner": "Plan", "developer": "Cambios", "qa": "Pruebas", "reviewer": "Revisión"}

ESTILO = """
:root{--bg:#070b07;--panel:#0b120b;--panel2:#0e170e;--grn:#4dff91;--grn-dim:#1f6b42;
--amber:#ffb43a;--red:#ff5d5d;--line:#15351f;--ink:#bdf5d2;--muted:#5c8a6d;--glow:rgba(77,255,145,.55)}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font-family:'Cascadia Code','Consolas',ui-monospace,monospace;
font-size:14px;line-height:1.55;animation:flick 7s infinite}
.crt{position:fixed;inset:0;pointer-events:none;z-index:50;
background:repeating-linear-gradient(0deg,rgba(0,0,0,0)0,rgba(0,0,0,.28)1px,rgba(0,0,0,0)2px,rgba(0,0,0,0)3px)}
.crt::after{content:'';position:absolute;left:0;right:0;height:120px;top:0;
background:linear-gradient(180deg,rgba(77,255,145,0),rgba(77,255,145,.06),rgba(77,255,145,0));animation:scan 7s linear infinite}
@keyframes scan{0%{top:-120px}100%{top:100%}}
@keyframes flick{0%,100%{opacity:1}92%{opacity:1}93%{opacity:.86}94%{opacity:1}97%{opacity:.93}}
@keyframes blink{50%{opacity:0}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 var(--here)}50%{box-shadow:0 0 9px 2px var(--here)}}
a{color:var(--grn)}button{cursor:pointer;font-family:inherit}
.app{display:flex;min-height:100vh}
.side{width:236px;flex:0 0 236px;background:var(--panel);border-right:1px solid var(--line);
display:flex;flex-direction:column;padding:20px 12px;position:sticky;top:0;height:100vh}
.brand{padding:4px 8px 16px;border-bottom:1px solid var(--line);margin-bottom:12px}
.brand b{font-size:20px;color:var(--grn);text-shadow:0 0 8px var(--glow);letter-spacing:2px;display:block}
.brand span{font-size:11px;color:var(--muted)}
.cursor::after{content:'\\2588';margin-left:2px;animation:blink 1s step-end infinite;color:var(--grn)}
.menu{display:flex;flex-direction:column;gap:2px}
.item{display:flex;align-items:center;gap:10px;padding:10px 11px;border-radius:4px;color:var(--ink);
text-decoration:none;cursor:pointer;font-size:13.5px;border:1px solid transparent;background:none;width:100%;text-align:left;font-family:inherit}
.item:hover{background:var(--panel2);border-color:var(--line);color:var(--grn)}
.item.activo{background:var(--panel2);border-color:var(--grn-dim);color:var(--grn);text-shadow:0 0 6px var(--glow)}
.item.activo::before{content:'>';margin-right:-4px;color:var(--grn);animation:blink 1.1s step-end infinite}
.item svg{width:18px;height:18px;flex:0 0 18px}
.side .pie{margin-top:auto;font-size:11px;color:var(--muted);padding-top:12px;border-top:1px solid var(--line)}
.main{flex:1 1 auto;min-width:0;display:flex;flex-direction:column}
.top{background:var(--panel);border-bottom:1px solid var(--line);padding:16px 26px}
.top h1{margin:0;font-size:19px;font-weight:700;color:var(--grn);text-shadow:0 0 8px var(--glow);letter-spacing:1px}
.top p{margin:3px 0 0;color:var(--muted);font-size:13px}
.cont{padding:22px 26px 50px;max-width:1040px}
.tiles{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px}
.tile{flex:1 1 170px;background:var(--panel);border:1px solid var(--line);border-radius:4px;padding:14px 16px;position:relative}
.tile::before{content:'';position:absolute;top:0;left:0;width:10px;height:10px;border-top:2px solid var(--grn-dim);border-left:2px solid var(--grn-dim)}
.tile .lbl{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.12em}
.tile .val{font-size:27px;font-weight:700;color:var(--grn);text-shadow:0 0 8px var(--glow);margin-top:3px}
.tile .det{font-size:12px;color:var(--muted)}
.card{background:var(--panel);border:1px solid var(--line);border-radius:4px;padding:20px;margin-bottom:16px}
.card h2{margin:0 0 13px;font-size:15px;font-weight:700;color:var(--grn);letter-spacing:1px;text-transform:uppercase}
.card h2::before{content:'// '}
.fila{display:flex;gap:10px;align-items:center;padding:10px 0;border-top:1px dashed var(--line)}
.fila:first-of-type{border-top:0}.grow{flex:1 1 auto;min-width:0}
.pill{font-size:11px;padding:2px 8px;border-radius:3px;border:1px solid var(--line);color:var(--muted);white-space:nowrap}
.pill.alta{border-color:#5a2f12;color:var(--amber)}.pill.media{border-color:var(--grn-dim);color:var(--grn)}.pill.baja{color:var(--muted)}
.muted{color:var(--muted);font-size:12.5px}.ok{color:var(--grn)}.warn{color:var(--amber)}
.bar{height:6px;border:1px solid var(--line);margin-top:5px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--grn-dim);box-shadow:0 0 6px var(--glow)}
code{font-family:inherit;font-size:12.5px;background:var(--panel2);color:var(--amber);padding:1px 5px;border:1px solid var(--line);border-radius:3px}
pre{background:#040704;color:var(--grn);padding:14px;border:1px solid var(--line);border-radius:4px;overflow:auto;font-size:12.5px;line-height:1.5}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:8px 10px 8px 0;border-top:1px dashed var(--line);vertical-align:top}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:12px}
.chip{border:1px solid var(--line);background:var(--panel);color:var(--muted);border-radius:3px;padding:5px 12px;font-size:12px;cursor:pointer;font-family:inherit}
.chip.on{border-color:var(--grn);color:var(--grn);text-shadow:0 0 5px var(--glow)}
.layers{display:flex;flex-direction:column;gap:9px;margin:12px 0}
.layer{border:1px solid var(--line);border-left:3px solid var(--grn-dim);padding:12px 14px}
.layer h3{margin:0 0 3px;font-size:14px;color:var(--grn)}.layer span{color:var(--muted);font-size:12.5px}
.arrow{text-align:center;color:var(--grn-dim)}
.flow{display:flex;flex-wrap:wrap;gap:7px;margin:10px 0}
.step{flex:1 1 100px;border:1px solid var(--line);padding:10px 12px}.step b{display:block;color:var(--grn)}.step span{color:var(--muted);font-size:12px}
.gloss dt{font-weight:700;margin-top:11px;color:var(--ink)}.gloss dd{margin:2px 0 0;color:var(--muted)}
.cargando{color:var(--grn-dim);padding:28px 0;text-align:center}
ul.lista{margin:0;padding-left:18px;line-height:1.9;color:var(--muted)}
.chatlog{display:flex;flex-direction:column;gap:7px;max-height:44vh;overflow:auto;padding:4px 2px 12px}
.msg{padding:8px 12px;border-radius:4px;max-width:88%;white-space:pre-wrap;word-wrap:break-word;border:1px solid var(--line)}
.msg.user{align-self:flex-end;color:var(--grn);border-color:var(--grn-dim)}
.msg.user::before{content:'tú> ';color:var(--muted)}
.msg.assistant{align-self:flex-start;color:var(--ink)}
.msg.assistant::before{content:'eva> ';color:var(--grn)}
.chatform{display:flex;gap:8px}
.chatform input{flex:1;padding:10px 13px;background:#040704;border:1px solid var(--line);border-radius:3px;font:inherit;color:var(--grn)}
.chatform input:focus,.ftarea input:focus{outline:0;border-color:var(--grn);box-shadow:0 0 6px var(--glow)}
.chatform button,.ftarea button{background:transparent;color:var(--grn);border:1px solid var(--grn-dim);border-radius:3px;padding:9px 18px;font-weight:700;letter-spacing:1px}
.chatform button:hover,.ftarea button:hover{background:var(--grn);color:#040704;box-shadow:0 0 10px var(--glow)}
.sugs{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
.sug{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:5px 12px;font-size:12px;color:var(--muted)}
.sug:hover{color:var(--grn);border-color:var(--grn-dim)}
.ftarea{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:12px}
.ftarea input{flex:1 1 200px;padding:9px 12px;background:#040704;border:1px solid var(--line);border-radius:3px;font:inherit;color:var(--grn)}
.ftarea select{padding:9px 10px;border:1px solid var(--line);border-radius:3px;font:inherit;background:var(--panel2);color:var(--ink)}
.done{background:transparent;border:1px solid var(--grn-dim);color:var(--grn);border-radius:3px;width:32px;height:32px;font-size:15px;flex:0 0 32px}
.done:hover{background:var(--grn);color:#040704}
/* Oficina */
.desks{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:16px}
.desk{border:1px solid var(--line);background:var(--panel);padding:14px;position:relative;transition:border-color .2s}
.desk:hover{border-color:var(--grn-dim)}
.desk.jefe{border-color:var(--grn-dim);background:var(--panel2)}
.desk .hd{display:flex;align-items:center;gap:9px;margin-bottom:8px}
.ava{width:34px;height:34px;border:1px solid var(--grn-dim);display:flex;align-items:center;justify-content:center;color:var(--grn);font-size:16px;flex:0 0 34px}
.desk b{color:var(--grn);letter-spacing:1px}
.light{width:9px;height:9px;border-radius:50%;flex:0 0 9px;margin-left:auto}
.light.ok{--here:var(--grn);background:var(--grn);animation:pulse 2.4s infinite}
.light.work{--here:var(--amber);background:var(--amber);animation:pulse 1s infinite}
.light.off{background:#20361f}
.desk .st{font-size:11px;text-transform:uppercase;letter-spacing:.1em}
.desk .st.ok{color:var(--grn)}.desk .st.work{color:var(--amber)}.desk .st.off{color:var(--muted)}
.desk .rol{color:var(--muted);font-size:12px;margin-top:6px}
.desk .task{color:var(--ink);font-size:12.5px;margin-top:6px;border-top:1px dashed var(--line);padding-top:6px;min-height:18px}
.reg{background:#040704;border:1px solid var(--line);padding:12px 14px;font-size:12.5px;color:var(--grn);max-height:200px;overflow:auto}
.reg .ln{padding:2px 0;border-bottom:1px dotted var(--line)}
.reg .ln::before{content:'> ';color:var(--grn-dim)}
@media(max-width:720px){.app{flex-direction:column}.side{width:100%;height:auto;position:static;flex-direction:row;flex-wrap:wrap;gap:3px}.brand{width:100%}.menu{flex-direction:row;flex-wrap:wrap}.item{width:auto}.side .pie{display:none}}
"""

ICONOS = {
    "eva": '<path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 16 0z"/><path d="M8 11h8M8 14h5"/>',
    "oficina": '<rect x="3" y="9" width="18" height="12" rx="1"/><path d="M3 9l3-5h12l3 5M8 13h3M8 17h3M15 13h1M15 17h1"/>',
    "tareas": '<path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
    "escritorio": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "github": '<circle cx="6" cy="6" r="2.4"/><circle cx="6" cy="18" r="2.4"/><circle cx="18" cy="9" r="2.4"/><path d="M6 8.4v7M18 11.4c0 3-4 3-9.5 5"/>',
    "kali": '<path d="M4 17l6-6-6-6M12 19h8"/>',
    "perfiles": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M5 17c0-2 2-3 4-3s4 1 4 3M14 9h4M14 13h4"/>',
    "aprende": '<path d="M4 5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2zM8 7h8M8 11h6"/>',
}
META = {
    "eva": ("EVA", "Háblale y ella hace las cosas"),
    "oficina": ("OFICINA", "El equipo de agentes y su estado"),
    "tareas": ("TAREAS", "Crea y completa tus pendientes"),
    "escritorio": ("ESCRITORIO", "Qué conviene ordenar · Eva no mueve nada"),
    "github": ("GITHUB", "Tus repositorios y qué les falta"),
    "kali": ("KALI // HTB", "La máquina virtual y la guía de la VPN"),
    "perfiles": ("PERFILES", "Certificados y mejoras de LinkedIn/GitHub"),
    "aprende": ("MANUAL", "Arquitectura, DDD y seguridad"),
}
PRIO_SEL = {1: "alta", 2: "media", 3: "baja"}
AVATARES = {"eva": "☰", "planner": "✎", "developer": "⌨", "qa": "⚑", "reviewer": "◎"}


def _esc(x):
    return html.escape(str(x))


def _markdown_min(texto):
    """Render mínimo de Markdown (encabezados, listas, tablas) con todo escapado."""
    out, en_tabla, en_lista = [], False, False

    def cerrar():
        nonlocal en_tabla, en_lista
        if en_tabla:
            out.append("</tbody></table>")
            en_tabla = False
        if en_lista:
            out.append("</ul>")
            en_lista = False

    for linea in texto.splitlines():
        s = linea.strip()
        if not s:
            cerrar()
        elif s.startswith("## ") or s.startswith("# "):
            cerrar()
            out.append(f"<h2>{_esc(s.lstrip('# '))}</h2>")
        elif s.startswith("> "):
            cerrar()
            out.append(f'<p class="muted">{_esc(s[2:])}</p>')
        elif s.startswith("|"):
            celdas = [c.strip() for c in s.strip("|").split("|")]
            if set("".join(celdas)) <= set("-: "):
                continue
            if not en_tabla:
                out.append("<table><tbody>")
                en_tabla = True
            out.append("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in celdas) + "</tr>")
        elif s.startswith("- "):
            if not en_lista:
                out.append('<ul class="lista">')
                en_lista = True
            out.append(f"<li>{_esc(s[2:])}</li>")
        else:
            cerrar()
            out.append(f"<p>{_esc(s)}</p>")
    cerrar()
    return "".join(out)


# ---------- lectura de la oficina (.agents) ----------
def _ultimo_handoff():
    d = AGENTES_DIR / "handoffs"
    archivos = [p for p in d.glob("*.md") if p.name != "LEEME.md"] if d.exists() else []
    if not archivos:
        return None, ""
    f = max(archivos, key=lambda p: p.stat().st_mtime)
    try:
        return f.stem, f.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return f.stem, ""


def _seccion_llena(texto, titulo):
    m = re.search(rf"^##\s*{re.escape(titulo)}\b(.*?)(?=^##\s|\Z)", texto, re.S | re.M)
    if not m:
        return False
    # Una línea que es solo un placeholder entre paréntesis "(pendiente ...)" no cuenta.
    reales = [ln.strip() for ln in m.group(1).splitlines()
              if ln.strip() and not re.fullmatch(r"\(.*\)", ln.strip())]
    return bool(reales)


def _estado_agentes(texto):
    """Deriva el estado de cada agente del último handoff (quién ya aportó)."""
    estados = {}
    pendiente_marcado = False
    for clave in ("planner", "developer", "qa", "reviewer"):
        if texto and _seccion_llena(texto, APORTE[clave]):
            estados[clave] = ("ok", "LISTO")
        elif not pendiente_marcado and texto:
            estados[clave] = ("work", "EN TURNO")
            pendiente_marcado = True
        else:
            estados[clave] = ("off", "EN ESPERA")
    terminado = all(estados[c][0] == "ok" for c in ("planner", "developer", "qa", "reviewer"))
    estados["eva"] = ("ok", "COORDINANDO") if texto else ("off", "EN ESPERA")
    return estados, terminado


def _bitacora_reciente(n=7):
    d = AGENTES_DIR / "bitacora"
    archivos = [p for p in d.glob("20*.md")] if d.exists() else []
    if not archivos:
        return []
    f = max(archivos, key=lambda p: p.stat().st_mtime)
    try:
        lineas = [ln.strip("- ").strip() for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines()
                  if ln.strip() and not ln.startswith("#")]
    except OSError:
        return []
    return lineas[-n:]


# ---------- datos ----------
def _tareas_rows():
    pend = tareas.listar()
    if not pend:
        return '<p class="muted">Sin tareas pendientes.</p>', []
    filas, areas = [], []
    for t in pend:
        clase = PRIO_SEL.get(t["prioridad"], "baja")
        areas.append(t["area"])
        filas.append(
            f'<div class="fila" data-area="{_esc(t["area"])}">'
            f'<button class="done" data-id="{int(t["id"])}" title="Completar">✓</button>'
            f'<span class="grow">{_esc(t["titulo"])}</span>'
            f'<span class="pill {clase}">{clase}</span><span class="pill">{_esc(t["area"])}</span></div>')
    return "".join(filas), sorted(set(areas))


def _escritorio_rows():
    grupos = {}
    for h in escritorio.analizar():
        if h["tipo"] not in ("proyecto", "carpeta"):
            grupos.setdefault(h["tipo"], []).append(h["sugerencia"])
    if not grupos:
        return "", 0
    total = sum(len(v) for v in grupos.values())
    filas = []
    for tipo, sugs in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        pct = round(len(sugs) / total * 100)
        filas.append(
            f'<div class="fila" style="flex-direction:column;align-items:stretch;gap:5px">'
            f'<div style="display:flex;justify-content:space-between"><span>{_esc(tipo)}</span>'
            f'<span class="muted">{len(sugs)}</span></div><div class="bar"><i style="width:{pct}%"></i></div>'
            f'<span class="muted">{_esc(sugs[0])}</span></div>')
    return "".join(filas), total


def _kali_line():
    try:
        e = kali.estado()
        est = '<span class="warn">ENCENDIDA</span>' if e["encendida"] else '<span class="muted">apagada</span>'
        return f'{_esc(e["vm"])} · {est} · {len(e["snapshots"])} snapshot(s)'
    except Exception:
        return '<span class="muted">No pude consultar VirtualBox.</span>'


# ---------- fragmentos de sección ----------
def frag_eva():
    n = len(tareas.listar())
    _, esc_n = _escritorio_rows()
    return f"""
<div class="tiles">
  <div class="tile"><div class="lbl">Tareas</div><div class="val">{n}</div><div class="det">pendientes</div></div>
  <div class="tile"><div class="lbl">Escritorio</div><div class="val">{esc_n}</div><div class="det">por ordenar</div></div>
  <div class="tile"><div class="lbl">Kali</div><div class="val" style="font-size:14px;margin-top:11px">{_kali_line()}</div></div>
</div>
<div class="card"><h2>Terminal de Eva</h2>
<p class="muted">Pídele cosas en lenguaje natural: usa sus herramientas (Ollama local). Ej.: "¿qué tengo pendiente?", "¿qué repos mejorar?", "agrega una tarea para publicar el post de Checkpoint".</p>
<div id="chatlog" class="chatlog"></div>
<form id="chatform" class="chatform"><input id="chatin" placeholder="_ escríbele a Eva…" autocomplete="off"><button type="submit">ENVIAR</button></form>
<div class="sugs"><button class="sug" type="button">¿Qué tengo pendiente?</button><button class="sug" type="button">¿Qué repos de GitHub mejorar?</button><button class="sug" type="button">Dame el resumen del día</button></div>
<p class="muted" style="margin-top:10px">Necesita Ollama corriendo. Eva no mueve, borra ni publica por su cuenta.</p></div>"""


def frag_oficina():
    nombre_ws, texto = _ultimo_handoff()
    estados, terminado = _estado_agentes(texto)
    ws = _esc(nombre_ws) if nombre_ws else "sin workstream activo"
    estado_global = "CERRADO" if terminado else ("EN CURSO" if texto else "INACTIVO")
    desks = []
    for clave, nombre, rol in ROLES:
        clase, etiqueta = estados[clave]
        if clave == "eva":
            tarea = f"Coordina: {ws}" if texto else "A la espera de un pedido."
        elif clase == "ok":
            tarea = "✓ Aportó a este workstream."
        elif clase == "work":
            tarea = "Trabajando en su parte…"
        else:
            tarea = "En espera de su turno."
        desks.append(
            f'<div class="desk {"jefe" if clave == "eva" else ""}"><div class="hd">'
            f'<div class="ava">{AVATARES.get(clave, "•")}</div><b>{_esc(nombre)}</b>'
            f'<span class="light {clase}"></span></div>'
            f'<div class="st {clase}">{etiqueta}</div>'
            f'<div class="rol">{_esc(rol)}</div><div class="task">{tarea}</div></div>')
    registro = _bitacora_reciente()
    feed = "".join(f'<div class="ln">{_esc(ln)}</div>' for ln in registro) or '<div class="ln muted">sin actividad registrada</div>'
    return f"""
<div class="tiles">
  <div class="tile"><div class="lbl">Workstream</div><div class="val" style="font-size:15px;margin-top:10px">{ws}</div></div>
  <div class="tile"><div class="lbl">Estado</div><div class="val" style="font-size:19px;margin-top:8px">{estado_global}</div></div>
  <div class="tile"><div class="lbl">Build</div><div class="val">v{_esc(__version__)}</div><div class="det">main</div></div>
</div>
<div class="card"><h2>Oficina de agentes</h2>
<p class="muted">Cada agente trabaja en su etapa y se pasa el relevo por el handoff. El semáforo indica quién ya aportó (verde), quién está en turno (ámbar) y quién espera.</p>
<div class="desks">{"".join(desks)}</div></div>
<div class="card"><h2>Registro de actividad</h2><div class="reg">{feed}</div></div>"""


def frag_tareas():
    filas, areas = _tareas_rows()
    opciones_area = "".join(f'<option value="{_esc(a)}">{_esc(a)}</option>' for a in tareas.AREAS)
    chips = '<div class="chips"><button class="chip on" data-filtro="*" type="button">todas</button>' + "".join(
        f'<button class="chip" data-filtro="{_esc(a)}" type="button">{_esc(a)}</button>' for a in areas) + "</div>" if areas else ""
    form = (f'<form id="ftarea" class="ftarea"><input name="titulo" placeholder="_ nueva tarea…" required>'
            f'<select name="area">{opciones_area}</select>'
            f'<select name="prioridad"><option value="1">alta</option><option value="2" selected>media</option><option value="3">baja</option></select>'
            f'<button type="submit">AGREGAR</button></form>')
    return f'<div class="card">{form}{chips}{filas}</div><p class="muted">El botón ✓ completa la tarea. También puedes pedírselo a Eva en la terminal.</p>'


def frag_escritorio():
    filas, total = _escritorio_rows()
    cuerpo = filas or '<p class="muted">Escritorio ordenado.</p>'
    return f'<div class="card"><h2>{total} elemento(s) por ordenar</h2>{cuerpo}' \
           '<p class="muted" style="margin-top:12px">Eva solo propone: mover o borrar lo decides tú.</p></div>'


def frag_github():
    from . import proyectos
    try:
        repos = sorted(proyectos.repos_github(), key=lambda r: r["name"].lower())
        bloques = []
        for clave, titulo in (("PUBLIC", "Públicos"), ("PRIVATE", "Privados")):
            grupo = [r for r in repos if r["visibility"] == clave]
            filas = [f'<div class="fila"><span class="grow"><code>{_esc(r["name"])}</code></span>'
                     f'<span class="muted">{_esc(", ".join(r["mejoras"]) or "ok")}</span></div>' for r in grupo]
            bloques.append(f'<div class="card"><h2>{titulo} ({len(grupo)})</h2>' + ("".join(filas) or '<p class="muted">ninguno</p>') + "</div>")
        return "".join(bloques)
    except Exception:
        return '<div class="card"><p class="warn">No se pudo consultar GitHub. Revisa <code>gh auth status</code>.</p></div>'


def frag_kali():
    try:
        guia = kali.guia_vpn()
    except Exception:
        guia = "No pude leer la guía (revisa config.json)."
    return f'<div class="card"><h2>Estado</h2><p>{_kali_line()}</p></div>' \
           f'<div class="card"><h2>Guía de la VPN de HTB</h2><pre>{_esc(guia)}</pre></div>'


def frag_perfiles():
    ruta = DATOS / "perfiles" / "certificados.md"
    if not ruta.exists():
        return ('<div class="card"><p class="muted">Aún no hay tracker de perfiles. '
                'Suelta certificados en <code>data/perfiles/inbox/</code> y dile a Eva "nuevo certificado".</p></div>')
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError:
        return '<div class="card"><p class="warn">No pude leer el tracker de perfiles.</p></div>'
    return '<div class="card">' + _markdown_min(texto) + "</div>"


def frag_aprende():
    gloss = [
        ("Entidad", "Objeto con identidad y reglas propias. En Eva: <code>Tarea</code>."),
        ("Value object", "Valor definido por su contenido. En Eva: <code>Area</code>, <code>Prioridad</code>."),
        ("Repositorio", "Interfaz para guardar/leer sin saber el detalle. <code>RepositorioTareasJSON</code>."),
        ("Caso de uso", "Una acción del sistema. <code>ServicioTareas.agregar/listar/completar</code>."),
        ("Inversión de dependencias", "El detalle (JSON) depende de la interfaz del dominio, no al revés."),
    ]
    filas_gloss = "".join(f"<dt>{t}</dt><dd>{d}</dd>" for t, d in gloss)
    pasos = [("planner", "plan + amenazas"), ("developer", "código"), ("qa", "pruebas"),
             ("reviewer", "veredicto"), ("tú", "merge / push")]
    flow = "".join(f'<div class="step"><b>{_esc(r)}</b><span>{_esc(h)}</span></div>' for r, h in pasos)
    return f"""
<div class="card"><h2>Arquitectura por capas (piloto DDD-lite en tareas)</h2>
<div class="layers">
  <div class="layer"><h3>Dominio</h3><span>Entidad <code>Tarea</code> + value objects. Reglas puras, sin IO.</span></div>
  <div class="arrow">↑ usa</div>
  <div class="layer"><h3>Aplicación</h3><span><code>ServicioTareas</code>: casos de uso, con repositorio y reloj inyectados.</span></div>
  <div class="arrow">↑ implementa el puerto</div>
  <div class="layer"><h3>Infraestructura</h3><span><code>RepositorioTareasJSON</code>: guarda en <code>data/tareas.json</code>.</span></div>
</div></div>
<div class="card"><h2>Glosario DDD</h2><dl class="gloss">{filas_gloss}</dl></div>
<div class="card"><h2>Cómo se construye cada cambio</h2><div class="flow">{flow}</div></div>
<div class="card"><h2>Seguridad y privacidad</h2><ul class="lista">
<li>Eva nunca mueve, borra, apaga ni publica por su cuenta: solo con un comando o acción tuya.</li>
<li><code>config.json</code> y <code>data/</code> no se suben a git.</li>
<li>Las acciones de la web usan un token propio de la página y solo escuchan en 127.0.0.1.</li>
<li>Hack The Box: solo write-ups de máquinas retiradas, sin flags, IPs ni credenciales.</li></ul></div>"""


SECCIONES = {
    "eva": frag_eva, "oficina": frag_oficina, "tareas": frag_tareas, "escritorio": frag_escritorio,
    "github": frag_github, "kali": frag_kali, "perfiles": frag_perfiles, "aprende": frag_aprende,
}


# ---------- acciones (POST) ----------
def _accion_chat(datos):
    from . import llm
    return {"texto": llm.responder(datos.get("historial") or [])}


def _accion_tarea_agregar(datos):
    titulo = str(datos.get("titulo", "")).strip()
    if not titulo:
        return {"error": "Falta el título."}
    try:
        prio = int(datos.get("prioridad", 2))
    except (ValueError, TypeError):
        prio = 2
    tareas.agregar(titulo, str(datos.get("area", "general")), prio)
    return {"ok": True}


def _accion_tarea_completar(datos):
    t = tareas.completar(datos.get("id"))
    return {"ok": bool(t)}


ACCIONES = {
    "chat": _accion_chat,
    "tarea_agregar": _accion_tarea_agregar,
    "tarea_completar": _accion_tarea_completar,
}


def _menu():
    return "".join(
        f'<button class="item" data-sec="{s}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONOS[s]}</svg>{_esc(META[s][0])}</button>'
        for s in SECCIONES)


def shell():
    metajson = ",".join(f'"{s}":["{_esc(t)}","{_esc(st)}"]' for s, (t, st) in META.items())
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Eva · terminal</title>
<style>{ESTILO}</style></head><body><div class="crt"></div><div class="app">
<nav class="side"><div class="brand"><b>EVA<span class="cursor"></span></b><span>v{_esc(__version__)} · sistema local</span></div>
<div class="menu">{_menu()}</div>
<div class="pie">[ TERMINAL LOCAL ]<br>nada sale de tu equipo.</div></nav>
<div class="main"><div class="top"><h1 id="st">EVA</h1><p id="ss">Háblale y ella hace las cosas</p></div>
<div class="cont" id="cont"><p class="cargando">cargando…</p></div></div></div>
<script>
const META={{{metajson}}},TOKEN="{TOKEN}";
const cont=document.getElementById('cont'),st=document.getElementById('st'),ss=document.getElementById('ss');
let CHAT=[],SEC='eva';
async function accion(nombre,datos){{
  const r=await fetch('/accion/'+nombre,{{method:'POST',headers:{{'Content-Type':'application/json','X-Eva-Token':TOKEN}},body:JSON.stringify(datos||{{}})}});
  if(!r.ok)throw new Error(r.status);return r.json();
}}
function pintarChat(){{const log=document.getElementById('chatlog');if(!log)return;log.innerHTML='';
  for(const m of CHAT){{const d=document.createElement('div');d.className='msg '+m.role;d.textContent=m.content;log.appendChild(d);}}
  log.scrollTop=log.scrollHeight;}}
async function enviarChat(txt){{txt=(txt||'').trim();if(!txt)return;
  const inp=document.getElementById('chatin');CHAT.push({{role:'user',content:txt}});
  CHAT.push({{role:'assistant',content:'…'}});pintarChat();if(inp){{inp.value='';inp.disabled=true;}}
  try{{const res=await accion('chat',{{historial:CHAT.filter(m=>m.content!=='…')}});
    CHAT[CHAT.length-1]={{role:'assistant',content:res.texto||res.error||'(sin respuesta)'}};}}
  catch(e){{CHAT[CHAT.length-1]={{role:'assistant',content:'No pude responder (¿Ollama encendido?).'}};}}
  pintarChat();if(inp){{inp.disabled=false;inp.focus();}}}}
function activar(){{
  const chips=cont.querySelectorAll('.chip');
  chips.forEach(c=>c.addEventListener('click',()=>{{chips.forEach(x=>x.classList.remove('on'));c.classList.add('on');
    const f=c.dataset.filtro;cont.querySelectorAll('.fila[data-area]').forEach(fi=>{{fi.style.display=(f==='*'||fi.dataset.area===f)?'':'none';}});}}));
  const ft=document.getElementById('ftarea');
  if(ft)ft.addEventListener('submit',async e=>{{e.preventDefault();const fd=new FormData(ft);
    try{{await accion('tarea_agregar',{{titulo:fd.get('titulo'),area:fd.get('area'),prioridad:fd.get('prioridad')}});cargar('tareas');}}catch(_){{}}}});
  cont.querySelectorAll('.done').forEach(b=>b.addEventListener('click',async()=>{{
    try{{await accion('tarea_completar',{{id:parseInt(b.dataset.id)}});cargar('tareas');}}catch(_){{}}}}));
  const cf=document.getElementById('chatform');
  if(cf){{cf.addEventListener('submit',e=>{{e.preventDefault();enviarChat(document.getElementById('chatin').value);}});
    cont.querySelectorAll('.sug').forEach(b=>b.addEventListener('click',()=>enviarChat(b.textContent)));pintarChat();}}
}}
async function cargar(sec){{if(!META[sec])sec='eva';SEC=sec;
  document.querySelectorAll('.item').forEach(a=>a.classList.toggle('activo',a.dataset.sec===sec));
  st.textContent=META[sec][0];ss.textContent=META[sec][1];
  cont.innerHTML='<p class="cargando">cargando…</p>';
  if(location.hash.slice(1)!==sec)history.replaceState(null,'','#'+sec);
  try{{const r=await fetch('/seccion/'+sec);cont.innerHTML=await r.text();activar();}}
  catch(e){{cont.innerHTML='<div class="card"><p class="warn">No se pudo cargar la sección.</p></div>';}}}}
document.querySelectorAll('.item').forEach(a=>a.addEventListener('click',()=>cargar(a.dataset.sec)));
window.addEventListener('hashchange',()=>cargar(location.hash.slice(1)));
cargar(location.hash.slice(1)||'eva');
</script></body></html>"""


class _Handler(http.server.BaseHTTPRequestHandler):
    def _local(self):
        return (self.headers.get("Host") or "").split(":")[0] in ("127.0.0.1", "localhost")

    def _responder(self, cuerpo, tipo="text/html; charset=utf-8", codigo=200):
        datos = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        if not self._local():   # no servir la página (lleva el token) a un Host no local
            self.send_error(403, "Solo local")
            return
        ruta = self.path.split("?")[0].rstrip("/") or "/"
        if ruta == "/":
            self._responder(shell())
        elif ruta.startswith("/seccion/") and ruta[len("/seccion/"):] in SECCIONES:
            self._responder(SECCIONES[ruta[len("/seccion/"):]]())
        else:
            self.send_error(404, "No encontrado")

    def do_POST(self):
        ruta = self.path.split("?")[0]
        nombre = ruta[len("/accion/"):] if ruta.startswith("/accion/") else ""
        if not self._local():
            self.send_error(403, "Solo local")
            return
        if nombre not in ACCIONES:
            self.send_error(404, "Accion desconocida")
            return
        if self.headers.get("X-Eva-Token") != TOKEN:   # anti-CSRF: solo nuestra página lo tiene
            self.send_error(403, "Token invalido")
            return
        try:
            largo = int(self.headers.get("Content-Length", 0) or 0)
        except ValueError:
            largo = 0
        if largo > 300000:
            self.send_error(413, "Demasiado grande")
            return
        try:
            datos = json.loads(self.rfile.read(largo) or "{}")
            if not isinstance(datos, dict):
                datos = {}
        except ValueError:
            datos = {}
        try:
            resultado = ACCIONES[nombre](datos)
        except Exception:
            resultado = {"error": "No se pudo completar la acción."}
        self._responder(json.dumps(resultado, ensure_ascii=False), "application/json; charset=utf-8")

    def log_message(self, *args):
        pass


def iniciar(puerto=8750):
    # Solo 127.0.0.1: nunca accesible desde otra máquina de la red.
    # Multihilo: una petición lenta (el chat esperando a Ollama) no congela el panel.
    with http.server.ThreadingHTTPServer(("127.0.0.1", puerto), _Handler) as s:
        print(f"Eva está en http://127.0.0.1:{puerto}  (Ctrl+C para detener)")
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            print("\nPanel detenido.")
