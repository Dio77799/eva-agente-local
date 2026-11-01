"""KELLY (agente de ánimo): lee cómo le escribes a Eva y ajusta el TONO de la respuesta.

Solo reglas locales (sin modelo, sin red): mira el último mensaje del usuario y busca
señales de frustración, prisa, dudas o buen ánimo. Devuelve una línea de tono que se
añade al prompt de sistema del chat.

Privacidad: NUNCA guarda tu texto. En data/kelly.json solo quedan conteos por ánimo y
el último ánimo leído (para mostrarlo en la Oficina).
"""
import re
import unicodedata

from .comun import ahora, guardar_json, leer_json

# Señales por ánimo (texto ya normalizado: minúsculas y sin acentos).
SENALES = {
    # Sin "error", "otra vez" ni "mal": en un asistente de desarrollo/HTB salen a diario
    # sin frustración ("corrige este error 404", "hazlo otra vez con otro nombre").
    "frustrado": ["no funciona", "no sirve", "sigue sin", "sigue fallando", "sigue igual",
                  "no anda", "harto", "ya te dije", "no es eso", "nada que ver", "otra vez falla"],
    "con prisa": ["rapido", "urgente", "ya mismo", "corto", "breve", "resumido", "solo dime",
                  "sin rodeos", "apurate", "prisa"],
    "con dudas": ["no entiendo", "no se como", "no se que", "como hago","como se", "que significa", "explicame",
                  "no me queda claro", "confundido", "perdido"],
    "contento": ["gracias", "genial", "perfecto", "excelente", "buenisimo", "me gusta", "bien hecho",
                 "increible", "chido", "bacano", "va bien"],
}

TONOS = {
    "frustrado": "El usuario parece frustrado: reconoce el problema en una frase, sin disculpas "
                 "largas, y ve directo a la solución concreta.",
    "con prisa": "El usuario tiene prisa: responde en 1 a 3 líneas, solo lo esencial.",
    "con dudas": "El usuario tiene dudas: explica paso a paso, con palabras simples y un ejemplo.",
    "contento": "El usuario está de buen ánimo: mantén un tono cálido y cercano, sin exagerar.",
    "neutral": "",
}

ARCHIVO = "kelly.json"


def _normalizar(texto):
    t = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def leer(texto):
    """Devuelve el ánimo detectado en un mensaje: frustrado | con prisa | con dudas |
    contento | neutral. Frustración pesa más que el resto (es lo que más urge atender)."""
    crudo = str(texto or "")
    t = _normalizar(crudo)
    puntos = {a: sum(1 for s in senales if re.search(r"\b" + re.escape(s) + r"\b", t))
              for a, senales in SENALES.items()}
    letras = [c for c in crudo if c.isalpha()]
    # Gritar = frase larga en MAYÚSCULAS (no una sigla suelta como "NMAP" o "HTB").
    if len(letras) >= 20 and len(crudo.split()) >= 4 and sum(c.isupper() for c in letras) / len(letras) > 0.7:
        puntos["frustrado"] += 2  # escribir EN MAYÚSCULAS
    if "!!" in crudo:
        puntos["frustrado"] += 1
    if crudo.count("?") >= 2:
        puntos["con dudas"] += 1
    puntos["frustrado"] *= 1.5
    mejor = max(puntos, key=puntos.get)
    return mejor if puntos[mejor] > 0 else "neutral"


def tono(animo):
    return TONOS.get(animo, "")


def estado():
    """Para la Oficina: {'ultimo', 'cuando', 'conteos'} (vacío si aún no hay lecturas).
    Normaliza el archivo: un kelly.json editado o corrupto nunca rompe chat ni Oficina."""
    try:
        d = leer_json(ARCHIVO, {})
    except (ValueError, OSError):
        return {}
    if not isinstance(d, dict) or not isinstance(d.get("ultimo"), str):
        return {}
    conteos = d.get("conteos") if isinstance(d.get("conteos"), dict) else {}
    return {"ultimo": d["ultimo"], "cuando": str(d.get("cuando", "")),
            "conteos": {str(k): v for k, v in conteos.items()
                        if isinstance(v, int) and not isinstance(v, bool) and v >= 0}}


def registrar(animo):
    """Suma el ánimo a los conteos locales (sin texto) y lo deja como el último leído."""
    conteos = estado().get("conteos", {})
    conteos[animo] = conteos.get(animo, 0) + 1
    guardar_json(ARCHIVO, {"ultimo": animo, "cuando": ahora(), "conteos": conteos})


def ajustar(historial):
    """Lee el último mensaje del usuario, registra el ánimo y devuelve (animo, linea_de_tono)."""
    ultimo = next((m.get("content", "") for m in reversed(historial or [])
                   if m.get("role") == "user"), "")
    animo = leer(ultimo)
    try:
        registrar(animo)
    except Exception:  # KELLY nunca debe tumbar el chat: sin registro, el tono igual aplica
        pass
    return animo, tono(animo)
