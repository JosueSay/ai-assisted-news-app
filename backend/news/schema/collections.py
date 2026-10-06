"""Colecciones físicas esperadas en MongoDB."""

from . import COLLECTIONS


def expected_collections() -> tuple[str, ...]:
    """Devuelve las siete colecciones aprobadas por el diseño."""
    return COLLECTIONS
