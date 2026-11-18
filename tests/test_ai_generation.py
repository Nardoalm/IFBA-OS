import tempfile
import threading
import unittest
from pathlib import Path

from ifba_ai.paths import AppPaths
from ifba_ai.service import AssistantService


class FakeSecretStore:
    def get(self):
        return "test-only-key"


class FakeStreamingClient:
    def __init__(self):
        self.arguments = None

    def stream_chat(self, *arguments):
        self.arguments = arguments
        yield "Resposta "
        yield "de teste."


class GenerationTests(unittest.TestCase):
    def test_generation_streams_and_persists_both_messages_per_user(self):
        with tempfile.TemporaryDirectory() as home:
            events = []
            done = threading.Event()

            def emit(event, conversation_id, value):
                events.append((event, conversation_id, value))
                if event in ("finished", "failed"):
                    done.set()

            client = FakeStreamingClient()
            service = AssistantService(
                paths=AppPaths(home=home, env={"HOME": home}),
                secret_store=FakeSecretStore(), nvidia_client=client, emit=emit,
            )
            conversation_id = service.storage.create_conversation("Java")
            service.start_generation(conversation_id, "Explique classes")
            self.assertTrue(done.wait(2), "generation worker did not finish")
            messages = service.storage.list_messages(conversation_id)
            self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
            self.assertEqual(messages[1]["content"], "Resposta de teste.")
            self.assertEqual([event[0] for event in events], ["delta", "delta", "finished"])
            self.assertEqual(client.arguments[0], "test-only-key")
            self.assertEqual(client.arguments[1], "deepseek-ai/deepseek-v4.1-flash")
            self.assertEqual(client.arguments[2][-1]["content"], "Explique classes")
            self.assertEqual(client.arguments[5], "iniciante")
            self.assertTrue(Path(home, ".local/share/ifba-ai/assistant.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
