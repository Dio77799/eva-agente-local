# Agentes y Oficina
## Qué hicimos (técnico)
- Flujo con agentes: planner -> developer -> qa -> reviewer, coordinados por un orquestador. Roles en .agents/agentes/*.md y normas compartidas (NORMAS.md, FLUJO.md).
- Cada cambio pasa por un handoff (un archivo por workstream) donde cada agente escribe su parte.
- Módulo Oficina: cada agente con apodo y un semáforo de estado derivado de qué secciones del último handoff están llenas, más un registro de actividad desde la bitácora.
## Utilidad
- Calidad: ningún cambio se da por bueno sin plan, pruebas y una revisión independiente.
- Visibilidad: se ve quién hace qué y en qué estado va el trabajo.
