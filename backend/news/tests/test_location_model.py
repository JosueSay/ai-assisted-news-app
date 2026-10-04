"""Tests para el modelo Location."""

from bson import ObjectId
from pydantic import ValidationError

from news.models import LocationLevel
from news.models.location import Location


def test_valid_location():
    loc = Location(
        name="Mexico City",
        country="Mexico",
        countryCode="MX",
        level=LocationLevel.city,
    )
    assert loc.name == "Mexico City"
    assert loc.level == LocationLevel.city
    assert loc.active is True


def test_location_with_optional_fields():
    loc = Location(
        name="Guadalajara",
        city="Guadalajara",
        region="Jalisco",
        country="Mexico",
        countryCode="MX",
        level=LocationLevel.city,
    )
    assert loc.city == "Guadalajara"
    assert loc.region == "Jalisco"


def test_invalid_level():
    try:
        Location(
            name="Invalid",
            country="X",
            countryCode="XX",
            level="invalid_level",
        )
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_default_active_true():
    loc = Location(
        name="Buenos Aires",
        country="Argentina",
        countryCode="AR",
        level=LocationLevel.city,
    )
    assert loc.active is True


def test_model_dump_mongo_includes_id():
    loc = Location(
        name="Lima",
        country="Peru",
        countryCode="PE",
        level=LocationLevel.city,
    )
    dumped = loc.model_dump_mongo()
    assert "_id" in dumped
    assert isinstance(dumped["_id"], ObjectId)