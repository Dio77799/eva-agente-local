"""Puertos del dominio: interfaces que la infraestructura implementa.

El dominio dice QUÉ necesita (listar/guardar tareas) sin saber CÓMO se guarda.
Esto es inversión de dependencias: el detalle (JSON) depende de la interfaz, no al revés.
"""
from typing import Protocol

from .tarea import Tarea


class RepositorioTareas(Protocol):
    def listar(self) -> list[Tarea]:
        ...

    def guardar(self, tareas: list[Tarea]) -> None:
        ...
