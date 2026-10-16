"""Etiquetas de presentación del catálogo canónico, sin alterar el esquema."""

from .topics import TOPICS

_ACCENTED_LABELS = {
    "tecnologia": "Tecnología",
    "economia": "Economía",
    "politica": "Política",
    "educacion": "Educación",
}


def topic_label(topic: str) -> str:
    return _ACCENTED_LABELS.get(topic, topic.replace("_", " ").capitalize())


def topic_catalog() -> list[dict[str, str]]:
    return [{"id": topic, "label": topic_label(topic)} for topic in TOPICS]
