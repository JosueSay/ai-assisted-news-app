"""Conexión a MongoDB para la aplicación de noticias.

Proporciona un cliente y una base de datos de MongoDB configurados
a partir de la configuración de noticias.

Separada completamente de assistant/.
"""

from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from .config import NewsDatabaseConfigurationError, NewsSettings
from .secret_loader import SecretFileError, load_secret


class NewsDatabaseError(RuntimeError):
    """Error de conexión o lectura de la base de datos de noticias."""


def _build_client(uri: str, timeout_ms: int) -> MongoClient:
    return MongoClient(
        uri,
        appname="ai-assisted-news",
        serverSelectionTimeoutMS=timeout_ms,
        uuidRepresentation="standard",
    )


def get_news_client(settings: NewsSettings) -> MongoClient:
    """Crea un MongoClient para la aplicación de noticias.

    El URI se carga desde el archivo configurado (keys/mongodb_uri por defecto).
    El cliente NO se autentica hasta la primera operación.

    Args:
        settings: Configuración de la base de datos de noticias.

    Returns:
        MongoClient configurado.

    Raises:
        NewsDatabaseError: Si no se puede leer el secreto.
    """
    try:
        uri = load_secret(settings.mongodb_uri_file)
    except SecretFileError as error:
        raise NewsDatabaseError(str(error)) from error
    return _build_client(uri, settings.mongodb_timeout_ms)


def get_news_database(settings: NewsSettings):
    """Obtiene la base de datos de noticias.

    Es equivalente a get_news_client(settings)[settings.mongodb_database].

    Args:
        settings: Configuración de la base de datos de noticias.

    Returns:
        Base de datos de MongoDB.
    """
    return get_news_client(settings)[settings.mongodb_database]


def ping_database(settings: NewsSettings) -> dict[str, str]:
    """Ejecuta un ping contra la base de datos de noticias.

    Útil para verificar conectividad. No crea colecciones ni modifica datos.

    Args:
        settings: Configuración de la base de datos de noticias.

    Returns:
        Diccionario con estado de la conexión.

    Raises:
        NewsDatabaseError: Si no se puede conectar.
    """
    client = get_news_client(settings)
    try:
        database = client[settings.mongodb_database]
        database.command("ping")
        return {
            "status": "ok",
            "database": settings.mongodb_database,
        }
    except PyMongoError as error:
        raise NewsDatabaseError(
            "No fue posible conectar con MongoDB. "
            "Verificá la URI en keys/mongodb_uri y la conectividad de red."
        ) from error
    finally:
        client.close()


def close_client(client: MongoClient) -> None:
    """Cierra un MongoClient de forma segura."""
    client.close()