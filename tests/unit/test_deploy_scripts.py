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
                        "deploy", "--only", "hosting", "--project", "auth-test", "--config", "firebase.json",
                    ])


if __name__ == "__main__":
    unittest.main()
