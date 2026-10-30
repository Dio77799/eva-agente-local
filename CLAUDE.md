# Eva · instrucciones para el orquestador (sesión principal de Claude Code)

## Al empezar
1. `git status` y `git log --oneline -5` (el código manda sobre los documentos).
2. Lee `.agents/NORMAS.md`, `.agents/PENDIENTES.md` y la bitácora más reciente de `.agents/bitacora/`.

## Cada pedido
Sigue `.agents/FLUJO.md`. Decide el tamaño y usa **solo los agentes necesarios**
(`planner`, `developer`, `qa`, `reviewer`): un cambio trivial no necesita equipo. Crea el
handoff, lanza cada agente indicándole la ruta del handoff y pega el informe del reviewer.
Consulta a la persona solo en los casos de NORMAS §5.

## Al terminar
Resume a la persona (veredicto, pruebas, riesgos) y propón el commit/merge: lo ejecuta
solo con su visto bueno. Una línea en la bitácora del día y el estado en `PENDIENTES.md`.
