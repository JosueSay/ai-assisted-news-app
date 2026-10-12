"""Tests de datos del catálogo de locations contra el modelo Location."""

from news.models import LocationLevel
from news.models.location import Location
from news.seed_catalog import (
    CATALOG_LOCATIONS,
    CATALOG_LOCATION_IDS,
    catalog_location_document,
)

EXPECTED_CODES = {
    "CA",
    "MX",
    "GT",
    "CR",
    "AR",
    "BR",
    "CU",
    "JM",
    "ES",
    "FR",
    "JP",
    "CN",
    "EG",
    "ZA",
    "AU",
    "NZ",
}


def test_catalog_has_exactly_16_locations() -> None:
    assert len(CATALOG_LOCATIONS) == 16


def test_catalog_country_codes_match_expected() -> None:
    assert {item["code"] for item in CATALOG_LOCATIONS} == EXPECTED_CODES


def test_catalog_codes_are_unique() -> None:
    codes = [item["code"] for item in CATALOG_LOCATIONS]
    assert len(set(codes)) == len(codes)


def test_catalog_names_are_non_empty() -> None:
    for item in CATALOG_LOCATIONS:
        assert item["name"].strip()
        assert item["country"].strip()


def test_catalog_entries_validate_with_location() -> None:
    for item in CATALOG_LOCATIONS:
        document = catalog_location_document(item)
        assert document["_id"] == CATALOG_LOCATION_IDS[item["code"]]
        location = Location.model_validate(document)
        assert location.level == LocationLevel.country
        assert location.active is True
        assert location.city is None
        assert location.region is None
