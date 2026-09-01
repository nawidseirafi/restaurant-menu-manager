from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.repositories import MenuRepository
from app.gui.theme import mark_button


class PriceEditorDialog(QDialog):
    """Schneller, autospeichernder Editor für Preisänderungen."""

    def __init__(self, repo: MenuRepository, parent=None):
        super().__init__(parent)
        self.repo = repo
        self._loading = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(350)
        self._save_timer.timeout.connect(self._flush_pending_changes)
        self._pending: dict[int, Decimal] = {}

        self.setWindowTitle("Preise bearbeiten")
        self.setMinimumSize(760, 460)
        self.resize(940, 590)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Gericht suchen…")
        self.search_edit.setClearButtonEnabled(False)
        self.search_edit.setFixedWidth(290)
        self.search_edit.setProperty("class", "searchField")
        self.search_edit.textChanged.connect(self._filter_rows)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Gericht", "Kategorie", "Bisheriger Preis", "Neuer Preis"])
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.itemChanged.connect(self._on_item_changed)

        self.status_label = QLabel("Änderungen werden automatisch gespeichert")
        self.status_label.setProperty("class", "hint")
        self.hit_label = QLabel("")
        self.hit_label.setProperty("class", "hint")

        done = QPushButton("Fertig")
        done.clicked.connect(self.accept)
        mark_button(done, "secondary")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 18, 22, 18)
        outer.setSpacing(14)
        outer.addWidget(self._header())
        outer.addWidget(self.table, 1)

        footer = QHBoxLayout()
        footer.addWidget(self.hit_label)
        footer.addSpacing(14)
        footer.addWidget(self.status_label)
        footer.addStretch(1)
        footer.addWidget(done)
        outer.addLayout(footer)

        QShortcut(QKeySequence.Find, self, activated=self._focus_search)
        QShortcut(QKeySequence("Esc"), self, activated=self._escape)
        self._load_rows()

    def _header(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        title = QLabel("Preise bearbeiten")
        title.setStyleSheet("font-size: 17px; font-weight: 650; color: #F2F4F5;")
        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(self.search_edit)
        return widget

    def _load_rows(self) -> None:
        self._loading = True
        items = self.repo.list_items(active_only=False)
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            name = QTableWidgetItem(item.name)
            name.setData(Qt.UserRole, item.id)
            name.setData(Qt.UserRole + 1, self._search_text(item))
            name.setFlags(name.flags() & ~Qt.ItemIsEditable)

            category = QTableWidgetItem(item.category.name if item.category else "")
            category.setFlags(category.flags() & ~Qt.ItemIsEditable)

            old_price = QTableWidgetItem(self._format_price(item.price))
            old_price.setFlags(old_price.flags() & ~Qt.ItemIsEditable)
            old_price.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            new_price = QTableWidgetItem(self._format_price(item.price))
            new_price.setData(Qt.UserRole, item.id)
            new_price.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, category)
            self.table.setItem(row, 2, old_price)
            self.table.setItem(row, 3, new_price)
            self.table.setRowHeight(row, 42)
        self._loading = False
        self._update_hit_count()

    @staticmethod
    def _format_price(value) -> str:
        return f"{float(value):.2f}".replace(".", ",") + " €"

    @staticmethod
    def _parse_price(text: str) -> Decimal:
        cleaned = text.strip().replace("€", "").replace("EUR", "").strip().replace(".", "").replace(",", ".")
        try:
            value = Decimal(cleaned).quantize(Decimal("0.01"))
        except InvalidOperation as exc:
            raise ValueError("Bitte einen gültigen Preis eingeben, z. B. 12,90.") from exc
        if value < 0 or value > 9999:
            raise ValueError("Der Preis muss zwischen 0 und 9999 Euro liegen.")
        return value

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading or item.column() != 3:
            return
        try:
            value = self._parse_price(item.text())
        except ValueError:
            self.status_label.setText("Ungültiger Preis")
            self.status_label.setStyleSheet("color: #E59B94;")
            return
        item_id = self.table.item(item.row(), 0).data(Qt.UserRole)
        self._pending[item_id] = value
        self.status_label.setText("Speichern …")
        self.status_label.setStyleSheet("")
        self._save_timer.start()

    def _flush_pending_changes(self) -> None:
        if not self._pending:
            return
        pending = dict(self._pending)
        try:
            for item_id, value in pending.items():
                self.repo.update_item_price(item_id, float(value))
        except Exception as exc:
            self.status_label.setText("Speichern fehlgeschlagen")
            self.status_label.setStyleSheet("color: #E59B94;")
            QMessageBox.warning(self, "Preis konnte nicht gespeichert werden", str(exc))
            return
        self._pending.clear()
        self.status_label.setText("Gespeichert")
        self.status_label.setStyleSheet("color: #9DBA6D;")
        QTimer.singleShot(1400, lambda: (self.status_label.setText("Änderungen werden automatisch gespeichert"), self.status_label.setStyleSheet("")))

    def _filter_rows(self, text: str) -> None:
        needle = text.strip().casefold()
        for row in range(self.table.rowCount()):
            searchable = self.table.item(row, 0).data(Qt.UserRole + 1)
            self.table.setRowHidden(row, bool(needle and needle not in searchable))
        self._update_hit_count()

    def _update_hit_count(self) -> None:
        visible = sum(not self.table.isRowHidden(row) for row in range(self.table.rowCount()))
        self.hit_label.setText(f"{visible} Treffer" if visible != 1 else "1 Treffer")

    def _search_text(self, item) -> str:
        return " ".join([
            item.name or "", item.description or "", item.category.name if item.category else "",
            item.allergens or "", item.additives or "", item.notes or "",
        ]).casefold()

    def _focus_search(self) -> None:
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _escape(self) -> None:
        if self.search_edit.text():
            self.search_edit.clear()
        else:
            self.reject()

    def accept(self) -> None:
        self._flush_pending_changes()
        super().accept()

    def reject(self) -> None:
        self._flush_pending_changes()
        super().reject()
