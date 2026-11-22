"""Native GTK first-run and settings window for the IFBA OS assistant."""

import json
import base64
import os
import sys
import traceback

try:
    import dbus
    import gi
    gi.require_version("Gtk", "3.0")
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import Gdk, GdkPixbuf, GLib, Gio, Gtk, Pango
except ImportError:
    sys.stderr.write("A interface exige GTK 3 e D-Bus Python instalados.\n")
    raise SystemExit(1)
except Exception:
    sys.stderr.write("Não foi possível iniciar GTK/D-Bus do IFBA AI:\n")
    traceback.print_exc(file=sys.stderr)
    raise SystemExit(1)


BUS_NAME = "org.ifba.OS.AI"
OBJECT_PATH = "/org/ifba/OS/AI"
INTERFACE = "org.ifba.OS.AI1"

from .tools import SystemTools
from .model_registry import DEFAULT_MODEL, MODELS, REASONING_LEVELS


class AssistantWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="IFBA AI")
        self.set_default_size(860, 580)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.proxy = None
        self.bus = None
        self.service_connection_started = False
        self.live_demo = False
        self.current_conversation = None
        self.generating = False
        self.last_visual_context = None
        self.guide_target_id = None
        self.highlight_overlay = None
        self.highlight_restore_source = None
        self.local_tools = SystemTools()
        self._build()

    def _build(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root)
        header = Gtk.HeaderBar(title="IFBA AI")
        header.set_show_close_button(True)
        # Keep the native GTK titlebar, but expose the full window controls
        # (minimize, maximize/restore and close) instead of close alone.
        header.set_decoration_layout("close,minimize,maximize:")
        self.set_titlebar(header)

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.pack_start(body, True, True, 0)
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        sidebar.set_size_request(220, -1)
        sidebar.get_style_context().add_class("sidebar")
        sidebar.set_border_width(18)
        body.pack_start(sidebar, False, False, 0)
        title = Gtk.Label()
        title.set_markup("<b>Conversas</b>")
        title.set_xalign(0)
        sidebar.pack_start(title, False, False, 4)
        self.new_chat = Gtk.Button(label="＋  Nova conversa")
        self.new_chat.set_sensitive(False)
        self.new_chat.connect("clicked", self._new_conversation)
        sidebar.pack_start(self.new_chat, False, False, 0)
        self.conversation_list = Gtk.ListBox()
        self.conversation_list.connect("row-activated", self._select_conversation)
        sidebar.pack_start(self.conversation_list, True, True, 0)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.stack.set_transition_duration(0)
        body.pack_start(self.stack, True, True, 0)
        self.chat_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.chat_page.set_border_width(28)
        self.stack.add_named(self.chat_page, "chat")
        self.messages_view = Gtk.TextView()
        self.messages_view.set_editable(False)
        self.messages_view.set_cursor_visible(False)
        self.messages_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.messages_buffer = self.messages_view.get_buffer()
        self.messages_buffer.set_text(
            "IFBA AI\n\nConectando ao serviço do assistente…"
        )
        self.messages_scroll = Gtk.ScrolledWindow()
        self.messages_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.messages_scroll.add(self.messages_view)
        self.chat_page.pack_start(self.messages_scroll, True, True, 0)
        composer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.input = Gtk.Entry()
        self.input.set_placeholder_text("Pergunte sobre uma disciplina ou aplicativo…")
        self.input.connect("activate", self._send_message)
        composer.pack_start(self.input, True, True, 0)
        self.send_button = Gtk.Button(label="Enviar")
        self.send_button.get_style_context().add_class("suggested-action")
        self.send_button.connect("clicked", self._send_message)
        composer.pack_start(self.send_button, False, False, 0)
        self.stop_button = Gtk.Button(label="Interromper")
        self.stop_button.set_sensitive(False)
        self.stop_button.connect("clicked", self._cancel_generation)
        composer.pack_start(self.stop_button, False, False, 0)
        self.highlight_button = Gtk.Button(label="Destacar controle")
        self.highlight_button.set_sensitive(False)
        self.highlight_button.connect("clicked", self._highlight_suggested_control)
        composer.pack_start(self.highlight_button, False, False, 0)
        self.chat_page.pack_end(composer, False, False, 0)

        self.settings_page = self._build_settings()
        settings_scroll = Gtk.ScrolledWindow()
        settings_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        settings_scroll.add(self.settings_page)
        self.stack.add_named(settings_scroll, "settings")
        self.stack.set_visible_child_name("chat")
        settings_button = Gtk.Button(label="Configurações")
        settings_button.connect("clicked", lambda *_: self.stack.set_visible_child_name("settings"))
        header.pack_end(settings_button)
        self.data_button = Gtk.Button(label="Memórias e dados")
        self.data_button.connect("clicked", self._manage_data)
        header.pack_end(self.data_button)
        self.tools_button = Gtk.Button(label="Ferramentas")
        self.tools_button.connect("clicked", self._open_tools)
        header.pack_end(self.tools_button)
        self.visual_button = Gtk.Button(label="Orientação visual")
        self.visual_button.set_tooltip_text("Capturar a janela ativa, revisar a prévia e decidir se deseja enviá-la à NVIDIA")
        self.visual_button.set_sensitive(False)
        self.visual_button.connect("clicked", self._capture_visual)
        header.pack_start(self.visual_button)
        status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status = Gtk.Label(label="Preparando o assistente…")
        self.status.set_xalign(0)
        self.status.set_margin_start(18)
        self.status.set_margin_end(18)
        self.status.set_margin_top(8)
        self.status.set_margin_bottom(8)
        status_row.pack_start(self.status, True, True, 0)
        self.retry_service_button = Gtk.Button(label="Tentar novamente")
        self.retry_service_button.set_no_show_all(True)
        self.retry_service_button.connect("clicked", self._retry_service)
        status_row.pack_end(self.retry_service_button, False, False, 0)
        root.pack_end(status_row, False, False, 0)

    def _build_settings(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        page.set_border_width(28)
        heading = Gtk.Label()
        heading.set_markup("<span size='x-large' weight='bold'>Configurar assistente</span>")
        heading.set_xalign(0)
        page.pack_start(heading, False, False, 0)

        intro = Gtk.Label(label="A IA é opcional. Sua chave será guardada no cofre de credenciais deste usuário.")
        intro.set_xalign(0)
        intro.set_line_wrap(True)
        page.pack_start(intro, False, False, 0)

        key_label = Gtk.Label(label="Chave NVIDIA API", xalign=0)
        page.pack_start(key_label, False, False, 0)
        self.key_entry = Gtk.Entry()
        key_label.set_mnemonic_widget(self.key_entry)
        self.key_entry.set_visibility(False)
        self.key_entry.set_input_purpose(Gtk.InputPurpose.PASSWORD)
        self.key_entry.set_placeholder_text("Cole sua chave pessoal; ela não será exibida novamente")
        page.pack_start(self.key_entry, False, False, 0)

        page.pack_start(Gtk.Label(label="Modelo", xalign=0), False, False, 0)
        self.model = Gtk.ComboBoxText()
        for model_id, metadata in MODELS.items():
            self.model.append(model_id, metadata["title"])
        self.model.set_active_id(DEFAULT_MODEL)
        self.model.connect("changed", self._update_model_hint)
        page.pack_start(self.model, False, False, 0)

        self.model_hint = Gtk.Label(xalign=0)
        self.model_hint.set_line_wrap(True)
        page.pack_start(self.model_hint, False, False, 0)

        page.pack_start(Gtk.Label(label="Nível de raciocínio", xalign=0), False, False, 0)
        reasoning_group = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        reasoning_group.set_layout(Gtk.ButtonBoxStyle.CENTER)
        reasoning_group.get_style_context().add_class("linked")
        page.pack_start(reasoning_group, False, False, 0)
        self.reasoning_buttons = {}
        labels = {"off": "Off", "low": "Baixo", "medium": "Médio", "high": "Alto"}
        for level in REASONING_LEVELS:
            button = Gtk.ToggleButton(label=labels[level])
            button.connect("toggled", self._on_reasoning_toggled, level)
            reasoning_group.add(button)
            self.reasoning_buttons[level] = button
        self.reasoning_buttons["off"].set_active(True)

        self.deep_mode_hint = Gtk.Label(xalign=0)
        self.deep_mode_hint.set_line_wrap(True)
        self.deep_mode_hint.get_style_context().add_class("dim-label")
        page.pack_start(self.deep_mode_hint, False, False, 0)
        self.reasoning_privacy = Gtk.Label(
            label="As respostas podem explicar conclusões e passos úteis; raciocínio interno bruto não é exibido."
        )
        self.reasoning_privacy.set_xalign(0)
        self.reasoning_privacy.set_line_wrap(True)
        self.reasoning_privacy.get_style_context().add_class("dim-label")
        page.pack_start(self.reasoning_privacy, False, False, 0)

        self.tokens = Gtk.SpinButton.new_with_range(1, 32768, 256)
        self.tokens.set_value(2048)
        page.pack_start(Gtk.Label(label="Limite máximo de tokens por resposta", xalign=0), False, False, 0)
        page.pack_start(self.tokens, False, False, 0)

        self.context_messages = Gtk.SpinButton.new_with_range(2, 100, 1)
        self.context_chars = Gtk.SpinButton.new_with_range(1000, 100000, 1000)
        self.history_retention = Gtk.SpinButton.new_with_range(0, 3650, 30)
        self.memory_retention = Gtk.SpinButton.new_with_range(0, 3650, 30)
        for label, widget in (("Mensagens recentes por conversa", self.context_messages),
                              ("Limite de caracteres enviados", self.context_chars),
                              ("Retenção do histórico (dias; 0 = apagar ao salvar)", self.history_retention),
                              ("Retenção das memórias (dias; 0 = apagar ao salvar)", self.memory_retention)):
            page.pack_start(Gtk.Label(label=label, xalign=0), False, False, 0)
            page.pack_start(widget, False, False, 0)

        self.memory = Gtk.CheckButton(label="Ativar memória educacional nesta conta")
        self.memory.set_active(False)
        page.pack_start(self.memory, False, False, 0)
        self.share_app = Gtk.CheckButton(label="Permitir compartilhar o nome do aplicativo ativo quando eu pedir ajuda")
        self.share_app.set_active(False)
        page.pack_start(self.share_app, False, False, 0)
        self.share_system = Gtk.CheckButton(label="Permitir compartilhar versão do sistema e ambiente gráfico")
        self.share_system.set_active(False)
        page.pack_start(self.share_system, False, False, 0)

        self.level = Gtk.ComboBoxText()
        for key, label in (("iniciante", "Iniciante"), ("intermediario", "Intermediário"),
                           ("avancado", "Avançado")):
            self.level.append(key, label)
        self.level.set_active_id("iniciante")
        page.pack_start(Gtk.Label(label="Nível de aprendizagem", xalign=0), False, False, 0)
        page.pack_start(self.level, False, False, 0)

        privacy = Gtk.Label(label="A memória começa desligada e só guarda registros que você criar. Com ela ligada, memórias relevantes e o resumo local desta conversa podem ser enviados à NVIDIA junto das mensagens recentes. Capturas e arquivos nunca são enviados automaticamente.")
        privacy.set_xalign(0)
        privacy.set_line_wrap(True)
        page.pack_start(privacy, False, False, 8)
        actions = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        actions.set_layout(Gtk.ButtonBoxStyle.END)
        page.pack_end(actions, False, False, 0)
        skip = Gtk.Button(label="Agora não")
        skip.connect("clicked", lambda *_: self.stack.set_visible_child_name("chat"))
        actions.add(skip)
        remove = Gtk.Button(label="Remover chave")
        remove.connect("clicked", self._remove_key)
        actions.add(remove)
        save = Gtk.Button(label="Salvar configurações")
        self.save_settings_button = save
        save.get_style_context().add_class("suggested-action")
        save.connect("clicked", self._save_settings)
        actions.add(save)
        return page

    def _selected_reasoning_level(self):
        return next((level for level, button in self.reasoning_buttons.items()
                     if button.get_active()), "off")

    def _on_reasoning_toggled(self, button, level):
        if button.get_active():
            for other_level, other_button in self.reasoning_buttons.items():
                if other_level != level and other_button.get_active():
                    other_button.set_active(False)
        self._update_model_hint()

    def _update_model_hint(self, *_args):
        if not hasattr(self, "model_hint") or not hasattr(self, "deep_mode_hint"):
            return
        model_id = self.model.get_active_id() or DEFAULT_MODEL
        metadata = MODELS.get(model_id, MODELS[DEFAULT_MODEL])
        self.model_hint.set_text(metadata["subtitle"])
        deep_mode = model_id == "moonshotai/kimi-k3.1-pro" and self._selected_reasoning_level() in ("medium", "high")
        self.deep_mode_hint.set_text(
            "Modo profundo: respostas podem levar alguns segundos" if deep_mode else ""
        )

    def _connect_service(self):
        if self.service_connection_started:
            return False
        self.service_connection_started = True
        self.retry_service_button.hide()
        self.status.set_text("Conectando ao serviço do assistente…")
        try:
            DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SessionBus()
            obj = self.bus.get_object(BUS_NAME, OBJECT_PATH, introspect=False)
            self.proxy = dbus.Interface(obj, dbus_interface=INTERFACE)
            self.bus.add_signal_receiver(self._on_delta, signal_name="MessageDelta", dbus_interface=INTERFACE)
            self.bus.add_signal_receiver(self._on_finished, signal_name="GenerationFinished", dbus_interface=INTERFACE)
            self.bus.add_signal_receiver(self._on_failed, signal_name="GenerationFailed", dbus_interface=INTERFACE)
            self.bus.add_signal_receiver(self._on_visual_guide, signal_name="VisualGuide", dbus_interface=INTERFACE)
            self.proxy.GetStatus(
                reply_handler=self._on_service_status,
                error_handler=self._on_service_error,
                timeout=5,
            )
        except Exception:
            self._on_service_error()
        return False

    def _retry_service(self, *_args):
        self.service_connection_started = False
        self.proxy = None
        self.bus = None
        self._connect_service()

    def _on_service_status(self, configured, store_available, live_demo, _model):
        self.retry_service_button.hide()
        self.live_demo = bool(live_demo)
        if self.live_demo:
            self.status.set_text(
                "Sessão Live de demonstração: o IFBA AI não armazena chaves, conversas, memórias ou capturas. "
                "Instale o sistema e use uma conta individual para ativar o assistente."
            )
            self.new_chat.set_sensitive(False)
            self.input.set_sensitive(False)
            self.send_button.set_sensitive(False)
            self.visual_button.set_sensitive(False)
            self.data_button.set_sensitive(False)
            self.tools_button.set_sensitive(False)
            self.key_entry.set_sensitive(False)
            self.save_settings_button.set_sensitive(False)
            self.stack.set_visible_child_name("settings")
            return
        if not store_available:
            self.status.set_text("Cofre indisponível ou bloqueado. Desbloqueie-o na sessão antes de salvar uma chave.")
        else:
            self.status.set_text("Chave configurada." if configured else "Assistente opcional: configure uma chave ou continue sem IA.")
        self.data_button.set_sensitive(True)
        self.tools_button.set_sensitive(True)
        self.key_entry.set_sensitive(True)
        self.save_settings_button.set_sensitive(True)
        self.new_chat.set_sensitive(bool(configured))
        self.visual_button.set_sensitive(bool(configured))
        try:
            if not configured:
                self.stack.set_visible_child_name("settings")
            self.proxy.GetSettings(
                reply_handler=self._on_settings_loaded,
                error_handler=self._on_service_error,
                timeout=5,
            )
        except Exception:
            self._on_service_error()

    def _on_settings_loaded(self, serialized):
        try:
            self._load_settings(serialized)
            self.proxy.ListConversations(
                reply_handler=self._on_conversations_loaded,
                error_handler=self._on_service_error,
                timeout=5,
            )
        except Exception:
            self._on_service_error()

    def _on_conversations_loaded(self, conversations):
        self._load_conversations(conversations)
        # A ready service with no selected conversation must still show a
        # useful prompt instead of leaving the dark chat surface empty.
        if self.stack.get_visible_child_name() == "chat" and not self.current_conversation:
            self._display_history()

    def _on_service_error(self, *_details):
        message = (
            "O serviço local do IFBA AI não respondeu.\n\n"
            "Confira se a sessão está conectada e use “Tentar novamente”. "
            "Nenhuma conversa foi iniciada."
        )
        self.messages_buffer.set_text("IFBA AI\n\n" + message)
        self.status.set_text("Serviço do assistente indisponível")
        self.new_chat.set_sensitive(False)
        self.visual_button.set_sensitive(False)
        self.data_button.set_sensitive(False)
        self.tools_button.set_sensitive(False)
        self.save_settings_button.set_sensitive(False)
        self.key_entry.set_sensitive(False)
        self.stack.set_visible_child_name("chat")
        self.retry_service_button.show()

    def _load_settings(self, serialized=None):
        values = json.loads(str(serialized if serialized is not None else self.proxy.GetSettings()))
        self.model.set_active_id(values["model_id"] if values["model_id"] in MODELS else DEFAULT_MODEL)
        for level, button in self.reasoning_buttons.items():
            button.set_active(level == values["reasoning_level"])
        self._update_model_hint()
        self.tokens.set_value(values["max_tokens"])
        self.memory.set_active(values["memory_enabled"])
        self.context_messages.set_value(values["context_max_messages"])
        self.context_chars.set_value(values["context_max_chars"])
        self.history_retention.set_value(values["history_retention_days"])
        self.memory_retention.set_value(values["memory_retention_days"])
        self.share_app.set_active(values["share_active_application"])
        self.share_system.set_active(values["share_system_profile"])
        self.level.set_active_id(values["education_level"])

    def _load_conversations(self, conversations=None):
        if not self.proxy:
            return
        for child in self.conversation_list.get_children():
            self.conversation_list.remove(child)
        rows = conversations if conversations is not None else self.proxy.ListConversations()
        for conversation_id, title, _updated in rows:
            row = Gtk.ListBoxRow()
            row.set_name(str(conversation_id))
            label = Gtk.Label(label=str(title), xalign=0)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_margin_top(8)
            label.set_margin_bottom(8)
            row.add(label)
            self.conversation_list.add(row)
        self.conversation_list.show_all()

    def _append_text(self, text):
        end = self.messages_buffer.get_end_iter()
        self.messages_buffer.insert(end, text)
        self.messages_view.scroll_to_iter(self.messages_buffer.get_end_iter(), 0.0, False, 0.0, 1.0)

    def _display_history(self):
        self.messages_buffer.set_text("")
        if not self.current_conversation:
            self._append_text("Olá, estudante!\n\nFaça uma pergunta para começar uma nova conversa.\n")
            return
        for role, content, _created in self.proxy.ListMessages(self.current_conversation):
            self._append_text(("Você" if str(role) == "user" else "IFBA AI") + "\n" + str(content) + "\n\n")

    def _new_conversation(self, *_):
        if self.live_demo or not self.proxy or self.generating:
            return
        self.current_conversation = str(self.proxy.CreateConversation("Nova conversa"))
        self._load_conversations()
        self._display_history()
        self.stack.set_visible_child_name("chat")

    def _select_conversation(self, _list, row):
        if self.generating:
            return
        self.current_conversation = row.get_name()
        self._display_history()
        self.stack.set_visible_child_name("chat")

    def _send_message(self, *_):
        prompt = self.input.get_text().strip()
        if self.live_demo or not self.proxy or not prompt or self.generating:
            return
        configured, _store, _live_demo, _model = self.proxy.GetStatus()
        if not configured:
            self.status.set_text("Configure sua chave NVIDIA pessoal para iniciar uma conversa.")
            self.stack.set_visible_child_name("settings")
            return
        if not self.current_conversation:
            self.current_conversation = str(self.proxy.CreateConversation(prompt[:60]))
        self.input.set_text("")
        self._append_text("Você\n" + prompt + "\n\nIFBA AI\n")
        self.generating = True
        self.send_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        self.status.set_text("Gerando resposta…")
        try:
            self.proxy.StartGeneration(self.current_conversation, prompt)
        except Exception:
            self._generation_done()
            self.status.set_text("Não foi possível iniciar a resposta. Verifique o serviço do assistente.")
            self._display_history()

    def _cancel_generation(self, *_):
        if self.proxy and self.generating:
            self.proxy.CancelGeneration()
            self.status.set_text("Interrompendo resposta…")

    def _on_delta(self, conversation_id, text):
        if str(conversation_id) == self.current_conversation:
            self._append_text(str(text))

    def _on_finished(self, conversation_id, state):
        if str(conversation_id) == self.current_conversation:
            self._append_text("\n\n")
            self.status.set_text("Resposta interrompida." if str(state) == "interrupted" else "Resposta concluída.")
        self._generation_done()
        self._load_conversations()

    def _on_failed(self, conversation_id, message):
        if str(conversation_id) == self.current_conversation:
            self._append_text("\n\n" + str(message) + "\n")
        self.status.set_text(str(message))
        self._generation_done()
        self._load_conversations()

    def _generation_done(self):
        self.generating = False
        self.send_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)
        self.visual_button.set_sensitive(bool(self.new_chat.get_sensitive()))

    def _capture_visual(self, *_):
        if self.live_demo or not self.proxy or self.generating:
            return
        selected_model = self.model.get_active_id() or DEFAULT_MODEL
        if selected_model not in MODELS:
            dialog = Gtk.MessageDialog(transient_for=self, modal=True,
                                       message_type=Gtk.MessageType.INFO,
                                       buttons=Gtk.ButtonsType.CLOSE,
                                       text="Selecione um modelo multimodal para orientação visual.")
            dialog.format_secondary_text(
                "O modelo atual não está habilitado para imagens. Selecione um dos modelos multimodais disponíveis."
            )
            dialog.run()
            dialog.destroy()
            self.stack.set_visible_child_name("settings")
            return
        try:
            windows = json.loads(str(self.proxy.ListVisibleWindows()))
            selected_context = self._choose_visual_window(windows)
        except Exception:
            selected_context = None
        if selected_context is None:
            return
        consent = Gtk.MessageDialog(transient_for=self, modal=True,
                                    message_type=Gtk.MessageType.WARNING,
                                    buttons=Gtk.ButtonsType.NONE,
                                    text="Revisar antes de compartilhar a janela ativa?")
        consent.format_secondary_text(
            "O IFBA OS tentará capturar somente a janela selecionada ({} · {}) e mostrará uma prévia. "
            "Nada será enviado até você confirmar na próxima tela. Não capture conteúdo privado ou de terceiros."
            .format(selected_context.get("application", "Aplicativo"), selected_context.get("title", "Janela"))
        )
        consent.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        consent.add_button("Capturar prévia", Gtk.ResponseType.ACCEPT)
        response = consent.run()
        consent.destroy()
        if response != Gtk.ResponseType.ACCEPT:
            return
        try:
            data = json.loads(str(self.proxy.CaptureActiveWindowPreview(int(selected_context["window_id"]))))
            context, image = data["context"], data["image"]
            if int(context.get("window_id", 0)) != int(selected_context["window_id"]):
                raise ValueError("A janela selecionada mudou.")
            encoded = image["data_url"].split(",", 1)[1]
            loader = GdkPixbuf.PixbufLoader.new_with_type("jpeg")
            loader.write(base64.b64decode(encoded, validate=True))
            loader.close()
            pixbuf = loader.get_pixbuf()
            if pixbuf is None:
                raise ValueError("A imagem de prévia não pôde ser aberta.")
            width = min(680, pixbuf.get_width())
            height = max(1, int(pixbuf.get_height() * width / pixbuf.get_width()))
            preview = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)
            self._show_visual_preview(context, image, preview)
        except Exception as error:
            message = "A janela ativa não pôde ser capturada com segurança."
            if error.__class__.__name__ == "DBusException":
                message = "O serviço de contexto visual não está disponível nesta sessão."
            dialog = Gtk.MessageDialog(transient_for=self, modal=True,
                                       message_type=Gtk.MessageType.WARNING,
                                       buttons=Gtk.ButtonsType.CLOSE,
                                       text=message)
            dialog.run()
            dialog.destroy()

    def _choose_visual_window(self, windows):
        if not windows:
            dialog = Gtk.MessageDialog(transient_for=self, modal=True,
                                       message_type=Gtk.MessageType.INFO,
                                       buttons=Gtk.ButtonsType.CLOSE,
                                       text="Não há janelas de aplicativos disponíveis para orientar.")
            dialog.run()
            dialog.destroy()
            return None
        dialog = Gtk.Dialog(title="Escolher janela para orientação", transient_for=self, modal=True)
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Continuar", Gtk.ResponseType.ACCEPT)
        box = dialog.get_content_area()
        box.set_spacing(12)
        label = Gtk.Label(label="Escolha qual janela deseja compartilhar. A lista fica apenas neste computador.")
        label.set_line_wrap(True)
        label.set_margin_start(16)
        label.set_margin_end(16)
        label.set_margin_top(16)
        box.pack_start(label, False, False, 0)
        selector = Gtk.ComboBoxText()
        for context in windows:
            title = str(context.get("title") or "Janela sem título")
            app = str(context.get("application") or "Aplicativo")
            selector.append(str(context["window_id"]), "{} — {}".format(app, title))
        selector.set_active(0)
        selector.set_margin_start(16)
        selector.set_margin_end(16)
        selector.set_margin_bottom(16)
        box.pack_start(selector, False, False, 0)
        dialog.show_all()
        response = dialog.run()
        selected_id = selector.get_active_id()
        dialog.destroy()
        if response != Gtk.ResponseType.ACCEPT or not selected_id:
            return None
        return next((context for context in windows
                     if int(context["window_id"]) == int(selected_id)), None)

    def _show_visual_preview(self, context, image, preview):
        title = str(context.get("title") or "Janela sem título")
        application = str(context.get("application") or "Aplicativo desconhecido")
        dialog = Gtk.Dialog(title="Prévia de captura", transient_for=self, modal=True)
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Enviar captura à NVIDIA", Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        box = dialog.get_content_area()
        box.set_spacing(10)
        label = Gtk.Label(label="{} · {}\n\nEsta imagem será enviada à NVIDIA somente após clicar em “Enviar captura à NVIDIA”.".format(application, title))
        label.set_line_wrap(True)
        label.set_xalign(0)
        label.set_margin_start(16)
        label.set_margin_end(16)
        label.set_margin_top(16)
        box.pack_start(label, False, False, 0)
        picture = Gtk.Image.new_from_pixbuf(preview)
        picture.set_tooltip_text("Prévia da imagem capturada; não salva automaticamente em disco")
        picture.set_margin_start(12)
        picture.set_margin_end(12)
        box.pack_start(picture, True, True, 0)
        warning = Gtk.Label(label="A captura fica apenas em memória até a confirmação. Campos de senha são bloqueados quando detectados por AT-SPI2.")
        warning.set_line_wrap(True)
        warning.set_xalign(0)
        warning.set_margin_start(16)
        warning.set_margin_end(16)
        warning.set_margin_bottom(12)
        box.pack_start(warning, False, False, 0)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        if response != Gtk.ResponseType.ACCEPT:
            return
        prompt = self.input.get_text().strip()
        if not prompt:
            self.status.set_text("Escreva uma pergunta antes de enviar a captura.")
            self.input.grab_focus()
            return
        if not self.current_conversation:
            self.current_conversation = str(self.proxy.CreateConversation(prompt[:60]))
        self.input.set_text("")
        self.last_visual_context = context
        self._append_text("Você\n{}\n[Captura autorizada: {}]\n\nIFBA AI\n".format(prompt, title))
        self.generating = True
        self.send_button.set_sensitive(False)
        self.visual_button.set_sensitive(False)
        self.stop_button.set_sensitive(True)
        self.status.set_text("Enviando a captura aprovada e analisando…")
        try:
            self.proxy.StartVisualGeneration(self.current_conversation, prompt,
                                             image["data_url"], json.dumps(context, ensure_ascii=False))
        except Exception:
            self._generation_done()
            self.last_visual_context = None
            self.status.set_text("Não foi possível iniciar a orientação visual.")
            self._display_history()

    def _on_visual_guide(self, conversation_id, serialized_result):
        if str(conversation_id) != self.current_conversation:
            return
        try:
            result = json.loads(str(serialized_result))
            self._append_text("Orientação visual · confiança {:.0f}%\n{}\nPróximo passo: {}\n{}\n\n".format(
                result["confidence"] * 100,
                result["explanation"], result["next_step"],
                "Revise a sugestão antes de agir." if result["needs_confirmation"] else "Confira a sugestão na janela aberta."))
            self.guide_target_id = result["target_id"]
            self.highlight_button.set_sensitive(
                self.guide_target_id is not None and result["confidence"] >= 0.65
                and self.last_visual_context is not None
            )
            self.status.set_text("A orientação veio do modelo; nenhuma ação foi executada.")
        except (ValueError, KeyError, TypeError):
            self.status.set_text("A resposta visual não pôde ser validada.")

    def _highlight_suggested_control(self, *_):
        if self.highlight_overlay is not None:
            self._restore_after_highlight()
            return
        if not self.last_visual_context or not self.guide_target_id:
            return
        try:
            from .overlay import HighlightOverlay
            current = json.loads(str(self.proxy.GetAccessibleControlBounds(
                int(self.last_visual_context["window_id"]), self.guide_target_id)))
            bounds = current["bounds"]
            if (len(bounds) != 4 or any(not isinstance(value, int) for value in bounds)
                    or bounds[2] < 16 or bounds[3] < 16 or bounds[2] > 4000 or bounds[3] > 2000):
                raise ValueError("bounds")
            label = current.get("name") or "Controle sugerido"
            self.hide()
            self.highlight_overlay = HighlightOverlay(bounds, label)
            self.highlight_overlay.connect("destroy", self._highlight_closed)
            self.highlight_button.set_label("Cancelar destaque")
            self.highlight_restore_source = GLib.timeout_add(
                6000, lambda: self._restore_after_highlight(from_timeout=True))
        except Exception:
            self.status.set_text("O controle mudou ou não possui posição acessível; não foi destacado.")

    def _restore_after_highlight(self, *_args, from_timeout=False):
        source = self.highlight_restore_source
        self.highlight_restore_source = None
        if source and not from_timeout:
            try:
                GLib.source_remove(source)
            except Exception:
                pass
        if self.highlight_overlay is not None:
            overlay = self.highlight_overlay
            self.highlight_overlay = None
            overlay.cancel()
        self.highlight_button.set_label("Destacar controle")
        self.show()
        self.present()
        return False

    def _highlight_closed(self, *_args):
        if self.highlight_overlay is None:
            return
        self.highlight_overlay = None
        if self.highlight_restore_source:
            try:
                GLib.source_remove(self.highlight_restore_source)
            except Exception:
                pass
            self.highlight_restore_source = None
        self.highlight_button.set_label("Destacar controle")
        self.show()
        self.present()

    def _save_settings(self, *_):
        if not self.proxy:
            self.status.set_text("O serviço local do assistente não está disponível.")
            return
        model = self.model.get_active_id() or DEFAULT_MODEL
        values = {
            "model_id": model,
            "reasoning_level": self._selected_reasoning_level(),
            "max_tokens": self.tokens.get_value_as_int(),
            "memory_enabled": self.memory.get_active(),
            "share_active_application": self.share_app.get_active(),
            "share_system_profile": self.share_system.get_active(),
            "education_level": self.level.get_active_id() or "iniciante",
            "context_max_messages": self.context_messages.get_value_as_int(),
            "context_max_chars": self.context_chars.get_value_as_int(),
            "history_retention_days": self.history_retention.get_value_as_int(),
            "memory_retention_days": self.memory_retention.get_value_as_int(),
        }
        try:
            key = self.key_entry.get_text().strip()
            if key:
                self.proxy.StoreApiKey(key)
                self.key_entry.set_text("")
            self.proxy.SaveSettings(json.dumps(values, ensure_ascii=False))
            self.proxy.PruneData(values["history_retention_days"], values["memory_retention_days"])
            configured, store_available, live_demo, _ = self.proxy.GetStatus()
            if live_demo:
                self.status.set_text("O IFBA AI não armazena dados na sessão Live compartilhada.")
                return
            if not store_available:
                self.status.set_text("Configurações salvas, mas o cofre está indisponível; a chave não foi armazenada.")
                return
            self.new_chat.set_sensitive(bool(configured))
            self.status.set_text("Configurações salvas neste usuário.")
            self.stack.set_visible_child_name("chat")
        except Exception:
            self.status.set_text("Não foi possível salvar. Confirme se o cofre está disponível e desbloqueado.")

    def _confirm_data_action(self, question):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
                                   message_type=Gtk.MessageType.WARNING,
                                   buttons=Gtk.ButtonsType.CANCEL, text=question)
        dialog.add_button("Confirmar", Gtk.ResponseType.ACCEPT)
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.ACCEPT

    def _manage_data(self, *_):
        if self.live_demo or not self.proxy:
            return
        dialog = Gtk.Dialog(title="Memórias e dados deste usuário", transient_for=self, modal=True)
        dialog.set_default_size(700, 500)
        dialog.add_button("Fechar", Gtk.ResponseType.CLOSE)
        box = dialog.get_content_area()
        box.set_spacing(10)
        intro = Gtk.Label(label="Esses dados ficam no perfil local deste usuário. Memórias inferidas são identificadas e editáveis. A exportação contém conversas e memórias; escolha um local privado.")
        intro.set_line_wrap(True)
        intro.set_margin_start(14)
        intro.set_margin_end(14)
        intro.set_margin_top(12)
        box.pack_start(intro, False, False, 0)
        listing = Gtk.ListBox()
        listing.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(270)
        scroll.add(listing)
        box.pack_start(scroll, True, True, 0)

        def refresh():
            for child in listing.get_children():
                listing.remove(child)
            for item in json.loads(str(self.proxy.ListMemories())):
                row = Gtk.ListBoxRow()
                row.memory_record = item
                inferred = " · inferida (revise)" if item["inferred"] else " · informada por você"
                label = Gtk.Label(label="{} · {}{}\n{}".format(item["category"], item["content"], inferred, item["updated_at"]), xalign=0)
                label.set_line_wrap(True)
                label.set_margin_start(10)
                label.set_margin_end(10)
                label.set_margin_top(8)
                label.set_margin_bottom(8)
                row.add(label)
                listing.add(row)
            listing.show_all()

        actions = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        actions.set_layout(Gtk.ButtonBoxStyle.START)
        box.pack_start(actions, False, False, 8)
        add = Gtk.Button(label="Adicionar")
        edit = Gtk.Button(label="Editar selecionada")
        remove = Gtk.Button(label="Excluir selecionada")
        export = Gtk.Button(label="Exportar dados")
        clear_history = Gtk.Button(label="Apagar histórico")
        clear_memories = Gtk.Button(label="Apagar memórias")
        for button in (add, edit, remove, export, clear_history, clear_memories):
            actions.add(button)

        def form(item=None):
            form_dialog = Gtk.Dialog(title="Editar memória" if item else "Nova memória", transient_for=dialog, modal=True)
            form_dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
            form_dialog.add_button("Salvar", Gtk.ResponseType.ACCEPT)
            fields = form_dialog.get_content_area()
            fields.set_spacing(8)
            category = Gtk.ComboBoxText()
            categories = (("learning_preference", "Preferência de aprendizagem"), ("language", "Linguagem"),
                          ("application", "Aplicativo"), ("learned_topic", "Assunto aprendido"),
                          ("difficulty", "Dificuldade relatada"), ("goal", "Objetivo"),
                          ("project", "Projeto de estudo"), ("other", "Outro"))
            for key, label in categories:
                category.append(key, label)
            category.set_active_id(item["category"] if item else "learning_preference")
            fields.pack_start(Gtk.Label(label="Tipo de memória", xalign=0), False, False, 0)
            fields.pack_start(category, False, False, 0)
            content = Gtk.TextView()
            content.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            content.get_buffer().set_text(item["content"] if item else "")
            content.set_size_request(480, 120)
            fields.pack_start(content, True, True, 0)
            inferred = Gtk.CheckButton(label="Marcar como inferida (deve ser revisada)")
            inferred.set_active(bool(item and item["inferred"]))
            fields.pack_start(inferred, False, False, 0)
            form_dialog.show_all()
            response = form_dialog.run()
            start, end = content.get_buffer().get_bounds()
            text = content.get_buffer().get_text(start, end, True)
            selected_category = category.get_active_id()
            is_inferred = inferred.get_active()
            form_dialog.destroy()
            if response != Gtk.ResponseType.ACCEPT:
                return
            try:
                if item:
                    self.proxy.UpdateMemory(item["id"], selected_category, text, is_inferred)
                else:
                    self.proxy.AddMemory(selected_category, text, is_inferred)
                refresh()
            except Exception:
                self.status.set_text("A memória não pôde ser salva. Evite dados identificadores ou credenciais.")

        add.connect("clicked", lambda *_: form())
        edit.connect("clicked", lambda *_: form(getattr(listing.get_selected_row(), "memory_record", None))
                     if listing.get_selected_row() else None)
        def delete_selected(*_):
            row = listing.get_selected_row()
            item = getattr(row, "memory_record", None) if row else None
            if item and self._confirm_data_action("Excluir esta memória permanentemente?"):
                self.proxy.DeleteMemory(item["id"])
                refresh()
        remove.connect("clicked", delete_selected)
        def export_data(*_):
            chooser = Gtk.FileChooserDialog(title="Exportar dados do assistente", transient_for=dialog,
                                            action=Gtk.FileChooserAction.SAVE)
            chooser.add_button("Cancelar", Gtk.ResponseType.CANCEL)
            chooser.add_button("Salvar", Gtk.ResponseType.ACCEPT)
            chooser.set_current_name("ifba-ai-export.json")
            if chooser.run() == Gtk.ResponseType.ACCEPT:
                try:
                    export_content = str(self.proxy.ExportData())
                    descriptor = os.open(chooser.get_filename(), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                        handle.write(export_content)
                    self.status.set_text("Exportação criada no local escolhido.")
                except FileExistsError:
                    self.status.set_text("O arquivo já existe; escolha outro nome para não sobrescrevê-lo.")
                except Exception:
                    self.status.set_text("A exportação não pôde ser salva.")
            chooser.destroy()
        export.connect("clicked", export_data)
        def clear_history(*_):
            if self._confirm_data_action("Apagar todas as conversas deste usuário? Essa ação não pode ser desfeita."):
                self.proxy.ClearHistory()
                self.current_conversation = None
                self._load_conversations()
                self._display_history()
        clear_history.connect("clicked", clear_history)
        def clear_memories(*_):
            if self._confirm_data_action("Apagar todas as memórias deste usuário? Essa ação não pode ser desfeita."):
                self.proxy.ClearMemories()
                refresh()
        clear_memories.connect("clicked", clear_memories)
        refresh()
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _open_tools(self, *_):
        if self.live_demo or not self.proxy:
            return
        dialog = Gtk.Dialog(title="Ferramentas locais autorizadas", transient_for=self, modal=True)
        dialog.set_default_size(620, 520)
        dialog.add_button("Fechar", Gtk.ResponseType.CLOSE)
        box = dialog.get_content_area()
        box.set_spacing(10)
        info = Gtk.Label(label="As ferramentas são iniciadas por você. Conteúdo de páginas ou documentos não autoriza ações. O assistente não pode executar comandos de terminal nem instalar pacotes.")
        info.set_line_wrap(True)
        info.set_margin_start(14)
        info.set_margin_end(14)
        info.set_margin_top(12)
        box.pack_start(info, False, False, 0)
        result = Gtk.TextView()
        result.set_editable(False)
        result.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(170)
        scroll.add(result)
        box.pack_start(scroll, True, True, 0)
        def show(value):
            result.get_buffer().set_text(json.dumps(value, ensure_ascii=False, indent=2))
        def safe(callback):
            try:
                value = callback()
                if value is not None:
                    show(value)
            except Exception:
                show({"erro": "A ação não pôde ser concluída. Revise a seleção e tente novamente."})
        controls = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.pack_start(controls, False, False, 8)
        def action(label, callback):
            button = Gtk.Button(label=label)
            button.connect("clicked", lambda *_args: safe(lambda: callback(button)))
            controls.pack_start(button, False, False, 0)
        apps = Gtk.ComboBoxText()
        controls.pack_start(apps, False, False, 0)
        def load_apps(*_):
            def load():
                apps.remove_all()
                for item in json.loads(str(self.proxy.ListInstalledApps())):
                    apps.append(item["id"], item["name"])
                if apps.get_model() and apps.get_model().iter_n_children(None):
                    apps.set_active(0)
                show({"aplicativos": apps.get_model().iter_n_children(None) if apps.get_model() else 0})
            safe(load)
        def open_app(*_):
            app_id = apps.get_active_id()
            if app_id:
                safe(lambda: json.loads(str(self.proxy.OpenApp(app_id))))
        action("Listar aplicativos instalados", lambda *_: load_apps())
        action("Abrir aplicativo selecionado", open_app)
        action("Consultar informações básicas do sistema", lambda *_: safe(lambda: json.loads(str(self.proxy.GetSystemInfo()))))
        url_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        url = Gtk.Entry()
        url.set_placeholder_text("https://…")
        url_row.pack_start(url, True, True, 0)
        open_url = Gtk.Button(label="Abrir URL")
        open_url.connect("clicked", lambda *_: safe(lambda: json.loads(str(self.proxy.OpenURL(url.get_text().strip())))))
        url_row.pack_start(open_url, False, False, 0)
        controls.pack_start(url_row, False, False, 0)
        choose = Gtk.Button(label="Escolher pasta para esta sessão")
        controls.pack_start(choose, False, False, 0)
        directory = Gtk.Entry()
        directory.set_placeholder_text("Caminho relativo (vazio = pasta selecionada)")
        controls.pack_start(directory, False, False, 0)
        query = Gtk.Entry()
        query.set_placeholder_text("Nome para localizar dentro da pasta selecionada")
        controls.pack_start(query, False, False, 0)
        action("Listar itens da pasta selecionada", lambda *_: safe(lambda: self.local_tools.list_directory(
            directory.get_text().strip() or ".")))
        action("Localizar arquivos por nome", lambda *_: safe(lambda: self.local_tools.find_files(
            query.get_text().strip())))
        def choose_directory(*_):
            chooser = Gtk.FileChooserDialog(title="Autorizar pasta nesta sessão", transient_for=dialog,
                                            action=Gtk.FileChooserAction.SELECT_FOLDER)
            chooser.add_button("Cancelar", Gtk.ResponseType.CANCEL)
            chooser.add_button("Selecionar", Gtk.ResponseType.ACCEPT)
            if chooser.run() == Gtk.ResponseType.ACCEPT:
                show({"pasta_autorizada": self.local_tools.grant_directory(chooser.get_filename())})
            chooser.destroy()
        choose.connect("clicked", lambda *_args: safe(choose_directory))
        rel = Gtk.Entry()
        rel.set_placeholder_text("nome-do-arquivo.txt (somente na pasta autorizada)")
        content = Gtk.Entry()
        content.set_placeholder_text("Conteúdo para novo arquivo de texto (até 512 KiB)")
        controls.pack_start(rel, False, False, 0)
        controls.pack_start(content, False, False, 0)
        def create_file(*_):
            plan = self.local_tools.prepare_create_file(rel.get_text(), content.get_text())
            if self._confirm_data_action("Criar um novo arquivo em {} ({} bytes)? Arquivos existentes não serão sobrescritos.".format(plan["path"], plan["bytes"])):
                show(self.local_tools.confirm_create_file(plan["confirmation_token"]))
            else:
                show({"cancelled": True, "plan": plan["path"]})
        action("Planejar e confirmar criação de arquivo", create_file)
        setting = Gtk.ComboBoxText()
        for key, label in (("display", "Tela"), ("appearance", "Aparência"), ("keyboard", "Teclado"),
                           ("network", "Rede"), ("sound", "Áudio")):
            setting.append(key, label)
        setting.set_active(0)
        controls.pack_start(setting, False, False, 0)
        action("Abrir configuração selecionada", lambda *_: safe(lambda: json.loads(str(
            self.proxy.OpenSystemSetting(setting.get_active_id())))))
        dialog.show_all()
        try:
            dialog.run()
        except Exception:
            self.status.set_text("A operação local não pôde ser concluída. Confira a pasta autorizada e os parâmetros.")
        dialog.destroy()

    def _remove_key(self, *_):
        if not self.proxy:
            return
        dialog = Gtk.MessageDialog(transient_for=self, modal=True,
                                  message_type=Gtk.MessageType.WARNING,
                                  buttons=Gtk.ButtonsType.CANCEL,
                                  text="Remover a chave NVIDIA deste usuário?")
        dialog.add_button("Remover", Gtk.ResponseType.ACCEPT)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            try:
                self.proxy.DeleteApiKey()
                self.new_chat.set_sensitive(False)
                self.status.set_text("Chave removida do cofre deste usuário.")
            except Exception:
                self.status.set_text("O cofre está indisponível; a chave não foi removida.")


class AssistantApplication(Gtk.Application):
    def __init__(self):
        # Gtk.Application is single-instance by default. HANDLES_COMMAND_LINE
        # makes later menu/desktop/terminal invocations activate the existing
        # window instead of silently exiting without presenting it.
        super().__init__(application_id="org.ifba.OS.Assistant",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

    def do_command_line(self, command_line):
        self.activate()
        return 0

    def do_activate(self):
        try:
            window = self.get_active_window()
            if window is None:
                window = AssistantWindow(self)
                window.show_all()
            window.present()
            GLib.idle_add(window._connect_service)
        except Exception:
            sys.stderr.write("Não foi possível abrir a janela do IFBA AI:\n")
            traceback.print_exc(file=sys.stderr)
            raise

    def do_startup(self):
        Gtk.Application.do_startup(self)
        provider = Gtk.CssProvider()
        css_path = "/usr/share/ifba-os/ifba-ai.css"
        try:
            provider.load_from_path(css_path)
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
        except (GLib.Error, TypeError):
            # Keep the assistant usable if the optional packaged theme is absent.
            pass

def main():
    AssistantApplication().run(sys.argv)


if __name__ == "__main__":
    main()
