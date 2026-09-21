from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)


class CategoryDialog(QDialog):
    def __init__(self, name="", description="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kategorie bearbeiten")
        self.resize(560, 340)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit(name)
        self.description_edit = QTextEdit()
        self.description_edit.setAcceptRichText(False)
        self.description_edit.setPlainText(description or "")
        self.description_edit.setPlaceholderText("Optionaler Hinweis unter der Kategorieüberschrift")
        form.addRow("Name", self.name_edit)
        form.addRow("Beschreibung", self.description_edit)
        layout.addLayout(form)
        hint = QLabel("Zum Entfernen des Hinweises die Beschreibung leeren.\nAnschließend die Vorschau oder den Export neu erstellen.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        buttons = QDialogButtonBox()
        self.save_button = buttons.addButton("Speichern", QDialogButtonBox.AcceptRole)
        buttons.addButton("Abbrechen", QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.name_edit.textChanged.connect(
            lambda text: self.save_button.setEnabled(bool(text.strip()))
        )
        self.save_button.setEnabled(bool(name.strip()))
        layout.addWidget(buttons)

