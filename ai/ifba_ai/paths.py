"""XDG paths used by the per-user assistant."""

import os
from pathlib import Path


class AppPaths:
    def __init__(self, home=None, env=None):
        env = os.environ if env is None else env
        self.home = Path(home or env.get("HOME", str(Path.home())))
        self.config = self._xdg_path(env, "XDG_CONFIG_HOME", self.home / ".config") / "ifba-ai"
        self.data = self._xdg_path(env, "XDG_DATA_HOME", self.home / ".local/share") / "ifba-ai"
        self.cache = self._xdg_path(env, "XDG_CACHE_HOME", self.home / ".cache") / "ifba-ai"
        self.settings = self.config / "settings.json"
        self.database = self.data / "assistant.sqlite3"

    @staticmethod
    def _xdg_path(env, name, default):
        value = Path(env.get(name, default))
        if not value.is_absolute():
            raise ValueError("Os caminhos XDG precisam ser absolutos.")
        return value

    def prepare(self):
        for directory in (self.config, self.data, self.cache):
            directory.mkdir(mode=0o700, parents=True, exist_ok=True)
            os.chmod(str(directory), 0o700)
