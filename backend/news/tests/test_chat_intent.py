"""Tests de la clasificación determinista de intención del chat."""

import pytest

from news.chat.intent import classify_message, normalize_text
from news.models import ResponseIntent


def test_normalize_text_removes_accents_and_symbols() -> None:
    assert normalize_text("¿Qué pasó en Japón HOY?") == "que paso en japon hoy"


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("¿Cuáles son las últimas noticias?", ResponseIntent.recent_news),
        ("Muéstrame los titulares", ResponseIntent.recent_news),
        ("Noticias de Guatemala", ResponseIntent.regional_news),
        ("¿Qué pasa en mi país?", ResponseIntent.regional_news),
        ("Noticias de tecnología", ResponseIntent.topic_news),
        ("Resume las noticias de México", ResponseIntent.summarize),
        ("Explícame por qué subió el precio", ResponseIntent.explain),
        ("Dame más detalle sobre el mercado digital", ResponseIntent.news_detail),
    ],
)
def test_classify_message_detects_intent(message: str, intent: ResponseIntent) -> None:
    assert classify_message(message, has_news_context=False).intent == intent


def test_classify_message_extracts_countries_and_topics() -> None:
    query = classify_message("Resume deportes en Costa Rica y Nueva Zelanda", has_news_context=False)

    assert query.country_codes == ("CR", "NZ")
    assert query.topics == ("deportes",)
    assert query.has_filters is True


def test_classify_message_marks_user_location() -> None:
    query = classify_message("noticias locales", has_news_context=False)

    assert query.intent == ResponseIntent.regional_news
    assert query.wants_user_location is True


def test_open_question_about_open_article_is_explain() -> None:
    query = classify_message("¿A quién beneficia esto?", has_news_context=True)

    assert query.intent == ResponseIntent.explain


def test_unmatched_message_returns_no_intent_and_search_terms() -> None:
    query = classify_message("receta de pastel de chocolate", has_news_context=False)

    assert query.intent is None
    assert query.terms == ("receta", "pastel", "chocolate")
