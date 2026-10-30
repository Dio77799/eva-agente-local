# Eva · guía para agentes

Cualquier agente (Claude Code, Copilot, un agente local) que trabaje en este repo:

1. Lee [`.agents/NORMAS.md`](.agents/NORMAS.md): arquitectura, código y **seguridad**.
2. Sigue [`.agents/FLUJO.md`](.agents/FLUJO.md): planner → developer → qa → reviewer, coordinados por un orquestador.
3. Los roles están en [`.agents/agentes/`](.agents/agentes/).
4. Antes de dar algo por terminado: `python .agents/verificar.py` en 0.

Resumen de reglas: Eva nunca mueve, borra ni publica por su cuenta; el núcleo usa solo la
librería estándar; `config.json` y `data/` son personales y no se suben; el LLM solo tiene
herramientas de lectura o de bajo impacto; HTB solo con máquinas retiradas.
