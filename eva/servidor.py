"""Panel web local de Eva: interactivo (tipo asistente), no solo lectura.

Sirve en 127.0.0.1 con la stdlib. Barra lateral + contenido que cambia sin recargar.
Permite HABLAR con Eva (chat con sus herramientas) y hacer acciones de bajo impacto
(crear/completar tareas) desde la interfaz. Las acciones van por POST /accion/<nombre>
con un token que solo conoce esta página (anti-CSRF), validando que el Host sea local;
todo lo dinámico se escapa; nada se expone fuera del equipo.
"""
import html
import http.server
import json
import secrets
import socketserver

from . import __version__, escritorio, kali, tareas
from .comun import DATOS

# Token de esta ejecución: la página lo incrusta y las acciones POST deben traerlo.
TOKEN = secrets.token_urlsafe(18)

# Paleta cálida (clay + crema) y tipografía Poppins, estilo panel de gestión.
ESTILO = """
:root{--clay:#c7a17a;--clay-dark:#af845f;--coffee:#6f4e37;--bg:#f9f5f0;--card:#fff;--ink:#2f271f;--muted:#8a7c6d;--line:#e9ded0}
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font-family:'Poppins','Segoe UI',system-ui,sans-serif;font-size:15px;line-height:1.55}
a{color:var(--clay-dark)}button{cursor:pointer;font-family:inherit}
.app{display:flex;min-height:100vh}
.side{width:234px;flex:0 0 234px;background:linear-gradient(180deg,var(--coffee),#5c4030);color:#f3e9dd;display:flex;flex-direction:column;padding:22px 14px;position:sticky;top:0;height:100vh}
.brand{display:flex;align-items:center;gap:12px;padding:0 8px 18px}
.brand .logo{width:42px;height:42px;border-radius:12px;background:var(--clay);color:#3a2616;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:20px}
.brand b{font-size:19px;display:block;line-height:1.1}.brand span{font-size:12px;color:#d8c6b2}
.menu{display:flex;flex-direction:column;gap:3px;margin-top:6px}
.item{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:10px;color:#eaddce;text-decoration:none;cursor:pointer;font-size:14.5px;border:0;background:none;width:100%;text-align:left;font-family:inherit}
.item:hover{background:rgba(255,255,255,.08)}.item.activo{background:var(--clay);color:#3a2616;font-weight:600}
.item svg{width:20px;height:20px;flex:0 0 20px}
.side .pie{margin-top:auto;font-size:12px;color:#cbb79f;padding:12px 10px 0;border-top:1px solid rgba(255,255,255,.12)}
.main{flex:1 1 auto;min-width:0;display:flex;flex-direction:column}
.top{background:var(--card);border-bottom:1px solid var(--line);padding:20px 30px}
.top h1{margin:0;font-size:23px;font-weight:600}.top p{margin:4px 0 0;color:var(--muted);font-size:14px}
.cont{padding:26px 30px 50px;max-width:1000px}
.tiles{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:22px}
.tile{flex:1 1 170px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:0 4px 14px rgba(111,78,55,.06)}
.tile .lbl{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.tile .val{font-size:30px;font-weight:700;color:var(--clay-dark);margin-top:4px}.tile .det{font-size:13px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;margin-bottom:18px;box-shadow:0 4px 14px rgba(111,78,55,.06)}
.card h2{margin:0 0 14px;font-size:17px;font-weight:600}
.fila{display:flex;gap:10px;align-items:center;padding:11px 0;border-top:1px solid var(--line)}
.fila:first-of-type{border-top:0}.grow{flex:1 1 auto;min-width:0}
.pill{font-size:12px;padding:3px 9px;border-radius:20px;background:#efe6da;color:#6f5a44;white-space:nowrap}
.pill.alta{background:#f4ddc4;color:#9a5a17}.pill.media{background:#e5ebf1;color:#3f6392}.pill.baja{background:#eee8df;color:#7a6b58}
.muted{color:var(--muted);font-size:13px}.ok{color:#3f7d4e}.warn{color:#b5751f}
.bar{height:7px;border-radius:4px;background:#efe6da;margin-top:5px;overflow:hidden}.bar>i{display:block;height:7px;border-radius:4px;background:var(--clay)}
code{font-family:ui-monospace,'Cascadia Code',monospace;font-size:13px;background:#f1e8dc;color:#6f5236;padding:1px 6px;border-radius:6px}
pre{background:#2f271f;color:#f3e9dd;padding:16px;border-radius:12px;overflow:auto;font-size:13px;line-height:1.5}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:9px 12px 9px 0;border-top:1px solid var(--line);vertical-align:top}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.chip{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:20px;padding:6px 14px;font-size:13px;cursor:pointer;font-family:inherit}
.chip.on{background:var(--clay);border-color:var(--clay);color:#3a2616;font-weight:600}
.layers{display:flex;flex-direction:column;gap:10px;margin:14px 0}
.layer{border-radius:12px;padding:14px 16px;border:1px solid var(--line)}
.layer h3{margin:0 0 4px;font-size:15px}.layer span{color:var(--muted);font-size:13.5px}
.l-dom{background:#eef3ec;border-color:#cfe0c9}.l-app{background:#eef1f6;border-color:#cdd8ea}.l-inf{background:#f6eef2;border-color:#e6cdda}
.arrow{text-align:center;color:var(--muted);font-size:17px}
.flow{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.step{flex:1 1 110px;background:#f3ebe0;border-radius:10px;padding:11px 13px}.step b{display:block}.step span{color:var(--muted);font-size:13px}
.gloss dt{font-weight:600;margin-top:12px}.gloss dd{margin:2px 0 0;color:var(--muted)}
.cargando{color:var(--muted);padding:30px 0;text-align:center}
ul.lista{margin:0;padding-left:20px;line-height:1.95;color:var(--muted)}
.chatlog{display:flex;flex-direction:column;gap:8px;max-height:46vh;overflow:auto;padding:4px 2px 12px}
.msg{padding:9px 13px;border-radius:12px;max-width:86%;white-space:pre-wrap;word-wrap:break-word}
.msg.user{align-self:flex-end;background:var(--clay);color:#3a2616}
.msg.assistant{align-self:flex-start;background:#f1e8dc;color:var(--ink)}
.chatform{display:flex;gap:8px}
.chatform input{flex:1;padding:11px 14px;border:1px solid var(--line);border-radius:10px;font:inherit}
.chatform button,.ftarea button{background:var(--clay-dark);color:#fff;border:0;border-radius:10px;padding:9px 18px;font-weight:600}
.sugs{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.sug{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:6px 13px;font-size:13px}
.ftarea{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.ftarea input{flex:1 1 200px;padding:9px 12px;border:1px solid var(--line);border-radius:10px;font:inherit}
.ftarea select{padding:9px 10px;border:1px solid var(--line);border-radius:10px;font:inherit;background:var(--card)}
.done{background:#eef3ec;border:1px solid #cfe0c9;color:#3f7d4e;border-radius:8px;width:34px;height:34px;font-size:16px;flex:0 0 34px}
@media(max-width:720px){.app{flex-direction:column}.side{width:100%;height:auto;position:static;flex-direction:row;flex-wrap:wrap;gap:4px}.brand{width:100%}.menu{flex-direction:row;flex-wrap:wrap}.item{width:auto}.side .pie{display:none}}
"""

