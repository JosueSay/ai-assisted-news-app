"""Los tipos Expo derivan del catálogo y enums aprobados, sin acceso a MongoDB."""

from pathlib import Path

from news.export_contract import render_contract
from news.presentation import topic_catalog
from news.topics import TOPICS


def test_frontend_catalog_preserves_canonical_order_and_all_topics():
    assert [item["id"] for item in topic_catalog()] == list(TOPICS)
    assert len(topic_catalog()) == 14


def test_versioned_typescript_contract_matches_domain():
    # En la imagen de tests solo puede estar montado backend; el check de Make/CI
    # comprueba el archivo real cuando también está disponible frontend.
    generated = (
        Path(__file__).resolve().parents[3] / "frontend/src/generated/newsContract.ts"
    )
    if generated.is_file():
        assert generated.read_text(encoding="utf-8") == render_contract()
    else:
        import pytest

        pytest.skip("El archivo de frontend se verifica con make news-contract-check")
