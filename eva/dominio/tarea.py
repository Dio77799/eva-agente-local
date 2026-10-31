"""La entidad Tarea y sus value objects (Area, Prioridad), con sus invariantes."""
import enum
from dataclasses import dataclass


class Area(enum.Enum):
    """Value object: el área a la que pertenece una tarea."""
    GENERAL = "general"
    ESCRITORIO = "escritorio"
    GITHUB = "github"
    HTB = "htb"
    CONTENIDO = "contenido"
    ESTUDIO = "estudio"

    @classmethod
    def coerce(cls, valor):
        """Convierte un valor a Area; uno desconocido cae en GENERAL (nunca lanza)."""
        if isinstance(valor, cls):
            return valor
        try:
            return cls(str(valor).strip().lower())
        except ValueError:
            return cls.GENERAL


class Prioridad(enum.IntEnum):
    """Value object: 1 alta, 2 media, 3 baja."""
    ALTA = 1
    MEDIA = 2
    BAJA = 3

    @classmethod
    def coerce(cls, valor):
        try:
            return cls(int(valor))
        except (ValueError, TypeError):
            return cls.MEDIA


@dataclass
class Tarea:
    """Entidad: tiene identidad (id) y protege sus propias reglas."""
    id: int
    titulo: str
    area: Area = Area.GENERAL
    prioridad: Prioridad = Prioridad.MEDIA
    estado: str = "pendiente"
    creada: str = ""
    hecha: "str | None" = None
    notas: str = ""

    def __post_init__(self):
        self.titulo = str(self.titulo).strip()
        if not self.titulo:
            raise ValueError("una tarea necesita un título")
        self.area = Area.coerce(self.area)
        self.prioridad = Prioridad.coerce(self.prioridad)

    @property
    def pendiente(self):
        return self.estado == "pendiente"

    def completar(self, cuando):
        """Regla: completar fija el estado y la fecha. No se puede 'descompletar' aquí."""
        self.estado = "hecha"
        self.hecha = cuando

    def a_dict(self):
        """Serializa a dict (la forma que esperan el CLI, el chat y la web)."""
        return {"id": self.id, "titulo": self.titulo, "area": self.area.value,
                "prioridad": int(self.prioridad), "estado": self.estado,
                "creada": self.creada, "hecha": self.hecha, "notas": self.notas}

    @classmethod
    def desde_dict(cls, d):
        return cls(id=d["id"], titulo=d["titulo"], area=d.get("area", "general"),
                   prioridad=d.get("prioridad", 2), estado=d.get("estado", "pendiente"),
                   creada=d.get("creada", ""), hecha=d.get("hecha"), notas=d.get("notas", ""))
