"""User-scoped assistant service facade shared by the GTK client and daemon."""

import json

from .paths import AppPaths
from .secrets import CredentialStoreError, SecretStore
from .settings import SettingsStore
from .storage import ConversationStore
from .nvidia import CancellationToken, NvidiaClient, NvidiaError, GenerationCancelled

import threading


class AssistantService:
    def __init__(self, paths=None, secret_store=None, nvidia_client=None, emit=None):
        self.paths = paths or AppPaths()
        self.settings = SettingsStore(self.paths)
        self.storage = ConversationStore(self.paths)
        self.secrets = secret_store or SecretStore()
        self.client = nvidia_client or NvidiaClient()
        self.emit = emit or (lambda *_args: None)
        self._generation_lock = threading.Lock()
        self._generation = None

    def status(self):
        try:
            configured = bool(self.secrets.get())
            store_available = True
        except CredentialStoreError:
            configured = False
            store_available = False
        return {"api_key_configured": configured, "credential_store_available": store_available,
                "settings": self.settings.read()}

    def save_settings(self, serialized):
        try:
            values = json.loads(serialized)
        except (TypeError, ValueError) as error:
            raise ValueError("As configurações recebidas não são válidas.") from error
        if not isinstance(values, dict):
            raise ValueError("As configurações precisam ser um objeto.")
        return self.settings.write(values)

    def store_api_key(self, secret):
        self.secrets.store(secret)

    def delete_api_key(self):
        self.secrets.delete()

    def start_generation(self, conversation_id, prompt):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20000:
            raise ValueError("A mensagem está vazia ou excede o limite permitido.")
        if not self._generation_lock.acquire(False):
            raise ValueError("Já existe uma resposta sendo gerada.")
        token = CancellationToken()
        self._generation = token
        try:
            self.storage.add_message(conversation_id, "user", prompt.strip())
            settings = self.settings.read()
            api_key = self.secrets.get()
            history = self.storage.list_messages(conversation_id, limit=24)
        except Exception:
            self._generation = None
            self._generation_lock.release()
            raise

        def run():
            answer = []
            try:
                for chunk in self.client.stream_chat(
                    api_key, settings["model_id"], history, settings["max_tokens"], token,
                    settings["education_level"]
                ):
                    answer.append(chunk)
                    self.emit("delta", conversation_id, chunk)
                if token.is_set():
                    raise GenerationCancelled("Geração interrompida.")
                final = "".join(answer)
                if final:
                    self.storage.add_message(conversation_id, "assistant", final)
                self.emit("finished", conversation_id, "")
            except GenerationCancelled:
                if answer:
                    self.storage.add_message(conversation_id, "assistant", "".join(answer))
                self.emit("finished", conversation_id, "interrupted")
            except NvidiaError as error:
                self.emit("failed", conversation_id, str(error))
            except Exception:
                self.emit("failed", conversation_id, "Ocorreu um erro local ao gerar ou salvar a resposta.")
            finally:
                self._generation = None
                self._generation_lock.release()

        threading.Thread(target=run, name="ifba-ai-generation", daemon=True).start()

    def cancel_generation(self):
        token = self._generation
        if token is None:
            return False
        token.cancel()
        return True
