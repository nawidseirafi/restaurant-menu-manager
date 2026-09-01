from __future__ import annotations

from urllib.parse import urlparse

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

DEFAULT_MENU_URL = "https://www.tacomex.de/menu"


class SettingsDialog(QDialog):
    """Small settings dialog for values that affect exports and QR codes."""

    def __init__(self, settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Einstellungen")
        self.setModal(True)
        self.setFixedSize(620, 300)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 22)
        root.setSpacing(12)

        title = QLabel("Einstellungen")
        title.setProperty("class", "dialogTitle")
        root.addWidget(title)

        subtitle = QLabel("QR-Code")
        subtitle.setProperty("class", "eyebrow")
        root.addWidget(subtitle)

        field_group = QVBoxLayout()
        field_group.setSpacing(6)

        label = QLabel("Menü-URL")
        label.setProperty("class", "fieldLabel")
        field_group.addWidget(label)

        self.menu_url_edit = QLineEdit()
        self.menu_url_edit.setPlaceholderText(DEFAULT_MENU_URL)
        self.menu_url_edit.setText((self.settings.menu_url or DEFAULT_MENU_URL).strip())
        self.menu_url_edit.setFixedHeight(40)
        self.menu_url_edit.setProperty("class", "settingsUrlField")
        self.menu_url_edit.selectAll()
        field_group.addWidget(self.menu_url_edit)

        hint = QLabel("Diese Adresse wird für neu erzeugte QR-Codes verwendet.")
        hint.setProperty("class", "hint")
        field_group.addWidget(hint)
        root.addLayout(field_group)

        root.addStretch(1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        cancel_button = QPushButton("Abbrechen")
        cancel_button.setProperty("role", "secondary")
        cancel_button.setFixedHeight(36)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(cancel_button)

        save_button = QPushButton("Speichern")
        save_button.setProperty("role", "accent")
        save_button.setFixedHeight(36)
        save_button.setDefault(True)
        save_button.clicked.connect(self._save)
        buttons.addWidget(save_button)

        root.addLayout(buttons)

    def _save(self) -> None:
        url = self.menu_url_edit.text().strip()
        if not self._is_valid_http_url(url):
            QMessageBox.warning(
                self,
                "Ungültige Menü-URL",
                "Bitte eine vollständige Adresse eingeben, z. B.\n"
                "https://www.tacomex.de/menu",
            )
            self.menu_url_edit.setFocus()
            return

        self.settings.menu_url = url.rstrip("/") if url != "https://" else url
        self.accept()

    @staticmethod
    def _is_valid_http_url(value: str) -> bool:
        if not value or " " in value:
            return False
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
