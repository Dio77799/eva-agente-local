"""Resumen del día: lo que Eva te diría al encender la computadora."""
from . import escritorio, kali, tareas
from .comun import bitacora


def hoy(rapido=False):
    lineas = ["=== Buenos días, soy Eva ==="]

    pendientes = tareas.listar()
    lineas.append(f"\nTareas pendientes: {len(pendientes)}")
    lineas += ["  " + tareas.formato(t) for t in pendientes[:7]]
    if len(pendientes) > 7:
        lineas.append(f"  ... y {len(pendientes) - 7} más (`python eva.py tareas`)")

    try:
        k = kali.estado()
        lineas.append(f"\nKali: {'ENCENDIDA' if k['encendida'] else 'apagada'} "
                      f"| snapshots: {len(k['snapshots'])}")
    except (OSError, KeyError) as e:
        lineas.append(f"\nKali: no pude consultar VirtualBox ({e})")
    activas = [m["maquina"] for m in kali.maquinas() if m["estado"] == "activa"]
    if activas:
        lineas.append("HTB en curso: " + ", ".join(activas))

    hallazgos = escritorio.analizar()
    desorden = [h for h in hallazgos if h["tipo"] not in ("proyecto", "carpeta")]
    lineas.append(f"\nEscritorio: {len(hallazgos)} elementos, {len(desorden)} por ordenar")

    if not rapido:
        try:
            from . import proyectos
            repos = proyectos.repos_github()
            mejorar = [r for r in repos if r["visibility"] == "PUBLIC" and r["mejoras"]]
            lineas.append(f"\nGitHub: {len(repos)} repos, {len(mejorar)} públicos con mejoras pendientes")
            lineas += [f"  - {r['name']}: {', '.join(r['mejoras'])}" for r in mejorar]
        except Exception as e:
            lineas.append(f"\nGitHub: sin datos ({e})")

    bitacora("resumen_hoy")
    return "\n".join(lineas)
