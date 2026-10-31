"""Contador: estima el consumo de energía del chat (Ollama corre el modelo en tu
equipo) y lo convierte a Lempiras, para ver si sale rentable.

El consumo se estima como: vatios asumidos (config `energia.watts`) × tiempo REAL de
cómputo medido. El costo = kWh × tarifa (`energia.lps_kwh`). Ambos parámetros se editan
en config.json. Los totales se guardan en data/contador.json (local).
"""
from .comun import ahora, config, guardar_json, leer_json


def _cfg():
    e = config().get("energia", {})
    return float(e.get("watts", 40)), float(e.get("lps_kwh", 4.0))


def _estado():
    defecto = {"consultas": 0, "wh": 0.0, "segundos": 0.0, "desde": ahora()}
    try:
        d = leer_json("contador.json", defecto)
        return d if isinstance(d, dict) else defecto
    except (ValueError, OSError):  # archivo corrupto: se empieza de nuevo sin romper
        return defecto


def registrar(segundos):
    """Suma una consulta: Wh = watts × horas de cómputo. Devuelve los Wh de esta consulta."""
    watts, _ = _cfg()
    segundos = max(float(segundos), 0.0)
    wh = watts * (segundos / 3600.0)
    d = _estado()
    d["consultas"] += 1
    d["wh"] += wh
    d["segundos"] += segundos
    guardar_json("contador.json", d)
    return wh


def convertir(kwh):
    """Convierte kWh a Lempiras con la tarifa configurada."""
    _, lps_kwh = _cfg()
    try:
        return float(kwh) * lps_kwh
    except (ValueError, TypeError):
        return 0.0


def resumen():
    watts, lps_kwh = _cfg()
    d = _estado()
    kwh = d["wh"] / 1000.0
    lps = kwh * lps_kwh
    return {
        "consultas": d["consultas"],
        "kwh": kwh,
        "lps": lps,
        "watts": watts,
        "lps_kwh": lps_kwh,
        "segundos": d["segundos"],
        "desde": d.get("desde", ""),
        "lps_por_consulta": (lps / d["consultas"]) if d["consultas"] else 0.0,
    }
