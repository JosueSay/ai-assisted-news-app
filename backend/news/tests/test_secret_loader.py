"""Tests para el módulo secret_loader."""

from pathlib import Path

import pytest

from news.secret_loader import SecretFileError, check_secret_file, load_secret


class TestLoadSecret:
    def test_load_secret_existing_file(self, tmp_path: Path) -> None:
        secret = "my_secret_value_123"
        file = tmp_path / "secret.txt"
        file.write_text(secret)
        assert load_secret(file) == secret

    def test_load_secret_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.txt"
        with pytest.raises(SecretFileError):
            load_secret(missing)

    def test_load_secret_empty_file(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.txt"
        empty.write_text("")
        with pytest.raises(SecretFileError):
            load_secret(empty)

    def test_load_secret_whitespace_stripped(self, tmp_path: Path) -> None:
        secret = "  \t\n  real_secret_value  \n\t  "
        file = tmp_path / "secret.txt"
        file.write_text(secret)
        assert load_secret(file) == "real_secret_value"

    def test_load_secret_exception_does_not_contain_value(
        self, tmp_path: Path
    ) -> None:
        secret = "super-secret-password-42"
        file = tmp_path / "secret.txt"
        file.write_text(secret)
        file.unlink()
        with pytest.raises(SecretFileError) as exc_info:
            load_secret(file)
        assert secret not in str(exc_info.value)
        assert "super" not in str(exc_info.value)


class TestCheckSecretFile:
    def test_check_secret_file_configured(self, tmp_path: Path) -> None:
        file = tmp_path / "secret.txt"
        file.write_text("some-uri")
        assert check_secret_file(file) == "configured"

    def test_check_secret_file_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist.txt"
        assert check_secret_file(missing) == "missing"

    def test_check_secret_file_invalid_empty(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty.txt"
        empty.write_text("")
        assert check_secret_file(empty) == "invalid"