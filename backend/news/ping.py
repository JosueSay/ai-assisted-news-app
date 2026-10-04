"""Comando de prueba de conexión MongoDB.

Ejecuta un ping contra la base de datos de noticias.
No crea colecciones, no inserta ni modifica datos.
"""

from .config import get_news_settings
from .database import NewsDatabaseError, ping_database


def run_ping() -> str:
    """Ejecuta ping y devuelve un mensaje sanitizado.

    Returns:
        Mensaje con el resultado del ping.

    Raises:
        SystemExit: Si la conexión falla.
    """
    settings = get_news_settings()
    try:
        result = ping_database(settings)
        return (
            f"MongoDB connection: OK\n"
            f"Database: {result['database']}"
        )
    except NewsDatabaseError as error:
        return f"MongoDB connection: FAILED\n{error}"


def main() -> None:
    print(run_ping())


if __name__ == "__main__":
    main()