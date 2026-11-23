import io
import json
import os
from importlib.util import find_spec
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from ifba_ai.model_registry import DEFAULT_MODEL, MODELS
from ifba_ai.preview_catalog import CATALOG_URL, MAX_CATALOG_BYTES, available_models


class PreviewCatalogTests(unittest.TestCase):
    def test_public_catalog_excludes_unknown_and_unlisted_models(self):
        supported = next(model for model in MODELS if model != DEFAULT_MODEL)

        def opener(request, timeout):
            self.assertEqual(request.full_url, CATALOG_URL)
            self.assertEqual(request.get_method(), "GET")
            self.assertFalse(request.has_header("Authorization"))
            self.assertEqual(timeout, 8)
            return io.BytesIO(json.dumps({"data": [{"id": supported}, {"id": "other/model"}]}).encode())

        self.assertEqual(available_models(opener), (supported,))

    def test_invalid_or_unavailable_catalog_does_not_restore_old_options(self):
        for payload in (b"[]", b'{"data": [{}]}', b"x" * (MAX_CATALOG_BYTES + 1)):
            with self.subTest(size=len(payload)), self.assertRaisesRegex(ValueError, "NVIDIA indisponível"):
                available_models(lambda *_args, **_kwargs: io.BytesIO(payload))

        def disconnected(*_args, **_kwargs):
            raise URLError("detalhes da rede")

        with self.assertRaisesRegex(ValueError, "NVIDIA indisponível"):
            available_models(disconnected)

    def test_current_launcher_opens_redesign_with_explicit_classic_action(self):
        root = Path(__file__).resolve().parents[1]
        desktop = (root / "packaging/ifba-ai.desktop").read_text()
        self.assertIn("\nExec=/usr/bin/ifba-ai-ui\n", desktop)
        self.assertIn("[Desktop Action Classic]\n", desktop)
        self.assertIn("\nExec=/usr/bin/ifba-ai-ui --interface-classica\n", desktop)
        launcher = (root / "packaging/ifba-ai-ui").read_text()
        self.assertIn('-m ifba_ai.ui "$@"', launcher)
        self.assertTrue(launcher.strip().endswith('-m ifba_ai.ui_preview "$@"'))


@unittest.skipUnless(
    all(find_spec(module) for module in ("gi", "dbus", "markdown_it", "pygments"))
    and bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")),
    "requires GTK 3, Markdown packages and a graphical session",
)
class PreviewGtkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ifba_ai.ui import Gio, Gtk
        cls.application = Gtk.Application(application_id="org.ifba.OS.Preview.Tests",
                                          flags=Gio.ApplicationFlags.NON_UNIQUE)
        cls.application.register()

    def setUp(self):
        from ifba_ai.ui_preview import PreviewWindow
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        config = patch.dict(os.environ, {"XDG_CONFIG_HOME": temporary.name})
        config.start()
        self.addCleanup(config.stop)
        self.window = PreviewWindow(self.application)
        self.window.show_all()
        self.addCleanup(self.window.destroy)

    def test_untrusted_markdown_is_plain_local_content(self):
        from ifba_ai.preview_messages import MARKDOWN, SyntaxTreeNode, code_markup, inline_markup

        source = '# <b>literal</b> [rótulo](https://example.org/)\n\n![alt](https://example.org/x.png)'
        nodes = SyntaxTreeNode(MARKDOWN.parse(source)).children
        markup = "".join(inline_markup(node.children) for node in nodes)
        self.assertIn("&lt;b&gt;literal&lt;/b&gt;", markup)
        self.assertIn("rótulo", markup)
        self.assertIn("alt", markup)
        self.assertNotIn("https:", markup)
        self.assertNotIn("<b>literal", markup)
        self.assertIn("&lt;", code_markup("print('x < y')", "python", True))

    def test_live_allows_interactive_demo_and_does_not_persist_appearance(self):
        window = self.window
        with patch.object(window, "_refresh_catalog") as refresh:
            window._on_service_status(False, True, True, DEFAULT_MODEL)
            refresh.assert_not_called()
        self.assertTrue(window.input.get_sensitive())
        self.assertTrue(window.suggestions.get_sensitive())
        self.assertTrue(window.data_button.get_sensitive())
        self.assertFalse(window.visual_button.get_sensitive())
        window.appearance_control.set_active_id("light")
        self.assertFalse(window.dark)
        self.assertFalse(window.appearance_file.exists())

    def test_rejected_async_send_preserves_draft(self):
        model = next(model for model in MODELS if model != DEFAULT_MODEL)

        class Proxy:
            def CreateConversation(self, _title, reply_handler, **_kwargs):
                reply_handler("test-conversation")

            def StartGeneration(self, _conversation, _prompt, error_handler, **_kwargs):
                error_handler()

            def ListMessages(self, _conversation, **_kwargs):
                return []

        window = self.window
        window.service_ready = window.configured = True
        window.saved_model = model
        window.catalog = (model,)
        window.proxy = Proxy()
        window.input.set_text("Minha pergunta")
        window._send_message()
        self.assertEqual(window.input.get_text(), "Minha pergunta")
        self.assertFalse(window.generating)
        self.assertIn("Não foi possível iniciar", window.status.get_text())
