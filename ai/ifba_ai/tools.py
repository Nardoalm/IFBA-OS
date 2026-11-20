"""Typed, user-scoped desktop tools. No shell or model-selected command execution."""

import os
import platform
import secrets
import stat
import time
from pathlib import Path
from urllib.parse import urlsplit


class ToolError(ValueError):
    pass


class SystemTools:
    """Small allowlisted operations; mutating file creation needs a one-shot confirmation."""

    MAX_FILE_BYTES = 512 * 1024
    XFCE_SETTINGS_IDS = {
        "display": "xfce-display-settings.desktop",
        "appearance": "xfce-appearance-settings.desktop",
        "keyboard": "xfce-keyboard-settings.desktop",
        "network": "nm-connection-editor.desktop",
        "sound": "pavucontrol.desktop",
    }
    KDE_SETTINGS_IDS = {
        "display": "kcm_kscreen.desktop",
        "appearance": "kcm_lookandfeel.desktop",
        "keyboard": "kcm_keyboard.desktop",
        "network": "kcm_networkmanagement.desktop",
        "sound": "kcm_pulseaudio.desktop",
    }

    def __init__(self, app_provider=None, app_launcher=None, uri_launcher=None,
                 system_provider=None, clock=None):
        self._app_provider = app_provider or self._gio_apps
        self._app_launcher = app_launcher or self._gio_launch
        self._uri_launcher = uri_launcher or self._gio_open_uri
        self._system_provider = system_provider or self._system_info
        self._clock = clock or time.monotonic
        self._root = None
        self._root_identity = None
        self._pending = {}

    @staticmethod
    def _gio_apps():
        try:
            import gi
            gi.require_version("Gio", "2.0")
            from gi.repository import Gio
        except (ImportError, ValueError) as error:
            raise ToolError("A lista de aplicativos não está disponível nesta sessão.") from error
        return {app.get_id(): app for app in Gio.AppInfo.get_all() if app.get_id()}

    @staticmethod
    def _gio_launch(app):
        try:
            app.launch([], None)
        except Exception as error:
            raise ToolError("O aplicativo não pôde ser aberto.") from error

    @staticmethod
    def _gio_open_uri(uri):
        try:
            import gi
            gi.require_version("Gio", "2.0")
            from gi.repository import Gio
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except Exception as error:
            raise ToolError("O endereço não pôde ser aberto no navegador.") from error

    @staticmethod
    def _system_info():
        return {
            "os": platform.system(), "release": platform.release(),
            "architecture": platform.machine(), "desktop": os.environ.get("XDG_CURRENT_DESKTOP", ""),
            "locale": os.environ.get("LANG", ""),
        }

    def list_installed_apps(self):
        apps = self._app_provider()
        return [{"id": app_id, "name": str(app.get_name())[:160]}
                for app_id, app in sorted(apps.items()) if app.get_name()]

    def open_app(self, app_id):
        if not isinstance(app_id, str) or len(app_id) > 200:
            raise ToolError("Aplicativo inválido.")
        app = self._app_provider().get(app_id)
        if app is None:
            raise ToolError("Esse aplicativo não está instalado ou disponível.")
        self._app_launcher(app)
        return {"opened": app_id}

    def system_info(self):
        return self._system_provider()

    def open_url(self, url):
        if not isinstance(url, str) or len(url) > 2048:
            raise ToolError("Endereço inválido.")
        parsed = urlsplit(url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or parsed.username or parsed.password:
            raise ToolError("Só é permitido abrir endereços HTTP ou HTTPS válidos.")
        self._uri_launcher(url)
        return {"opened": url}

    def open_settings(self, setting):
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        settings = self.KDE_SETTINGS_IDS if "kde" in desktop or "plasma" in desktop else self.XFCE_SETTINGS_IDS
        app_id = settings.get(setting)
        if app_id is None:
            raise ToolError("Essa configuração não está na lista permitida.")
        return self.open_app(app_id)

    def open_xfce_settings(self, setting):
        return self.open_settings(setting)

    def grant_directory(self, path):
        if not isinstance(path, str) or not os.path.isabs(path):
            raise ToolError("Escolha uma pasta local válida.")
        candidate = Path(path)
        try:
            resolved = candidate.resolve(strict=True)
            info = resolved.stat()
        except OSError as error:
            raise ToolError("A pasta selecionada não está disponível.") from error
        if not stat.S_ISDIR(info.st_mode):
            raise ToolError("O caminho selecionado não é uma pasta.")
        self._root = resolved
        self._root_identity = (info.st_dev, info.st_ino)
        self._pending.clear()
        return str(resolved)

    def _require_root(self):
        if self._root is None:
            raise ToolError("Escolha uma pasta nesta sessão antes de consultar arquivos.")
        try:
            info = self._root.stat()
        except OSError as error:
            raise ToolError("A pasta autorizada não está mais disponível.") from error
        if not stat.S_ISDIR(info.st_mode) or (info.st_dev, info.st_ino) != self._root_identity:
            raise ToolError("A pasta autorizada mudou; selecione-a novamente.")
        return self._root

    def _inside_root(self, relative_path, must_exist=False):
        if not isinstance(relative_path, str) or not relative_path or os.path.isabs(relative_path):
            raise ToolError("Caminho relativo inválido.")
        parts = Path(relative_path).parts
        if any(part in ("..", ".") or "\x00" in part for part in parts):
            raise ToolError("O caminho precisa permanecer dentro da pasta autorizada.")
        root = self._require_root()
        target = root.joinpath(*parts)
        cursor = root
        for part in parts:
            cursor = cursor / part
            try:
                info = cursor.lstat()
            except FileNotFoundError:
                continue
            except OSError as error:
                raise ToolError("Não foi possível validar o caminho.") from error
            if stat.S_ISLNK(info.st_mode):
                raise ToolError("Links simbólicos não são aceitos por esta operação.")
        try:
            target.resolve(strict=must_exist).relative_to(root)
        except (OSError, ValueError) as error:
            raise ToolError("O caminho está fora da pasta autorizada.") from error
        return target

    def list_directory(self, relative_path="."):
        if relative_path == ".":
            root = self._require_root()
            directory = root
        else:
            directory = self._inside_root(relative_path, must_exist=True)
        if not directory.is_dir():
            raise ToolError("O caminho autorizado não é uma pasta.")
        results = []
        try:
            for entry in sorted(os.scandir(directory), key=lambda item: item.name.casefold())[:300]:
                if entry.is_symlink():
                    continue
                results.append({"name": entry.name[:255], "directory": entry.is_dir(follow_symlinks=False),
                                "file": entry.is_file(follow_symlinks=False)})
        except OSError as error:
            raise ToolError("Não foi possível consultar essa pasta.") from error
        return results

    def find_files(self, query, max_results=100):
        if not isinstance(query, str) or not query.strip() or len(query) > 200:
            raise ToolError("Digite um nome para localizar.")
        if not 1 <= max_results <= 300:
            raise ToolError("Limite de resultados inválido.")
        root = self._require_root()
        found = []
        visited_directories = 0
        for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
            visited_directories += 1
            if visited_directories > 2000:
                break
            relative_depth = len(Path(current).relative_to(root).parts)
            dirs[:] = [name for name in dirs if not name.startswith(".") and
                       not (Path(current) / name).is_symlink()] if relative_depth < 6 else []
            for name in files:
                path = Path(current) / name
                if name.startswith(".") or path.is_symlink() or query.casefold() not in name.casefold():
                    continue
                found.append(str(path.relative_to(root)))
                if len(found) >= max_results:
                    return found
        return found

    def prepare_create_file(self, relative_path, content):
        if not isinstance(content, str) or not content or len(content.encode("utf-8")) > self.MAX_FILE_BYTES:
            raise ToolError("O novo arquivo está vazio ou excede 512 KiB.")
        target = self._inside_root(relative_path)
        if target.parent != self._require_root():
            raise ToolError("Para criar arquivo com segurança, selecione primeiro a pasta de destino.")
        try:
            if os.path.lexists(target):
                raise ToolError("Já existe um arquivo com esse nome; a ferramenta não sobrescreve arquivos.")
        except OSError as error:
            raise ToolError("Não foi possível verificar o destino.") from error
        token = secrets.token_urlsafe(32)
        self._pending[token] = {"path": str(target), "content": content,
                                "expires": self._clock() + 120,
                                "root_identity": self._root_identity}
        return {"confirmation_token": token, "path": str(target),
                "bytes": len(content.encode("utf-8")), "expires_in_seconds": 120}

    def confirm_create_file(self, token):
        pending = self._pending.pop(token, None)
        if pending is None or pending["expires"] < self._clock():
            raise ToolError("A confirmação expirou ou já foi usada. Gere um novo plano.")
        root = self._require_root()
        if pending["root_identity"] != self._root_identity or Path(pending["path"]).parent != root:
            raise ToolError("O destino mudou desde o plano; gere um novo plano.")
        target = Path(pending["path"])
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = None
        created_identity = None
        try:
            descriptor = os.open(target, flags, 0o600)
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode):
                raise ToolError("O destino deixou de ser um arquivo regular.")
            created_identity = (info.st_dev, info.st_ino)
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                descriptor = None
                handle.write(pending["content"])
                handle.flush()
                os.fsync(handle.fileno())
            after = target.lstat()
            if not stat.S_ISREG(after.st_mode) or (after.st_dev, after.st_ino) != created_identity:
                raise ToolError("O arquivo criado mudou antes da verificação final.")
            return {"created": str(target), "verified": True}
        except FileExistsError as error:
            raise ToolError("O destino já existe; nenhum arquivo foi sobrescrito.") from error
        except OSError as error:
            try:
                after = target.lstat()
                if created_identity == (after.st_dev, after.st_ino):
                    target.unlink()
            except OSError:
                pass
            raise ToolError("Não foi possível criar o arquivo com segurança.") from error
        finally:
            if descriptor is not None:
                os.close(descriptor)
