"""Inspección no destructiva del dataset de noticias demo (Loop 05).

Solo lee la colección `news` y reporta diferencias contra las fixtures
deterministas de `demo_news.py` usando `slug` como identidad natural.
Nunca inserta, modifica ni elimina documentos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pymongo.database import Database

from .config import get_news_settings
from .database import get_news_client
from .demo_news import EXPECTED_NEWS_COUNT, get_demo_news_documents
from .models.reading_time import compute_reading_time
from .seed_catalog import CATALOG_LOCATION_IDS
from .topics import TOPICS


@dataclass
class NewsCheckResult:
    database: str
    expected: int = EXPECTED_NEWS_COUNT
    found: int = 0
    missing: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    countries_expected: int = len(CATALOG_LOCATION_IDS)
    countries_covered: int = 0
    country_gaps: dict[str, int] = field(default_factory=dict)
    invalid_topics: list[str] = field(default_factory=list)
    uncovered_topics: list[str] = field(default_factory=list)
    drafts: int = 0
    published: int = 0
    verification: dict[str, int] = field(default_factory=dict)
    image_types: dict[str, int] = field(default_factory=dict)
    coherence_issues: list[str] = field(default_factory=list)
    external: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing
            or self.duplicates
            or self.country_gaps
            or self.invalid_topics
            or self.uncovered_topics
            or self.coherence_issues
            or self.external
        )

    def format(self) -> str:
        lines = [
            f"News check: {'OK' if self.ok else 'DRIFT DETECTED'}",
            f"Database: {self.database}",
            f"News: {self.found}/{self.expected}",
            f"Countries: {self.countries_covered}/{self.countries_expected}",
            f"Drafts: {self.drafts} Published: {self.published}",
            f"Duplicates: {len(self.duplicates)}",
            f"External: {len(self.external)}",
        ]
        if self.missing:
            lines.append("Missing news: " + ", ".join(self.missing))
        if self.duplicates:
            lines.append("Duplicated news: " + ", ".join(self.duplicates))
        if self.country_gaps:
            gaps = ", ".join(f"{code}({total})" for code, total in sorted(self.country_gaps.items()))
            lines.append("Country gaps: " + gaps)
        if self.invalid_topics:
            lines.append("Invalid topics in: " + ", ".join(self.invalid_topics))
        if self.uncovered_topics:
            lines.append("Uncovered topics: " + ", ".join(self.uncovered_topics))
        if self.coherence_issues:
            lines.append(
                "Coherence issues in: " + ", ".join(self.coherence_issues)
            )
        if self.external:
            lines.append("External news: " + ", ".join(self.external))
        return "\n".join(lines)


def check_news_data(database: Database) -> NewsCheckResult:
    expected_docs = {doc["slug"]: doc for doc in get_demo_news_documents()}
    id_to_code = {value: key for key, value in CATALOG_LOCATION_IDS.items()}

    counts: dict[str, int] = {}
    first_seen: dict[str, dict] = {}
    for document in database["news"].find({}):
        slug = document.get("slug")
        counts[slug] = counts.get(slug, 0) + 1
        if slug not in first_seen:
            first_seen[slug] = document

    result = NewsCheckResult(database=database.name, found=sum(counts.values()))
    result.missing = sorted(set(expected_docs) - set(counts))
    result.duplicates = sorted(slug for slug, total in counts.items() if total > 1)
    result.external = sorted(set(counts) - set(expected_docs))

    per_country: dict[str, int] = {code: 0 for code in CATALOG_LOCATION_IDS}
    seen_topics: set[str] = set()
    for slug in sorted(set(expected_docs) & set(counts)):
        expected = expected_docs[slug]
        location_id = expected["geographicScope"]["locationIds"][0]
        code = id_to_code.get(location_id)
        if code is not None:
            per_country[code] += 1
        document = first_seen[slug]
        topics = document.get("topics", [])
        if not isinstance(topics, list) or any(
            not isinstance(topic, str) or topic not in TOPICS for topic in topics
        ):
            result.invalid_topics.append(slug)
        else:
            seen_topics.update(topics)
        status = document.get("status")
        if status == "draft":
            result.drafts += 1
            if document.get("publishedAt") is not None:
                result.coherence_issues.append(slug)
        elif status == "published":
            result.published += 1
            content = document.get("content", "")
            expected_wc, expected_min = compute_reading_time(content)
            if (
                document.get("wordCount") != expected_wc
                or document.get("estimatedReadingMinutes") != expected_min
                or document.get("publishedAt") is None
            ):
                result.coherence_issues.append(slug)
        else:
            result.coherence_issues.append(slug)
        verification = (document.get("verification") or {}).get("status")
        result.verification[verification] = result.verification.get(verification, 0) + 1
        image_type = (document.get("image") or {}).get("type")
        result.image_types[image_type] = result.image_types.get(image_type, 0) + 1
        image = document.get("image") or {}
        # The seed intentionally preserves existing news. Detect old placeholders
        # and attribution drift so a successful local reseed proves image parity.
        if image != expected["image"]:
            if slug not in result.coherence_issues:
                result.coherence_issues.append(slug)
        if image.get("type") in {"ai_generated", "ai_modified"} and not (
            image.get("aiDisclosure") and str(image.get("aiDisclosure")).strip()
        ):
            if slug not in result.coherence_issues:
                result.coherence_issues.append(slug)

    result.country_gaps = {
        code: total for code, total in per_country.items() if total != 2
    }
    result.countries_covered = sum(1 for total in per_country.values() if total == 2)
    result.uncovered_topics = sorted(set(TOPICS) - seen_topics)
    result.invalid_topics = sorted(result.invalid_topics)
    result.coherence_issues = sorted(result.coherence_issues)
    return result


def run_news_check() -> str:
    settings = get_news_settings()
    client = get_news_client(settings)
    try:
        result = check_news_data(client[settings.mongodb_database])
        return result.format()
    finally:
        client.close()


def main() -> None:
    result = run_news_check()
    print(result)
    if "DRIFT DETECTED" in result:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
