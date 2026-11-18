"""On-demand X11 window metadata and transient screenshot capture."""

import base64
import hashlib
import re


SENSITIVE_WINDOW_RE = re.compile(r"login|sign[ -]?in|password|senha|autentica", re.I)
MAX_SCREENSHOT_BYTES = 140 * 1024
MAX_CONTROLS = 160
MAX_TREE_DEPTH = 8


class VisualContextError(RuntimeError):
    pass


def _text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value or "")


def collect_controls(pid, atspi=None):
    """Return a bounded accessibility outline without reading text field values."""
    if atspi is None:
        try:
            import pyatspi as atspi
        except ImportError as error:
            raise VisualContextError("O serviço de acessibilidade AT-SPI2 não está disponível.") from error
    desktop = atspi.Registry.getDesktop(0)
    output = []
    identity_counts = {}
    has_password_control = False

    def visit(node, depth):
        nonlocal has_password_control
        if depth > MAX_TREE_DEPTH or len(output) >= MAX_CONTROLS:
            return
        try:
            role = _text(node.get_role_name())
            if role.lower() in ("password text", "password field"):
                has_password_control = True
            name = _text(node.get_name())[:120]
            description = _text(node.get_description())[:160]
            if role.lower() in ("push button", "button", "menu item", "check box", "radio button",
                                "combo box", "text", "text entry", "entry", "page tab", "table cell"):
                identity = (role.lower(), name.lower())
                occurrence = identity_counts.get(identity, 0)
                identity_counts[identity] = occurrence + 1
                digest = hashlib.sha256("{}\0{}\0{}\0{}".format(pid, role.lower(),
                                                                   name.lower(), occurrence).encode("utf-8")).hexdigest()[:12]
                rect = None
                try:
                    component = node.queryComponent()
                    extents = component.getExtents(atspi.DESKTOP_COORDS)
                    rect = [int(extents.x), int(extents.y), int(extents.width), int(extents.height)]
                except Exception:
                    pass
                enabled = True
                try:
                    enabled = bool(node.getState().contains(atspi.STATE_ENABLED))
                except Exception:
                    pass
                output.append({"id": "control-{}".format(digest), "role": role,
                               "name": name, "description": description,
                               "enabled": enabled, "bounds": rect})
            count = min(int(node.childCount), MAX_CONTROLS - len(output))
            for index in range(max(0, count)):
                try:
                    visit(node.getChildAtIndex(index), depth + 1)
                except Exception:
                    continue
        except Exception:
            return

    for app_index in range(int(desktop.childCount)):
        if len(output) >= MAX_CONTROLS:
            break
        try:
            app = desktop.getChildAtIndex(app_index)
            if int(app.get_process_id()) == int(pid):
                visit(app, 0)
        except Exception:
            continue
    return {"controls": output, "has_password_control": has_password_control}


def active_window_context(display_factory=None, atspi=None, window_id=None):
    """Query the current X11 active window; no polling or background capture."""
    if display_factory is None:
        try:
            from Xlib import display as xdisplay
            display_factory = xdisplay.Display
        except ImportError as error:
            raise VisualContextError("A detecção de janela requer X11 e python3-xlib.") from error
    connection = display_factory()
    try:
        root = connection.screen().root
        if window_id is None:
            active_atom = connection.intern_atom("_NET_ACTIVE_WINDOW")
            active = root.get_full_property(active_atom, 0)
            if active is None or not active.value:
                raise VisualContextError("Nenhuma janela ativa foi encontrada.")
            xid = int(active.value[0])
        else:
            xid = int(window_id)
        return _describe_window(connection, root, xid, atspi)
    finally:
        connection.close()


def _describe_window(connection, root, xid, atspi=None, include_controls=True):
    window = connection.create_resource_object("window", int(xid))
    attributes = window.get_attributes()
    if int(attributes.map_state) != 2:
        raise VisualContextError("A janela selecionada não está visível.")
    title_atom = connection.intern_atom("_NET_WM_NAME")
    title_prop = window.get_full_property(title_atom, 0)
    title = _text(title_prop.value) if title_prop else ""
    pid_atom = connection.intern_atom("_NET_WM_PID")
    pid_prop = window.get_full_property(pid_atom, 0)
    pid = int(pid_prop.value[0]) if pid_prop and pid_prop.value else 0
    class_hint = window.get_wm_class() or ("", "")
    geometry = window.get_geometry()
    translated = window.translate_coords(root, 0, 0)
    window_class = " ".join(_text(part) for part in class_hint if part)
    accessibility = collect_controls(pid, atspi=atspi) if include_controls and pid > 0 else {
        "controls": [], "has_password_control": False}
    return {
        "window_id": int(xid),
        "pid": pid,
        "title": title[:240],
        "application": window_class[:160] or "Aplicativo desconhecido",
        "geometry": [int(translated.x), int(translated.y), int(geometry.width), int(geometry.height)],
        "controls": accessibility["controls"],
        "has_password_control": accessibility["has_password_control"],
    }


