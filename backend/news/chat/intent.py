"""Clasificación determinista de la intención de un mensaje de chat.

No usa IA: la intención se decide con reglas sobre el texto normalizado para que
las consultas resolubles con la base no consuman presupuesto.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ..models import ResponseIntent

SUMMARIZE_PHRASES = ("resum", "sintetiz", "en pocas palabras", "en breve")
EXPLAIN_PHRASES = (
    "explica",
    "explicame",
    "por que",
    "que significa",
    "como afecta",
    "que implica",
    "contexto",
    "analiza",
)
DETAIL_PHRASES = ("detalle", "mas sobre", "cuentame sobre", "de que trata", "fuentes")
RECENT_PHRASES = (
    "ultima",
    "ultimas",
    "reciente",
    "hoy",
    "noticias",
    "novedades",
    "que paso",
    "que hay de nuevo",
    "titulares",
)
LOCAL_PHRASES = ("mi pais", "mi zona", "mi region", "cerca de mi", "donde estoy", "local")

COUNTRY_ALIASES: dict[str, str] = {
    "canada": "CA",
    "mexico": "MX",
    "guatemala": "GT",
    "costa rica": "CR",
    "argentina": "AR",
    "brasil": "BR",
    "brazil": "BR",
    "cuba": "CU",
    "jamaica": "JM",
    "espana": "ES",
    "francia": "FR",
    "japon": "JP",
    "china": "CN",
    "egipto": "EG",
    "sudafrica": "ZA",
    "australia": "AU",
    "nueva zelanda": "NZ",
}

TOPIC_ALIASES: dict[str, str] = {
    "actualidad": "actualidad",
    "tecnologia": "tecnologia",
    "tecnologica": "tecnologia",
    "ciencia": "tecnologia",
    "economia": "economia",
    "economica": "economia",
    "mercado": "economia",
    "negocios": "economia",
    "finanzas": "economia",
    "cultura": "cultura",
    "cultural": "cultura",
    "arte": "cultura",
    "musica": "cultura",
    "cine": "cultura",
    "lectura": "cultura",
    "deporte": "deportes",
    "deportes": "deportes",
    "deportiva": "deportes",
    "futbol": "deportes",
    "liga": "deportes",
}

STOPWORDS = {
    "algo",
    "alguna",
    "algunas",
    "cual",
    "cuales",
    "cuando",
    "como",
    "cuentame",
    "dame",
    "desde",
    "donde",
    "esta",
    "estas",
    "este",
    "esto",
    "estos",
    "hablame",
    "hasta",
    "hola",
    "muestrame",
    "noticia",
    "noticias",
    "para",
    "pasado",
    "puedes",
    "quiero",
    "saber",
    "sobre",
    "tiene",
    "tienes",
    "todo",
    "ultima",
    "ultimas",
    "reciente",
    "recientes",
    "explica",
    "explicame",
    "resume",
    "resumen",
    "resumir",
    "resumeme",
    "significa",
    "detalle",
    "detalles",
    "fuentes",
    "porque",
}


def normalize_text(value: str) -> str:
    """Minúsculas sin tildes ni signos, con espacios simples."""
    decomposed = unicodedata.normalize("NFD", value)
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    cleaned = re.sub(r"[^a-z0-9ñ ]+", " ", without_marks.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    padded = f" {text} "
    return any(f" {phrase}" in padded for phrase in phrases)


def _contains_word(text: str, word: str) -> bool:
    return f" {word} " in f" {text} "


@dataclass(frozen=True)
class ClassifiedQuery:
    """Resultado de clasificar un mensaje.

    `intent` es None cuando ninguna regla aplica: el servicio decide entonces si
    la búsqueda por términos encuentra noticias o si la petición es `unsupported`.
    """

    intent: ResponseIntent | None
    country_codes: tuple[str, ...] = ()
    topics: tuple[str, ...] = ()
    terms: tuple[str, ...] = ()
    wants_user_location: bool = False

    @property
    def has_filters(self) -> bool:
        return bool(self.country_codes or self.topics or self.wants_user_location)


def classify_message(message: str, *, has_news_context: bool) -> ClassifiedQuery:
    """Clasifica un mensaje en una de las intenciones de `responseMetadata.intent`."""
    text = normalize_text(message)
    country_codes = tuple(
        dict.fromkeys(code for alias, code in COUNTRY_ALIASES.items() if _contains_word(text, alias))
    )
    topics = tuple(
        dict.fromkeys(topic for alias, topic in TOPIC_ALIASES.items() if _contains_word(text, alias))
    )
    wants_user_location = _contains_phrase(text, LOCAL_PHRASES)
    terms = tuple(
        dict.fromkeys(
            word
            for word in text.split()
            if len(word) >= 4
            and word not in STOPWORDS
            and word not in COUNTRY_ALIASES
            and word not in TOPIC_ALIASES
        )
    )

    wants_summary = _contains_phrase(text, SUMMARIZE_PHRASES)
    wants_explanation = _contains_phrase(text, EXPLAIN_PHRASES)
    wants_detail = _contains_phrase(text, DETAIL_PHRASES)

    if wants_summary:
        intent: ResponseIntent | None = ResponseIntent.summarize
    elif wants_explanation:
        intent = ResponseIntent.explain
    elif wants_detail:
        intent = ResponseIntent.news_detail
    elif has_news_context:
        # Una pregunta abierta sobre la noticia abierta se trata como explicación.
        intent = ResponseIntent.explain
    elif country_codes or wants_user_location:
        intent = ResponseIntent.regional_news
    elif topics:
        intent = ResponseIntent.topic_news
    elif _contains_phrase(text, RECENT_PHRASES):
        intent = ResponseIntent.recent_news
    else:
        intent = None

    return ClassifiedQuery(
        intent=intent,
        country_codes=country_codes,
        topics=topics,
        terms=terms,
        wants_user_location=wants_user_location,
    )