ICONOS = {
    "eva": '<path d="M21 12a8 8 0 0 1-8 8H5l-2 2V12a8 8 0 0 1 16 0z"/><path d="M8 11h8M8 14h5"/>',
    "tareas": '<path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
    "escritorio": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "github": '<circle cx="6" cy="6" r="2.4"/><circle cx="6" cy="18" r="2.4"/><circle cx="18" cy="9" r="2.4"/><path d="M6 8.4v7M18 11.4c0 3-4 3-9.5 5"/>',
    "kali": '<path d="M4 17l6-6-6-6M12 19h8"/>',
    "perfiles": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M5 17c0-2 2-3 4-3s4 1 4 3M14 9h4M14 13h4"/>',
    "aprende": '<path d="M4 5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2zM8 7h8M8 11h6"/>',
}
META = {
    "eva": ("Eva", "Háblale y ella hace las cosas"),
    "tareas": ("Tareas", "Crea y completa tus pendientes"),
    "escritorio": ("Escritorio", "Qué conviene ordenar · Eva no mueve nada"),
    "github": ("GitHub", "Tus repositorios y qué les falta"),
    "kali": ("Kali y HTB", "La máquina virtual y la guía de la VPN"),
    "perfiles": ("Perfiles", "Certificados y mejoras de LinkedIn/GitHub"),
    "aprende": ("Entender Eva", "Arquitectura, DDD y seguridad"),
}
PRIO_SEL = {1: "alta", 2: "media", 3: "baja"}


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
                continue  # fila separadora de la tabla
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


