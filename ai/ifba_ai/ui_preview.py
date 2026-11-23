"""GTK 3 frontend for the existing IFBA AI D-Bus service."""

import json
from pathlib import Path
from threading import Thread

from .paths import AppPaths
from .preview_catalog import available_models
from .preview_messages import label, render
from .ui import (
    AssistantApplication, AssistantWindow, Gdk, Gio, GLib, Gtk, MODELS, Pango,
)

STYLE = Path("/usr/share/ifba-os/ifba-ai-preview.css")
LOGO = Path("/usr/share/ifba-os/assets/icons/ai-assistant-orb.png")


def box(spacing=0):
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)


def styled(widget, name):
    widget.get_style_context().add_class(name)
    return widget


def icon_button(icon, title, callback):
    button = Gtk.Button()
    button.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
    button.set_tooltip_text(title)
    button.get_accessible().set_name(title)
    button.connect("clicked", callback)
    return styled(button, "flat")


def scrolled(child):
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroll.add(child)
    return scroll


def logo(size):
    image = Gtk.Image()
    if LOGO.is_file():
        from gi.repository import GdkPixbuf
        image.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_scale(str(LOGO), size, size, True))
    return image


class ComposerInput(Gtk.TextView):
    def get_text(self):
        buffer = self.get_buffer()
        return buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)

    def set_text(self, text):
        self.get_buffer().set_text(text)


