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

    def stream_chat(self, *arguments, **kwargs):
        self.arguments = arguments
        self.options = kwargs
        yield "Resposta "
        yield "de teste."


class FakeVisualStreamingClient(FakeStreamingClient):
    def stream_chat(self, *arguments, **kwargs):
        self.arguments = arguments
        self.options = kwargs
        yield '{"explanation":"Abra File.","next_step":"Escolha New Class.",'
        yield '"target_id":"control-1","confidence":0.9,"needs_confirmation":true}'


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
            self.assertIsNone(client.options["image_data_url"])
            self.assertTrue(Path(home, ".local/share/ifba-ai/assistant.sqlite3").exists())

    def test_visual_generation_keeps_image_ephemeral_and_validates_control(self):
        with tempfile.TemporaryDirectory() as home:
            events = []
            done = threading.Event()
            def emit(event, conversation_id, value):
                events.append((event, conversation_id, value))
                if event in ("finished", "failed"):
                    done.set()
            client = FakeVisualStreamingClient()
            service = AssistantService(
                paths=AppPaths(home=home, env={"HOME": home}),
                secret_store=FakeSecretStore(), nvidia_client=client, emit=emit,
            )
            settings = service.settings.read()
            settings["model_id"] = "deepseek-ai/deepseek-v4.1-flash"
            service.settings.write(settings)
            conversation_id = service.storage.create_conversation("Eclipse")
            image = "data:image/jpeg;base64,YQ=="
            context = {"window_id": 42, "application": "eclipse", "controls": [
                {"id": "control-1", "role": "menu item", "name": "New Class", "bounds": [10, 20, 100, 30]}]}
            service.start_visual_generation(conversation_id, "Como crio uma classe?", image,
                                            __import__("json").dumps(context))
            self.assertTrue(done.wait(2), "visual generation worker did not finish")
            messages = service.storage.list_messages(conversation_id)
            self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
            self.assertNotIn("data:image", " ".join(message["content"] for message in messages))
            self.assertIn(("guide", conversation_id,
                           '{"explanation": "Abra File.", "next_step": "Escolha New Class.", '
                           '"target_id": "control-1", "confidence": 0.9, "needs_confirmation": true}'), events)
            self.assertEqual(client.options["image_data_url"], image)


if __name__ == "__main__":
    unittest.main()
