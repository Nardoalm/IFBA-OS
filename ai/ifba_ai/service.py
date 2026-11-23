"""User-scoped assistant service facade shared by the GTK client and daemon."""

import json
import threading
from pathlib import Path

from .paths import AppPaths
from .secrets import CredentialStoreError, SecretStore
from .settings import DEFAULTS, SettingsStore, validate_settings
from .storage import ConversationStore
from .nvidia import CancellationToken, NvidiaClient, NvidiaError, GenerationCancelled
from .nvidia import MAX_RESPONSE_BYTES
from .nvidia import MULTIMODAL_MODELS
from .visual import VisualContextError, capture_active_window, validate_visual_result

LIVE_DEMO_MARKER = Path("/etc/ifba-os/live-demo")


class AssistantService:
    def __init__(self, paths=None, secret_store=None, nvidia_client=None, emit=None,
                 live_demo_marker=LIVE_DEMO_MARKER):
        self.paths = paths or AppPaths()
        self.live_demo = Path(live_demo_marker).is_file()
        self.settings = SettingsStore(self.paths)
        self.storage = ConversationStore(self.paths, in_memory=self.live_demo)
        self._ephemeral_settings = dict(DEFAULTS)
        self._ephemeral_api_key = None
        self.secrets = secret_store or SecretStore()
        self.client = nvidia_client or NvidiaClient()
        from .tools import SystemTools
        self.tools = SystemTools()
        self.emit = emit or (lambda *_args: None)
        self._generation_lock = threading.Lock()
        self._generation = None

    def status(self):
        if self.live_demo:
            return {"api_key_configured": bool(self._ephemeral_api_key),
                    "credential_store_available": True,
                    "live_demo": True,
                    "settings": dict(self._ephemeral_settings)}
        try:
            configured = bool(self.secrets.get())
            store_available = True
        except CredentialStoreError:
            configured = False
            store_available = False
        return {"api_key_configured": configured, "credential_store_available": store_available,
                "live_demo": False, "settings": self.settings.read()}

    def get_settings(self):
        if self.live_demo:
            return dict(self._ephemeral_settings)
        return self.settings.read()

    def require_installed_session(self):
        if self.live_demo:
            raise ValueError("Este recurso está disponível após instalar o IFBA OS.")

    def save_settings(self, serialized):
        try:
            values = json.loads(serialized)
        except (TypeError, ValueError) as error:
            raise ValueError("As configurações recebidas não são válidas.") from error
        if self.live_demo:
            self._ephemeral_settings = validate_settings(values)
            return dict(self._ephemeral_settings)
        return self.settings.write(values)

    def store_api_key(self, secret):
        if self.live_demo:
            cleaned = (secret or "").strip()
            if not cleaned:
                raise CredentialStoreError("Informe uma chave da API NVIDIA válida.")
            self._ephemeral_api_key = cleaned
            return
        self.secrets.store(secret)

    def delete_api_key(self):
        if self.live_demo:
            self._ephemeral_api_key = None
            return
        self.secrets.delete()

    def start_generation(self, conversation_id, prompt):
        self._start_generation(conversation_id, prompt)

    def list_visible_windows(self):
        self.require_installed_session()
        from .visual import list_visible_windows
        return list_visible_windows()

    def capture_visual_preview(self, window_id):
        self.require_installed_session()
        from .visual import active_window_context
        context = active_window_context(window_id=int(window_id))
        image = capture_active_window(context=context)
        return json.dumps({"context": context, "image": image}, ensure_ascii=False)

    def get_active_window_context(self):
        self.require_installed_session()
        from .visual import active_window_context
        return active_window_context()

    def get_accessible_control_bounds(self, window_id, target_id):
        self.require_installed_session()
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
        self.require_installed_session()
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
            settings = self.get_settings()
            if visual_context is not None and settings["model_id"] not in MULTIMODAL_MODELS:
                raise ValueError("Selecione o modelo multimodal documentado para enviar uma captura.")
            use_demo_reply = False
            if self.live_demo:
                api_key = self._ephemeral_api_key
                use_demo_reply = not bool(api_key)
            else:
                api_key = self.secrets.get()
            self.storage.add_message(conversation_id, "user", prompt.strip())
            history = self.storage.build_bounded_context(
                conversation_id,
                max_messages=settings["context_max_messages"],
                max_chars=settings["context_max_chars"],
            )
        except Exception:
            self._generation = None
            self._generation_lock.release()
            raise

        def run():
            answer = []
            answer_bytes = 0
            try:
                stream = (
                    self._stream_demo_reply(prompt.strip())
                    if use_demo_reply
                    else self.client.stream_chat(
                        api_key, settings["model_id"], history, settings["max_tokens"], token,
                        settings["education_level"], image_data_url=image_data_url,
                        visual_context=visual_context,
                        reasoning_level=settings["reasoning_level"],
                        educational_context=self._educational_context(
                            prompt, conversation_id, include_memories=not self.live_demo and settings["memory_enabled"]),
                    )
                )
                for chunk in stream:
                    if token.is_set():
                        raise GenerationCancelled("Geração interrompida.")
                    if not isinstance(chunk, str) or len(chunk) > MAX_RESPONSE_BYTES:
                        raise NvidiaError("A resposta excedeu o limite permitido.")
                    chunk_bytes = len(chunk.encode("utf-8"))
                    if answer_bytes + chunk_bytes > MAX_RESPONSE_BYTES:
                        raise NvidiaError("A resposta excedeu o limite permitido.")
                    answer_bytes += chunk_bytes
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

    def _educational_context(self, query, conversation_id, include_memories):
        payload = {}
        summary = self.storage.conversation_summary(conversation_id)
        if summary:
            payload["conversation_summary"] = summary
        memories = self.storage.search_memories(query, limit=8) if include_memories else []
        if memories:
            payload["memories"] = [
                {"category": item["category"], "content": item["content"],
                 "inferred": bool(item["inferred"])} for item in memories
            ]
        if not payload:
            return ""
        return "Memórias que o estudante pode revisar/corrigir: " + json.dumps(payload,
            ensure_ascii=False, separators=(",", ":"))

    def _stream_demo_reply(self, prompt):
        lower = prompt.lower()
        if any(word in lower for word in ("código", "codigo", "python", "bug", "erro", "programar")):
            reply = (
                "### Análise em Modo Demonstração (IFBA AI)\n\n"
                "Recebi sua solicitação de programação. No IFBA OS você pode depurar e testar código diretamente no **Terminal** ou no **VSCodium**:\n\n"
                "```python\n"
                "def saudacao_ifba(nome: str) -> str:\n"
                "    return f\"Olá, {nome}! Bem-vindo ao IFBA OS.\"\n"
                "```\n\n"
                "Se quiser testar modelos NVIDIA NIM na nuvem durante a sessão Live, informe uma chave temporária em **Configurações** (ela fica apenas na memória desta sessão)."
            )
        elif any(word in lower for word in ("resuma", "resumir", "texto", "documento")):
            reply = (
                "### Resumo em Modo Demonstração (IFBA AI)\n\n"
                "Posso organizar textos, destacar pontos-chave e estruturar tópicos de estudo:\n\n"
                "- **Ideia central:** síntese objetiva do conteúdo enviado\n"
                "- **Pontos principais:** conceitos e definições essenciais\n"
                "- **Próximo passo:** revisão rápida ou geração de perguntas\n\n"
                "Para respostas completas via nuvem NVIDIA NIM, adicione uma chave temporária em **Configurações** ou instale o sistema."
            )
        elif any(word in lower for word in ("plano", "estudo", "estudar", "prova")):
            reply = (
                "### Plano de Estudo (Modo Demonstração)\n\n"
                "Sugestão de roteiro em 3 blocos:\n"
                "1. **Fundamentos (25 min):** leitura ativa e anotações dos conceitos centrais.\n"
                "2. **Prática (30 min):** resolução de exercícios no caderno ou no VSCodium.\n"
                "3. **Revisão (15 min):** resumo com suas próprias palavras.\n\n"
                "Adicione uma chave temporária em **Configurações** para receber um plano personalizado da NVIDIA."
            )
        else:
            reply = (
                f"### IFBA AI · Modo Demonstração (Live)\n\n"
                f"Sua pergunta foi recebida: *\"{prompt[:180]}\"*\n\n"
                "Nesta sessão Live, as conversas ficam apenas na memória do serviço. "
                "Para usar os modelos completos da NVIDIA NIM agora mesmo, você pode inserir uma chave temporária em **Configurações**."
            )
        words = reply.split(" ")
        for index, word in enumerate(words):
            yield word if index == 0 else " " + word
