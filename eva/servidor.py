"""Panel web local de Eva (solo lectura). Sirve en 127.0.0.1 con la stdlib.

No expone nada fuera de tu equipo y no ejecuta acciones: solo muestra el estado
(tareas, escritorio, Kali y, bajo demanda, GitHub). Todo valor dinámico se escapa
con html.escape para que un nombre de archivo o de repo no inyecte HTML.
"""
import html
import http.server
import socketserver

from . import __version__, escritorio, kali, tareas

ESTILO = """
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#e6edf3;font-family:'Segoe UI',system-ui,sans-serif;font-size:15px;line-height:1.5}
a{color:#8ab4ff}
.wrap{max-width:1100px;margin:0 auto;padding:32px 24px 56px}
h1{font-size:30px;margin:0 0 4px}
h2{font-size:18px;margin:0 0 12px}
.sub{color:#9aa6b4;font-family:ui-monospace,'Cascadia Code',monospace;font-size:13px}
.tiles{display:flex;flex-wrap:wrap;gap:14px;margin:24px 0}
.tile{flex:1 1 200px;background:#161b22;border:1px solid #262d38;border-radius:12px;padding:16px 18px}
.tile .lbl{color:#9aa6b4;font-family:ui-monospace,monospace;font-size:12px}
.tile .val{font-size:28px;font-weight:600;margin-top:4px}
.card{background:#161b22;border:1px solid #262d38;border-radius:12px;padding:20px;margin-bottom:18px}
.row{display:flex;gap:10px;padding:10px 0;border-top:1px solid #222934}
.row:first-of-type{border-top:0}
.pill{font-family:ui-monospace,monospace;font-size:12px;padding:2px 8px;border-radius:6px;background:#222a35;color:#c3ccd7}
.alta{background:#3a2a12;color:#f2c27a}.media{background:#1d2b44;color:#a9c7ff}.baja{background:#222a35;color:#c3ccd7}
.muted{color:#9aa6b4;font-size:13px}
.ok{color:#8fd0a6}.warn{color:#f2c27a}
.bar{height:6px;border-radius:3px;background:#222a35;margin-top:4px}
.bar>i{display:block;height:6px;border-radius:3px;background:#6ea8ff}
code{font-family:ui-monospace,monospace;font-size:13px;color:#b4bfcc}
.nav{display:flex;gap:16px;margin:10px 0 0;font-size:14px}
.nav a{text-decoration:none}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px 10px 8px 0;vertical-align:top;border-top:1px solid #222934}
th{color:#9aa6b4;font-family:ui-monospace,monospace;font-size:12px;font-weight:500}
.layers{display:flex;flex-direction:column;gap:10px;margin:14px 0}
.layer{border-radius:10px;padding:14px 16px;border:1px solid #262d38}
.layer h3{margin:0 0 4px;font-size:15px}
.l-dom{background:#14201a;border-color:#27402f}
.l-app{background:#161d2b;border-color:#28374f}
.l-inf{background:#201a22;border-color:#3a2a3f}
.arrow{text-align:center;color:#9aa6b4;font-size:18px}
.gloss dt{font-weight:600;margin-top:12px;color:#e6edf3}
.gloss dd{margin:2px 0 0;color:#b4bfcc}
.flow{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.step{flex:1 1 120px;background:#1c2531;border-radius:8px;padding:10px 12px}
.step b{display:block}.step span{color:#9aa6b4;font-size:13px}
"""


def _nav(actual=""):
    enlaces = [("/", "Panel"), ("/aprende", "Entender Eva"), ("/github", "GitHub")]
    return '<div class="nav">' + " ".join(
        f'<a href="{h}"{" style=color:#e6edf3" if h == actual else ""}>{t}</a>' for h, t in enlaces) + "</div>"

PRIO = {1: ("alta", "alta"), 2: ("media", "media"), 3: ("baja", "baja")}


def _esc(x):
    return html.escape(str(x))


def _tareas_html():
    pend = tareas.listar()
    if not pend:
        return '<p class="muted">Sin tareas pendientes. 🎉</p>'
    filas = []
    for t in pend:
        clase, texto = PRIO.get(t["prioridad"], ("baja", "?"))
        filas.append(
            f'<div class="row"><span>{_esc(t["titulo"])}</span>'
            f'<span class="pill {clase}">{texto}</span>'
            f'<span class="pill">{_esc(t["area"])}</span></div>')
    return "".join(filas)


def _escritorio_html():
    grupos = {}
    for h in escritorio.analizar():
        if h["tipo"] not in ("proyecto", "carpeta"):
            grupos.setdefault(h["tipo"], []).append((h["item"], h["sugerencia"]))
    if not grupos:
        return '<p class="muted">Escritorio ordenado.</p>', 0
    total = sum(len(v) for v in grupos.values())
    filas = []
    for tipo, items in sorted(grupos.items(), key=lambda kv: -len(kv[1])):
        pct = round(len(items) / total * 100)
        filas.append(
            f'<div class="row" style="flex-direction:column;gap:4px">'
            f'<div style="display:flex;justify-content:space-between">'
            f'<span>{_esc(tipo)}</span><span class="muted">{len(items)}</span></div>'
            f'<div class="bar"><i style="width:{pct}%"></i></div>'
            f'<span class="muted">{_esc(items[0][1])}</span></div>')
    return "".join(filas), total


