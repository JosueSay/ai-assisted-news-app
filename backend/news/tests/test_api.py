"""Tests para adaptación de documentos MongoDB a la API de noticias."""

from datetime import datetime, timezone

from bson import ObjectId

from news.api import AdminNewsCreateRequest, _create_news_document, document_to_article
from news.seed_catalog import CATALOG_LOCATION_IDS, catalog_location_document
from news.tests.test_schema_initialize import FakeDatabase as SchemaFakeDatabase


class FakeCollection:
    def find_one(self, _query, _projection=None):
        return {"displayName": "Autora Prueba"}


class AuthorFakeDatabase:
    def __getitem__(self, _name):
        return FakeCollection()


def test_document_to_article_maps_published_news() -> None:
    document = {
        "_id": ObjectId("670000000000000000000101"),
        "slug": "nota-prueba",
        "title": "Nota prueba",
        "summary": "Resumen",
        "topics": ["tecnologia"],
        "authorId": ObjectId("670000000000000000000002"),
        "publishedAt": datetime(2026, 10, 4, tzinfo=timezone.utc),
        "content": "Primer párrafo.\n\nSegundo párrafo.",
        "estimatedReadingMinutes": 2,
        "sources": [],
        "image": {"url": None, "alt": None, "credit": "Pendiente", "rights": "Prueba"},
    }

    article = document_to_article(AuthorFakeDatabase(), document)

    assert article.id == "670000000000000000000101"
    assert article.slug == "nota-prueba"
    assert article.category == "tecnologia"
    assert article.author == "Autora Prueba"
    assert article.body == ["Primer párrafo.", "Segundo párrafo."]
    assert article.image.src is None
    assert article.image.alt == "Imagen no disponible para Nota prueba."


def test_document_to_article_falls_back_to_actualidad_for_unknown_topic() -> None:
    document = {
        "_id": ObjectId("670000000000000000000101"),
        "slug": "nota-prueba",
        "title": "Nota prueba",
        "summary": "Resumen",
        "topics": ["otro"],
        "authorId": None,
        "publishedAt": None,
        "content": "Contenido",
        "estimatedReadingMinutes": 1,
        "sources": [{"name": "Fuente prueba"}],
        "image": {},
    }

    article = document_to_article(AuthorFakeDatabase(), document)

    assert article.category == "actualidad"
    assert article.author == "Redacción AI News"
    assert article.source == "Fuente prueba"


def test_create_news_document_inserts_news_author_and_audit_log() -> None:
    db = SchemaFakeDatabase()
    location = catalog_location_document(
        {"code": "GT", "name": "Guatemala", "country": "Guatemala"}
    )
    db["locations"].replace_one({"_id": CATALOG_LOCATION_IDS["GT"]}, location, upsert=True)
    payload = AdminNewsCreateRequest(
        title="Nueva noticia manual",
        slug="nueva-noticia-manual",
        summary="Resumen de la noticia manual.",
        content="Primer párrafo.\n\nSegundo párrafo con contexto suficiente.",
        topic="actualidad",
        keywords=["manual"],
        locationId=str(CATALOG_LOCATION_IDS["GT"]),
        sourceName="Fuente local",
        sourceUrl="https://example.com/noticia",
    )

    document = _create_news_document(db, payload, "admin")

    assert document["slug"] == "nueva-noticia-manual"
    assert document["status"] == "published"
    assert document["publishedAt"] is not None
    assert document["authorId"] in db["users"].documents
    assert len(db["news"].documents) == 1
    assert len(db["auditLogs"].documents) == 1
