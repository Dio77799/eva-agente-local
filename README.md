# Eva: agente personal local

Eva es una asistente que corre **100 % en tu computadora**: organiza tus tareas, te dice
qué sobra en el escritorio, audita qué proyectos puedes publicar sin filtrar secretos,
controla tu VM de Kali para practicar en Hack The Box y convierte tus notas en borradores
de posts sin datos sensibles. Tiene línea de comandos, un chat con IA local y un panel web.

- Sin dependencias: solo Python 3.10+ (librería estándar).
- IA opcional y local con [Ollama](https://ollama.com) (modelo con herramientas, ej. `qwen3:8b`).
- Opcional: `gh` (GitHub CLI) y VirtualBox.

## Instalación
```bash
git clone <este repo> && cd eva-agente-local
cp config.example.json config.json   # edítalo con tus rutas
python eva.py --help
```

## Comandos
| Comando | Qué hace |
|---|---|
| `python eva.py` / `hoy` | Resumen del día (`--rapido` sin consultar GitHub) |
| `tareas [ver\|nueva\|hecha]` | `tareas nueva Subir demo -a github -p 1`, `tareas hecha 3` |
| `escritorio [--tareas]` | Clasifica el escritorio y sugiere qué hacer (no mueve nada) |
| `proyectos [--github]` | Proyectos locales: privado / con secretos / candidato. `--github` audita tus repos |
| `kali [estado\|encender\|apagar\|snapshot\|vpn]` | Control de la VM y guía de la VPN |
| `htb [ver\|nueva\|post] <maquina>` | Cuaderno de máquinas y borrador de post (`--llm` para pulirlo) |
| `chat` | Conversación en lenguaje natural con herramientas (Ollama); al salir libera el modelo |
| `servidor [--puerto 8750]` | Panel web local de solo lectura (`http://127.0.0.1:8750`) |

## Panel web
`python eva.py servidor` abre un panel en `127.0.0.1` (solo tu equipo, solo lectura):
- **Panel**: tareas, estado del escritorio y de la VM de Kali.
- **Entender Eva** (`/aprende`): guía del proyecto, la arquitectura por capas y un glosario DDD.
- **GitHub**: tus repos y qué les falta (descripción, topics).

## Arquitectura
El módulo de **tareas** es un piloto de DDD ligero, separado en capas; `eva/tareas.py` es la
fachada que conserva la API pública:
```
eva/dominio/          reglas puras: entidad Tarea, value objects Area/Prioridad, puertos
eva/aplicacion/       casos de uso (ServicioTareas), con repositorio y reloj inyectados
eva/infraestructura/  detalles técnicos (RepositorioTareasJSON)
eva/                  resto de módulos (escritorio, kali, proyectos, llm, servidor...)
eva.py                CLI
airflow/dags/         orquestación programada (fase 2)
data/                 tus datos: tareas, notas HTB, borradores, bitácora (no se publica)
```
El dominio y los casos de uso se prueban **sin tocar disco** (ver `tests/`).

## Cómo se construye
Un equipo de agentes (planner → developer → qa → reviewer) coordinado por la sesión
principal, con la seguridad en cada etapa. Ver [`AGENTS.md`](AGENTS.md) y
[`.agents/`](.agents/). Antes de dar algo por terminado: `python .agents/verificar.py`.

## Seguridad y privacidad
- Eva **nunca** mueve, borra, apaga ni publica por su cuenta: solo con un comando tuyo.
- `config.json` y `data/` son personales y no se suben a git.
- En el chat, el modelo solo tiene herramientas de lectura; los errores no filtran rutas ni tokens.
- Hack The Box: solo se publican write-ups de máquinas retiradas, sin flags, IPs ni credenciales.

## Licencia
[MIT](LICENSE)
