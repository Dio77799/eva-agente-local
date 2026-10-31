# Arquitectura
## Qué hicimos (técnico)
- Núcleo en Python con SOLO la librería estándar (sin dependencias): fácil de auditar y de correr en cualquier equipo.
- Piloto DDD-lite en tareas, en capas: dominio (entidad Tarea + value objects Area/Prioridad, reglas puras), aplicación (ServicioTareas, casos de uso con repositorio y reloj inyectados) e infraestructura (RepositorioTareasJSON). eva/tareas.py quedó como fachada con la misma API.
- verificar.py comprueba que el núcleo siga solo-stdlib (rglob sobre eva/).
## Utilidad
- El dominio se prueba sin tocar disco (repo en memoria): pruebas rápidas y confiables.
- Cambiar de JSON a SQLite no tocaría las reglas (inversión de dependencias).
- Aprendizaje real de DDD aplicado a un proyecto propio.
