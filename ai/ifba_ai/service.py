"""User-scoped assistant service facade shared by the GTK client and daemon."""

import json
import threading

from .paths import AppPaths
from .secrets import CredentialStoreError, SecretStore
from .settings import SettingsStore
from .storage import ConversationStore
from .nvidia import CancellationToken, NvidiaClient, NvidiaError, GenerationCancelled
from .nvidia import MULTIMODAL_MODEL
from .visual import VisualContextError, capture_active_window, validate_visual_result


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
        self._start_generation(conversation_id, prompt)

    def list_visible_windows(self):
        from .visual import list_visible_windows
        return list_visible_windows()

    def capture_visual_preview(self, window_id):
        from .visual import active_window_context
        context = active_window_context(window_id=int(window_id))
        image = capture_active_window(context=context)
        return json.dumps({"context": context, "image": image}, ensure_ascii=False)

    def get_active_window_context(self):
        from .visual import active_window_context
        return active_window_context()

    def get_accessible_control_bounds(self, window_id, target_id):
        from .visual import active_window_context
        context = active_window_context(window_id=window_id)
        for control in context.get("controls", []):
            if control.get("id") == target_id:
                bounds = control.get("bounds")
                if (isinstance(bounds, list) and len(bounds) == 4
                        and all(isinstance(value, int) for value in bounds)
                        and bounds[2] > 0 and bounds[3] > 0):
                    return {"bounds": bounds, "name": control.get("name") or control.get("role") or "Controle sugerido"}
                break
        raise VisualContextError("O controle não está mais disponível na janela.")

    def start_visual_generation(self, conversation_id, prompt, image_data_url, serialized_context):
        if not isinstance(serialized_context, str) or len(serialized_context) > 30000:
            raise ValueError("O contexto visual excede o limite permitido.")
        try:
            context = json.loads(serialized_context)
        except (TypeError, ValueError) as error:
            raise ValueError("O contexto da janela não é válido.") from error
        if not isinstance(context, dict) or not isinstance(context.get("window_id"), int):
            raise ValueError("A janela selecionada não é válida.")
        if not isinstance(image_data_url, str) or len(image_data_url) > 256000:
            raise ValueError("A captura visual excede o limite permitido.")
        self._start_generation(conversation_id, prompt, image_data_url=image_data_url,
                               visual_context=context)

    def _start_generation(self, conversation_id, prompt, image_data_url=None, visual_context=None):
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 20000:
            raise ValueError("A mensagem está vazia ou excede o limite permitido.")
        if not self._generation_lock.acquire(False):
            raise ValueError("Já existe uma resposta sendo gerada.")
        token = CancellationToken()
        self._generation = token
        try:
            settings = self.settings.read()
            if visual_context is not None and settings["model_id"] != MULTIMODAL_MODEL:
                raise ValueError("Selecione o modelo multimodal documentado para enviar uma captura.")
            api_key = self.secrets.get()
            self.storage.add_message(conversation_id, "user", prompt.strip())
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
                    settings["education_level"], image_data_url=image_data_url,
                    visual_context=visual_context,
                ):
                    answer.append(chunk)
                    if visual_context is None:
                        self.emit("delta", conversation_id, chunk)
                if token.is_set():
                    raise GenerationCancelled("Geração interrompida.")
                final = "".join(answer)
                if final:
                    if visual_context is None:
                        saved_response = final
                    else:
                        result = validate_visual_result(final, visual_context)
                        saved_response = result["explanation"] + "\n\nPróximo passo: " + result["next_step"]
                        self.emit("guide", conversation_id, json.dumps(result, ensure_ascii=False))
                    self.storage.add_message(conversation_id, "assistant", saved_response)
                self.emit("finished", conversation_id, "")
            except GenerationCancelled:
                if answer:
                    self.storage.add_message(conversation_id, "assistant", "".join(answer))
                self.emit("finished", conversation_id, "interrupted")
            except NvidiaError as error:
                self.emit("failed", conversation_id, str(error))
            except VisualContextError as error:
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
