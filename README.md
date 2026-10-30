# Eva: agente personal local

Eva es una asistente de línea de comandos que corre 100 % en tu computadora:
organiza tus tareas, te dice qué sobra en el escritorio, audita qué proyectos puedes
publicar sin filtrar secretos, controla tu VM de Kali para practicar en Hack The Box y
convierte tus notas en borradores de posts sin datos sensibles.

- Sin dependencias: solo Python 3.10+ (librería estándar).
- IA opcional y local con [Ollama](https://ollama.com) (modelo con soporte de herramientas, ej. `qwen3:8b`).
- Opcional: `gh` (GitHub CLI) y VirtualBox.

## Instalación
```bash
git clone <este repo> && cd Eva
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
| `chat` | Conversación en lenguaje natural con herramientas (Ollama) |

## Estructura
```
eva.py               CLI
eva/                 módulos (cada función es reutilizable desde Airflow u otro agente)
airflow/dags/        orquestación programada (fase 2)
data/                tus datos: tareas, notas HTB, borradores, bitácora (no se publica)
```

## Licencia
MIT
