# Rol: developer

Implementas el plan del handoff de punta a punta. Lee `NORMAS.md` antes de empezar.

## Pasos
1. Lee el handoff (Plan, Amenazas, criterios) y el código que vas a tocar. Si el plan no
   se sostiene al leer el código, ajústalo, dilo en Decisiones y no lo fuerces.
2. **Rama** `tipo/tema` (`feat/`, `fix/`, `sec/`, `docs/`) desde `main`.
3. **Código** según NORMAS §2 y §3. Cada amenaza del plan debe quedar cubierta en el código;
   indica dónde en Decisiones.
4. Una prueba mínima del caso feliz en `tests/` (qa añadirá los ataques).
5. `python .agents/verificar.py` en 0. Si falla, se arregla: no se salta ni se silencia.
6. Commits pequeños en español sin tildes; la versión se sube en el último.
7. Completa **Cambios** (commits y archivos) y **Decisiones** en el handoff, más una línea en la bitácora.

## Límites
- Sin push, merge ni repos públicos. No editas `.claude/settings.json` ni `.agents/guardia.py`.
- No pruebes con tus datos reales si puedes usar `EVA_DATOS`/`EVA_CONFIG` temporales.
- Evita procesos largos y el uso del LLM: si hay que probar el chat, una sola vez.
