"""Exercise deployment commands with fake CLIs; never access cloud or keys/."""

import json
import os
import subprocess
import tempfile
import unittest
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class DeploymentTests(unittest.TestCase):
    def test_setup_keys_creates_optional_expo_file_and_preserves_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            (temporary / "keys").mkdir()
            existing = temporary / "keys/expo_token"
            existing.touch()
            with existing.open("r+b") as fixture:
                fixture.truncate(64)  # Synthetic bytes; never read a real credential.
            original = existing.stat()
            for _ in range(2):
                completed = subprocess.run(
                    ["make", "-f", str(ROOT / "Makefile"), "setup-keys"],
                    cwd=temporary, capture_output=True, text=True, check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(existing.stat().st_size, original.st_size)
                self.assertEqual(existing.stat().st_mtime_ns, original.st_mtime_ns)
                for name in ("mongodb_uri", "openai_api_key"):
                    self.assertEqual((temporary / "keys" / name).stat().st_size, 0)

    def test_expo_build_waits_and_exports_only_a_successful_apk(self):
        project = json.loads((ROOT / "frontend/app.json").read_text())["expo"]["extra"]["eas"]["projectId"]
        for outcome in ("success", "failed", "invalid", "no-token"):
            with self.subTest(outcome=outcome), tempfile.TemporaryDirectory() as directory:
                temporary = Path(directory)
                env_file = temporary / "runner-env"
                calls = temporary / "calls.json"
                result = [{"status": "FINISHED", "platform": "ANDROID", "buildProfile": "apk",
                           "distribution": "INTERNAL", "app": {"id": project},
                           "artifacts": {"buildUrl": "https://expo.dev/artifacts/eas/test-ci.apk"}}]
                if outcome == "invalid":
                    result[0]["status"] = "ERRORED"
                fake = temporary / "npx"
                fake.write_text(
                    "#!/usr/bin/env python3\nimport json, pathlib, sys\n"
                    f"pathlib.Path({str(calls)!r}).write_text(json.dumps(sys.argv[1:]))\n"
                    f"print({json.dumps(result)!r})\n"
                    f"sys.exit({1 if outcome == 'failed' else 0})\n"
                )
                fake.chmod(0o755)
                completed = subprocess.run(
                    ["bash", "deploy/expo/build-ci.sh"], cwd=ROOT,
                    env={**os.environ, "PATH": f"{temporary}:{os.environ['PATH']}",
                         "EXPO_TOKEN": "test-token-only" if outcome != "no-token" else "",
                         "GITHUB_ENV": str(env_file)},
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(completed.returncode == 0, outcome == "success", completed.stderr)
                self.assertNotIn("test-token-only", completed.stdout + completed.stderr)
                if outcome == "success":
                    self.assertIn("EXPO_PUBLIC_ANDROID_DOWNLOAD_URL=https://expo.dev/artifacts/eas/test-ci.apk", env_file.read_text())
                    arguments = json.loads(calls.read_text())
                    for flag in ("--wait", "--json", "--non-interactive", "--freeze-credentials"):
                        self.assertIn(flag, arguments)
                else:
                    self.assertFalse(env_file.exists())
                if outcome == "no-token":
                    self.assertFalse(calls.exists())

    def test_ci_preflight_requires_firebase_region_and_consistent_model_prices(self):
        valid = {
            "WIF_PROVIDER": "projects/123/locations/global/workloadIdentityPools/github/providers/test",
            "DEPLOYER_SA": "deployer@cloud-test.iam.gserviceaccount.com",
            "PROJECT_ID": "cloud-test",
            "REGION": "us-east4",
            "NEWS_FIREBASE_PROJECT_ID": "auth-test",
            "EXPO_PUBLIC_FIREBASE_API_KEY": "public-fixture",
            "EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN": "auth-test.firebaseapp.com",
            "EXPO_PUBLIC_FIREBASE_PROJECT_ID": "auth-test",
            "EXPO_PUBLIC_FIREBASE_APP_ID": "public-app-fixture",
            "CHATBOT_PROVIDER": "openai",
            "NEWS_CHAT_INPUT_USD_PER_MILLION": "0.25",
            "NEWS_CHAT_OUTPUT_USD_PER_MILLION": "2.00",
        }
        for overrides, expected in (
            ({}, 0),
            ({"REGION": ""}, 1),
            ({"EXPO_PUBLIC_FIREBASE_APP_ID": ""}, 1),
            ({"EXPO_PUBLIC_FIREBASE_PROJECT_ID": "other-test"}, 1),
            ({"NEWS_CHAT_INPUT_USD_PER_MILLION": ""}, 1),
            ({"NEWS_CHAT_OUTPUT_USD_PER_MILLION": "invalid"}, 1),
        ):
            with self.subTest(overrides=overrides):
                result = subprocess.run(
                    ["bash", "deploy/gcp/check-ci-config.sh"], cwd=ROOT,
                    env={**os.environ, **valid, **overrides},
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertNotIn("public-fixture", result.stdout + result.stderr)

    def test_ci_hosting_uses_cloud_run_urls_and_stops_on_lookup_failure(self):
        for fail_lookup in (False, True):
            with self.subTest(fail_lookup=fail_lookup), tempfile.TemporaryDirectory() as directory:
                temporary = Path(directory)
                calls = temporary / "calls.jsonl"
                for name in ("gcloud", "node", "npm", "firebase"):
                    executable = temporary / name
                    executable.write_text(
                        "#!/usr/bin/env python3\n"
                        "import json, os, sys\n"
                        "name = os.path.basename(sys.argv[0])\n"
                        "with open(os.environ['DEPLOY_TEST_CALLS'], 'a') as output:\n"
                        "    output.write(json.dumps({'name': name, 'args': sys.argv[1:], 'news': os.getenv('EXPO_PUBLIC_NEWS_API_BASE_URL'), 'chat': os.getenv('EXPO_PUBLIC_ASSISTANT_API_BASE_URL'), 'dotenv': os.getenv('EXPO_NO_DOTENV')}) + '\\n')\n"
                        "if name == 'gcloud':\n"
                        "    if os.environ['FAIL_LOOKUP'] == '1': sys.exit(1)\n"
                        "    print('https://' + sys.argv[4] + '.example.test')\n"
                    )
                    executable.chmod(0o755)
                result = subprocess.run(
                    ["bash", "deploy/firebase/ci.sh"], cwd=ROOT,
                    env={
                        **os.environ,
                        "PATH": f"{directory}:{os.environ['PATH']}",
                        "DEPLOY_TEST_CALLS": str(calls),
                        "PROJECT_ID": "cloud-test",
                        "NEWS_FIREBASE_PROJECT_ID": "auth-test",
                        "FAIL_LOOKUP": "1" if fail_lookup else "0",
                    }, text=True, capture_output=True, check=False,
                )
                self.assertTrue(calls.exists(), result.stderr)
                commands = [json.loads(line) for line in calls.read_text().splitlines()]
                if fail_lookup:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual([command["name"] for command in commands], ["gcloud"])
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual([command["name"] for command in commands], ["gcloud", "gcloud", "node", "npm", "firebase"])
                    for command in commands[2:]:
                        self.assertEqual(command["news"], "https://news-api.example.test")
                        self.assertEqual(command["chat"], "https://news-chatbot.example.test")
                        self.assertEqual(command["dotenv"], "1")
                    self.assertIn("auth-test", commands[-1]["args"])

    def test_bootstrap_grants_hosting_roles_to_pipeline_on_firebase_project(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            calls = temporary / "calls.jsonl"
            executable = temporary / "gcloud"
            executable.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "with open(os.environ['DEPLOY_TEST_CALLS'], 'a') as output:\n"
                "    output.write(json.dumps(sys.argv[1:]) + '\\n')\n"
                "if 'describe' in sys.argv: print('123456789')\n"
            )
            executable.chmod(0o755)
            result = subprocess.run(
                ["bash", "deploy/gcp/bootstrap.sh"], cwd=ROOT,
                env={
                    **os.environ,
                    "PATH": f"{directory}:{os.environ['PATH']}",
                    "DEPLOY_TEST_CALLS": str(calls),
                    "PROJECT_ID": "cloud-test",
                    "NEWS_FIREBASE_PROJECT_ID": "auth-test",
                    "GITHUB_REPO": "new-owner/news-test",
                }, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            commands = [json.loads(line) for line in calls.read_text().splitlines()]
            expected_condition = "assertion.repository=='new-owner/news-test' && assertion.ref=='refs/heads/main'"
            self.assertTrue(any(
                command[:4] == ["iam", "workload-identity-pools", "providers", "update-oidc"]
                and expected_condition in command for command in commands
            ), "Existing WIF provider must follow repository transfers")
            self.assertTrue(any(
                command[:3] == ["iam", "service-accounts", "add-iam-policy-binding"]
                and any(value.endswith("/attribute.repository/new-owner/news-test") for value in command)
                for command in commands
            ))
            for role in ("roles/firebasehosting.admin", "roles/serviceusage.apiKeysViewer", "roles/serviceusage.serviceUsageConsumer"):
                self.assertTrue(any(
                    command[:3] == ["projects", "add-iam-policy-binding", "auth-test"]
                    and role in command
                    and "serviceAccount:gh-deployer@cloud-test.iam.gserviceaccount.com" in command
                    for command in commands
                ), role)

    def test_hosting_includes_expo_font_assets_inside_exported_node_modules(self):
        hosting = json.loads((ROOT / "firebase.json").read_text())["hosting"]
        self.assertEqual(hosting["public"], "frontend/dist")
        for asset in (
            "assets/node_modules/@expo-google-fonts/newsreader/600SemiBold/Newsreader_600SemiBold.hash.ttf",
            "assets/node_modules/@expo-google-fonts/roboto/400Regular/Roboto_400Regular.hash.ttf",
        ):
            self.assertFalse(
                any(fnmatch(asset, pattern) for pattern in hosting["ignore"]),
                f"Hosting excludes required Expo font: {asset}",
            )

    def test_make_keeps_local_dotenv_out_of_hosting_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            (temporary / "deploy").symlink_to(ROOT / "deploy", target_is_directory=True)
            (temporary / ".env").write_text(
                "EXPO_PUBLIC_NEWS_API_BASE_URL=http://localhost:8020\n"
                "EXPO_PUBLIC_ASSISTANT_API_BASE_URL=http://localhost:8010\n"
                "NEWS_FIREBASE_PROJECT_ID=local-auth-test\n"
            )
            node = temporary / "node"
            node.write_text(
                "#!/usr/bin/env python3\n"
                "import os, sys\n"
                "assert sys.argv[-1] == 'production-auth-test'\n"
                "assert os.environ['EXPO_PUBLIC_NEWS_API_BASE_URL'] == 'https://api.example.test'\n"
                "assert os.environ['EXPO_PUBLIC_ASSISTANT_API_BASE_URL'] == 'https://chat.example.test'\n"
            )
            node.chmod(0o755)
            result = subprocess.run(
                ["make", "-f", str(ROOT / "Makefile"), "firebase-check-config"],
                cwd=temporary, env={
                    **os.environ,
                    "PATH": f"{directory}:{os.environ['PATH']}",
                    "PROJECT_ID": "cloud-test",
                    "NEWS_FIREBASE_PROJECT_ID": "production-auth-test",
                    "EXPO_PUBLIC_NEWS_API_BASE_URL": "https://api.example.test",
                    "EXPO_PUBLIC_ASSISTANT_API_BASE_URL": "https://chat.example.test",
                },
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_cloud_run_receives_firebase_cors_and_only_current_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            calls = temporary / "calls.jsonl"
            for name in ("gcloud", "docker"):
                executable = temporary / name
                executable.write_text(
                    "#!/usr/bin/env python3\n"
                    "import json, os, sys\n"
                    "with open(os.environ['DEPLOY_TEST_CALLS'], 'a') as output:\n"
                    "    output.write(json.dumps(sys.argv) + '\\n')\n"
                    "if sys.argv[1:4] == ['run', 'services', 'describe']:\n"
                    "    print('https://fixture.run.app')\n"
                )
                executable.chmod(0o755)
            environment = {
                **os.environ,
                "PATH": f"{directory}:{os.environ['PATH']}",
                "DEPLOY_TEST_CALLS": str(calls),
                "PROJECT_ID": "news-deploy-test",
                "NEWS_FIREBASE_PROJECT_ID": "news-auth-test",
                "NEWS_API_ALLOWED_ORIGINS": "https://news-auth-test.web.app,https://portal.example.test",
                "CHATBOT_ALLOWED_ORIGINS": "https://news-auth-test.web.app,https://portal.example.test",
                "CHATBOT_PROVIDER": "stub",
                "ALLOW_PUBLIC": "0",
                "TAG": "test",
            }
            result = subprocess.run(
                ["bash", "deploy/gcp/deploy.sh"], cwd=ROOT, env=environment,
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            commands = [json.loads(line)[1:] for line in calls.read_text().splitlines()]
            deployments = [command for command in commands if command[:2] == ["run", "deploy"]]
            self.assertEqual(len(deployments), 2)
            for command in deployments:
                raw_env = command[command.index("--set-env-vars") + 1]
                delimiter = raw_env.split("^")[1] if raw_env.startswith("^") else ","
                values = raw_env[3:] if raw_env.startswith("^") else raw_env
                variables = dict(item.split("=", 1) for item in values.split(delimiter))
                self.assertEqual(variables["NEWS_FIREBASE_PROJECT_ID"], "news-auth-test")
                cors_key = "NEWS_API_ALLOWED_ORIGINS" if command[2] == "news-api" else "CHATBOT_ALLOWED_ORIGINS"
                self.assertEqual(variables[cors_key], environment[cors_key])
                self.assertNotIn("NEWS_ADMIN_PASSWORD_FILE", variables)
                secrets = command[command.index("--set-secrets") + 1]
                self.assertEqual(secrets, "/secrets/mongodb/uri=news-mongodb-uri:latest")

    def test_hosting_checks_before_export_and_targets_the_auth_project(self):
        for fail_check in (False, True):
            with self.subTest(fail_check=fail_check), tempfile.TemporaryDirectory() as directory:
                temporary = Path(directory)
                calls = temporary / "calls.jsonl"
                for name in ("node", "npm", "firebase"):
                    executable = temporary / name
                    executable.write_text(
                        "#!/usr/bin/env python3\n"
                        "import json, os, sys\n"
                        "with open(os.environ['DEPLOY_TEST_CALLS'], 'a') as output:\n"
                        "    output.write(json.dumps(sys.argv) + '\\n')\n"
                        "if sys.argv[0].endswith('/node') and os.environ['FAIL_CHECK'] == '1':\n"
                        "    sys.exit(1)\n"
                    )
                    executable.chmod(0o755)
                result = subprocess.run(
                    ["bash", "deploy/firebase/hosting.sh"], cwd=ROOT,
                    env={
                        **os.environ,
                        "PATH": f"{directory}:{os.environ['PATH']}",
                        "DEPLOY_TEST_CALLS": str(calls),
                        "PROJECT_ID": "cloud-test",
                        "NEWS_FIREBASE_PROJECT_ID": "auth-test",
                        "FAIL_CHECK": "1" if fail_check else "0",
                    },
                    text=True, capture_output=True, check=False,
                )
                commands = [json.loads(line) for line in calls.read_text().splitlines()]
                self.assertEqual(commands[0][1:], ["frontend/scripts/check-deploy-config.cjs", "auth-test"])
                if fail_check:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(len(commands), 1)
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(commands[1][1:], ["run", "export:web", "--", "--clear"])
                    self.assertEqual(commands[2][1:], [
                        "deploy", "--only", "hosting", "--project", "auth-test", "--config", "firebase.json", "--non-interactive",
                    ])


if __name__ == "__main__":
    unittest.main()
