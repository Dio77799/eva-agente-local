"""Panel web local de Eva (solo lectura), estilo tipo app con barra lateral.

Sirve en 127.0.0.1 con la stdlib. Una barra lateral (sidebar) y un área de contenido
que cambia sin recargar (fetch a /seccion/<nombre>): se ve una sección a la vez, no todo
amontonado. No expone nada fuera del equipo, no ejecuta acciones y escapa todo lo dinámico.
"""
import html
import http.server
import socketserver

from . import __version__, escritorio, kali, tareas

# Paleta cálida (clay + crema) y tipografía Poppins, estilo panel de gestión.
ESTILO = """
:root{
  --clay:#c7a17a; --clay-dark:#af845f; --coffee:#6f4e37;
  --bg:#f9f5f0; --card:#ffffff; --ink:#2f271f; --muted:#8a7c6d; --line:#e9ded0;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font-family:'Poppins','Segoe UI',system-ui,sans-serif;font-size:15px;line-height:1.55}
a{color:var(--clay-dark)}
.app{display:flex;min-height:100vh}

/* Sidebar */
.side{width:234px;flex:0 0 234px;background:linear-gradient(180deg,var(--coffee),#5c4030);color:#f3e9dd;display:flex;flex-direction:column;padding:22px 14px;position:sticky;top:0;height:100vh}
.brand{display:flex;align-items:center;gap:12px;padding:0 8px 18px}
.brand .logo{width:42px;height:42px;border-radius:12px;background:var(--clay);color:#3a2616;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:20px}
.brand b{font-size:19px;display:block;line-height:1.1}
.brand span{font-size:12px;color:#d8c6b2}
.menu{display:flex;flex-direction:column;gap:3px;margin-top:6px}
.item{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:10px;color:#eaddce;text-decoration:none;cursor:pointer;font-size:14.5px;border:0;background:none;width:100%;text-align:left;font-family:inherit}
.item:hover{background:rgba(255,255,255,.08)}
.item.activo{background:var(--clay);color:#3a2616;font-weight:600}
.item svg{width:20px;height:20px;flex:0 0 20px}
.side .pie{margin-top:auto;font-size:12px;color:#cbb79f;padding:12px 10px 0;border-top:1px solid rgba(255,255,255,.12)}

/* Contenido */
.main{flex:1 1 auto;min-width:0;display:flex;flex-direction:column}
.top{background:var(--card);border-bottom:1px solid var(--line);padding:20px 30px}
.top h1{margin:0;font-size:23px;font-weight:600}
.top p{margin:4px 0 0;color:var(--muted);font-size:14px}
.cont{padding:26px 30px 50px;max-width:1000px}

/* Piezas */
.tiles{display:flex;flex-wrap:wrap;gap:16px;margin-bottom:22px}
.tile{flex:1 1 180px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:0 4px 14px rgba(111,78,55,.06)}
.tile .lbl{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.tile .val{font-size:30px;font-weight:700;color:var(--clay-dark);margin-top:4px}
.tile .det{font-size:13px;color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;margin-bottom:18px;box-shadow:0 4px 14px rgba(111,78,55,.06)}
.card h2{margin:0 0 14px;font-size:17px;font-weight:600}
.fila{display:flex;gap:10px;align-items:center;padding:11px 0;border-top:1px solid var(--line)}
.fila:first-of-type{border-top:0}
.grow{flex:1 1 auto;min-width:0}
.pill{font-size:12px;padding:3px 9px;border-radius:20px;background:#efe6da;color:#6f5a44;white-space:nowrap}
.pill.alta{background:#f4ddc4;color:#9a5a17}.pill.media{background:#e5ebf1;color:#3f6392}.pill.baja{background:#eee8df;color:#7a6b58}
.muted{color:var(--muted);font-size:13px}
.ok{color:#3f7d4e}.warn{color:#b5751f}
.bar{height:7px;border-radius:4px;background:#efe6da;margin-top:5px;overflow:hidden}
.bar>i{display:block;height:7px;border-radius:4px;background:var(--clay)}
code{font-family:ui-monospace,'Cascadia Code',monospace;font-size:13px;background:#f1e8dc;color:#6f5236;padding:1px 6px;border-radius:6px}
pre{background:#2f271f;color:#f3e9dd;padding:16px;border-radius:12px;overflow:auto;font-size:13px;line-height:1.5}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:9px 12px 9px 0;border-top:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.03em}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.chip{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:20px;padding:6px 14px;font-size:13px;cursor:pointer;font-family:inherit}
.chip.on{background:var(--clay);border-color:var(--clay);color:#3a2616;font-weight:600}
.layers{display:flex;flex-direction:column;gap:10px;margin:14px 0}
.layer{border-radius:12px;padding:14px 16px;border:1px solid var(--line)}
.layer h3{margin:0 0 4px;font-size:15px}.layer span{color:var(--muted);font-size:13.5px}
.l-dom{background:#eef3ec;border-color:#cfe0c9}.l-app{background:#eef1f6;border-color:#cdd8ea}.l-inf{background:#f6eef2;border-color:#e6cdda}
.arrow{text-align:center;color:var(--muted);font-size:17px}
.flow{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.step{flex:1 1 110px;background:#f3ebe0;border-radius:10px;padding:11px 13px}
.step b{display:block}.step span{color:var(--muted);font-size:13px}
.gloss dt{font-weight:600;margin-top:12px}.gloss dd{margin:2px 0 0;color:var(--muted)}
.cargando{color:var(--muted);padding:30px 0;text-align:center}
ul.lista{margin:0;padding-left:20px;line-height:1.95;color:var(--muted)}
@media(max-width:720px){.app{flex-direction:column}.side{width:100%;height:auto;position:static;flex-direction:row;flex-wrap:wrap;gap:4px}.brand{width:100%}.menu{flex-direction:row;flex-wrap:wrap}.item{width:auto}.side .pie{display:none}}
"""

