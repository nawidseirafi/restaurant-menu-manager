from __future__ import annotations

from PySide6.QtCore import QLocale, Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QMessageBox,
    QDoubleSpinBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.database.repositories import MenuRepository
from app.gui.theme import mark_button


class PriceEditorDialog(QDialog):
    def __init__(self, repo: MenuRepository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.setWindowTitle("Preise bearbeiten")
        self.resize(760, 520)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Gericht", "Bisheriger Preis", "Neuer Preis"])
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        mark_button(buttons.button(QDialogButtonBox.Save), "primary")
        mark_button(buttons.button(QDialogButtonBox.Cancel), "secondary")
        buttons.accepted.connect(self.apply_changes)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        title = QLabel("PREISE BEARBEITEN")
        title.setProperty("class", "panelTitle")
        layout.addWidget(title)
        layout.addWidget(self.table)
        layout.addWidget(buttons)
        self._load_rows()

    def _load_rows(self) -> None:
        items = self.repo.list_items(active_only=False)
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            name = QTableWidgetItem(item.name)
            name.setData(Qt.UserRole, item.id)
            name.setFlags(name.flags() & ~Qt.ItemIsEditable)
            old_price = QTableWidgetItem(f"{item.price:.2f}")
            old_price.setFlags(old_price.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, old_price)
            self.table.setCellWidget(row, 2, self._price_spin(float(item.price)))

    def _price_spin(self, value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0, 9999)
        spin.setDecimals(2)
        spin.setSingleStep(0.50)
        spin.setSuffix(" EUR")
        spin.setLocale(QLocale(QLocale.German, QLocale.Germany))
        spin.setValue(value)
        return spin

    def apply_changes(self) -> None:
        try:
            for row in range(self.table.rowCount()):
                item_id = self.table.item(row, 0).data(Qt.UserRole)
                spin = self.table.cellWidget(row, 2)
                self.repo.update_item_price(item_id, spin.value())
        except ValueError as exc:
            QMessageBox.warning(self, "Preis ungueltig", str(exc))
            return
        self.accept()
