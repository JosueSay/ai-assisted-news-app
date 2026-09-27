"""Tests para el módulo reading_time (funciones puras, sin dependencias externas)."""

from news.models.reading_time import (
    compute_reading_time,
    count_words,
    estimate_reading_minutes,
)


def test_count_words_empty():
    assert count_words("") == 0


def test_count_words_basic():
    assert count_words("hello world") == 2


def test_count_words_multiple_spaces():
    assert count_words("hello   world") == 2


def test_estimate_reading_minutes_zero():
    assert estimate_reading_minutes(0) == 1


def test_estimate_reading_minutes_under_200():
    assert estimate_reading_minutes(150) == 1


def test_estimate_reading_minutes_exact_200():
    assert estimate_reading_minutes(200) == 1


def test_estimate_reading_minutes_ceil():
    assert estimate_reading_minutes(300) == 2


def test_compute_reading_time_integration():
    wc, mins = compute_reading_time("hello world")
    assert wc == 2
    assert mins == 1