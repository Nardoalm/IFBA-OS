import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai.ifba_ai.paths import AppPaths
from ai.ifba_ai.secrets import CredentialStoreError, SecretStore
from ai.ifba_ai.settings import DEFAULTS, SettingsError, SettingsStore
from ai.ifba_ai.storage import ConversationStore, SCHEMA_VERSION


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def paths_for(self, name):
        return AppPaths(home=self.root / name, env={})

    def test_xdg_directories_and_database_are_private(self):
        paths = self.paths_for("student")
        store = ConversationStore(paths)
        conversation = store.create_conversation()
        store.add_message(conversation, "user", "Explain Java classes")
        self.assertEqual(stat.S_IMODE(paths.config.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(paths.data.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(paths.database.stat().st_mode), 0o600)
        self.assertEqual(store.list_messages(conversation)[0]["content"], "Explain Java classes")

    def test_sqlite_schema_migration_and_conversation_persistence(self):
        paths = self.paths_for("student")
        store = ConversationStore(paths)
        identifier = store.create_conversation("Java")
        store.add_message(identifier, "user", "Como crio uma classe?")
        reopened = ConversationStore(paths)
        self.assertEqual(reopened.list_conversations()[0]["id"], identifier)
        self.assertEqual(reopened.list_messages(identifier)[0]["role"], "user")
        self.assertEqual(SCHEMA_VERSION, 1)

    def test_separate_linux_users_get_separate_databases_and_settings(self):
        first = self.paths_for("matricula-1")
        second = self.paths_for("matricula-2")
        ConversationStore(first).create_conversation("Private to first")
        SettingsStore(first).write(dict(DEFAULTS, education_level="avancado"))
        self.assertEqual(ConversationStore(second).list_conversations(), [])
        self.assertEqual(SettingsStore(second).read()["education_level"], "iniciante")
        self.assertNotEqual(first.database, second.database)

    def test_settings_reject_invalid_token_limit_and_write_mode_0600(self):
        paths = self.paths_for("student")
        settings = SettingsStore(paths)
        settings.write(DEFAULTS)
        self.assertEqual(stat.S_IMODE(paths.settings.stat().st_mode), 0o600)
        with self.assertRaises(SettingsError):
            settings.write(dict(DEFAULTS, max_tokens=0))
        with self.assertRaises(SettingsError):
            settings.write(dict(DEFAULTS, api_key="never persist secrets here"))
        self.assertNotIn("api_key", json.loads(paths.settings.read_text(encoding="utf-8")))

    def test_memory_is_scoped_to_private_database(self):
        store = ConversationStore(self.paths_for("student"))
        identifier = store.add_memory("learning_preference", "Prefers examples", inferred=True)
        self.assertEqual(store.list_memories()[0]["id"], identifier)
        self.assertEqual(store.list_memories()[0]["inferred"], 1)

    def test_relative_xdg_path_is_rejected(self):
        with self.assertRaises(ValueError):
            AppPaths(home=self.root / "student", env={"XDG_CONFIG_HOME": "relative-config"})

    @patch("ai.ifba_ai.secrets.shutil.which", return_value="/usr/bin/secret-tool")
    def test_secret_is_passed_via_stdin_and_never_command_arguments(self, _which):
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        secret = "nvapi-example-not-real"
        SecretStore(runner=runner, username="matricula").store(secret)
        command, kwargs = calls[0]
        self.assertNotIn(secret, command)
        self.assertEqual(kwargs["input"], secret)
        self.assertIn("--label=IFBA OS NVIDIA API key", command)

    @patch("ai.ifba_ai.secrets.shutil.which", return_value="/usr/bin/secret-tool")
    def test_missing_secret_and_locked_store_are_distinguished(self, _which):
        def missing(command, **kwargs):
            return type("Result", (), {"returncode": 1, "stdout": "", "stderr": ""})()

        self.assertIsNone(SecretStore(runner=missing).get())

        def locked(command, **kwargs):
            return type("Result", (), {"returncode": 1, "stdout": "", "stderr": "secret service locked"})()

        with self.assertRaises(CredentialStoreError):
            SecretStore(runner=locked).get()

    @patch("ai.ifba_ai.secrets.shutil.which", return_value="/usr/bin/secret-tool")
    def test_secret_service_errors_are_redacted(self, _which):
        secret = "nvapi-example-not-real"

        def failure(command, **kwargs):
            return type("Result", (), {"returncode": 1, "stdout": "", "stderr": secret})()

        with self.assertRaises(CredentialStoreError) as raised:
            SecretStore(runner=failure).store(secret)
        self.assertNotIn(secret, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
