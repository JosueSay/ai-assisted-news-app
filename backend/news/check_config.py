"""Comprobación segura de configuración de base de datos.

Permite verificar el estado de la configuración sin exponer secretos.
"""

import sys

from .config import get_news_settings
from .secret_loader import check_secret_file


def run_check() -> str:
    """Verifica la configuración de la DB de noticias y reporta el estado.

    Returns:
        Mensaje legible con el estado.
    """
    settings = get_news_settings()

    uri_status = check_secret_file(settings.mongodb_uri_file)

    lines = [
        "=== AI Assisted News — DB Check ===",
        f"Database:             {settings.mongodb_database}",
        f"URI file:             {settings.mongodb_uri_file}",
        f"MongoDB credential:   {uri_status}",
        f"MongoDB required:     {'yes' if settings.mongodb_required else 'no'}",
        f"Timeout (ms):         {settings.mongodb_timeout_ms}",
    ]

    if uri_status == "missing":
        lines.append("")
        lines.append(
            "  La credencial MongoDB no está configurada. "
            "Creá keys/mongodb_uri con la URI de Atlas."
        )
        lines.append("  Ver keys/README.md para instrucciones.")

    return "\n".join(lines)


def main() -> None:
    result = run_check()
    print(result)
    uri_status = check_secret_file(get_news_settings().mongodb_uri_file)
    sys.exit(0 if uri_status == "configured" else 1)


if __name__ == "__main__":
    main()