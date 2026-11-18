"""Native GTK first-run and settings window for the IFBA OS assistant."""

import json
import base64
import sys

try:
    import dbus
    import gi
    gi.require_version("Gtk", "3.0")
    from dbus.mainloop.glib import DBusGMainLoop
    from gi.repository import GdkPixbuf, GLib, Gtk, Pango
except ImportError:
    sys.stderr.write("A interface exige GTK 3 e D-Bus Python instalados.\n")
    raise SystemExit(1)


BUS_NAME = "org.ifba.OS.AI"
OBJECT_PATH = "/org/ifba/OS/AI"
INTERFACE = "org.ifba.OS.AI1"


class AssistantWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="Assistente IFBA OS")
        self.set_default_size(860, 580)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.proxy = None
        self.bus = None
        self.current_conversation = None
        self.generating = False
        self.last_visual_context = None
        self.guide_target_id = None
        self.highlight_overlay = None
        self.highlight_restore_source = None
        self._build()
        self._connect_service()

    def _build(self):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root)
        header = Gtk.HeaderBar(title="Assistente IFBA OS")
        header.set_show_close_button(True)
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
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)
        body.pack_start(self.stack, True, True, 0)
        self.chat_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.chat_page.set_border_width(28)
        self.stack.add_named(self.chat_page, "chat")
        self.messages_view = Gtk.TextView()
        self.messages_view.set_editable(False)
        self.messages_view.set_cursor_visible(False)
        self.messages_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.messages_buffer = self.messages_view.get_buffer()
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
        settings_button = Gtk.Button(label="Configurações")
        settings_button.connect("clicked", lambda *_: self.stack.set_visible_child_name("settings"))
        header.pack_end(settings_button)
        self.visual_button = Gtk.Button(label="Orientação visual")
        self.visual_button.set_tooltip_text("Capturar a janela ativa, revisar a prévia e decidir se deseja enviá-la à NVIDIA")
        self.visual_button.set_sensitive(False)
        self.visual_button.connect("clicked", self._capture_visual)
        header.pack_start(self.visual_button)
        self.status = Gtk.Label(label="Conectando ao serviço do assistente…")
        self.status.set_xalign(0)
        self.status.set_margin_start(18)
        self.status.set_margin_end(18)
        self.status.set_margin_top(8)
        self.status.set_margin_bottom(8)
        root.pack_end(self.status, False, False, 0)

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
        self.model = Gtk.ComboBoxText.new_with_entry()
        self.model.append("deepseek-ai/deepseek-v4.1-flash", "DeepSeek V4.1 Flash")
        self.model.append("microsoft/phi-4-multimodal-instruct", "Microsoft Phi-4 Multimodal")
        self.model.set_active_id("deepseek-ai/deepseek-v4.1-flash")
        page.pack_start(self.model, False, False, 0)

        self.tokens = Gtk.SpinButton.new_with_range(1, 32768, 256)
        self.tokens.set_value(2048)
        page.pack_start(Gtk.Label(label="Limite máximo de tokens por resposta", xalign=0), False, False, 0)
        page.pack_start(self.tokens, False, False, 0)

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

        privacy = Gtk.Label(label="Não enviamos capturas de tela ou arquivos automaticamente. Você pode continuar usando o sistema sem configurar IA.")
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
        save.get_style_context().add_class("suggested-action")
        save.connect("clicked", self._save_settings)
        actions.add(save)
        return page

    def _connect_service(self):
        try:
            DBusGMainLoop(set_as_default=True)
            self.bus = dbus.SessionBus()
            obj = self.bus.get_object(BUS_NAME, OBJECT_PATH)
            self.proxy = dbus.Interface(obj, dbus_interface=INTERFACE)
            self.bus.add_signal_receiver(self._on_delta, signal_name="MessageDelta", dbus_interface=INTERFACE)
            self.bus.add_signal_receiver(self._on_finished, signal_name="GenerationFinished", dbus_interface=INTERFACE)
            self.bus.add_signal_receiver(self._on_failed, signal_name="GenerationFailed", dbus_interface=INTERFACE)
            self.bus.add_signal_receiver(self._on_visual_guide, signal_name="VisualGuide", dbus_interface=INTERFACE)
            configured, store_available, model = self.proxy.GetStatus()
            if not store_available:
                self.status.set_text("Cofre indisponível ou bloqueado. Desbloqueie-o na sessão antes de salvar uma chave.")
            else:
                self.status.set_text("Chave configurada." if configured else "Assistente opcional: configure uma chave ou continue sem IA.")
            self.new_chat.set_sensitive(bool(configured))
            self.visual_button.set_sensitive(bool(configured))
            self._load_settings()
            self._load_conversations()
            if not configured:
                self.stack.set_visible_child_name("settings")
        except Exception:
            self.status.set_text("Não foi possível iniciar o serviço. Verifique a sessão D-Bus e o cofre de credenciais.")
            self.stack.set_visible_child_name("settings")

    def _load_settings(self):
        values = json.loads(str(self.proxy.GetSettings()))
        self.model.get_child().set_text(values["model_id"])
        self.tokens.set_value(values["max_tokens"])
        self.memory.set_active(values["memory_enabled"])
        self.share_app.set_active(values["share_active_application"])
        self.share_system.set_active(values["share_system_profile"])
        self.level.set_active_id(values["education_level"])

    def _load_conversations(self):
        if not self.proxy:
            return
        for child in self.conversation_list.get_children():
            self.conversation_list.remove(child)
        for conversation_id, title, _updated in self.proxy.ListConversations():
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
            self._append_text(("Você" if str(role) == "user" else "Assistente IFBA OS") + "\n" + str(content) + "\n\n")

    def _new_conversation(self, *_):
        if not self.proxy or self.generating:
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
        if not self.proxy or not prompt or self.generating:
            return
        configured, _store, _model = self.proxy.GetStatus()
        if not configured:
            self.status.set_text("Configure sua chave NVIDIA pessoal para iniciar uma conversa.")
            self.stack.set_visible_child_name("settings")
            return
        if not self.current_conversation:
            self.current_conversation = str(self.proxy.CreateConversation(prompt[:60]))
        self.input.set_text("")
        self._append_text("Você\n" + prompt + "\n\nAssistente IFBA OS\n")
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
        if not self.proxy or self.generating:
            return
        selected_model = self.model.get_child().get_text().strip()
        if selected_model != "microsoft/phi-4-multimodal-instruct":
            dialog = Gtk.MessageDialog(transient_for=self, modal=True,
                                       message_type=Gtk.MessageType.INFO,
                                       buttons=Gtk.ButtonsType.CLOSE,
                                       text="Selecione um modelo multimodal para orientação visual.")
            dialog.format_secondary_text(
                "O modelo de texto atual não foi validado para imagens. "
                "A captura só é permitida com Microsoft Phi-4 Multimodal, cuja documentação NVIDIA descreve entrada de imagens."
            )
            dialog.run()
            dialog.destroy()
            self.stack.set_visible_child_name("settings")
            self.model.get_child().set_text("microsoft/phi-4-multimodal-instruct")
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
        self._append_text("Você\n{}\n[Captura autorizada: {}]\n\nAssistente IFBA OS\n".format(prompt, title))
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
        model = self.model.get_child().get_text().strip()
        values = {
            "model_id": model,
            "max_tokens": self.tokens.get_value_as_int(),
            "memory_enabled": self.memory.get_active(),
            "share_active_application": self.share_app.get_active(),
            "share_system_profile": self.share_system.get_active(),
            "education_level": self.level.get_active_id() or "iniciante",
        }
        try:
            key = self.key_entry.get_text().strip()
            if key:
                self.proxy.StoreApiKey(key)
                self.key_entry.set_text("")
            self.proxy.SaveSettings(json.dumps(values, ensure_ascii=False))
            configured, store_available, _ = self.proxy.GetStatus()
            if not store_available:
                self.status.set_text("Configurações salvas, mas o cofre está indisponível; a chave não foi armazenada.")
                return
            self.new_chat.set_sensitive(bool(configured))
            self.status.set_text("Configurações salvas neste usuário.")
            self.stack.set_visible_child_name("chat")
        except Exception:
            self.status.set_text("Não foi possível salvar. Confirme se o cofre está disponível e desbloqueado.")

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
        super().__init__(application_id="org.ifba.OS.Assistant", flags=0)

    def do_activate(self):
        window = AssistantWindow(self)
        window.show_all()
        window.present()


def main():
    AssistantApplication().run(sys.argv)


if __name__ == "__main__":
    main()
