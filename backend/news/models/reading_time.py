"""Función pura para calcular el tiempo de lectura estimado.

Fórmula: estimatedReadingMinutes = ceil(wordCount / 200)
Velocidad de referencia: 200 palabras por minuto.
"""

import math


def count_words(text: str) -> int:
    """Cuenta las palabras en un texto.

    Una palabra es cualquier secuencia separada por espacios en blanco.
    Coincide con la definición del diseño: solo el cuerpo (content),
    no incluye title, summary, pies de imagen ni créditos.
    """
    return len(text.split())


def estimate_reading_minutes(word_count: int) -> int:
    """Calcula los minutos estimados de lectura.

    Args:
        word_count: Cantidad de palabras.

    Returns:
        Minutos enteros redondeados hacia arriba. Mínimo 1.
    """
    if word_count <= 0:
        return 1
    return max(1, math.ceil(word_count / 200))


def compute_reading_time(content: str) -> tuple[int, int]:
    """Calcula wordCount y estimatedReadingMinutes a partir del contenido.

    Args:
        content: Cuerpo de la noticia.

    Returns:
        Tupla (wordCount, estimatedReadingMinutes).
    """
    wc = count_words(content)
    return wc, estimate_reading_minutes(wc)