class PreviewWindow(AssistantWindow):
    def _build(self):
        self.set_default_size(1050, 640)
        self.set_size_request(530, 450)
        styled(self, "ai-preview")
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual is not None and screen.is_composited():
            self.set_visual(visual)
            styled(self, "preview-translucent")
        self.catalog = ()
        self.catalog_pending = False
        self.catalog_error = ""
        self.saved_model = None
        self.configured = False
        self.store_available = False
        self.service_ready = False
        self.active_generation = None
        self.request_pending = False
        self.cancelling = False
        self.streaming_label = None
        self.streaming_body = None
        self.delta_source = 0
        self.message_cards = []
        self.updating_models = False
        self.sidebar_open = True
        self.last_width = 0
        self.appearance_file = AppPaths().config / "preview-appearance"
        self.appearance = self._read_appearance()
        self.system_theme = Gtk.Settings.get_default().get_property("gtk-theme-name")
        self.system_dark = Gtk.Settings.get_default().get_property("gtk-application-prefer-dark-theme")
        self._apply_appearance()

        body = Gtk.Box()
        self.add(body)
        self.sidebar = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_RIGHT,
                                    transition_duration=160, reveal_child=True)
        self.sidebar.set_hexpand(False)
        body.pack_start(self.sidebar, False, False, 0)
        self.sidebar.add(self._build_sidebar())
        main = styled(box(), "preview-content")
        body.pack_start(main, True, True, 0)
        toolbar = styled(Gtk.Box(spacing=3), "preview-toolbar")
        toolbar.pack_end(icon_button("view-sidetree-symbolic", "Alternar barra lateral", self._toggle_sidebar),
                         False, False, 0)
        toolbar.pack_end(icon_button("document-open-recent-symbolic", "Histórico de conversas",
                                     self._open_history), False, False, 0)
        main.pack_start(toolbar, False, False, 0)
        self.stack = Gtk.Stack()
        main.pack_start(self.stack, True, True, 0)
        self._build_chat()

        form = self._build_settings()
        form.set_border_width(0)
        self._group_settings(form)
        self.settings_page = form
        for column in (self.transcript, self.settings_page):
            column.set_margin_start(24)
            column.set_margin_end(24)
        settings_panel = box()
        settings_panel.pack_start(scrolled(form), True, True, 0)
        self.settings_footer = styled(box(6), "settings-footer")
        self.settings_footer.set_margin_start(24)
        self.settings_footer.set_margin_end(24)
        self.settings_footer.pack_start(self.settings_notice, False, False, 0)
        self.settings_footer.pack_end(self.settings_actions, False, False, 0)
        settings_panel.pack_end(self.settings_footer, False, False, 0)
        self.stack.add_named(settings_panel, "settings")
        self._show_page("chat")
        self.connect("size-allocate", self._adapt_sidebar)
        self.stack.connect("notify::visible-child-name", self._update_navigation)
        self.connect("key-press-event", self._window_key)
        self._sync_actions()

    def _build_sidebar(self):
        sidebar = styled(box(11), "preview-sidebar")
        sidebar.set_size_request(264, -1)
        brand = Gtk.Box(spacing=10)
        mark = logo(34)
        brand.pack_start(mark, False, False, 0)
        brand.pack_start(label("IFBA AI", "sidebar-brand"), False, False, 0)
        brand.pack_start(label("Beta", "beta-badge"), False, False, 0)
        sidebar.pack_start(brand, False, False, 4)

        self.new_chat = styled(Gtk.Button(), "primary-action")
        new_row = Gtk.Box(spacing=8)
        new_row.pack_start(Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON), False, False, 0)
        new_row.pack_start(Gtk.Label(label="Nova conversa", xalign=0), True, True, 0)
        new_row.pack_end(label("Ctrl+N", "shortcut-hint"), False, False, 0)
        self.new_chat.add(new_row)
        self.new_chat.connect("clicked", self._new_conversation)
        self.new_chat.set_tooltip_text("Nova conversa (Ctrl+N)")
        sidebar.pack_start(self.new_chat, False, False, 0)
        navigation = box(3)
        self.nav_home = self._nav_button("go-home-symbolic", "Início", self._new_conversation)
        navigation.pack_start(self.nav_home, False, False, 0)
        models = self._nav_button("view-list-symbolic", "Modelos", self._open_models)
        navigation.pack_start(models, False, False, 0)
        self.tools_button = self._nav_button("tools-symbolic", "Ferramentas", self._open_tools)
        navigation.pack_start(self.tools_button, False, False, 0)
        self.data_button = self._nav_button("view-pim-notes-symbolic", "Memórias", self._manage_data)
        navigation.pack_start(self.data_button, False, False, 0)
        self.nav_settings = self._nav_button("preferences-system-symbolic", "Configurações", self._open_settings)
        navigation.pack_start(self.nav_settings, False, False, 0)
        sidebar.pack_start(navigation, False, False, 0)
        sidebar.pack_start(Gtk.Separator(), False, False, 0)
        sidebar.pack_start(label("Conversas recentes", "section-label"), False, False, 0)

        self.conversation_list = styled(Gtk.ListBox(), "history-list")
        self.conversation_list.connect("row-activated", self._select_conversation)
        self.empty_history = label("Suas conversas aparecem aqui.", "muted")
        self.empty_history.set_valign(Gtk.Align.START)
        self.conversation_list.set_placeholder(self.empty_history)
        self.empty_history.show()
        sidebar.pack_start(scrolled(self.conversation_list), True, True, 0)

        profile = styled(Gtk.Box(spacing=10), "local-profile")
        name = GLib.get_real_name() or GLib.get_user_name()
        if name == "Unknown":
            name = GLib.get_user_name()
        avatar = styled(Gtk.Label(label=name[:1].upper()), "profile-avatar")
        avatar.set_size_request(34, 34)
        profile.pack_start(avatar, False, False, 0)
        identity = box(2)
        profile_name = Gtk.Label(label=name, xalign=0, ellipsize=Pango.EllipsizeMode.END)
        identity.pack_start(profile_name, False, False, 0)
        identity.pack_start(label("Conta local do IFBA OS", "muted"), False, False, 0)
        profile.pack_start(identity, True, True, 0)
        sidebar.pack_end(profile, False, False, 0)
        return sidebar

    def _nav_button(self, icon, title, callback):
        button = styled(Gtk.Button(), "nav-item")
        row = Gtk.Box(spacing=10)
        row.pack_start(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON), False, False, 0)
        row.pack_start(Gtk.Label(label=title, xalign=0, wrap=True), True, True, 0)
        button.add(row)
        button.connect("clicked", callback)
        return button

    def _suggestion_button(self, icon, title, subtitle_text, callback):
        button = styled(Gtk.Button(), "nav-item")
        row = Gtk.Box(spacing=10)
        row.pack_start(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON), False, False, 0)
        text_col = box(1)
        text_col.pack_start(label(title, "suggestion-title"), False, False, 0)
        text_col.pack_start(label(subtitle_text, "suggestion-subtitle"), False, False, 0)
        row.pack_start(text_col, True, True, 0)
        button.add(row)
        button.connect("clicked", callback)
        return button

    def _build_chat(self):
        self.chat_page = box(0)
        self.stack.add_named(self.chat_page, "chat")
        self.chat_modes = Gtk.Stack()
        self.chat_page.pack_start(self.chat_modes, True, True, 0)
        self.home = box(10)
        self.home.set_halign(Gtk.Align.FILL)
        self.home.set_valign(Gtk.Align.CENTER)
        self.home.set_margin_start(36)
        self.home.set_margin_end(36)
        self.home.set_margin_top(12)
        self.home.set_margin_bottom(40)
        mark = logo(90)
        mark.set_margin_bottom(6)
        self.home.pack_start(mark, False, False, 0)
        self.home.pack_start(styled(Gtk.Label(label="IFBA AI"), "hero-title"), False, False, 0)
        subtitle = label("Sua assistente de IA integrada ao IFBA OS", "hero-subtitle")
        subtitle.set_xalign(0.5)
        subtitle.set_justify(Gtk.Justification.CENTER)
        subtitle.set_margin_bottom(18)
        self.home.pack_start(subtitle, False, False, 0)
        self.chat_modes.add_named(scrolled(self.home), "home")

        self.transcript = styled(box(18), "transcript")
        self.transcript.set_margin_top(20)
        self.transcript.set_margin_bottom(16)
        self.messages_scroll = scrolled(self.transcript)
        self.chat_modes.add_named(self.messages_scroll, "messages")

        self.composer_area = box(12)
        self.composer = styled(box(8), "composer")
        self.composer_area.pack_start(self.composer, False, False, 0)
        self.input = styled(ComposerInput(wrap_mode=Gtk.WrapMode.WORD_CHAR, accepts_tab=False), "prompt")
        self.input.get_accessible().set_name("Como posso ajudar você hoje?")
        self.input.connect("key-press-event", self._composer_key)
        self.input.get_buffer().connect("changed", self._composer_changed)
        input_scroll = scrolled(self.input)
        input_scroll.set_min_content_height(47)
        input_scroll.set_max_content_height(132)
        input_scroll.set_propagate_natural_height(True)
        editor = Gtk.Overlay()
        editor.add(input_scroll)
        self.placeholder = styled(Gtk.Label(label="Como posso ajudar você hoje?", xalign=0), "placeholder")
        self.placeholder.set_halign(Gtk.Align.START)
        self.placeholder.set_valign(Gtk.Align.START)
        editor.add_overlay(self.placeholder)
        editor.set_overlay_pass_through(self.placeholder, True)
        self.composer.pack_start(editor, False, False, 0)

        controls = Gtk.Box(spacing=6)
        self.composer.pack_end(controls, False, False, 0)
        self.composer_tools = icon_button("preferences-system-symbolic", "Ferramentas", self._open_tools)
        self.visual_button = icon_button("camera-photo-symbolic", "Orientação visual", self._capture_visual)
        self.highlight_button = Gtk.Button(label="Destacar controle")
        self.highlight_button.set_no_show_all(True)
        self.highlight_button.connect("clicked", self._highlight_suggested_control)
        controls.pack_start(self.composer_tools, False, False, 0)
        controls.pack_start(self.visual_button, False, False, 0)
        controls.pack_start(self.highlight_button, False, False, 0)
        self.quick_model = Gtk.ComboBoxText()
        self.quick_model.get_accessible().set_name("Modelo NVIDIA")
        self.quick_model.connect("changed", self._quick_model_changed)
        self.send_button = styled(icon_button("mail-send-symbolic", "Enviar mensagem (Enter)",
                                              self._send_message), "send-action")
        self.stop_button = styled(icon_button("process-stop-symbolic", "Interromper geração",
                                              self._cancel_generation), "send-action")
        self.send_button.set_no_show_all(True)
        self.stop_button.set_no_show_all(True)
        controls.pack_end(self.send_button, False, False, 0)
        controls.pack_end(self.stop_button, False, False, 0)
        controls.pack_end(self.quick_model, False, False, 0)
        self.send_button.get_child().show()
        self.send_button.show()
        self.stop_button.get_child().show()

        self.suggestions = Gtk.FlowBox(max_children_per_line=4, min_children_per_line=2,
                                       selection_mode=Gtk.SelectionMode.NONE,
                                       column_spacing=10, row_spacing=8, homogeneous=True)
        for icon, title, subtitle_text, prompt in (
            ("applications-development-symbolic", "Programar", "e depurar código", "Ajude-me a entender este código:\n"),
            ("text-x-generic-symbolic", "Analisar", "documentos", "Analise e destaque os pontos principais deste texto:\n"),
            ("view-list-symbolic", "Planejar", "um estudo", "Ajude-me a organizar um plano de estudo para "),
            ("help-whatsthis-symbolic", "Explicar", "um conceito", "Explique de forma simples o conceito de "),
        ):
            suggestion = self._suggestion_button(icon, title, subtitle_text,
                                                 lambda _button, value=prompt: self._suggest(value))
            self.suggestions.add(styled(suggestion, "suggestion"))
        self.composer_area.pack_start(self.suggestions, False, False, 0)

        status_row = Gtk.Box(spacing=7)
        self.spinner = Gtk.Spinner()
        self.spinner.set_no_show_all(True)
        status_row.pack_start(self.spinner, False, False, 0)
        self.status = label("Conectando ao serviço do assistente…", "status-text")
        self.status.set_selectable(True)
        status_row.pack_start(self.status, True, True, 0)
        self.retry_service_button = Gtk.Button(label="Tentar novamente")
        self.retry_service_button.set_no_show_all(True)
        self.retry_service_button.connect("clicked", self._retry_service)
        status_row.pack_end(self.retry_service_button, False, False, 0)
        self.open_key = Gtk.Button(label="Configurar NVIDIA")
        self.open_key.set_no_show_all(True)
        self.open_key.connect("clicked", self._open_settings)
        status_row.pack_end(self.open_key, False, False, 0)
        self.composer_area.pack_start(status_row, False, False, 0)
        self.chat_page.pack_end(self.composer_area, False, False, 0)
        self._mount_composer(True)

    def _mount_composer(self, home):
        target = self.home if home else self.chat_page
        parent = self.composer_area.get_parent()
        if parent is not target:
            if parent:
                parent.remove(self.composer_area)
            if home:
                target.pack_start(self.composer_area, False, False, 0)
            else:
                target.pack_end(self.composer_area, False, False, 0)
        self.suggestions.set_no_show_all(not home)
        self.suggestions.set_visible(home)
        self.chat_modes.set_visible_child_name("home" if home else "messages")
        self.composer_area.set_margin_start(0 if home else 24)
        self.composer_area.set_margin_end(0 if home else 24)
        self.composer_area.set_margin_bottom(16)

    def _adapt_sidebar(self, _widget, allocation):
        width = allocation.width
        if (self.last_width < 830) != (width < 830) or not self.last_width:
            self.sidebar_open = width >= 830
            self.sidebar.set_reveal_child(self.sidebar_open)
        self.last_width = width

    def _toggle_sidebar(self, *_):
        self.sidebar_open = not self.sidebar_open
        self.sidebar.set_reveal_child(self.sidebar_open)

    def _open_history(self, *_):
        if not self.sidebar_open:
            self._toggle_sidebar()
        self.conversation_list.grab_focus()

    def _window_key(self, _widget, event):
        if event.keyval in (Gdk.KEY_n, Gdk.KEY_N) and event.state & Gdk.ModifierType.CONTROL_MASK:
            self._new_conversation()
            return True
        return False

    def _composer_key(self, _widget, event):
        if event.keyval not in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            return False
        if event.state & Gdk.ModifierType.SHIFT_MASK:
            return False
        if not self.input.im_context_filter_keypress(event):
            self._send_message()
        return True

    def _composer_changed(self, *_):
        self.placeholder.set_visible(not self.input.get_text())
        self._sync_actions()

    def _suggest(self, prompt):
        if not self.live_demo:
            self.input.set_text(prompt)
            self.input.grab_focus()
            buffer = self.input.get_buffer()
            buffer.place_cursor(buffer.get_end_iter())

    def _show_page(self, name):
        self.stack.set_visible_child_name(name)

    def _update_navigation(self, *_):
        name = self.stack.get_visible_child_name()
        for item, selected in ((self.nav_home, name == "chat"), (self.nav_settings, name == "settings")):
            style = item.get_style_context()
            (style.add_class if selected else style.remove_class)("nav-selected")

    def _open_settings(self, *_):
        self._show_page("settings")

    def _open_models(self, *_):
        self._open_settings()
        self.model.grab_focus()

    def _group_settings(self, form):
        children = form.get_children()
        for child in children:
            form.remove(child)
        heading = label("Configurações", "settings-title")
        form.pack_start(heading, False, False, 0)
        self.settings_notice = label("", "status-text")

        appearance = styled(box(7), "settings-group")
        appearance.pack_start(label("Aparência", "group-title"), False, False, 0)
        self.appearance_control = Gtk.ComboBoxText()
        self.appearance_control.get_accessible().set_name("Aparência do IFBA AI")
        for key, title in (("dark", "Escura"), ("light", "Clara"), ("system", "Do sistema")):
            self.appearance_control.append(key, title)
        self.appearance_control.set_active_id(self.appearance)
        self.appearance_control.connect("changed", self._appearance_changed)
        appearance.pack_start(self.appearance_control, False, False, 0)

        # Reuse the legacy controls and their D-Bus settings bindings.
        model_start = children.index(self.model_section_start)
        privacy_start = children.index(self.privacy_section_start)
        sections = (("Credencial NVIDIA", children[1:model_start]),
                    ("Modelo e raciocínio", children[model_start:privacy_start]),
                    ("Memórias, armazenamento e permissões", children[privacy_start:-1]))
        for index, (name, widgets) in enumerate(sections):
            panel = styled(box(8), "settings-group")
            panel.pack_start(label(name, "group-title"), False, False, 0)
            for widget in widgets:
                panel.pack_start(widget, False, False, 0)
                if isinstance(widget, Gtk.CheckButton):
                    widget.get_child().set_line_wrap(True)
                    widget.get_child().set_max_width_chars(1)
                if widget is self.model_hint:
                    self.catalog_retry = Gtk.Button(label="Atualizar modelos")
                    self.catalog_retry.connect("clicked", self._refresh_catalog)
                    self.catalog_retry.set_halign(Gtk.Align.START)
                    panel.pack_start(self.catalog_retry, False, False, 0)
            if index == 2:
                panel.pack_start(label(
                    "A orientação visual pede para escolher uma janela, revisar a prévia e confirmar o envio à NVIDIA.",
                    "muted"), False, False, 0)
            form.pack_start(panel, False, False, 0)
            if index == 0:
                form.pack_start(appearance, False, False, 0)
        self.settings_actions = children[-1]
        for action in self.settings_actions.get_children():
            self.settings_actions.set_child_non_homogeneous(action, True)
        children[0].destroy()
        self.model.remove_all()
        self.model.connect("changed", lambda *_: self._sync_model_hint())

    def _read_appearance(self):
        try:
            value = self.appearance_file.read_text().strip()
        except (OSError, UnicodeError):
            return "dark"
        return value if value in ("dark", "light", "system") else "dark"

    def _apply_appearance(self):
        settings = Gtk.Settings.get_default()
        self.dark = self.appearance == "dark" or (self.appearance == "system" and (
            self.system_dark or "dark" in self.system_theme.lower()))
        theme = self.system_theme
        if self.appearance != "system" and theme in {"Breeze", "Breeze-Dark"}:
            theme = "Breeze-Dark" if self.dark else "Breeze"
        settings.set_property("gtk-theme-name", theme)
        settings.set_property("gtk-application-prefer-dark-theme", self.dark)
        style = self.get_style_context()
        (style.add_class if self.dark else style.remove_class)("preview-dark")
        (style.remove_class if self.dark else style.add_class)("preview-light")

    def _appearance_changed(self, widget):
        self.appearance = widget.get_active_id()
        self._apply_appearance()
        for role, content, body in self.message_cards:
            if role == "assistant" and body is not self.streaming_body:
                render(body, content, role, self.dark)
        if self.service_ready and not self.live_demo:
            try:
                self.appearance_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                target = Gio.File.new_for_path(str(self.appearance_file))
                target.replace_contents(self.appearance.encode(), None, False, Gio.FileCreateFlags.PRIVATE, None)
            except (OSError, GLib.Error):
                self._set_status("A preferência de aparência vale apenas para esta sessão.")

    def _set_status(self, message, *, error=False):
        for status in (self.status, self.settings_notice):
            status.set_text(message)
            style = status.get_style_context()
            (style.add_class if error else style.remove_class)("status-error")

    def _on_service_status(self, configured, store_available, live_demo, model):
        self.retry_service_button.hide()
        self.live_demo = bool(live_demo)
        self.configured = bool(configured)
        self.store_available = bool(store_available)
        self.saved_model = str(model)
        self.service_ready = True
        if self.live_demo:
            if not self.catalog:
                self.catalog = tuple(MODELS)
            self._sync_actions()
            self._set_status("Modo demonstração (Live) ativo · Respostas locais para teste (Enter para enviar)")
            self.catalog_retry.set_sensitive(False)
            self._update_models()
            self.proxy.GetSettings(reply_handler=self._on_settings_loaded,
                                   error_handler=self._on_service_error, timeout=5)
            return
        self._sync_actions()
        self._ready_status()
        self._refresh_catalog()
        self.proxy.GetSettings(reply_handler=self._on_settings_loaded,
                               error_handler=self._on_service_error, timeout=5)

    def _ready_status(self):
        if self.live_demo:
            if self.configured:
                self._set_status("Modo demonstração (Live) com chave temporária · Enter para enviar")
            else:
                self._set_status("Modo demonstração (Live) ativo · Respostas locais para teste (Enter para enviar)")
        elif not self.store_available:
            self._set_status("Cofre indisponível. Desbloqueie o cofre de credenciais da sessão.")
        elif not self.configured:
            self._set_status("Configure sua chave NVIDIA para iniciar uma conversa.")
        elif self.catalog_error:
            self._set_status(self.catalog_error, error=True)
        elif self.catalog_pending:
            self._set_status("Verificando modelos na NVIDIA…")
        elif self.saved_model not in self.catalog:
            self._set_status("Selecione um modelo disponível na NVIDIA para enviar mensagens.")
        else:
            self._set_status("Enter para enviar · Shift+Enter para nova linha")

    def _on_service_error(self, *_):
        self.service_ready = False
        self._generation_done()
        self._set_status("Serviço local indisponível. Tente conectar novamente.", error=True)
        self.retry_service_button.show()

    def _load_settings(self, serialized=None):
        data = str(serialized if serialized is not None else self.proxy.GetSettings(timeout=5))
        self.saved_model = json.loads(data)["model_id"]
        super()._load_settings(data)
        self._update_models()

    def _refresh_catalog(self, *_):
        if self.live_demo or not self.service_ready or self.catalog_pending:
            return
        self.catalog_pending = True
        self.catalog_error = ""
        self.catalog_retry.set_sensitive(False)
        self._ready_status()
        self._sync_actions()

        def lookup():
            try:
                result, error = available_models(), ""
            except ValueError as failure:
                result, error = (), str(failure)
            GLib.idle_add(self._catalog_loaded, result, error)

        Thread(target=lookup, daemon=True).start()

    def _catalog_loaded(self, result, error):
        self.catalog_pending = False
        self.catalog = result
        self.catalog_error = error or ("" if result else "Nenhum modelo compatível retornado pela NVIDIA.")
        self.catalog_retry.set_sensitive(self.service_ready and not self.live_demo)
        self._update_models()
        if self.service_ready and not self.generating:
            self._ready_status()
        return False

    def _update_models(self):
        self.updating_models = True
        draft = self.model.get_active_id()
        choices = ((self.model, draft if draft in self.catalog else self.saved_model),
                   (self.quick_model, self.saved_model))
        for control, selection in choices:
            control.remove_all()
            title = "Modelos indisponíveis" if self.catalog_error else "Escolher modelo"
            control.append("", title)
            for model_id in self.catalog:
                control.append(model_id, MODELS[model_id]["title"])
            control.set_active_id(selection if selection in self.catalog else "")
        self.updating_models = False
        self._sync_model_hint()
        self._sync_actions()

    def _sync_model_hint(self):
        if not hasattr(self, "catalog_retry"):
            return
        selection = self.model.get_active_id()
        metadata = MODELS.get(selection)
        for button in self.reasoning_buttons.values():
            button.set_sensitive(bool(metadata and metadata.get("reasoning")))
        if metadata:
            self.model_hint.set_text(metadata["subtitle"])
        elif self.live_demo:
            self.model_hint.set_text("Modo demonstração ativo; escolha um modelo para testar.")
        else:
            self.model_hint.set_text(self.catalog_error or "Escolha um modelo do catálogo NVIDIA.")

    def _quick_model_changed(self, control):
        model = control.get_active_id()
        if self.updating_models or model not in self.catalog or model == self.saved_model or self.generating:
            return
        try:
            values = json.loads(str(self.proxy.GetSettings(timeout=5)))
            values["model_id"] = model
            self.proxy.SaveSettings(json.dumps(values), timeout=5)
            self.saved_model = model
            self.model.set_active_id(model)
            self._ready_status()
        except Exception:
            self._set_status("Não foi possível alterar o modelo. A seleção anterior foi preservada.")
        self._update_models()

    def _save_settings(self, *_):
        if not self.service_ready or self.generating:
            return
        values = self._settings_values()
        values["model_id"] = self.model.get_active_id() or self.saved_model
        try:
            key = self.key_entry.get_text().strip()
            if key:
                self.proxy.StoreApiKey(key, timeout=18)
                self.key_entry.set_text("")
            self.proxy.SaveSettings(json.dumps(values, ensure_ascii=False), timeout=5)
            self.saved_model = values["model_id"]
            self.proxy.PruneData(values["history_retention_days"], values["memory_retention_days"], timeout=5)
            configured, store_available, _, _ = self.proxy.GetStatus(timeout=12)
            self.configured, self.store_available = bool(configured), bool(store_available)
            self._load_conversations()
            self._update_models()
            self._set_status("Configurações salvas nesta sessão Live." if self.live_demo else "Configurações salvas neste usuário.")
        except Exception:
            self._set_status("Não foi possível concluir o salvamento. Confira o cofre e o serviço local.")

    def _remove_key(self, *_):
        if not self.service_ready or self.generating:
            return
        super()._remove_key()
        try:
            configured, store_available, _, _ = self.proxy.GetStatus(timeout=12)
            self.configured, self.store_available = bool(configured), bool(store_available)
        except Exception:
            self.configured = False
        self._sync_actions()

    def _sync_actions(self):
        normal = self.service_ready
        idle = normal and not self.generating
        demo_ready = self.live_demo and idle
        ready = demo_ready or (idle and self.configured and self.saved_model in self.catalog and not self.catalog_pending)
        self.new_chat.set_sensitive(not self.generating)
        self.nav_home.set_sensitive(not self.generating)
        self.data_button.set_sensitive(idle)
        self.tools_button.set_sensitive(idle)
        self.composer_tools.set_sensitive(idle)
        self.visual_button.set_sensitive(idle and not self.live_demo and ready and bool(MODELS.get(self.saved_model, {}).get("image")))
        self.input.set_sensitive(True)
        self.input.set_editable(not self.request_pending)
        self.suggestions.set_sensitive(not self.generating)
        self.open_key.set_visible(idle and not self.configured and not self.live_demo)
        self.send_button.set_sensitive(ready and bool(self.input.get_text().strip()))
        self.send_button.set_visible(not self.generating)
        self.stop_button.set_visible(self.generating)
        self.stop_button.set_sensitive(self.generating and not self.request_pending and not self.cancelling)
        self.spinner.set_visible(self.generating)
        (self.spinner.start if self.generating else self.spinner.stop)()
        self.model.set_sensitive(idle and bool(self.catalog))
        self.quick_model.set_sensitive(idle and bool(self.catalog) and not self.catalog_pending)
        self.key_entry.set_sensitive(idle and self.store_available)
        self.settings_actions.set_sensitive(idle)
        self.conversation_list.set_sensitive(idle)

    def _load_conversations(self, conversations=None):
        try:
            super()._load_conversations(conversations)
        except Exception:
            self._set_status("Não foi possível carregar o histórico.")
            return
        for row in self.conversation_list.get_children():
            title = row.get_child()
            row.remove(title)
            title.set_hexpand(True)
            title.set_single_line_mode(True)
            line = Gtk.Box(spacing=8)
            line.pack_start(Gtk.Image.new_from_icon_name("dialog-messages-symbolic",
                                                        Gtk.IconSize.MENU), False, False, 0)
            line.pack_start(title, True, True, 0)
            row.add(line)
            row.show_all()
            if row.get_name() == self.current_conversation:
                self.conversation_list.select_row(row)

    def _new_conversation(self, *_):
        if self.generating:
            return
        if self.current_conversation:
            self.input.set_text("")
        self.current_conversation = None
        self.conversation_list.unselect_all()
        self._display_history()
        self._show_page("chat")
        self.input.grab_focus()

    def _select_conversation(self, _list, row):
        if not self.generating and self.service_ready:
            self.current_conversation = row.get_name()
            self._display_history()
            self._show_page("chat")
            if self.last_width < 830 and self.sidebar_open:
                self._toggle_sidebar()

    def _display_history(self):
        for child in self.transcript.get_children():
            child.destroy()
        self.message_cards.clear()
        self.highlight_button.hide()
        self.guide_target_id = self.last_visual_context = None
        self._mount_composer(not self.current_conversation)
        if self.current_conversation:
            try:
                for role, content, _ in self.proxy.ListMessages(self.current_conversation, timeout=5):
                    self._add_message(str(role), str(content))
            except Exception:
                self._set_status("Não foi possível abrir esta conversa.")
            self._scroll_end()

    def _add_message(self, role, content, streaming=False):
        card = styled(box(8), "message-user" if role == "user" else "message-assistant")
        card.pack_start(label("Você" if role == "user" else "IFBA AI", "message-author"), False, False, 0)
        body = box(10)
        card.pack_start(body, False, False, 0)
        self.transcript.pack_start(card, False, False, 0)
        card.show_all()
        if streaming:
            self.streaming_body = body
            self.streaming_label = label()
            self.streaming_label.set_selectable(True)
            body.pack_start(self.streaming_label, False, False, 0)
            self.streaming_label.show()
            self.pending_text = []
            self.delta_source = 0
        else:
            self.message_cards.append((role, content, body))
            render(body, content, role, self.dark)
        return body

    def _append_text(self, text):
        # Reused visual guide callback displays its validated explanation and next step.
        if self.streaming_label:
            self.pending_text.append(str(text))
            self.streaming_label.set_text("".join(self.pending_text)[-32000:])
        else:
            self._add_message("assistant", str(text))

    def _submit_visual_capture(self, context, image, title):
        self._submit(self.input.get_text().strip(), context=context, image=image, title=title)

    def _send_message(self, *_):
        self._submit(self.input.get_text().strip())

    def _submit(self, prompt, *, context=None, image=None, title=""):
        if not self.service_ready or self.generating or not prompt:
            return
        if len(prompt) > 20000:
            self._set_status("A mensagem ultrapassa o limite de 20 mil caracteres.")
            return
        if not self.live_demo:
            if not self.configured:
                self._open_settings()
                return
            if self.saved_model not in self.catalog or self.catalog_pending:
                self._ready_status()
                return
        self.request_pending = True
        self.generating = True
        self._sync_actions()
        self._set_status("Preparando a conversa…")

        def rejected(*_details):
            if self.active_generation and not self.input.get_text():
                self.input.set_text(self.sent_prompt)
            self._generation_done()
            self._display_history()
            self._set_status("Não foi possível iniciar a resposta. Confira o serviço e a credencial NVIDIA.",
                             error=True)

        def accepted(_started):
            if self.active_generation is not None:
                self.request_pending = False
                self._sync_actions()

        def start(conversation_id):
            self.current_conversation = str(conversation_id)
            self._begin_response(prompt, context, title)
            parameters = (self.current_conversation, prompt)
            options = dict(reply_handler=accepted, error_handler=rejected, timeout=15)
            try:
                if context is None:
                    self.proxy.StartGeneration(*parameters, **options)
                else:
                    self.proxy.StartVisualGeneration(*parameters, image["data_url"],
                                                     json.dumps(context, ensure_ascii=False), **options)
            except Exception:
                rejected()

        try:
            if self.current_conversation:
                start(self.current_conversation)
            else:
                title = " ".join(prompt.split())[:60]
                self.proxy.CreateConversation(title, reply_handler=start, error_handler=rejected, timeout=5)
        except Exception:
            rejected()

    def _begin_response(self, prompt, context, title):
        self.active_generation = self.current_conversation
        self._mount_composer(False)
        self.highlight_button.hide()
        self.guide_target_id = None
        self.last_visual_context = context
        self.sent_prompt = self.input.get_text()
        self.input.set_text("")
        self._add_message("user", prompt + (f"\n[Captura autorizada: {title}]" if context else ""))
        self._add_message("assistant", "", streaming=True)
        self._set_status("Analisando captura aprovada…" if context else "Gerando resposta…")
        self._scroll_end()

    def _cancel_generation(self, *_):
        if not self.generating or self.request_pending or self.cancelling:
            return
        try:
            if self.proxy.CancelGeneration(timeout=5):
                self.cancelling = True
                self._sync_actions()
                self._set_status("Interrompendo resposta…")
        except Exception:
            self._set_status("O serviço não confirmou a interrupção. Tente novamente.")

    def _on_delta(self, conversation_id, text):
        if str(conversation_id) != self.active_generation or not self.streaming_label:
            return
        self.pending_text.append(str(text))
        if not self.delta_source:
            self.delta_source = GLib.timeout_add(80, self._flush_delta)

    def _flush_delta(self):
        self.delta_source = 0
        if self.streaming_label:
            follow = self._near_bottom()
            self.streaming_label.set_text("".join(self.pending_text)[-32000:])
            if follow:
                self._scroll_end()
        return False

    def _on_visual_guide(self, conversation_id, result):
        if str(conversation_id) != self.active_generation:
            return
        super()._on_visual_guide(conversation_id, result)
        self.highlight_button.set_visible(self.highlight_button.get_sensitive())

    def _on_finished(self, conversation_id, state):
        if str(conversation_id) == self.active_generation:
            self._finish_response("Resposta interrompida." if str(state) == "interrupted" else "Resposta concluída.")

    def _on_failed(self, conversation_id, message):
        if str(conversation_id) == self.active_generation:
            self._finish_response(str(message), partial_error=True)

    def _finish_response(self, status, partial_error=False):
        follow = self._near_bottom()
        content = "".join(self.pending_text)
        if partial_error and content:
            content += "\n\n*Resposta parcial desta sessão.*"
        render(self.streaming_body, content or status, "assistant", self.dark)
        self.message_cards.append(("assistant", content or status, self.streaming_body))
        self._generation_done()
        self._load_conversations()
        self._set_status(status, error=partial_error)
        if follow:
            self._scroll_end()

    def _generation_done(self):
        if getattr(self, "delta_source", 0):
            GLib.source_remove(self.delta_source)
            self.delta_source = 0
        self.streaming_label = None
        self.streaming_body = None
        self.active_generation = None
        self.request_pending = False
        self.cancelling = False
        self.generating = False
        self._sync_actions()

    def _near_bottom(self):
        adjustment = self.messages_scroll.get_vadjustment()
        return adjustment.get_upper() - adjustment.get_page_size() - adjustment.get_value() < 85

    def _scroll_end(self):
        def follow():
            adjustment = self.messages_scroll.get_vadjustment()
            adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
            return False
        GLib.idle_add(follow, priority=GLib.PRIORITY_LOW)


class PreviewApplication(AssistantApplication):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="org.ifba.OS.Assistant.Preview",
                                 flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

    def do_startup(self):
        Gtk.Application.do_startup(self)
        provider = Gtk.CssProvider()
        provider.load_from_path(str(STYLE))
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_USER + 1)

    def do_activate(self):
        window = self.get_active_window()
        if window is None:
            window = PreviewWindow(self)
            window.show_all()
            window._sync_actions()
        window.present()
        GLib.idle_add(window._connect_service)


def main():
    import sys
    PreviewApplication().run(sys.argv)


if __name__ == "__main__":
    main()
