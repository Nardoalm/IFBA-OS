# IFBA OS educational assistant

## Status

The assistant is an optional native GTK/XFCE feature. Source includes a per-user D-Bus service, GTK settings/chat/visual guidance, private conversation persistence, and Secret Service adapter. Stage 2 implements NVIDIA streaming chat, cancellation, bounded text context, and user-readable error handling. Stage 3 source adds local window selection, AT-SPI metadata, two-step screenshot confirmation, multimodal routing, structured response validation, and a temporary overlay. No authenticated live request or VM desktop check has been made.

## User interface

Launch `ifba-ai-ui` from the applications menu, panel launcher, or `Ctrl+Alt+I`. The GTK window allows the user to store or remove a personal NVIDIA API key, select a model ID, set a response-token ceiling, choose a learning level, and control memory/context preferences. The chat has conversation history, new/select conversation, streaming output, send, and stop controls. It also offers “Agora não.” No chat window opens automatically during login.

The password-style key field is cleared after storage. Existing secrets are never read back into the UI. A locked or unavailable Secret Service is surfaced; the application never writes a key to settings, SQLite, environment files, command-line arguments, or logs.

## NVIDIA API contract for Stage 2

Research checked on 2026-11-18 against NVIDIA's current official docs:

- Hosted endpoint base: `https://integrate.api.nvidia.com/v1`.
- Chat request: `POST /chat/completions` with a `model`, `messages`, `max_tokens`, and `stream` fields.
- NVIDIA documents this LLM endpoint as OpenAI Chat Completions compatible and shows Bearer credentials.
- With `stream: true`, the endpoint returns SSE partial deltas terminated by `data: [DONE]`.
- The model-specific endpoint reference identifies DeepSeek V4.1 Flash as `deepseek-ai/deepseek-v4.1-flash`; availability, permitted request fields, model caps, account entitlement, and endpoint behavior can change. Validate a model at runtime or from the authenticated model catalog; do not assume every model supports vision or tools.

Sources: [NVIDIA LLM API reference](https://docs.api.nvidia.com/nim/reference/llm-apis), [DeepSeek V4.1 Flash endpoint reference](https://docs.api.nvidia.com/nim/reference/nvidia-deepseek-v4_1-flash-infer), and [NVIDIA API Catalog quickstart](https://docs.api.nvidia.com/nim/docs/api-quickstart).

The image-capable route was checked against NVIDIA's [Phi-4 Multimodal endpoint reference](https://docs.api.nvidia.com/nim/reference/microsoft-phi-4-multimodal-instruct-infer), which documents image content and streaming for that model-specific endpoint.

The client posts the educational system instruction, selected level, model ID, output ceiling, and bounded recent text messages. It streams SSE deltas and handles cancellation, bounded retries for rate limits/transient service failures, timeouts, invalid models, authentication, account access, and connectivity failures. Retries stop after a response starts. Model identifiers are syntax-validated; real availability and entitlement are checked by NVIDIA at request time. Context is capped at 24 recent messages and 24,000 characters. Model-specific limits can be lower.

Visual guidance requires `microsoft/phi-4-multimodal-instruct`, whose official NVIDIA reference documents image input and SSE; its model-specific endpoint is used. Other models, including the default DeepSeek text model, cannot receive screenshots through this client. The student selects one local application window, agrees to capture it, reviews a preview, and separately confirms sending it to NVIDIA. The image is held in memory, resized and JPEG-compressed below 140 KiB, and never written to disk or SQLite. Login/password windows are blocked when detected from title or AT-SPI2. The model receives the selected window's accessible control names and must return JSON with a target ID from that control list; local code rejects invalid IDs and re-queries bounds before showing a temporary click-through outline. No controls are clicked or typed into.

The project has not made an authenticated real request. API tests use mocked HTTP; no key is included in tests. Live connectivity, account entitlement, latency, pricing, image acceptance, and real NVIDIA behavior remain unverified. The visual feature needs a real X11/AT-SPI integration check; focus-change monitoring, selected-region capture, and tutorial-state detection remain open.

## Data paths

- Configuration: `~/.config/ifba-ai/settings.json` (mode `0600`). Contains model ID, max output tokens, learning level, and opt-in booleans only.
- Data: `~/.local/share/ifba-ai/assistant.sqlite3` (mode `0600`, directory mode `0700`). Schema version 1 provides conversations, messages, and editable memory records.
- Credentials: user's Secret Service keyring, via `secret-tool`. There is no plaintext fallback.
- Cache: `~/.cache/ifba-ai/` (mode `0700`); no screen captures are currently written.

## D-Bus API

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the name/interface and current methods. D-Bus only communicates within the logged-in user's session; the service runs as that user and is hardened through a systemd user unit. Extend the current contract rather than creating another database or daemon.

## Educational behavior and safety

The current system prompt answers in Portuguese by default, explains concepts and steps, adapts to the selected learning level, encourages understanding, discloses uncertainty, and says it cannot claim system actions. User-provided pages/documents/screens are data, not authorization. No arbitrary shell, silent installation, automatic screen sharing, or unsupervised privileged actions are available.
