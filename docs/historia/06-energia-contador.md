# Energía (Contador)
## Qué hicimos (técnico)
- eva/contador.py mide el tiempo REAL de cómputo de cada consulta (time.monotonic en llm.responder) y lo convierte a energía (vatios asumidos, config) y a Lempiras (tarifa, config). Totales en data/contador.json, tolerante a archivo corrupto.
- Módulo Contador con totales y un conversor kWh -> Lempiras.
## Utilidad
- Saber si correr la IA en local sale rentable. Dato real medido: ~0.17 Wh por consulta, cerca de 0.0007 Lempiras (energía despreciable).