ICONOS = {
    "inicio": '<path d="M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10"/>',
    "tareas": '<path d="M9 6h11M9 12h11M9 18h11M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
    "escritorio": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/>',
    "github": '<circle cx="6" cy="6" r="2.4"/><circle cx="6" cy="18" r="2.4"/><circle cx="18" cy="9" r="2.4"/><path d="M6 8.4v7M18 11.4c0 3-4 3-9.5 5"/>',
    "kali": '<path d="M4 17l6-6-6-6M12 19h8"/>',
    "aprende": '<path d="M4 5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2zM8 7h8M8 11h6"/>',
}
META = {
    "inicio": ("Inicio", "Qué es Eva y cómo se usa"),
    "tareas": ("Tareas", "Tus pendientes por área y prioridad"),
    "escritorio": ("Escritorio", "Qué conviene ordenar · Eva no mueve nada"),
    "github": ("GitHub", "Tus repositorios y qué les falta"),
    "kali": ("Kali y HTB", "La máquina virtual y la guía de la VPN"),
    "aprende": ("Entender Eva", "Arquitectura, DDD y seguridad"),
}


def _esc(x):
    return html.escape(str(x))


# ---------- datos ----------
def _tareas_rows():
    pend = tareas.listar()
    if not pend:
        return '<p class="muted">Sin tareas pendientes. 🎉</p>', []
    prio = {1: ("alta", "alta"), 2: ("media", "media"), 3: ("baja", "baja")}
    filas, areas = [], []
    for t in pend:
        clase, texto = prio.get(t["prioridad"], ("baja", "?"))
        areas.append(t["area"])
        filas.append(
            f'<div class="fila" data-area="{_esc(t["area"])}"><span class="grow">{_esc(t["titulo"])}</span>'
            f'<span class="pill {clase}">{texto}</span><span class="pill">{_esc(t["area"])}</span></div>')
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
def frag_inicio():
    n = len(tareas.listar())
    _, esc_n = _escritorio_rows()
    cmds = [("hoy", "Resumen del día"), ("tareas", "Ver y crear pendientes"),
            ("escritorio", "Ordenar el escritorio"), ("proyectos --github", "Auditar repos"),
            ("kali vpn", "Guía de la VPN de HTB"), ("chat", "Hablar con Eva (IA local)")]
    lista = "".join(f"<tr><td><code>python eva.py {_esc(c)}</code></td><td>{_esc(d)}</td></tr>" for c, d in cmds)
    return f"""
<div class="tiles">
  <div class="tile"><div class="lbl">Tareas</div><div class="val">{n}</div><div class="det">pendientes</div></div>
  <div class="tile"><div class="lbl">Escritorio</div><div class="val">{esc_n}</div><div class="det">por ordenar</div></div>
  <div class="tile"><div class="lbl">Kali</div><div class="val" style="font-size:16px;margin-top:12px">{_kali_line()}</div></div>
</div>
<div class="card"><h2>¿Qué es Eva?</h2>
<p>Tu asistente personal que corre <b>100% en tu equipo</b>. Organiza tareas, ordena el escritorio, audita tus repos de GitHub, maneja la VM de Kali para Hack The Box y prepara borradores de contenido, <b>sin exponer datos</b>. Usa el menú de la izquierda para moverte; cada pantalla muestra una sola cosa a la vez.</p></div>
<div class="card"><h2>Cómo se usa (línea de comandos)</h2>
<p class="muted">Este panel es de solo lectura. Las acciones se hacen por consola o por el chat:</p>
<table><tbody>{lista}</tbody></table></div>"""