def _kali_html():
    try:
        e = kali.estado()
        estado = '<span class="warn">ENCENDIDA</span>' if e["encendida"] else '<span class="muted">apagada</span>'
        return f'VM {_esc(e["vm"])}: {estado} · {len(e["snapshots"])} snapshot(s)'
    except Exception:
        return '<span class="muted">No pude consultar VirtualBox.</span>'


def pagina():
    esc_html, esc_n = _escritorio_html()
    n_tareas = len(tareas.listar())
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eva · panel</title><style>{ESTILO}</style></head><body><div class="wrap">
<h1>Eva</h1><div class="sub">v{_esc(__version__)} · panel local de solo lectura</div>
{_nav("/")}
<div class="tiles">
  <div class="tile"><div class="lbl">tareas</div><div class="val">{n_tareas}</div></div>
  <div class="tile"><div class="lbl">escritorio</div><div class="val">{esc_n}</div><div class="muted">por ordenar</div></div>
  <div class="tile"><div class="lbl">kali</div><div class="val" style="font-size:20px;margin-top:10px">{_kali_html()}</div></div>
</div>
<div class="card"><h2>Pendientes</h2>{_tareas_html()}</div>
<div class="card"><h2>Escritorio</h2>{esc_html}
<p class="muted" style="margin-top:12px">Eva solo propone: mover o borrar lo decides tú.</p></div>
<div class="card"><h2>GitHub</h2><p class="muted">La auditoría consulta <code>gh</code> y tarda unos segundos.</p>
<p><a href="/github">Ver repos y mejoras →</a></p></div>
<p class="muted">Panel de solo lectura en tu equipo. Para acciones usa <code>python eva.py</code> o el chat.</p>
</div></body></html>"""


def pagina_github():
    from . import proyectos
    try:
        repos = sorted(proyectos.repos_github(), key=lambda r: r["name"].lower())
        bloques = []
        for clave, titulo in (("PUBLIC", "Públicos"), ("PRIVATE", "Privados")):
            grupo = [r for r in repos if r["visibility"] == clave]
            filas = [f'<div class="row"><span><code>{_esc(r["name"])}</code></span>'
                     f'<span class="muted">{_esc(", ".join(r["mejoras"]) or "ok")}</span></div>'
                     for r in grupo]
            bloques.append(f'<div class="card"><h2>{titulo} ({len(grupo)})</h2>' + ("".join(filas) or '<p class="muted">ninguno</p>') + "</div>")
        cuerpo = "".join(bloques)
    except Exception:
        cuerpo = '<div class="card"><p class="warn">No se pudo consultar GitHub. Revisa <code>gh auth status</code>.</p></div>'
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eva · GitHub</title><style>{ESTILO}</style></head><body><div class="wrap">
<h1>GitHub</h1><div class="sub">repos y mejoras</div>{_nav("/github")}{cuerpo}</div></body></html>"""


def pagina_aprende():
    cmd = [
        ("hoy", "Resumen del día: tareas, Kali, escritorio, repos."),
        ("tareas", "Ver, crear y completar tareas por área y prioridad."),
        ("escritorio", "Clasifica el escritorio y sugiere orden (no mueve nada)."),
        ("proyectos [--github]", "Proyectos locales (privado/secretos/candidato) y auditoría de repos."),
        ("kali [encender|vpn|snapshot]", "Controla la VM de Kali y da la guía de la VPN de HTB."),
        ("htb [nueva|post]", "Cuaderno de máquinas y borrador de post (solo máquinas retiradas)."),
        ("chat", "Conversa en lenguaje natural con herramientas (Ollama local)."),
        ("servidor", "Este panel web local de solo lectura."),
    ]
    filas_cmd = "".join(f"<tr><td><code>python eva.py {_esc(c)}</code></td><td>{_esc(d)}</td></tr>" for c, d in cmd)
    gloss = [
        ("Entidad", "Objeto con identidad propia y reglas que se protegen a sí mismo. En Eva: <code>Tarea</code> (valida su título, área y prioridad)."),
        ("Value object (objeto-valor)", "Valor sin identidad, definido por su contenido. En Eva: <code>Area</code> y <code>Prioridad</code> (enums)."),
        ("Repositorio", "Interfaz para guardar y leer entidades sin saber el detalle. En Eva: <code>RepositorioTareas</code> (puerto) y <code>RepositorioTareasJSON</code> (implementación)."),
        ("Caso de uso", "Una acción que el sistema ofrece. En Eva: <code>ServicioTareas.agregar/listar/completar</code>."),
        ("Capa de dominio", "Las reglas puras, sin archivos ni red. Se prueba sola."),
        ("Capa de aplicación", "Orquesta el dominio con los repositorios. No tiene reglas ni IO."),
        ("Capa de infraestructura", "Los detalles técnicos: JSON hoy, quizá SQLite mañana."),
        ("Inversión de dependencias", "El detalle (JSON) depende de la interfaz del dominio, no al revés: por eso se puede cambiar sin tocar las reglas."),
    ]
    filas_gloss = "".join(f"<dt>{t}</dt><dd>{d}</dd>" for t, d in gloss)
    pasos = [("planner", "plan + amenazas"), ("developer", "código + rama"),
             ("qa", "pruebas + ataques"), ("reviewer", "veredicto"), ("tú", "merge / push")]
    flow = "".join(f'<div class="step"><b>{_esc(r)}</b><span>{_esc(h)}</span></div>' for r, h in pasos)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eva · entender el proyecto</title><style>{ESTILO}</style></head><body><div class="wrap">