# ---------- datos ----------
def _tareas_rows():
    pend = tareas.listar()
    if not pend:
        return '<p class="muted">Sin tareas pendientes. 🎉</p>', []
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
  <div class="tile"><div class="lbl">Kali</div><div class="val" style="font-size:15px;margin-top:12px">{_kali_line()}</div></div>
</div>
<div class="card"><h2>Habla con Eva</h2>
<p class="muted">Pídele cosas en lenguaje natural: ella usa sus herramientas (Ollama local). Ej.: "¿qué tengo pendiente?", "¿qué repos mejorar?", "agrega una tarea para publicar el post de Checkpoint".</p>
<div id="chatlog" class="chatlog"></div>
<form id="chatform" class="chatform"><input id="chatin" placeholder="Escríbele a Eva…" autocomplete="off"><button type="submit">Enviar</button></form>
<div class="sugs"><button class="sug" type="button">¿Qué tengo pendiente?</button><button class="sug" type="button">¿Qué repos de GitHub mejorar?</button><button class="sug" type="button">Dame el resumen del día</button></div>
<p class="muted" style="margin-top:10px">Necesita Ollama corriendo. Eva no mueve, borra ni publica por su cuenta.</p></div>"""


def frag_tareas():
    filas, areas = _tareas_rows()
    opciones_area = "".join(f'<option value="{_esc(a)}">{_esc(a)}</option>' for a in tareas.AREAS)
    chips = '<div class="chips"><button class="chip on" data-filtro="*" type="button">Todas</button>' + "".join(
        f'<button class="chip" data-filtro="{_esc(a)}" type="button">{_esc(a)}</button>' for a in areas) + "</div>" if areas else ""
    form = (f'<form id="ftarea" class="ftarea"><input name="titulo" placeholder="Nueva tarea…" required>'
            f'<select name="area">{opciones_area}</select>'
            f'<select name="prioridad"><option value="1">alta</option><option value="2" selected>media</option><option value="3">baja</option></select>'
            f'<button type="submit">Agregar</button></form>')
    return f'<div class="card">{form}{chips}{filas}</div><p class="muted">El botón ✓ completa la tarea. También puedes pedírselo a Eva en el chat.</p>'


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
  <div class="layer l-dom"><h3>Dominio</h3><span>Entidad <code>Tarea</code> + value objects. Reglas puras, sin IO.</span></div>
  <div class="arrow">↑ usa</div>
  <div class="layer l-app"><h3>Aplicación</h3><span><code>ServicioTareas</code>: casos de uso, con repositorio y reloj inyectados.</span></div>
  <div class="arrow">↑ implementa el puerto</div>
  <div class="layer l-inf"><h3>Infraestructura</h3><span><code>RepositorioTareasJSON</code>: guarda en <code>data/tareas.json</code>.</span></div>
</div></div>
<div class="card"><h2>Glosario DDD</h2><dl class="gloss">{filas_gloss}</dl></div>
<div class="card"><h2>Cómo se construye cada cambio</h2><div class="flow">{flow}</div></div>
<div class="card"><h2>Seguridad y privacidad</h2><ul class="lista">
<li>Eva nunca mueve, borra, apaga ni publica por su cuenta: solo con un comando o acción tuya.</li>
<li><code>config.json</code> y <code>data/</code> no se suben a git.</li>
<li>Las acciones de la web usan un token propio de la página y solo escuchan en 127.0.0.1.</li>
<li>Hack The Box: solo write-ups de máquinas retiradas, sin flags, IPs ni credenciales.</li></ul></div>"""


SECCIONES = {
    "eva": frag_eva, "tareas": frag_tareas, "escritorio": frag_escritorio,
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
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Eva · panel</title>
<style>{ESTILO}</style></head><body><div class="app">
<nav class="side"><div class="brand"><div class="logo">E</div><div><b>Eva</b><span>v{_esc(__version__)} · local</span></div></div>
<div class="menu">{_menu()}</div>
<div class="pie">Interactiva y local.<br>Nada sale de tu equipo.</div></nav>
<div class="main"><div class="top"><h1 id="st">Eva</h1><p id="ss">Háblale y ella hace las cosas</p></div>
<div class="cont" id="cont"><p class="cargando">Cargando…</p></div></div></div>
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
  cont.innerHTML='<p class="cargando">Cargando…</p>';
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
        if not self._local():   # no servir la página (que lleva el token) a un Host no local
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
    with socketserver.TCPServer(("127.0.0.1", puerto), _Handler) as s:
        print(f"Eva está en http://127.0.0.1:{puerto}  (Ctrl+C para detener)")
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            print("\nPanel detenido.")