def list_visible_windows(display_factory=None, atspi=None):
    """List visible application windows for a local user to choose explicitly."""
    if display_factory is None:
        try:
            from Xlib import display as xdisplay
            display_factory = xdisplay.Display
        except ImportError as error:
            raise VisualContextError("A detecção de janela requer X11 e python3-xlib.") from error
    connection = display_factory()
    try:
        root = connection.screen().root
        atom = connection.intern_atom("_NET_CLIENT_LIST_STACKING")
        prop = root.get_full_property(atom, 0)
        if prop is None or not prop.value:
            atom = connection.intern_atom("_NET_CLIENT_LIST")
            prop = root.get_full_property(atom, 0)
        if prop is None or not prop.value:
            raise VisualContextError("Não há janelas visíveis para selecionar.")
        contexts = []
        for xid in list(prop.value)[:80]:
            try:
                context = _describe_window(connection, root, int(xid), include_controls=False)
                if "assistente ifba os" not in context["title"].lower():
                    contexts.append(context)
            except Exception:
                continue
        return contexts
    finally:
        connection.close()


def capture_active_window(context=None, display_factory=None, atspi=None):
    """Capture and JPEG-encode only the active window, in memory, for preview."""
    context = context or active_window_context(display_factory=display_factory, atspi=atspi)
    title = context.get("title", "")
    if SENSITIVE_WINDOW_RE.search(title) or context.get("has_password_control"):
        raise VisualContextError("A janela parece conter autenticação ou senha; a captura foi bloqueada.")
    if display_factory is None:
        try:
            from Xlib import display as xdisplay
            display_factory = xdisplay.Display
        except ImportError as error:
            raise VisualContextError("A captura requer X11 e python3-xlib.") from error
    try:
        import gi
        gi.require_version("Gdk", "3.0")
        gi.require_version("GdkX11", "3.0")
        from gi.repository import Gdk, GdkPixbuf, GdkX11
    except (ImportError, ValueError) as error:
        raise VisualContextError("A captura de janela GTK/X11 não está disponível.") from error
    connection = display_factory()
    try:
        display = Gdk.Display.get_default() or Gdk.Display.open(None)
        if display is None:
            raise VisualContextError("Não foi possível conectar à sessão gráfica X11.")
        window = GdkX11.X11Window.foreign_new_for_display(display, int(context["window_id"]))
        if window is None:
            raise VisualContextError("Não foi possível acessar a janela ativa para captura.")
        geometry = context.get("geometry") or []
        width, height = int(geometry[2]), int(geometry[3])
        if width < 80 or height < 60 or width > 12000 or height > 12000:
            raise VisualContextError("O tamanho da janela ativa não é válido para captura.")
        pixbuf = Gdk.pixbuf_get_from_window(window, 0, 0, width, height)
        if pixbuf is None:
            raise VisualContextError("A janela não permitiu a captura de pré-visualização.")
        max_width = 1440
        if pixbuf.get_width() > max_width:
            scaled_height = max(1, int(pixbuf.get_height() * max_width / pixbuf.get_width()))
            pixbuf = pixbuf.scale_simple(max_width, scaled_height, GdkPixbuf.InterpType.BILINEAR)
        encoded = None
        for quality in (78, 68, 58, 48):
            _success, buffer = pixbuf.save_to_bufferv("jpeg", ["quality"], [str(quality)])
            encoded = bytes(buffer)
            if len(encoded) <= MAX_SCREENSHOT_BYTES:
                break
        if encoded is None or len(encoded) > MAX_SCREENSHOT_BYTES:
            raise VisualContextError("A captura excede o limite seguro de envio; reduza o tamanho da janela.")
        return {"mime_type": "image/jpeg", "data_url": "data:image/jpeg;base64," +
                base64.b64encode(encoded).decode("ascii"), "bytes": len(encoded),
                "width": pixbuf.get_width(), "height": pixbuf.get_height()}
    finally:
        connection.close()


def validate_visual_result(value, context):
    """Validate model output against the current accessible-control IDs."""
    import json
    try:
        result = json.loads(value)
    except (TypeError, ValueError) as error:
        raise VisualContextError("A resposta visual não veio em formato válido.") from error
    if not isinstance(result, dict):
        raise VisualContextError("A resposta visual não veio em formato válido.")
    explanation = result.get("explanation")
    next_step = result.get("next_step")
    confidence = result.get("confidence")
    target_id = result.get("target_id")
    needs_confirmation = result.get("needs_confirmation")
    valid_ids = {item.get("id") for item in context.get("controls", [])}
    if (not isinstance(explanation, str) or len(explanation) > 4000
            or not isinstance(next_step, str) or len(next_step) > 1000
            or isinstance(confidence, bool) or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
            or not isinstance(needs_confirmation, bool)
            or (target_id is not None and (not isinstance(target_id, str) or target_id not in valid_ids))):
        raise VisualContextError("A resposta visual continha campos ou controles não reconhecidos.")
    return {"explanation": explanation, "next_step": next_step, "target_id": target_id,
            "confidence": float(confidence), "needs_confirmation": needs_confirmation}
