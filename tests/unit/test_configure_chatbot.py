"""Configuración no secreta del chatbot: pruebas sin Docker ni credenciales."""

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/configure_chatbot.py"


class ConfigureChatbotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = self.root / ".env"
        self.original = (
            "# Configuración de prueba\nNEWS_DB_MODE=atlas\n"
            "NEWS_MONGODB_DATABASE=fixture_database\n"
            "EXPO_PUBLIC_NEWS_API_BASE_URL=http://localhost:8120\n"
            "CHATBOT_PROVIDER=openai\n"
        )
        self.env.write_text(self.original, encoding="utf-8")

    def module(self):
        self.assertTrue(SCRIPT.is_file(), "Falta el selector de proveedor del chatbot")
        spec = importlib.util.spec_from_file_location("configure_chatbot", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_stub_preserves_database_urls_comments_and_is_idempotent(self):
        module = self.module()
        module.configure("stub", self.root, {})
        expected = self.original.replace(
            "CHATBOT_PROVIDER=openai", "CHATBOT_PROVIDER=stub"
        )
        self.assertEqual(self.env.read_text(encoding="utf-8"), expected)
        module.configure("stub", self.root, {})
        self.assertEqual(self.env.read_text(encoding="utf-8"), expected)

    def test_missing_env_requires_explicit_database_configuration(self):
        module = self.module()
        self.env.unlink()
        with self.assertRaises(module.ConfigurationError):
            module.configure("stub", self.root, {})
        self.assertFalse(self.env.exists())

    def test_api_without_credential_file_leaves_env_untouched(self):
        module = self.module()
        with self.assertRaises(module.ConfigurationError):
            module.configure("openai", self.root, {})
        self.assertEqual(self.env.read_text(encoding="utf-8"), self.original)

    def test_api_without_prices_leaves_env_untouched(self):
        module = self.module()
        with (
            patch.object(module, "credential_present", return_value=True),
            self.assertRaises(module.ConfigurationError),
        ):
            module.configure("openai", self.root, {})
        self.assertEqual(self.env.read_text(encoding="utf-8"), self.original)

    def test_api_parameters_are_persisted_without_changing_database(self):
        module = self.module()
        settings = {
            "OPENAI_MODEL": "fixture-model",
            "NEWS_CHAT_INPUT_USD_PER_MILLION": "1.25",
            "NEWS_CHAT_OUTPUT_USD_PER_MILLION": "3.5",
        }
        with patch.object(module, "credential_present", return_value=True):
            module.configure("openai", self.root, settings)
        result = self.env.read_text(encoding="utf-8")
        for key, value in settings.items():
            self.assertIn(f"{key}={value}\n", result)
        self.assertIn("NEWS_DB_MODE=atlas\n", result)
        self.assertIn("NEWS_MONGODB_DATABASE=fixture_database\n", result)
        self.assertEqual(result.count("CHATBOT_PROVIDER="), 1)

    def test_api_reads_existing_quoted_configuration_and_removes_provider_duplicates(
        self,
    ):
        module = self.module()
        self.env.write_text(
            self.original + "CHATBOT_PROVIDER=stub\n"
            'NEWS_CHAT_INPUT_USD_PER_MILLION="1.25" # fixture\n'
            "NEWS_CHAT_OUTPUT_USD_PER_MILLION=3.5\n",
            encoding="utf-8",
        )
        with patch.object(module, "credential_present", return_value=True):
            module.configure("openai", self.root, {})
        result = self.env.read_text(encoding="utf-8")
        self.assertEqual(result.count("CHATBOT_PROVIDER="), 1)
        self.assertIn("CHATBOT_PROVIDER=openai\n", result)

    def test_make_exported_quoted_values_are_accepted(self):
        module = self.module()
        with patch.object(module, "credential_present", return_value=True):
            module.configure(
                "openai",
                self.root,
                {
                    "OPENAI_MODEL": '"fixture-model"',
                    "NEWS_CHAT_INPUT_USD_PER_MILLION": '"1.25"',
                    "NEWS_CHAT_OUTPUT_USD_PER_MILLION": '"3.5"',
                },
            )
        self.assertIn(
            "OPENAI_MODEL=fixture-model\n", self.env.read_text(encoding="utf-8")
        )

    def test_credential_check_never_opens_secret_content(self):
        from types import SimpleNamespace

        module = self.module()
        with (
            patch.object(Path, "is_file", return_value=True),
            patch.object(Path, "stat", return_value=SimpleNamespace(st_size=8)),
            patch.object(Path, "open", side_effect=AssertionError("No leer secretos")),
        ):
            self.assertTrue(module.credential_present(self.root))

    def test_invalid_prices_or_model_cannot_corrupt_env(self):
        module = self.module()
        for bad in ("NaN", "Infinity", "-1", "1;bad", "1\nCHATBOT_PROVIDER=stub"):
            with (
                self.subTest(bad=bad),
                patch.object(module, "credential_present", return_value=True),
            ):
                with self.assertRaises(module.ConfigurationError):
                    module.configure(
                        "openai",
                        self.root,
                        {
                            "NEWS_CHAT_INPUT_USD_PER_MILLION": bad,
                            "NEWS_CHAT_OUTPUT_USD_PER_MILLION": "2",
                        },
                    )
                self.assertEqual(self.env.read_text(encoding="utf-8"), self.original)
        with (
            patch.object(module, "credential_present", return_value=True),
            self.assertRaises(module.ConfigurationError),
        ):
            module.configure(
                "openai",
                self.root,
                {
                    "OPENAI_MODEL": "unsafe$(command)",
                    "NEWS_CHAT_INPUT_USD_PER_MILLION": "1",
                    "NEWS_CHAT_OUTPUT_USD_PER_MILLION": "2",
                },
            )
        self.assertEqual(self.env.read_text(encoding="utf-8"), self.original)

    def test_make_stub_target_works_in_an_isolated_project(self):
        self.assertTrue(SCRIPT.is_file(), "Falta el selector de proveedor del chatbot")
        (self.root / "scripts").mkdir()
        (self.root / "scripts/configure_chatbot.py").write_bytes(SCRIPT.read_bytes())
        (self.root / "Makefile").write_bytes((ROOT / "Makefile").read_bytes())
        result = subprocess.run(
            ["make", "chatbot-stub"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CHATBOT_PROVIDER=stub\n", self.env.read_text(encoding="utf-8"))

    def test_make_api_alias_reports_missing_key_without_changing_env(self):
        self.assertTrue(SCRIPT.is_file())
        (self.root / "scripts").mkdir()
        (self.root / "scripts/configure_chatbot.py").write_bytes(SCRIPT.read_bytes())
        (self.root / "Makefile").write_bytes((ROOT / "Makefile").read_bytes())
        result = subprocess.run(
            ["make", "chatbot-api"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("keys/openai_api_key", result.stderr)
        self.assertEqual(self.env.read_text(encoding="utf-8"), self.original)


if __name__ == "__main__":
    unittest.main()
