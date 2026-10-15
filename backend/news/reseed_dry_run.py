"""CLI no destructivo del dry-run de reseed (Loop 06).

Muestra el plan real (conteos inspeccionados, externos preservados)
sin modificar nada. Invocado por `make db-reseed-dry-run`.
"""

from __future__ import annotations

from .config import get_news_settings
from .database import get_news_client
from .reseed import plan_dry_run


def run_reseed_dry_run() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        plan = plan_dry_run(
            client[settings.mongodb_database],
            settings.mongodb_mode,
            settings.mongodb_database,
        )
        return plan.format()
    finally:
        client.close()


def main() -> None:
    print(run_reseed_dry_run())


if __name__ == "__main__":
    main()
