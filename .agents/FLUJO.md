# Flujo de cada workstream · el orquestador es la sesión principal

| Paso | Quién | Resultado en `handoffs/AAAA-MM-DD-<tema>.md` |
|---|---|---|
| 0 | orquestador | Tamaño del cambio y agentes necesarios (abajo). Crea el handoff con el pedido de la persona |
| 1 | `planner` | **Plan** (máx. 15 líneas) + **Amenazas** (máx. 5) + criterios de aceptación. Si toca NORMAS §5: se detiene y el orquestador pregunta |
| 2 | `developer` | Rama `tipo/tema`, código, **Cambios** y **Decisiones** |
| 3 | `qa` | Prueba que falla al revertir + ataques de seguridad: **Pruebas** |
| 4 | `reviewer` | Una pasada solo de lectura: **Revisión**, con veredicto y hallazgos con severidad |
| 5 | orquestador | Si vuelve a desarrollo, otra ronda 2→4 (máx. 2 rondas; luego decide la persona). Si está listo: resume a la persona y propone el commit/merge |
| Siempre | quien cierra el paso | Una línea en `bitacora/AAAA-MM-DD.md` y el estado en `PENDIENTES.md` |

## Tamaños
- **Trivial** (texto, una línea): orquestador o developer, y `verificar.py`. Sin agentes extra.
- **Normal**: developer → qa → reviewer. El planner solo si hay más de un módulo o una duda de diseño.
- **Sensible** (NORMAS §5, seguridad, herramientas del LLM, datos del usuario): los cuatro, siempre.
- Si basta con correr una prueba, se corre sin agente.

## Reglas
- Un workstream por rama. Un cambio de seguridad va en su propio workstream.
- Los agentes se pasan el trabajo **solo por el handoff**: cada uno lee lo anterior y
  escribe su sección. El reviewer no edita: el orquestador pega su informe.
- Nada se da por hecho sin la salida de `verificar.py` y de la prueba pegada en el handoff.
- La persona decide el merge y el push (NORMAS §6).

## Plantilla del handoff
```markdown
# <tema> · <fecha>
Pedido: <lo que pidió la persona, literal y corto>
## Plan            (planner)
## Amenazas        (planner: qué podría salir mal en seguridad/privacidad y cómo se evita)
## Cambios         (developer: commits y archivos)
## Decisiones      (cualquiera: una línea cada una)
## Pruebas         (qa: comandos, salida resumida, contraprueba, ataques)
## Revisión        (reviewer: veredicto, hallazgos con severidad y cómo reproducirlos)
## Fuera de alcance
```