<h1>Entender Eva</h1><div class="sub">v{_esc(__version__)} · guía para estudiar todo lo que tenemos</div>
{_nav("/aprende")}

<div class="card"><h2>1. Qué es Eva</h2>
<p>Un asistente personal que corre <b>100% en tu equipo</b> (Python, solo librería estándar; IA opcional con Ollama). Organiza tareas, ordena el escritorio, audita tus repos de GitHub, maneja la VM de Kali para Hack The Box y convierte tus notas en borradores de contenido, siempre sin exponer datos.</p>
<table><thead><tr><th>Comando</th><th>Qué hace</th></tr></thead><tbody>{filas_cmd}</tbody></table></div>

<div class="card"><h2>2. Cómo está construida (arquitectura por capas)</h2>
<p>El módulo de <b>tareas</b> es el piloto de <b>DDD-lite</b> (Domain-Driven Design, versión ligera para aprender). La lógica se separó en tres capas; <code>eva/tareas.py</code> quedó como <b>fachada</b> con la misma API, así nada del resto de Eva se rompió.</p>
<div class="layers">
  <div class="layer l-dom"><h3>Dominio · <code>eva/dominio/</code></h3><span class="muted">La entidad <code>Tarea</code> y los value objects <code>Area</code>/<code>Prioridad</code>. Reglas puras, sin archivos ni red: se prueba sola.</span></div>
  <div class="arrow">↑ usa</div>
  <div class="layer l-app"><h3>Aplicación · <code>eva/aplicacion/</code></h3><span class="muted"><code>ServicioTareas</code>: los casos de uso. Recibe el repositorio y el reloj inyectados, no sabe de JSON.</span></div>
  <div class="arrow">↑ implementa el puerto</div>
  <div class="layer l-inf"><h3>Infraestructura · <code>eva/infraestructura/</code></h3><span class="muted"><code>RepositorioTareasJSON</code>: guarda en <code>data/tareas.json</code>. Para cambiar a SQLite bastaría otra clase con el mismo puerto.</span></div>
</div>
<p class="muted">Beneficio real: el dominio y los casos de uso se prueban sin tocar disco (ver <code>tests/test_dominio.py</code>, con un repositorio en memoria). El resto de módulos (escritorio, kali, github...) aún son funciones directas; se migrarán si aporta claridad.</p></div>

<div class="card"><h2>3. Glosario DDD</h2><dl class="gloss">{filas_gloss}</dl></div>

<div class="card"><h2>4. Cómo se construye cada cambio</h2>
<p>Un equipo de agentes coordinado por la sesión principal. Cada uno vigila la seguridad en su etapa; tú decides el merge y el push.</p>
<div class="flow">{flow}</div>
<p class="muted">Reglas en <code>.agents/NORMAS.md</code>; flujo en <code>.agents/FLUJO.md</code>. Una puerta mecánica (<code>.agents/verificar.py</code>) revisa sintaxis, que el núcleo use solo la librería estándar, que no haya secretos ni datos personales en lo publicable, y que las pruebas pasen.</p></div>

<div class="card"><h2>5. Seguridad y privacidad</h2>
<ul class="muted" style="margin:0;padding-left:20px;line-height:1.9">
<li>Eva <b>nunca</b> mueve, borra, apaga ni publica por su cuenta: solo con un comando tuyo.</li>
<li><code>config.json</code> y <code>data/</code> son personales y no se suben a git.</li>
<li>En el chat, el modelo solo tiene herramientas de lectura; los errores no le filtran rutas ni tokens.</li>
<li>Hack The Box: solo se publican write-ups de máquinas retiradas, sin flags, IPs ni credenciales.</li>
</ul></div>
</div></body></html>"""


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/":
            cuerpo = pagina()
        elif ruta == "/github":
            cuerpo = pagina_github()
        elif ruta == "/aprende":
            cuerpo = pagina_aprende()
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
        pass  # sin ruido en la consola


def iniciar(puerto=8750):
    # Solo 127.0.0.1: nunca accesible desde otra máquina de la red.
    with socketserver.TCPServer(("127.0.0.1", puerto), _Handler) as s:
        print(f"Eva está en http://127.0.0.1:{puerto}  (Ctrl+C para detener)")
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            print("\nPanel detenido.")
