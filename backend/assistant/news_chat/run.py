"""Entrada del chat de noticias idéntica en desarrollo local y Docker."""

import os

from dotenv import load_dotenv
from news.config import ROOT_ENV_FILE


def configure_news_environment() -> None:
    load_dotenv(ROOT_ENV_FILE, override=False)
    # Los modos históricos permanecen disponibles mediante assistant.app.
    os.environ["MONGODB_CONTEXT_MODE"] = "news"


def main() -> None:
    configure_news_environment()
    import uvicorn

    uvicorn.run("assistant.app:app", host="0.0.0.0", port=8010)


if __name__ == "__main__":
    main()
