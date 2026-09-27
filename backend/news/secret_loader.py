"""Carga segura de secretos desde archivos.

Nunca imprime, registra, expone ni incluye el valor del secreto
en excepciones o representaciones.
"""

from pathlib import Path


class SecretFileError(RuntimeError):
    """Error relacionado con la lectura de un archivo de secretos."""


def load_secret(path: Path) -> str:
    """Lee un secreto desde un archivo.

    Args:
        path: Ruta al archivo que contiene el secreto.

    Returns:
        El valor del secreto sin whitespace exterior.

    Raises:
        SecretFileError: Si el archivo no existe, no es regular o está vacío.
    """
    if not path.exists():
        raise SecretFileError(
            f"No se encontró el archivo de credencial: {path}. "
            "Consultá keys/README.md para instrucciones."
        )
    if not path.is_file():
        raise SecretFileError(
            f"La ruta no es un archivo regular: {path}."
        )
    raw = path.read_bytes()
    decoded = raw.decode("utf-8").strip()
    if not decoded:
        raise SecretFileError(
            f"El archivo de credencial está vacío: {path}. "
            "Debe contener únicamente el valor del secreto."
        )
    return decoded


def check_secret_file(path: Path) -> str:
    """Verifica el estado de un archivo de secretos sin revelar su contenido.

    Args:
        path: Ruta al archivo de secretos.

    Returns:
        "configured" si existe, es regular y no está vacío.
        "missing" si no existe.
        "invalid" si existe pero está vacío.
    """
    if not path.exists():
        return "missing"
    if not path.is_file():
        return "invalid"
    if not path.read_bytes().strip():
        return "invalid"
    return "configured"