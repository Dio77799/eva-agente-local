# Seguridad
## Qué hicimos (técnico)
- Seguridad en cada etapa (NORMAS §3). verificar.py: sintaxis, solo-stdlib, sin eval/exec/shell, sin secretos ni datos personales en lo publicable, pruebas. guardia.py: hook que bloquea comandos peligrosos.
- Panel: solo 127.0.0.1, token anti-CSRF por ejecución y validación de Host local en GET y POST; acciones por whitelist y de bajo impacto.
- Agente Hank: auditoría del propio sistema (dependencias de terceros, ejecución peligrosa, conexiones solo locales, secretos, privacidad en git, herramientas del chat, panel).
- config.json y data/ nunca van a git; los errores del chat no filtran rutas ni tokens.
## Utilidad
- Eva no se vuelve un riesgo: no filtra datos, no usa terceros ocultos, no actúa por su cuenta.
