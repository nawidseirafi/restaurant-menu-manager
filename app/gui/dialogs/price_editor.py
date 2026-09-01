from __future__ import annotations

from PySide6.QtCore import QLocale, Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QDoubleSpinBox,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories import MenuRepository
from app.gui.theme import mark_button


class PriceEditorDialog(QDialog):
    def __init__(self, repo: MenuRepository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.setWindowTitle("Preise bearbeiten")
        self.resize(920, 560)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Gericht suchen…")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedWidth(310)
        self.search_edit.setProperty("class", "searchField")
        self.search_edit.textChanged.connect(self._filter_rows)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Gericht", "Kategorie", "Bisheriger Preis", "Neuer Preis"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 4):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        mark_button(buttons.button(QDialogButtonBox.Save), "primary")
        mark_button(buttons.button(QDialogButtonBox.Cancel), "secondary")
        buttons.accepted.connect(self.apply_changes)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        title = QLabel("PREISE BEARBEITEN")
        title.setProperty("class", "panelTitle")
        layout.addWidget(self._header(title))
        layout.addWidget(self.table)
        layout.addWidget(buttons)
        self._load_rows()

    def _header(self, title: QLabel) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(title)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(spacer)
        layout.addWidget(self.search_edit)
        return widget

    def _load_rows(self) -> None:
        items = self.repo.list_items(active_only=False)
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            name = QTableWidgetItem(item.name)
            name.setData(Qt.UserRole, item.id)
            name.setData(Qt.UserRole + 1, self._search_text(item))
            name.setFlags(name.flags() & ~Qt.ItemIsEditable)
            category = QTableWidgetItem(item.category.name if item.category else "")
            category.setFlags(category.flags() & ~Qt.ItemIsEditable)
            old_price = QTableWidgetItem(f"{item.price:.2f}".replace(".", ","))
            old_price.setFlags(old_price.flags() & ~Qt.ItemIsEditable)
            old_price.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, category)
            self.table.setItem(row, 2, old_price)
            self.table.setCellWidget(row, 3, self._price_spin(float(item.price)))

    def _price_spin(self, value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0, 9999)
        spin.setDecimals(2)
        spin.setSingleStep(0.50)
        spin.setSuffix(" EUR")
        spin.setLocale(QLocale(QLocale.German, QLocale.Germany))
        spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        spin.setMinimumWidth(130)
        spin.setValue(value)
        return spin

    def _filter_rows(self, text: str) -> None:
        needle = text.strip().casefold()
        for row in range(self.table.rowCount()):
            searchable = self.table.item(row, 0).data(Qt.UserRole + 1)
            self.table.setRowHidden(row, bool(needle and needle not in searchable))

    def _search_text(self, item) -> str:
        return " ".join(
            [
                item.name or "",
                item.description or "",
                item.category.name if item.category else "",
                item.allergens or "",
                item.additives or "",
                item.notes or "",
            ]
        ).casefold()

    def apply_changes(self) -> None:
        try:
            for row in range(self.table.rowCount()):
                item_id = self.table.item(row, 0).data(Qt.UserRole)
                spin = self.table.cellWidget(row, 3)
                self.repo.update_item_price(item_id, spin.value())
        except ValueError as exc:
            QMessageBox.warning(self, "Preis ungueltig", str(exc))
            return
        self.accept()
