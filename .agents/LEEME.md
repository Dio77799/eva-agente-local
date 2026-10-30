# .agents · el equipo que construye Eva

Cuatro agentes con normas compartidas, coordinados por la sesión principal (el **orquestador**).
Adaptado de un flujo developer/reviewer de un equipo real, con la seguridad como parte de cada rol.

| Archivo | Para qué |
|---|---|
| `NORMAS.md` | Normas en una página. **Todo agente lo lee primero** |
| `FLUJO.md` | Orquestación: planner → developer → qa → reviewer, tamaños y plantilla del handoff |
| `agentes/` | Los cuatro roles (fuente de verdad). `.claude/agents/` solo los envuelve |
| `verificar.py` | Comprobaciones mecánicas de todo cambio (salida 0 = ok) |
| `guardia.py` | Hook de Claude Code que niega comandos peligrosos (push forzado, `--no-verify`, subir datos personales...) |
| `handoffs/` · `bitacora/` · `PENDIENTES.md` | Estado de trabajo. **Locales: no se publican** |

Los roles están escritos en Markdown sin dependencias de una herramienta concreta: Claude Code
los usa vía `.claude/agents/`, y otro orquestador (Airflow, un agente con Ollama) puede leerlos igual.
