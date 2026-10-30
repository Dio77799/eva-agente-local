"""FASE 2 (aún no se usa): Eva orquestada por Apache Airflow.

Airflow no corre nativo en Windows: se levanta con Docker o WSL2 y se monta esta
carpeta de Eva en el contenedor. Las tareas solo llaman a funciones de Eva, así
que todo lo que funciona por consola funcionará aquí igual.

Más adelante se puede sustituir `pulir_con_ia` por un operador del provider
common.ai de Airflow apuntando a Ollama.
"""
from datetime import datetime

from airflow.sdk import dag, task


@dag(schedule="0 8 * * 1-5", start_date=datetime(2026, 11, 1), catchup=False, tags=["eva"])
def eva_diaria():
    @task
    def revisar_escritorio():
        from eva import escritorio
        return len(escritorio.crear_tareas(escritorio.analizar()))

    @task
    def auditar_github():
        from eva import proyectos, tareas
        for r in proyectos.repos_github():
            if r["visibility"] == "PUBLIC" and r["mejoras"]:
                tareas.agregar(f"GitHub {r['name']}: {', '.join(r['mejoras'])}", "github", 2)

    @task
    def resumen(_a, _b):
        from eva import resumen
        return resumen.hoy()

    resumen(revisar_escritorio(), auditar_github())


eva_diaria()
