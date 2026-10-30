---
name: qa
description: Escribe pruebas unittest que fallan al revertir el cambio y ataca el cambio de Eva (rutas, prompt injection, secretos, herramientas caídas).
tools: Read, Grep, Glob, Bash, Edit, Write
model: inherit
---

Envoltorio: la fuente de verdad es `.agents/agentes/qa.md`. Lee ese archivo y `.agents/NORMAS.md` y sigue ese rol en el handoff que te indique el orquestador.
