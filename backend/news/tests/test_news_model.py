"""Tests para el modelo News (incluye modelos embebidos)."""

from datetime import datetime, timezone

from bson import ObjectId
from pydantic import ValidationError

from news.models import (
    ImageType,
    LocationLevel,
    NewsStatus,
    SourceType,
    VerificationStatus,
)
from news.models.news import (
    AiAssistance,
    GeographicScope,
    Image,
    News,
    Source,
    Verification,
)


def _minimal_news_kwargs(**overrides) -> dict:
    author_id = ObjectId()
    scope = GeographicScope(level=LocationLevel.country)
    verification = Verification(status=VerificationStatus.confirmed)
    image = Image(type=ImageType.photograph, url="https://example.com/img.jpg")
    kwargs = dict(
        slug="test-news",
        title="Test News",
        summary="A summary",
        content="Some content here",
        authorId=author_id,
        geographicScope=scope,
        verification=verification,
        image=image,
    )
    kwargs.update(overrides)
    return kwargs


def test_valid_draft():
    news = News(**{**_minimal_news_kwargs(), "status": NewsStatus.draft})
    assert news.status == NewsStatus.draft


def test_valid_published():
    news = News(
        **{
            **_minimal_news_kwargs(),
            "status": NewsStatus.published,
            "publishedAt": datetime.now(timezone.utc),
            "wordCount": 3,
            "estimatedReadingMinutes": 1,
        }
    )
    assert news.status == NewsStatus.published


def test_draft_rejects_published_at():
    try:
        News(**{**_minimal_news_kwargs(), "publishedAt": datetime.now(timezone.utc)})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_published_requires_published_at_and_consistent_reading_time():
    try:
        News(**{**_minimal_news_kwargs(), "status": NewsStatus.published})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass

    try:
        News(
            **{
                **_minimal_news_kwargs(),
                "status": NewsStatus.published,
                "publishedAt": datetime.now(timezone.utc),
                "wordCount": 2,
                "estimatedReadingMinutes": 1,
            }
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_invalid_status():
    try:
        News(**{**_minimal_news_kwargs(), "status": "deleted"})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_invalid_verification_status():
    try:
        verif = Verification(status="unknown_status")
        News(**{**_minimal_news_kwargs(), "verification": verif})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_invalid_source_type():
    try:
        source = Source(
            name="Test",
            url="https://example.com",
            sourceType="invalid_source_type",
            accessedAt=datetime.now(timezone.utc),
        )
        News(**{**_minimal_news_kwargs(), "sources": [source]})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_invalid_url_format():
    try:
        source = Source(
            name="Test",
            url="ftp://example.com",
            sourceType=SourceType.media,
            accessedAt=datetime.now(timezone.utc),
        )
        News(**{**_minimal_news_kwargs(), "sources": [source]})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_invalid_image_type():
    try:
        img = Image(url="https://example.com/img.jpg", type="invalid_type")
        News(**{**_minimal_news_kwargs(), "image": img})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_invalid_geographic_level():
    try:
        scope = GeographicScope(level="invalid_level")
        News(**{**_minimal_news_kwargs(), "geographicScope": scope})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_invalid_word_count_negative():
    try:
        News(**{**_minimal_news_kwargs(), "wordCount": -5})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_recompute_reading_time():
    news = News(
        slug="test-news",
        title="Test News",
        summary="A summary",
        content="one two three four five",
        authorId=ObjectId(),
        geographicScope=GeographicScope(level=LocationLevel.country),
        verification=Verification(status=VerificationStatus.confirmed),
        image=Image(type=ImageType.photograph, url="https://example.com/img.jpg"),
    )
    assert news.wordCount == 0
    assert news.estimatedReadingMinutes == 1
    news.recompute_reading_time()
    assert news.wordCount == 5
    assert news.estimatedReadingMinutes == 1


def test_incomplete_http_url_is_rejected():
    try:
        Source(
            name="Incomplete",
            url="https://",
            sourceType=SourceType.media,
            accessedAt=datetime.now(timezone.utc),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_source_url_validation():
    valid_source = Source(
        name="Valid HTTP",
        url="http://example.com",
        sourceType=SourceType.media,
        accessedAt=datetime.now(timezone.utc),
    )
    assert valid_source.url == "http://example.com"

    valid_source_https = Source(
        name="Valid HTTPS",
        url="https://example.com",
        sourceType=SourceType.media,
        accessedAt=datetime.now(timezone.utc),
    )
    assert valid_source_https.url == "https://example.com"

    try:
        Source(
            name="Invalid",
            url="file:///local/path",
            sourceType=SourceType.media,
            accessedAt=datetime.now(timezone.utc),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass

    try:
        Source(
            name="No protocol",
            url="example.com",
            sourceType=SourceType.media,
            accessedAt=datetime.now(timezone.utc),
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_image_url_validation():
    img_none = Image(url=None, type=ImageType.none)
    assert img_none.url is None

    img_http = Image(url="http://example.com/img.jpg", type=ImageType.photograph)
    assert img_http.url == "http://example.com/img.jpg"

    img_https = Image(url="https://example.com/img.jpg", type=ImageType.photograph)
    assert img_https.url == "https://example.com/img.jpg"

    try:
        Image(url="ftp://bad.com/img.jpg", type=ImageType.photograph)
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_image_type_none_allows_null_url():
    img = Image(url=None, type=ImageType.none)
    assert img.url is None
    assert img.type == ImageType.none


def test_image_type_none_rejects_url_or_alt():
    for kwargs in (
        {"url": "https://example.com/image.jpg"},
        {"alt": "Texto alternativo"},
    ):
        try:
            Image(type=ImageType.none, **kwargs)
            assert False, "Expected ValidationError"
        except ValidationError:
            pass


def test_ai_image_requires_disclosure_and_matching_assistance():
    try:
        Image(type=ImageType.ai_generated, url="https://example.com/image.jpg")
        assert False, "Expected ValidationError"
    except ValidationError:
        pass

    ai_image = Image(
        type=ImageType.ai_generated,
        url="https://example.com/image.jpg",
        aiDisclosure="Imagen generada con IA.",
    )
    try:
        News(**{**_minimal_news_kwargs(), "image": ai_image})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass

    news = News(
        **{
            **_minimal_news_kwargs(),
            "image": ai_image,
            "aiAssistance": AiAssistance(imageGenerated=True),
        }
    )
    assert news.aiAssistance.imageGenerated is True


def test_ai_assistance_defaults():
    aa = AiAssistance()
    assert aa.summaryGenerated is False
    assert aa.topicsGenerated is False
    assert aa.imageGenerated is False
    assert aa.humanReviewed is False


def test_model_dump_mongo_includes_id():
    news = News(**_minimal_news_kwargs())
    dumped = news.model_dump_mongo()
    assert "_id" in dumped
    assert isinstance(dumped["_id"], ObjectId)
