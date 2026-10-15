"""Tests para el catálogo estático de topics."""

import re

import pytest

from news.topics import TOPICS, get_topics, is_valid_topic, normalize_topic

EXPECTED_TOPICS = (
    "actualidad",
    "tecnologia",
    "ciencia",
    "economia",
    "negocios",
    "politica",
    "deportes",
    "salud",
    "educacion",
    "cultura",
    "entretenimiento",
    "medio_ambiente",
    "seguridad",
    "internacional",
)


def test_topics_catalog_matches_expected() -> None:
    assert get_topics() == EXPECTED_TOPICS
    assert TOPICS == EXPECTED_TOPICS


def test_topics_are_unique() -> None:
    assert len(set(get_topics())) == len(get_topics())


def test_topics_stable_format() -> None:
    for topic in get_topics():
        assert topic
        assert topic == topic.lower()
        assert " " not in topic
        assert re.fullmatch(r"[a-z_]+", topic)


def test_valid_topics_accepted() -> None:
    for topic in EXPECTED_TOPICS:
        assert is_valid_topic(topic) is True


def test_invalid_topics_rejected() -> None:
    for bad in ["Tecnología", "tecnología", "technology", "tech", "medio ambiente", "", "   "]:
        assert is_valid_topic(bad) is False


def test_normalize_accepts_defined_variants() -> None:
    assert normalize_topic("Actualidad") == "actualidad"
    assert normalize_topic("  tecnologia  ") == "tecnologia"


def test_normalize_rejects_unknown_without_translation() -> None:
    with pytest.raises(ValueError):
        normalize_topic("technology")
    with pytest.raises(ValueError):
        normalize_topic("Tecnología")


def test_normalize_rejects_non_string() -> None:
    with pytest.raises(ValueError):
        normalize_topic(None)  # type: ignore[arg-type]