def frag_tareas():
    filas, areas = _tareas_rows()
    chips = '<div class="chips"><button class="chip on" data-filtro="*">Todas</button>' + "".join(
        f'<button class="chip" data-filtro="{_esc(a)}">{_esc(a)}</button>' for a in areas) + "</div>" if areas else ""
    return f'{chips}<div class="card">{filas}</div><p class="muted">Para crear o completar: <code>python eva.py tareas</code> o el chat.</p>'


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


def frag_aprende():
    gloss = [
        ("Entidad", "Objeto con identidad y reglas propias. En Eva: <code>Tarea</code>."),
        ("Value object", "Valor definido por su contenido, sin identidad. En Eva: <code>Area</code>, <code>Prioridad</code>."),
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
<p>La lógica de tareas se separó en tres capas; <code>eva/tareas.py</code> quedó como fachada con la misma API, así nada se rompió.</p>
<div class="layers">
  <div class="layer l-dom"><h3>Dominio</h3><span>Entidad <code>Tarea</code> + value objects. Reglas puras, sin IO: se prueba sola.</span></div>
  <div class="arrow">↑ usa</div>
  <div class="layer l-app"><h3>Aplicación</h3><span><code>ServicioTareas</code>: casos de uso, con repositorio y reloj inyectados.</span></div>
  <div class="arrow">↑ implementa el puerto</div>
  <div class="layer l-inf"><h3>Infraestructura</h3><span><code>RepositorioTareasJSON</code>: guarda en <code>data/tareas.json</code>. Cambiar a SQLite no tocaría el dominio.</span></div>
</div></div>
<div class="card"><h2>Glosario DDD</h2><dl class="gloss">{filas_gloss}</dl></div>
<div class="card"><h2>Cómo se construye cada cambio</h2><div class="flow">{flow}</div>
<p class="muted">Reglas en <code>.agents/NORMAS.md</code>; una puerta mecánica (<code>.agents/verificar.py</code>) revisa seguridad y pruebas.</p></div>
<div class="card"><h2>Seguridad y privacidad</h2><ul class="lista">
<li>Eva nunca mueve, borra, apaga ni publica por su cuenta: solo con un comando tuyo.</li>
<li><code>config.json</code> y <code>data/</code> no se suben a git.</li>
<li>En el chat, el modelo solo tiene herramientas de lectura; los errores no filtran rutas ni tokens.</li>
<li>Hack The Box: solo write-ups de máquinas retiradas, sin flags, IPs ni credenciales.</li>
</ul></div>"""


SECCIONES = {
    "inicio": frag_inicio, "tareas": frag_tareas, "escritorio": frag_escritorio,
    "github": frag_github, "kali": frag_kali, "aprende": frag_aprende,
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
<div class="pie">Panel de solo lectura.<br>Nada sale de tu equipo.</div></nav>
<div class="main"><div class="top"><h1 id="st">Inicio</h1><p id="ss">Qué es Eva y cómo se usa</p></div>
<div class="cont" id="cont"><p class="cargando">Cargando…</p></div></div></div>
<script>
const META={{{metajson}}};
const cont=document.getElementById('cont'),st=document.getElementById('st'),ss=document.getElementById('ss');
function filtros(){{
  const chips=cont.querySelectorAll('.chip');
  chips.forEach(c=>c.addEventListener('click',()=>{{
    chips.forEach(x=>x.classList.remove('on'));c.classList.add('on');
    const f=c.dataset.filtro;
    cont.querySelectorAll('.fila[data-area]').forEach(fi=>{{fi.style.display=(f==='*'||fi.dataset.area===f)?'':'none';}});
  }}));
}}
async function cargar(sec){{
  if(!META[sec])sec='inicio';
  document.querySelectorAll('.item').forEach(a=>a.classList.toggle('activo',a.dataset.sec===sec));
  st.textContent=META[sec][0];ss.textContent=META[sec][1];
  cont.innerHTML='<p class="cargando">Cargando…</p>';
  if(location.hash.slice(1)!==sec)history.replaceState(null,'','#'+sec);
  try{{const r=await fetch('/seccion/'+sec);cont.innerHTML=await r.text();filtros();}}
  catch(e){{cont.innerHTML='<div class="card"><p class="warn">No se pudo cargar la sección.</p></div>';}}
}}
document.querySelectorAll('.item').forEach(a=>a.addEventListener('click',()=>cargar(a.dataset.sec)));
window.addEventListener('hashchange',()=>cargar(location.hash.slice(1)));
cargar(location.hash.slice(1)||'inicio');
</script></body></html>"""


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ruta = self.path.split("?")[0].rstrip("/") or "/"
        if ruta == "/":
            cuerpo = shell()
        elif ruta.startswith("/seccion/"):
            nombre = ruta[len("/seccion/"):]
            if nombre not in SECCIONES:   # whitelist: sin path traversal
                self.send_error(404, "Seccion desconocida")
                return
            cuerpo = SECCIONES[nombre]()
        else:
            self.send_error(404, "No encontrado")
            return
        datos = cuerpo.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

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
