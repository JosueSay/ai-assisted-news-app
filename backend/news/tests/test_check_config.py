"""Tests para el módulo check_config."""

import os
from pathlib import Path

from news.check_config import run_check
from news.config import get_news_settings

MISSING_URI = "/tmp/nonexistent_mongodb_uri_for_test"


class TestRunCheck:
    def test_run_check_reports_configured(self, tmp_path: Path) -> None:
        uri_file = tmp_path / "mongodb_uri"
        uri_file.write_text("mongodb://localhost:27017")
        os.environ["NEWS_MONGODB_URI_FILE"] = str(uri_file)
        output = run_check()
        assert "configured" in output
        assert "missing" not in output

    def test_run_check_reports_missing(self) -> None:
        os.environ["NEWS_MONGODB_URI_FILE"] = MISSING_URI
        output = run_check()
        assert "missing" in output
        assert "configured" not in output

    def test_run_check_output_contains_database_name(self) -> None:
        output = run_check()
        assert get_news_settings().mongodb_database in output