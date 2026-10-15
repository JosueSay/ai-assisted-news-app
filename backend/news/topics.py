"""Catálogo estático versionado de topics.

Los topics NO son una colección MongoDB: `users.onboarding.selectedTopics`,
`users.inferredInterests[].topic` y `news.topics` son strings libres que
comparten este vocabulario para evitar variantes del mismo concepto
(`tecnologia` / `Tecnología` / `technology` / `tech`).

Los valores persistidos son minúsculas, sin espacios y estables.
La única normalización definida es recorte de espacios y minúsculas;
no hay traducciones automáticas ni plegado de acentos.
"""

from __future__ import annotations

TOPICS: tuple[str, ...] = (
    "actualidad",
    "tecnologia",
    "ciencia",
    "economia",
    "negocios",
    "politica",
    "deportes",
    "salud",
    "educacion",
    "cultura",
    "entretenimiento",
    "medio_ambiente",
    "seguridad",
    "internacional",
)


def get_topics() -> tuple[str, ...]:
    """Devuelve los topics permitidos en orden estable."""
    return TOPICS


def is_valid_topic(value: str) -> bool:
    """Indica si el valor ya es un topic canónico del catálogo."""
    return isinstance(value, str) and value in TOPICS


def normalize_topic(value: str) -> str:
    """Normaliza recorte de espacios y minúsculas y valida contra el catálogo.

    No traduce ni pliega acentos: `Tecnología` no se convierte en `tecnologia`.
    """
    if not isinstance(value, str):
        raise ValueError("topic debe ser un string del catálogo")
    canonical = value.strip().lower()
    if canonical not in TOPICS:
        raise ValueError(f"topic no permitido: {value.strip()}")
    return canonical
