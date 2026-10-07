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
    admin_password_status = check_secret_file(settings.admin_password_file)

    lines = [
        "=== AI Assisted News — DB Check ===",
        f"Mode:                 {settings.mongodb_mode}",
        f"Database:             {settings.mongodb_database}",
        f"MongoDB required:     {'yes' if settings.mongodb_required else 'no'}",
        f"Timeout (ms):         {settings.mongodb_timeout_ms}",
        f"Admin username:       {settings.admin_username}",
        f"Admin password file:  {settings.admin_password_file}",
        f"Admin credential:     {admin_password_status}",
    ]

    if settings.uses_secret_file:
        lines.insert(3, f"URI file:             {settings.mongodb_uri_file}")
        lines.insert(4, f"MongoDB credential:   {uri_status}")
    else:
        lines.insert(3, "MongoDB source:       local docker service")

    if settings.uses_secret_file and uri_status == "missing":
        lines.append("")
        lines.append(
            "  La credencial MongoDB no está configurada. "
            "Creá keys/mongodb_uri con la URI de Atlas."
        )
        lines.append("  Ver keys/README.md para instrucciones.")

    if admin_password_status != "configured":
        lines.append("")
        lines.append(
            "  La contraseña admin local no está configurada. "
            "Creá keys/news_admin_password con un valor no vacío para usar el panel admin."
        )

    return "\n".join(lines)


def main() -> None:
    result = run_check()
    print(result)
    settings = get_news_settings()
    if not settings.uses_secret_file:
        sys.exit(0 if settings.mongodb_configured else 1)
    uri_status = check_secret_file(settings.mongodb_uri_file)
    sys.exit(0 if uri_status == "configured" else 1)


if __name__ == "__main__":
    main()
