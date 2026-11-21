#!/usr/bin/python3
"""Native KDE welcome screen for IFBA OS."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from PyQt6.QtCore import QProcess, QSettings, QTimer, QUrl, Qt
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


CONFIG_RELATIVE_PATH = Path("ifba-os") / "welcome.ini"
DOCS_PATH = Path("/usr/share/doc/ifba-os/welcome.html")
BUILD_INFO_PATH = Path("/usr/share/ifba-os/build-info.json")

ACADEMIC_PORTALS = (
    ("SUAP", "Portal público do IFBA", "https://suap.ifba.edu.br/"),
    ("AVA IFBA", "Ambiente virtual público", "https://ava.ifba.edu.br/"),
)

# Fixed executable allowlist. No command is loaded from the web or a user file.
APPLICATIONS = (
    ("IFBA AI", "Assistente opcional", "/usr/bin/ifba-ai-ui", ()),
    ("Thonny", "Aprenda e programe em Python", "thonny", ()),
    ("LibreOffice Writer", "Escrita e trabalhos acadêmicos", "lowriter", ()),
    ("GCompris", "Atividades educativas", "gcompris-qt", ()),
)


def user_config_path() -> Path:
    configured = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(configured) if configured and Path(configured).is_absolute() else Path.home() / ".config"
    return base / CONFIG_RELATIVE_PATH


def show_at_login(path: Path | None = None) -> bool:
    settings = QSettings(str(path or user_config_path()), QSettings.Format.IniFormat)
    return settings.value("showAtLogin", True, type=bool)


def save_show_at_login(show: bool, path: Path | None = None) -> None:
    target = path or user_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    settings = QSettings(str(target), QSettings.Format.IniFormat)
    settings.setValue("showAtLogin", bool(show))
    settings.sync()


def resolve_program(executable: str) -> str | None:
    candidate = Path(executable)
    if candidate.is_absolute():
        return str(candidate) if candidate.is_file() and os.access(candidate, os.X_OK) else None
    found = shutil.which(executable)
    if found:
        return found
    for directory in (Path("/usr/bin"), Path("/usr/games"), Path("/usr/local/bin")):
        candidate = directory / executable
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def system_version() -> str:
    try:
        info = json.loads(BUILD_INFO_PATH.read_text(encoding="utf-8"))
        version = info.get("system_version")
        if isinstance(version, str) and version.strip():
            return version.strip()
    except (OSError, json.JSONDecodeError):
        pass
    return ""


def start_detached(program: str, arguments: tuple[str, ...] = ()) -> bool:
    result = QProcess.startDetached(program, list(arguments))
    return result[0] if isinstance(result, tuple) else bool(result)


class WelcomeWindow(QMainWindow):
    def __init__(self, config_path: Path | None = None):
        super().__init__()
        self.config_path = config_path or user_config_path()
        self.setWindowTitle("IFBA OS · Boas-vindas")
        self.setMinimumSize(760, 600)
        self.resize(1020, 760)
        self.setObjectName("welcomeWindow")
        self._buttons: dict[str, QPushButton] = {}
        self.setStyleSheet(STYLE)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("welcomeScroll")
        content = QWidget()
        content.setObjectName("welcomeContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(36, 26, 36, 24)
        layout.setSpacing(20)

        layout.addWidget(self._header())
        layout.addWidget(self._portals_section())
        layout.addWidget(self._services_section())
        layout.addWidget(self._tools_section())
        layout.addStretch(1)

        footer = QHBoxLayout()
        self.hide_at_login = QCheckBox("Não mostrar novamente ao entrar")
        self.hide_at_login.setObjectName("hideAtLogin")
        self.hide_at_login.setChecked(not show_at_login(self.config_path))
        self.hide_at_login.toggled.connect(self._save_visibility)
        footer.addWidget(self.hide_at_login)
        footer.addStretch(1)
        close_button = QPushButton("Concluir")
        close_button.setObjectName("primaryButton")
        close_button.clicked.connect(self.close)
        footer.addWidget(close_button)
        layout.addLayout(footer)

        scroll.setWidget(content)
        self.setCentralWidget(scroll)

    def _header(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("hero")
        row = QHBoxLayout(frame)
        row.setContentsMargins(26, 22, 26, 22)
        identity = QLabel("IFBA OS")
        identity.setObjectName("identity")
        identity.setAlignment(Qt.AlignmentFlag.AlignCenter)
        identity.setFixedSize(78, 42)
        text = QVBoxLayout()
        title = QLabel("Boas-vindas!")
        title.setObjectName("heroTitle")
        subtitle = QLabel("Acesse os portais, conheça as ferramentas e personalize seu começo.")
        subtitle.setObjectName("heroSubtitle")
        subtitle.setWordWrap(True)
        text.addWidget(title)
        text.addWidget(subtitle)
        row.addWidget(identity, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addLayout(text, 1)
        version = system_version()
        if version:
            badge = QLabel(f"Versão {version}")
            badge.setObjectName("versionBadge")
            row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
        return frame

    def _section(self, title: str, hint: str = "") -> tuple[QWidget, QGridLayout]:
        section = QWidget()
        outer = QVBoxLayout(section)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)
        heading_row = QHBoxLayout()
        heading = QLabel(title)
        heading.setObjectName("sectionTitle")
        heading_row.addWidget(heading)
        heading_row.addStretch(1)
        if hint:
            note = QLabel(hint)
            note.setObjectName("sectionHint")
            heading_row.addWidget(note)
        outer.addLayout(heading_row)
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        outer.addWidget(grid_host)
        return section, grid

    def _card(self, title: str, description: str, button_text: str, action) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(17, 15, 17, 15)
        layout.setSpacing(7)
        name = QLabel(title)
        name.setObjectName("cardTitle")
        detail = QLabel(description)
        detail.setObjectName("cardDescription")
        detail.setWordWrap(True)
        button = QPushButton(button_text)
        button.setObjectName("actionButton")
        button.clicked.connect(action)
        self._buttons[title] = button
        layout.addWidget(name)
        layout.addWidget(detail, 1)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        return card

    def _portals_section(self) -> QWidget:
        section, grid = self._section("Acesso acadêmico", "Links para os sites públicos")
        for index, (name, description, url) in enumerate(ACADEMIC_PORTALS):
            card = self._card(name, description, "Abrir portal", lambda _checked=False, url=url: self._open_url(url))
            grid.addWidget(card, 0, index)
        return section

    def _services_section(self) -> QWidget:
        section, grid = self._section("IFBA OS")
        cards = (
            ("IFBA AI", "Assistente opcional. A configuração da API fica no próprio aplicativo.",
             "Abrir IFBA AI", lambda: self._launch("/usr/bin/ifba-ai-ui")),
            ("Documentação", "Ajuda local sobre o sistema e seus limites.",
             "Ler documentação", self._open_documentation),
            ("Atualizações", "Confira as atualizações disponíveis no Discover.",
             "Abrir atualizações", self._open_updates),
        )
        for index, item in enumerate(cards):
            grid.addWidget(self._card(*item), 0, index)
        return section

    def _tools_section(self) -> QWidget:
        section, grid = self._section("Ferramentas educacionais instaladas")
        visible = []
        for name, description, executable, arguments in APPLICATIONS[1:]:
            resolved = resolve_program(executable)
            if resolved:
                visible.append((name, description, resolved, arguments))

        if not visible:
            empty = QLabel("Nenhuma ferramenta educacional foi detectada nesta instalação.")
            empty.setObjectName("emptyState")
            grid.addWidget(empty, 0, 0, 1, 3)
        else:
            for index, (name, description, executable, arguments) in enumerate(visible):
                card = self._card(
                    name,
                    description,
                    "Abrir ferramenta",
                    lambda _checked=False, executable=executable, arguments=arguments:
                        self._launch(executable, arguments),
                )
                grid.addWidget(card, index // 3, index % 3)
        return section

    def _save_visibility(self, hide: bool) -> None:
        save_show_at_login(not hide, self.config_path)

    def _notify_launch_failure(self, name: str) -> None:
        QMessageBox.warning(self, "Não foi possível abrir", f"{name} não está disponível nesta instalação.")

    def _launch(self, executable: str, arguments: tuple[str, ...] = ()) -> None:
        resolved = resolve_program(executable)
        if not resolved:
            self._notify_launch_failure(Path(executable).name or "Aplicativo")
            return
        if not start_detached(resolved, arguments):
            self._notify_launch_failure(Path(resolved).name)

    def _open_url(self, url: str) -> None:
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(self, "Não foi possível abrir", "Verifique se há um navegador instalado.")

    def _open_documentation(self) -> None:
        if not DOCS_PATH.is_file():
            QMessageBox.information(self, "Documentação", "A documentação local não está disponível nesta instalação.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(DOCS_PATH)))

    def _open_updates(self) -> None:
        discover = shutil.which("plasma-discover")
        if not discover:
            QMessageBox.information(self, "Atualizações", "O Discover não está disponível nesta instalação.")
            return
        if not start_detached(discover, ("--mode", "update")):
            QMessageBox.warning(self, "Atualizações", "Não foi possível abrir o Discover.")


STYLE = """
QMainWindow, QScrollArea, QWidget#welcomeContent { background: #171a1c; color: #eef0ef; }
QFrame#hero { background: #202527; border: 1px solid #303638; border-radius: 18px; }
QLabel#identity { color: #ffffff; background: #287342; border-radius: 11px; font-weight: 700; letter-spacing: 1px; }
QLabel#heroTitle { font-size: 27px; font-weight: 700; color: #f5f6f5; }
QLabel#heroSubtitle, QLabel#sectionHint { color: #b5bcba; }
QLabel#versionBadge { color: #d6e7db; background: #293b31; border: 1px solid #42684e; border-radius: 10px; padding: 6px 10px; }
QLabel#sectionTitle { color: #f0f2f1; font-size: 17px; font-weight: 650; }
QFrame#card { background: #202527; border: 1px solid #303638; border-radius: 14px; }
QLabel#cardTitle { color: #f4f6f5; font-size: 15px; font-weight: 650; }
QLabel#cardDescription, QLabel#emptyState { color: #b5bcba; }
QPushButton { color: #eef0ef; background: #303638; border: 1px solid #46504d; border-radius: 9px; padding: 8px 13px; }
QPushButton:hover { background: #394640; border-color: #5d8669; }
QPushButton:pressed { background: #24392b; }
QPushButton:focus { border: 2px solid #62a875; }
QPushButton#primaryButton { color: white; background: #287342; border: 1px solid #3a8c56; font-weight: 650; min-width: 110px; }
QPushButton#primaryButton:hover { background: #32834e; }
QCheckBox { color: #c9cfcc; spacing: 9px; }
QCheckBox::indicator { width: 17px; height: 17px; }
QCheckBox::indicator:checked { background: #287342; border: 1px solid #62a875; border-radius: 4px; }
QCheckBox::indicator:unchecked { background: #202527; border: 1px solid #74807a; border-radius: 4px; }
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Boas-vindas do IFBA OS")
    parser.add_argument("--autostart", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    config_path = user_config_path()
    if args.autostart and not show_at_login(config_path):
        return 0

    app = QApplication(sys.argv[:1])
    app.setApplicationName("IFBA OS Welcome")
    app.setOrganizationName("IFBA OS")
    app.setFont(QFont("Inter", 10))
    window = WelcomeWindow(config_path)

    if args.autostart:
        QTimer.singleShot(2500, window.show)
    else:
        window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
