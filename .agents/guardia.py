"""Hook PreToolUse de Claude Code: niega comandos peligrosos para Eva.

Lee el JSON de la llamada por stdin. Sale con 2 (negado; el motivo le llega a Claude) o 0.
Solo una persona edita este archivo (NORMAS §6).
"""
import json
import re
import sys

REGLAS = [
    (r"--no-verify|core\.hooksPath", "no se saltan los hooks de git"),
    (r"git\b[^;&|]*\bpush\b", "el push lo hace una persona (NORMAS §6)"),
    (r"git\b[^;&|]*\badd\b[^;&|]*(-f\b|--force)", "git add -f fuerza archivos ignorados"),
    (r"git\b[^;&|]*\badd\b[^;&|]*(config\.json|\bdata\b|handoffs|bitacora|PENDIENTES)",
     "config.json, data/ y el estado de .agents son personales"),
    (r"git\b[^;&|]*\b(merge|rebase)\b[^;&|]*\bmain\b|git\b[^;&|]*checkout\b[^;&|]*\bmain\b[^;&|]*&&[^;&|]*merge",
     "el merge a main lo decide una persona"),
    (r"git\b[^;&|]*\breset\b[^;&|]*--hard|git\b[^;&|]*\bclean\b[^;&|]*-[a-z]*f",
     "comando destructivo de git: pídelo a la persona"),
    (r"\bgh\b[^;&|]*\b(repo\s+(create|edit|delete)|release|gist|pr\s+(create|merge))",
     "publicar en GitHub lo decide una persona"),
    (r"\brm\b[^;&|]*-[a-z]*r[^;&|]*\b(data|Desktop|Escritorio)\b|Remove-Item[^;&|]*(data|Desktop)",
     "no se borran datos del usuario"),
]
ESCRIBE = r"(\brm\b|\bmv\b|\bcp\b|>|sed\s+-i|Set-Content|Out-File|Remove-Item|Move-Item|tee\b)"


def main():
    try:
        datos = json.load(sys.stdin)
    except ValueError:
        return 0  # entrada inesperada: no bloquea el trabajo normal
    comando = str((datos.get("tool_input") or {}).get("command", ""))
    for patron, motivo in REGLAS:
        if re.search(patron, comando, re.I):
            print(f"BLOQUEADO por .agents/guardia.py: {motivo}.", file=sys.stderr)
            return 2
    if re.search(r"guardia\.py|\.claude[/\\]settings", comando) and re.search(ESCRIBE, comando):
        print("BLOQUEADO: la guardia y settings.json solo los edita una persona.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
