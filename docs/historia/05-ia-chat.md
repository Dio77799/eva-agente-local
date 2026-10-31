# IA y chat
## Qué hicimos (técnico)
- Chat con Ollama local (sin librerías externas, vía urllib). llm.responder reutiliza _turno: hasta 5 rondas de herramientas (tool-calling) por pregunta.
- Herramientas de solo lectura o bajo impacto; lo que el modelo lee se trata como dato (anti prompt-injection); los errores no llegan al modelo.
- Modelo configurable. Se comprobó que un 3B es rápido pero débil en tool-calling; qwen3:8b es el adecuado para el chat.
## Utilidad
- Le hablas en lenguaje natural y Eva ejecuta con sus herramientas (tipo asistente), todo en local y gratis.
