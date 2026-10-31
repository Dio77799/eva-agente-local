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
"""

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
<h1>GitHub</h1><div class="sub"><a href="/">← panel</a></div>{cuerpo}</div></body></html>"""


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/":
            cuerpo = pagina()
        elif ruta == "/github":
            cuerpo = pagina_github()
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
