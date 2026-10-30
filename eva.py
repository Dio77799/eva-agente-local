"""Eva - punto de entrada. Ejecuta `python eva.py --help` para ver los comandos."""
import argparse
import sys

from eva import contenido, escritorio, kali, llm, proyectos, resumen, tareas

sys.stdout.reconfigure(encoding="utf-8")


def cmd_tareas(a):
    if a.accion == "nueva":
        print("Creada:", tareas.formato(tareas.agregar(" ".join(a.texto), a.area, a.prioridad)))
    elif a.accion == "hecha":
        t = tareas.completar(a.texto[0])
        print("Hecha:", tareas.formato(t) if t else "no existe ese id")
    else:
        lista = tareas.listar(a.area, todas=a.todas)
        print("\n".join(tareas.formato(t) for t in lista) or "Sin tareas pendientes.")


def cmd_escritorio(a):
    hallazgos = escritorio.analizar()
    for tipo in sorted({h["tipo"] for h in hallazgos}):
        grupo = [h for h in hallazgos if h["tipo"] == tipo]
        print(f"\n[{tipo.upper()}] ({len(grupo)}) -> {grupo[0]['sugerencia']}")
        for h in grupo:
            print("   -", h["item"])
    if a.tareas:
        creadas = escritorio.crear_tareas(hallazgos)
        print(f"\nSe crearon/actualizaron {len(creadas)} tareas en el área 'escritorio'.")
    print("\nEva no movió nada. Tú decides qué hacer con cada grupo.")


def cmd_proyectos(a):
    if a.github:
        for r in proyectos.repos_github():
            estado = ", ".join(r["mejoras"]) or "ok"
            print(f"{r['visibility']:8} {r['name']:35} {estado}")
        return
    print("Analizando proyectos (puede tardar un poco)...")
    for p in sorted(proyectos.informe(), key=lambda x: x["veredicto"]):
        remoto = p.get("remoto") or "sin remoto"
        print(f"\n* {p['nombre']}  ->  {p['veredicto']}")
        print(f"    {p['ruta']} | {remoto} | cambios sin commit: {p.get('cambios_sin_commit', '-')}")
        for rel, motivo in p.get("sensibles", [])[:5]:
            print(f"      ! {rel} ({motivo})")


def cmd_kali(a):
    if a.accion == "encender":
        print(kali.encender(a.sin_ventana))
    elif a.accion == "apagar":
        print(kali.apagar())
    elif a.accion == "snapshot":
        print(kali.snapshot(a.nombre))
    elif a.accion == "vpn":
        print(kali.guia_vpn())
    else:
        e = kali.estado()
        print(f"{e['vm']}: {'ENCENDIDA' if e['encendida'] else 'apagada'}")
        print("Snapshots:", ", ".join(e["snapshots"]) or "ninguno")


def cmd_htb(a):
    if a.accion == "nueva":
        print("Notas creadas en:", kali.nueva_maquina(a.nombre, a.ip, a.dificultad, a.sistema))
    elif a.accion == "post":
        archivo = kali.HTB / f"{a.nombre.lower()}.md"
        try:
            print("Borrador:", contenido.borrador_htb(archivo, usar_llm=a.llm))
        except (ValueError, FileNotFoundError) as e:
            print("No se generó:", e)
    else:
        for m in kali.maquinas():
            print(f"{m['maquina']:20} {m['estado']:10} {m['archivo']}")


def main():
    p = argparse.ArgumentParser(prog="eva", description="Eva, tu agente personal")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("hoy", help="resumen del día").add_argument("--rapido", action="store_true")
    sub.add_parser("chat", help="conversar con Eva (Ollama local)")

    t = sub.add_parser("tareas", help="ver / crear / completar tareas")
    t.add_argument("accion", nargs="?", choices=["ver", "nueva", "hecha"], default="ver")
    t.add_argument("texto", nargs="*")
    t.add_argument("-a", "--area", default=None)
    t.add_argument("-p", "--prioridad", type=int, default=2, choices=[1, 2, 3])
    t.add_argument("--todas", action="store_true")

    sub.add_parser("escritorio", help="analizar el escritorio").add_argument(
        "--tareas", action="store_true", help="crear tareas con las sugerencias")

    sub.add_parser("proyectos", help="proyectos locales y privacidad").add_argument(
        "--github", action="store_true", help="auditar tus repos en GitHub")

    k = sub.add_parser("kali", help="VM de Kali y VPN de HTB")
    k.add_argument("accion", nargs="?", default="estado",
                   choices=["estado", "encender", "apagar", "snapshot", "vpn"])
    k.add_argument("--sin-ventana", action="store_true")
    k.add_argument("--nombre")

    h = sub.add_parser("htb", help="cuaderno de máquinas HTB y posts")
    h.add_argument("accion", nargs="?", default="ver", choices=["ver", "nueva", "post"])
    h.add_argument("nombre", nargs="?")
    h.add_argument("--ip", default="")
    h.add_argument("--dificultad", default="")
    h.add_argument("--sistema", default="")
    h.add_argument("--llm", action="store_true", help="pulir el post con Ollama")

    a = p.parse_args()
    if a.cmd == "hoy":
        print(resumen.hoy(a.rapido))
    elif a.cmd == "chat":
        llm.conversar()
    elif a.cmd in ("htb",) and a.accion != "ver" and not a.nombre:
        p.error("indica el nombre de la máquina")
    elif a.cmd:
        globals()[f"cmd_{a.cmd}"](a)
    else:
        print(resumen.hoy(rapido=True))
        print("\n(`python eva.py --help` para ver todo lo que sé hacer)")


if __name__ == "__main__":
    main()
