"""Umbrales de la compuerta HITL. ARCHIVO PROTEGIDO: no se edita sin autorización explícita.

p >= TAU_AUTO            -> se ejecuta automáticamente
TAU_REV <= p < TAU_AUTO  -> pasa a revisión humana
p < TAU_REV              -> se escala o rechaza (cola de fallidos)

Una probabilidad nunca concede autorización por sí sola: si falla un invariante
de negocio, se exige revisión humana sin importar el valor de p.
"""

TAU_AUTO: float = 0.85
TAU_REV: float = 0.60
