"""Selecciona el proveedor conservando el resto del .env. Solo usa stdlib."""

import argparse
import math
import os
import re
import shlex
import stat
import tempfile
from pathlib import Path

PRICE_FIELDS = (
    "NEWS_CHAT_INPUT_USD_PER_MILLION",
    "NEWS_CHAT_OUTPUT_USD_PER_MILLION",
)
ASSIGNMENT = re.compile(r"^(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=")


class ConfigurationError(ValueError):
    pass


def credential_present(root: Path) -> bool:
    """Solo metadatos; jamás abre ni lee el archivo de secreto."""
    path = root / "keys/openai_api_key"
    return path.is_file() and path.stat().st_size > 0


def unquote_value(value: str, key: str) -> str:
    try:
        parts = shlex.split(value, comments=True)
    except ValueError:
        raise ConfigurationError(f"Revisa el formato de {key}.") from None
    if len(parts) != 1:
        raise ConfigurationError(f"Configura {key} en .env o como argumento de make.")
    return parts[0]


def configure(provider: str, root: Path, environ: dict[str, str]) -> None:
    if provider not in {"stub", "openai"}:
        raise ConfigurationError("El proveedor debe ser stub u openai.")
    env_path = root / ".env"
    if not env_path.is_file() or env_path.is_symlink():
        raise ConfigurationError(
            "Primero crea un .env regular con make env-local o make env-atlas."
        )
    with env_path.open(encoding="utf-8", newline="") as source:
        original = source.read()
    updates = {"CHATBOT_PROVIDER": provider}
    if provider == "openai":
        if not credential_present(root):
            raise ConfigurationError(
                "Falta keys/openai_api_key o está vacío. Completa ese archivo manualmente."
            )
        existing = {}
        for line in original.splitlines():
            match = ASSIGNMENT.match(line.lstrip())
            if match and match[1] in (*PRICE_FIELDS, "OPENAI_MODEL"):
                raw = line.lstrip()[match.end() :].strip()
                existing[match[1]] = unquote_value(raw, match[1]) if raw else ""
        for key in PRICE_FIELDS:
            value = unquote_value(environ.get(key) or existing.get(key, ""), key)
            try:
                price = float(value)
            except ValueError:
                raise ConfigurationError(
                    f"Configura {key} en .env o como argumento de make."
                ) from None
            if not math.isfinite(price) or price < 0 or "\n" in value or "\r" in value:
                raise ConfigurationError(
                    f"{key} debe ser un precio finito y no negativo."
                )
            updates[key] = value.strip()
        model = environ.get("OPENAI_MODEL") or existing.get("OPENAI_MODEL")
        if model:
            model = unquote_value(model, "OPENAI_MODEL")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,119}", model):
                raise ConfigurationError(
                    "OPENAI_MODEL debe contener un identificador de modelo válido."
                )
            updates["OPENAI_MODEL"] = model
    result = []
    written = set()
    newline = "\r\n" if "\r\n" in original else "\n"
    for line in original.splitlines(keepends=True):
        match = ASSIGNMENT.match(line.lstrip())
        if match and match[1] in updates:
            key = match[1]
            if key not in written:
                result.append(f"{key}={updates[key]}{newline}")
                written.add(key)
        else:
            result.append(line)
    for key, value in updates.items():
        if key not in written:
            if result and not result[-1].endswith(("\n", "\r")):
                result[-1] += newline
            result.append(f"{key}={value}{newline}")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=root,
            prefix=".env.chatbot-",
            delete=False,
        ) as target:
            temporary = Path(target.name)
            target.write("".join(result))
        temporary.chmod(stat.S_IMODE(env_path.stat().st_mode))
        temporary.replace(env_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=("stub", "openai"))
    args = parser.parse_args()
    try:
        settings = {
            key: os.environ[key]
            for key in (*PRICE_FIELDS, "OPENAI_MODEL")
            if key in os.environ
        }
        configure(args.provider, Path(__file__).resolve().parents[1], settings)
    except (ConfigurationError, OSError) as error:
        parser.exit(1, f"{error}\nNo se cambió la selección del proveedor.\n")
    print(
        f"CHATBOT_PROVIDER={args.provider} guardado; el resto de la configuración se conserva."
    )
    print("Aplica la selección con: make chatbot-up")


if __name__ == "__main__":
    main()
