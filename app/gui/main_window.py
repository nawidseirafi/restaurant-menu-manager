from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from PySide6.QtCore import QLocale, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.database.db import DEFAULT_DB_PATH
from app.database.repositories import MenuRepository
from app.database.repositories.menu_repository import ValidationError
from app.gui.dialogs.price_editor import PriceEditorDialog
from app.gui.theme import apply_theme, mark_button
from app.models import Category, CategoryType, MenuItem
from app.services.backup_service import BackupService
from app.services.html_exporter import HtmlExporter
from app.services.json_service import JsonService
from app.services.pdf_exporter import PdfExporter
from app.services.qr_exporter import QrExporter

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
ITEM_ID_ROLE = Qt.UserRole
CATEGORY_ID_ROLE = Qt.UserRole + 1


class ReorderTableWidget(QTableWidget):
    rowsReordered = Signal(list)

    def dropEvent(self, event) -> None:
        before = self._row_ids()
        super().dropEvent(event)
        after = self._row_ids()
        if after and after != before:
            self.rowsReordered.emit(after)

    def _row_ids(self) -> list[int]:
        ids = []
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item:
                ids.append(item.data(Qt.UserRole))
        return ids


class ImagePathEdit(QLineEdit):
    imageDropped = Signal(str)
    clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Bild auswählen oder hier ablegen")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if self._image_path_from_event(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        path = self._image_path_from_event(event)
        if path:
            self.imageDropped.emit(path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _image_path_from_event(self, event) -> str | None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in IMAGE_SUFFIXES:
                return str(path)
        return None


class ImagePreviewLabel(QLabel):
    imageDropped = Signal(str)
    clicked = Signal()

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event) -> None:
        if self._image_path_from_event(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        path = self._image_path_from_event(event)
        if path:
            self.imageDropped.emit(path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _image_path_from_event(self, event) -> str | None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in IMAGE_SUFFIXES:
                return str(path)
        return None


class MainWindow(QMainWindow):
    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory
        self.session = session_factory()
        self.repo = MenuRepository(self.session)
        self.current_category_id: int | None = None
        self.current_item_id: int | None = None
        self._loading = False
        self._dirty = False
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(450)
        self._autosave_timer.timeout.connect(self._perform_autosave)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(120)
        self._search_timer.timeout.connect(self.reload_items)

        self.setWindowTitle("TacoMex Menu Manager")
        self.setMinimumSize(1120, 720)
        self.resize(1500, 900)
        self._build_ui()
        self._install_shortcuts()
        self.reload_categories()
        self.statusBar().showMessage("Bereit")

    def closeEvent(self, event) -> None:
        if not self._autosave_if_dirty():
            event.ignore()
            return
        self.session.close()
        super().closeEvent(event)

    def _build_ui(self) -> None:
        self._build_toolbar()

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._category_panel())
        splitter.addWidget(self._items_panel())
        splitter.addWidget(self._editor_panel())
        splitter.setSizes([330, 600, 570])
        self.setCentralWidget(splitter)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Aktionen")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)

        self.actions: dict[str, QPushButton | QAction] = {}
        title = QLabel("TacoMex Menu Manager")
        title.setProperty("class", "appTitle")
        toolbar.addWidget(title)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        menu = QMenu(self)
        export_menu = menu.addMenu("Export")
        for label, key, handler in [
            ("Vorschau", "preview", self.preview_html),
            ("PDF erstellen", "pdf", self.export_pdf),
            ("HTML erstellen", "html", self.export_html),
            ("QR-Code erstellen", "qr", self.export_qr),
        ]:
            action = QAction(label, self)
            action.triggered.connect(handler)
            export_menu.addAction(action)
            self.actions[key] = action

        data_menu = menu.addMenu("Daten")
        for label, key, handler in [
            ("Backup erstellen", "backup", self.create_backup),
            ("Backup wiederherstellen", "restore", self.restore_backup),
            ("JSON exportieren", "json_export", self.export_json),
            ("JSON importieren", "json_import", self.import_json),
        ]:
            action = QAction(label, self)
            action.triggered.connect(handler)
            data_menu.addAction(action)
            self.actions[key] = action

        app_menu = menu.addMenu("Anwendung")
        prices_action = QAction("Preise bearbeiten", self)
        prices_action.triggered.connect(self.edit_prices)
        app_menu.addAction(prices_action)
        self.actions["prices"] = prices_action
        quit_action = QAction("Beenden", self)
        quit_action.triggered.connect(self.close)
        app_menu.addAction(quit_action)
        self.actions["quit"] = quit_action

        menu_button = QToolButton()
        menu_button.setText("Menü")
        menu_button.setProperty("class", "menuButton")
        menu_button.setPopupMode(QToolButton.InstantPopup)
        menu_button.setMenu(menu)
        menu_button.setToolTip("Menü")
        toolbar.addWidget(menu_button)
        self._add_toolbar_button(toolbar, "settings", "Einstellungen", QStyle.SP_FileDialogDetailedView, self.open_settings)

    def _add_toolbar_button(self, toolbar: QToolBar, key: str, text: str, icon: QStyle.StandardPixmap, handler, role: str = "secondary") -> None:
        button = QPushButton(self.style().standardIcon(icon), text)
        button.clicked.connect(handler)
        button.setToolTip(text)
        mark_button(button, role)
        toolbar.addWidget(button)
        self.actions[key] = button

    def _category_panel(self) -> QFrame:
        panel = self._panel_frame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        self.category_title = self._panel_title("KATEGORIEN")
        layout.addWidget(self._panel_header(self.category_title, self.new_category, "Kategorie hinzufügen"))
        self.category_table = ReorderTableWidget(0, 2)
        self.category_table.setHorizontalHeaderLabels(["Kategorie", ""])
        self.category_table.horizontalHeader().setVisible(False)
        self.category_table.verticalHeader().setVisible(False)
        self.category_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.category_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.category_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.category_table.setDragDropMode(QAbstractItemView.InternalMove)
        self.category_table.setDefaultDropAction(Qt.MoveAction)
        self.category_table.setDragDropOverwriteMode(False)
        self.category_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.category_table.setShowGrid(False)
        self.category_table.horizontalHeader().setStretchLastSection(False)
        self.category_table.setColumnWidth(1, 44)
        self.category_table.itemSelectionChanged.connect(self.on_category_selected)
        self.category_table.customContextMenuRequested.connect(self.show_category_menu)
        self.category_table.rowsReordered.connect(self.reorder_categories)
        layout.addWidget(self.category_table, 1)
        return panel

    def _items_panel(self) -> QFrame:
        panel = self._panel_frame()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        self.items_title = self._panel_title("GERICHTE")
        self.item_search_edit = QLineEdit()
        self.item_search_edit.setPlaceholderText("Gericht suchen…")
        self.item_search_edit.setClearButtonEnabled(False)
        self.item_search_edit.setFixedWidth(310)
        self.item_search_edit.setProperty("class", "searchField")
        self.item_search_edit.textChanged.connect(self.on_search_changed)
        layout.addWidget(self._items_header())
        self.items_table = ReorderTableWidget(0, 6)
        self.items_table.setHorizontalHeaderLabels(["Name", "Preis", "Aktiv", "Veg.", "Vegan", "Scharf"])
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.setDragDropMode(QAbstractItemView.InternalMove)
        self.items_table.setDefaultDropAction(Qt.MoveAction)
        self.items_table.setDragDropOverwriteMode(False)
        self.items_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.items_table.setAlternatingRowColors(False)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.horizontalHeader().setStretchLastSection(False)
        self.items_table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 6):
            self.items_table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.items_table.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.items_table.doubleClicked.connect(lambda *_: self.name_edit.setFocus())
        self.items_table.customContextMenuRequested.connect(self.show_item_menu)
        self.items_table.rowsReordered.connect(self.reorder_items)
        layout.addWidget(self.items_table, 1)
        return panel

    def _editor_panel(self) -> QScrollArea:
        frame = self._panel_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 18)
        layout.setSpacing(14)
        layout.addWidget(self._panel_title("GERICHT BEARBEITEN"))

        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setFixedHeight(78)
        self.price_spin = self._money_spin()
        self.second_price_spin = self._money_spin()
        self.second_price_spin.setSpecialValueText("—")
        self.second_price_label_edit = QLineEdit()
        self.category_combo = QComboBox()
        self.active_check = QCheckBox("Aktiv")
        self.vegetarian_check = QCheckBox("Vegetarisch")
        self.vegan_check = QCheckBox("Vegan")
        self.spicy_spin = QSpinBox()
        self.spicy_spin.setRange(0, 5)
        self.spicy_spin.setSingleStep(1)
        self.spicy_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spicy_spin.setFixedWidth(58)
        self.spicy_spin.setAlignment(Qt.AlignCenter)
        self.allergens_edit = QLineEdit()
        self.additives_edit = QLineEdit()

        self.image_path_edit = ImagePathEdit()
        self.image_path_edit.setPlaceholderText("Bild auswählen oder hier ablegen")
        self.image_path_edit.clicked.connect(self.select_image)
        self.image_path_edit.imageDropped.connect(self.set_image_path)
        self.image_preview = ImagePreviewLabel("Bild hier ablegen\noder klicken")
        self.image_preview.setProperty("class", "imagePreview")
        self.image_preview.setMinimumHeight(112)
        self.image_preview.setMaximumHeight(150)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setToolTip("Bild auswählen oder hier ablegen")
        self.image_preview.clicked.connect(self.select_image)
        self.image_preview.imageDropped.connect(self.set_image_path)
        self.remove_image_button = QToolButton()
        self.remove_image_button.setText("×")
        self.remove_image_button.setToolTip("Bild entfernen")
        self.remove_image_button.setProperty("class", "iconButton")
        self.remove_image_button.clicked.connect(self.remove_image)

        image_header = QHBoxLayout()
        image_header.setContentsMargins(0, 0, 0, 0)
        image_header.addWidget(self.image_path_edit, 1)
        image_header.addWidget(self.remove_image_button)
        image_box = QWidget()
        image_layout = QVBoxLayout(image_box)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(8)
        image_layout.addLayout(image_header)
        image_layout.addWidget(self.image_preview)

        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(72)

        def add_field(label_text: str, field: QWidget, required: bool = False) -> None:
            label = QLabel(label_text + (" *" if required else ""))
            label.setProperty("class", "fieldLabel")
            if required:
                label.setStyleSheet("color: #D9B45B;")
            layout.addWidget(label)
            layout.addWidget(field)

        add_field("Name", self.name_edit, True)
        add_field("Beschreibung", self.description_edit)

        price_row = QWidget()
        price_layout = QHBoxLayout(price_row)
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(10)
        price_col = QVBoxLayout()
        price_col.setSpacing(5)
        price_label = QLabel("Preis *")
        price_label.setProperty("class", "fieldLabel")
        price_label.setStyleSheet("color: #D9B45B;")
        price_col.addWidget(price_label)
        price_col.addWidget(self.price_spin)
        second_col = QVBoxLayout()
        second_col.setSpacing(5)
        second_label = QLabel("Zweiter Preis")
        second_label.setProperty("class", "fieldLabel")
        second_col.addWidget(second_label)
        second_col.addWidget(self.second_price_spin)
        price_layout.addLayout(price_col, 1)
        price_layout.addLayout(second_col, 1)
        layout.addWidget(price_row)

        add_field("Label zweiter Preis", self.second_price_label_edit)
        add_field("Kategorie", self.category_combo, True)

        status_label = QLabel("Status")
        status_label.setProperty("class", "fieldLabel")
        layout.addWidget(status_label)
        layout.addWidget(self._status_row())

        add_field("Allergene", self.allergens_edit)
        add_field("Zusatzstoffe", self.additives_edit)
        add_field("Bild", image_box)
        add_field("Notizen", self.notes_edit)
        layout.addStretch(1)

        for widget in [
            self.name_edit, self.description_edit, self.price_spin, self.second_price_spin,
            self.second_price_label_edit, self.category_combo, self.active_check,
            self.vegetarian_check, self.vegan_check, self.spicy_spin, self.allergens_edit,
            self.additives_edit, self.image_path_edit, self.notes_edit,
        ]:
            self._connect_dirty(widget)
        self.image_path_edit.textChanged.connect(lambda *_: self._update_image_preview())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(frame)
        return scroll

    def _panel_frame(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "panel")
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return frame

    def _panel_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("class", "panelTitle")
        return label

    def _panel_header(self, title: QLabel, add_handler, tooltip: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(title)
        layout.addStretch(1)
        button = QToolButton()
        button.setText("+")
        button.setToolTip(tooltip)
        button.setProperty("class", "addButton")
        button.clicked.connect(add_handler)
        layout.addWidget(button)
        return widget

    def _items_header(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.items_title)
        layout.addStretch(1)
        layout.addWidget(self.item_search_edit)
        button = QToolButton()
        button.setText("+")
        button.setToolTip("Gericht hinzufügen")
        button.setProperty("class", "addButton")
        button.clicked.connect(self.new_item)
        layout.addWidget(button)
        return widget

    def _required_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setProperty("class", "required")
        return label

    def _status_row(self) -> QWidget:
        widget = QFrame()
        widget.setProperty("class", "softGroup")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 7, 10, 7)
        layout.setSpacing(10)
        layout.addWidget(self.active_check)
        layout.addWidget(self.vegetarian_check)
        layout.addWidget(self.vegan_check)
        layout.addStretch(1)
        spicy_label = QLabel("Schärfe")
        spicy_label.setProperty("class", "hint")
        layout.addWidget(spicy_label)
        layout.addWidget(self.spicy_spin)
        return widget

    def _money_spin(self) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0, 9999)
        spin.setDecimals(2)
        spin.setSingleStep(0.50)
        spin.setSuffix(" EUR")
        spin.setLocale(QLocale(QLocale.German, QLocale.Germany))
        spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        return spin

    def _connect_dirty(self, widget: QWidget) -> None:
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(self._mark_dirty)
        elif isinstance(widget, QTextEdit):
            widget.textChanged.connect(self._mark_dirty)
        elif isinstance(widget, QDoubleSpinBox):
            widget.valueChanged.connect(self._mark_dirty)
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(self._mark_dirty)
        elif isinstance(widget, QCheckBox):
            widget.toggled.connect(self._mark_dirty)
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(self._mark_dirty)

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence.Save, self, activated=self.save_item)
        QShortcut(QKeySequence.Delete, self, activated=self.delete_selected)
        QShortcut(QKeySequence("F2"), self, activated=self.rename_category)
        QShortcut(QKeySequence("Ctrl+D"), self, activated=self.duplicate_item)
        QShortcut(QKeySequence.Find, self, activated=self.focus_search)
        QShortcut(QKeySequence("Esc"), self, activated=self.clear_search)

    def on_search_changed(self) -> None:
        if self._loading:
            return
        self._search_timer.start()

    def focus_search(self) -> None:
        self.item_search_edit.setFocus()
        self.item_search_edit.selectAll()

    def clear_search(self) -> None:
        if self.item_search_edit.text():
            self.item_search_edit.clear()
        elif self.item_search_edit.hasFocus():
            self.items_table.setFocus()

    def reload_categories(self, select_category_id: int | None = None) -> None:
        self._loading = True
        previous = select_category_id or self.current_category_id
        self.category_table.setRowCount(0)
        self.category_combo.clear()
        categories = self.repo.list_categories(active_only=False)
        counts = {category.id: len(category.items) for category in categories}
        self.category_table.setRowCount(len(categories))
        for row, category in enumerate(categories):
            name = category.name if category.active else f"{category.name}  inaktiv"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, category.id)
            count_item = QTableWidgetItem(str(counts[category.id]))
            count_item.setData(Qt.UserRole, category.id)
            count_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.category_table.setItem(row, 0, name_item)
            self.category_table.setItem(row, 1, count_item)
            self.category_table.setRowHeight(row, 40)
            self.category_combo.addItem(category.name, category.id)
        self.category_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._loading = False
        if categories:
            target = previous if previous else categories[0].id
            self._select_category_by_id(target)
        self._update_buttons()

    def reload_items(self, select_item_id: int | None = None) -> None:
        if self._search_query():
            self.reload_search_results(select_item_id)
            return
        self._loading = True
        self.items_table.setRowCount(0)
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["Name", "Preis", "Aktiv", "Veg.", "Vegan", "Scharf"])
        self.items_table.setDragEnabled(True)
        self.items_table.setDragDropMode(QAbstractItemView.InternalMove)
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 6):
            self.items_table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)
        category = self.repo.get_category(self.current_category_id) if self.current_category_id else None
        self.items_title.setText(f"GERICHTE - {category.name.upper()}" if category else "GERICHTE")
        if not self.current_category_id:
            self._loading = False
            self._update_buttons()
            return

        items = self.repo.list_items(self.current_category_id, active_only=False)
        self.items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            values = [
                f"{item.sort_order}.  {item.name}",
                f"{item.price:.2f} EUR".replace(".", ","),
                "Ja" if item.active else "Nein",
                "Ja" if item.vegetarian else "",
                "Ja" if item.vegan else "",
                str(item.spicy_level) if item.spicy_level else "",
            ]
            self._set_item_row(row, item, values, center_columns={1, 2, 3, 4, 5})
            self.items_table.setRowHeight(row, 42)
        self._loading = False

        if items:
            self._select_item_by_id(select_item_id or self.current_item_id or items[0].id)
        else:
            self.current_item_id = None
            self._clear_editor()
        self._update_status()
        self._update_buttons()

    def reload_search_results(self, select_item_id: int | None = None) -> None:
        if not self._autosave_if_dirty():
            return
        self._loading = True
        query = self._search_query()
        self.items_title.setText("GERICHTE - SUCHE")
        self.items_table.setRowCount(0)
        self.items_table.setColumnCount(3)
        self.items_table.setHorizontalHeaderLabels(["Name", "Kategorie", "Preis"])
        self.items_table.setDragEnabled(False)
        self.items_table.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)

        results = self._search_items(query)
        self.items_table.setRowCount(len(results))
        for row, item in enumerate(results):
            category_name = item.category.name if item.category else ""
            values = [
                item.name,
                category_name,
                f"{item.price:.2f} EUR".replace(".", ","),
            ]
            self._set_item_row(row, item, values, center_columns={2})
            self.items_table.setRowHeight(row, 42)
        self._loading = False

        if results:
            target_id = select_item_id or self.current_item_id
            if target_id and any(item.id == target_id for item in results):
                self._select_item_by_id(target_id)
            else:
                self.current_item_id = None
                self.items_table.clearSelection()
                self._clear_editor()
            self.statusBar().showMessage(f"{len(results)} Treffer")
        else:
            self.current_item_id = None
            self._clear_editor()
            self.statusBar().showMessage("Keine Gerichte gefunden")
        self._update_buttons()

    def on_category_selected(self) -> None:
        if self._loading:
            return
        selected = self.category_table.selectedItems()
        if not selected:
            return
        if not self._autosave_if_dirty():
            return
        self.current_category_id = selected[0].data(Qt.UserRole)
        if self._search_query():
            self._update_status()
            return
        self.current_item_id = None
        self.reload_items()

    def on_item_selection_changed(self) -> None:
        if self._loading:
            return
        selected = self.items_table.selectedItems()
        if not selected:
            self.current_item_id = None
            self._update_buttons()
            return
        new_id = selected[0].data(Qt.UserRole)
        category_id = selected[0].data(CATEGORY_ID_ROLE)
        if new_id == self.current_item_id:
            return
        if not self._autosave_if_dirty():
            self._select_item_by_id(self.current_item_id)
            return
        self.current_item_id = new_id
        item = self.repo.get_item(self.current_item_id)
        if item:
            if self._search_query() and category_id:
                self.current_category_id = category_id
                self._select_category_by_id(category_id)
            self._load_item(item)
        self._update_buttons()

    def _load_item(self, item: MenuItem) -> None:
        self._loading = True
        self.name_edit.setText(item.name)
        self.description_edit.setPlainText(item.description or "")
        self.price_spin.setValue(float(item.price))
        self.second_price_spin.setValue(float(item.second_price or 0))
        self.second_price_label_edit.setText(item.second_price_label or "")
        self.category_combo.setCurrentIndex(max(0, self.category_combo.findData(item.category_id)))
        self.active_check.setChecked(item.active)
        self.vegetarian_check.setChecked(item.vegetarian)
        self.vegan_check.setChecked(item.vegan)
        self.spicy_spin.setValue(item.spicy_level)
        self.allergens_edit.setText(item.allergens or "")
        self.additives_edit.setText(item.additives or "")
        self.image_path_edit.setText(item.image_path or "")
        self.notes_edit.setPlainText(item.notes or "")
        self._update_image_preview()
        self._loading = False
        self._dirty = False

    def _clear_editor(self) -> None:
        self._loading = True
        for widget in [self.name_edit, self.second_price_label_edit, self.allergens_edit, self.additives_edit, self.image_path_edit]:
            widget.clear()
        self.description_edit.clear()
        self.notes_edit.clear()
        self.price_spin.setValue(0)
        self.second_price_spin.setValue(0)
        self.active_check.setChecked(False)
        self.vegetarian_check.setChecked(False)
        self.vegan_check.setChecked(False)
        self.spicy_spin.setValue(0)
        self._update_image_preview()
        self._loading = False
        self._dirty = False

    def new_category(self) -> None:
        name, ok = QInputDialog.getText(self, "Neue Kategorie", "Name")
        if ok and name.strip():
            category = Category(name=name.strip(), sort_order=len(self.repo.list_categories()) + 1, type=CategoryType.food)
            saved = self._run_user_action(lambda: self.repo.save_category(category), "Kategorie erstellt")
            if saved:
                self.reload_categories(saved.id)

    def rename_category(self) -> None:
        category = self._selected_category()
        if not category:
            return
        name, ok = QInputDialog.getText(self, "Kategorie bearbeiten", "Name", text=category.name)
        if ok and name.strip():
            category.name = name.strip()
            self._run_user_action(lambda: self.repo.save_category(category), "Kategorie gespeichert")
            self.reload_categories(category.id)

    def toggle_category(self) -> None:
        category = self._selected_category()
        if category:
            category.active = not category.active
            self._run_user_action(lambda: self.repo.save_category(category), "Kategorie aktualisiert")
            self.reload_categories(category.id)

    def show_category_menu(self, position) -> None:
        row = self.category_table.rowAt(position.y())
        if row >= 0:
            self.category_table.selectRow(row)
        category = self._selected_category()
        if not category:
            return
        menu = QMenu(self)
        rename_action = menu.addAction("Umbenennen")
        toggle_action = menu.addAction("Deaktivieren" if category.active else "Aktivieren")
        menu.addSeparator()
        delete_action = menu.addAction("Löschen")
        delete_action.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxCritical))
        selected = menu.exec(self.category_table.viewport().mapToGlobal(position))
        if selected == rename_action:
            self.rename_category()
        elif selected == toggle_action:
            self.toggle_category()
        elif selected == delete_action:
            self.delete_category()

    def delete_category(self) -> None:
        category = self._selected_category()
        if category and QMessageBox.question(self, "Loeschen", f"Kategorie '{category.name}' loeschen?") == QMessageBox.Yes:
            self.repo.delete_category(category.id)
            self.current_category_id = None
            self.reload_categories()
            self.statusBar().showMessage("Kategorie geloescht", 3000)

    def move_category(self, direction: int) -> None:
        category = self._selected_category()
        if category:
            self.repo.reorder_category(category.id, direction)
            self.reload_categories(category.id)
            self.statusBar().showMessage("Kategorie sortiert", 2500)

    def reorder_categories(self, category_ids: list[int]) -> None:
        current_id = self.current_category_id
        self._run_user_action(lambda: self.repo.set_category_order(category_ids), "Kategorie-Reihenfolge gespeichert")
        self.reload_categories(current_id)

    def new_item(self) -> None:
        if not self.current_category_id:
            QMessageBox.information(self, "Kategorie fehlt", "Bitte zuerst eine Kategorie auswaehlen.")
            return
        if not self._autosave_if_dirty():
            return
        item = MenuItem(
            category_id=self.current_category_id,
            name="Neues Gericht",
            description="",
            price=0,
            sort_order=len(self.repo.list_items(self.current_category_id)) + 1,
            active=True,
        )
        saved = self._run_user_action(lambda: self.repo.save_item(item), "Gericht erstellt")
        if saved:
            self.reload_categories(self.current_category_id)
            self.reload_items(saved.id)
            self.name_edit.setFocus()
            self.name_edit.selectAll()

    def save_item(self) -> None:
        item = self.repo.get_item(self.current_item_id) if self.current_item_id else None
        if not item:
            QMessageBox.information(self, "Auswahl fehlt", "Bitte ein Gericht auswaehlen.")
            return
        previous_category_id = item.category_id
        try:
            self._apply_editor_to_item(item)
            self.repo.save_item(item)
        except (ValidationError, ValueError) as exc:
            QMessageBox.warning(self, "Eingabe pruefen", str(exc))
            return
        self._dirty = False
        self._autosave_timer.stop()
        self.current_category_id = item.category_id
        self.reload_categories(item.category_id)
        if previous_category_id == item.category_id:
            self.reload_items(item.id)
        self.statusBar().showMessage("Gericht gespeichert", 3000)

    def duplicate_item(self) -> None:
        if self.current_item_id:
            saved = self._run_user_action(lambda: self.repo.duplicate_item(self.current_item_id), "Gericht dupliziert")
            if saved:
                self.reload_items(saved.id)

    def toggle_item(self) -> None:
        item = self.repo.get_item(self.current_item_id) if self.current_item_id else None
        if item:
            item.active = not item.active
            self._run_user_action(lambda: self.repo.save_item(item), "Gericht aktualisiert")
            self.reload_items(item.id)

    def show_item_menu(self, position) -> None:
        row = self.items_table.rowAt(position.y())
        if row >= 0:
            self.items_table.selectRow(row)
        item = self.repo.get_item(self.current_item_id) if self.current_item_id else None
        if not item:
            return
        menu = QMenu(self)
        duplicate_action = menu.addAction("Duplizieren")
        toggle_action = menu.addAction("Deaktivieren" if item.active else "Aktivieren")
        menu.addSeparator()
        delete_action = menu.addAction("Löschen")
        delete_action.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxCritical))
        selected = menu.exec(self.items_table.viewport().mapToGlobal(position))
        if selected == duplicate_action:
            self.duplicate_item()
        elif selected == toggle_action:
            self.toggle_item()
        elif selected == delete_action:
            self.delete_item()

    def delete_selected(self) -> None:
        if self.category_table.hasFocus():
            self.delete_category()
        elif self.items_table.hasFocus() or self.current_item_id:
            self.delete_item()

    def delete_item(self) -> None:
        item = self.repo.get_item(self.current_item_id) if self.current_item_id else None
        if item and QMessageBox.question(self, "Loeschen", f"Gericht '{item.name}' loeschen?") == QMessageBox.Yes:
            self.repo.delete_item(item.id)
            self.current_item_id = None
            self.reload_items()
            self.statusBar().showMessage("Gericht geloescht", 3000)

    def move_item(self, direction: int) -> None:
        if self.current_item_id:
            item_id = self.current_item_id
            self.repo.reorder_item(item_id, direction)
            self.reload_items(item_id)
            self.statusBar().showMessage("Gericht sortiert", 2500)

    def reorder_items(self, item_ids: list[int]) -> None:
        if not self.current_category_id:
            return
        current_id = self.current_item_id
        self._run_user_action(lambda: self.repo.set_item_order(self.current_category_id, item_ids), "Gericht-Reihenfolge gespeichert")
        self.reload_items(current_id)

    def edit_prices(self) -> None:
        dialog = PriceEditorDialog(self.repo, self)
        if dialog.exec():
            self.reload_items(self.current_item_id)
            if self.current_item_id:
                item = self.repo.get_item(self.current_item_id)
                if item:
                    self._load_item(item)
            self.statusBar().showMessage("Preise aktualisiert", 3000)

    def preview_html(self) -> None:
        target = PROJECT_ROOT / "exports" / "preview"
        result = self._run_user_action(lambda: HtmlExporter().export(self.session, target), "Vorschau erstellt")
        if result:
            QMessageBox.information(self, "Vorschau erstellt", f"HTML-Vorschau wurde erstellt:\n{result}")

    def export_html(self) -> None:
        target = QFileDialog.getExistingDirectory(self, "HTML-Export Ordner", str(PROJECT_ROOT / "exports" / "html"))
        if target:
            self._run_user_action(lambda: HtmlExporter().export(self.session, Path(target)), "HTML exportiert")

    def export_pdf(self) -> None:
        target, _ = QFileDialog.getSaveFileName(self, "PDF exportieren", str(PROJECT_ROOT / "exports" / "menu.pdf"), "PDF (*.pdf)")
        if target:
            self._run_user_action(lambda: asyncio.run(PdfExporter().export(self.session, Path(target))), "PDF exportiert")

    def export_qr(self) -> None:
        settings = self.repo.get_settings()
        target, _ = QFileDialog.getSaveFileName(self, "QR-Code exportieren", str(PROJECT_ROOT / "exports" / "qr-code.png"), "PNG (*.png);;SVG (*.svg)")
        if target:
            exporter = QrExporter()
            path = Path(target)
            self._run_user_action(
                lambda: exporter.export_svg(settings.menu_url, path) if path.suffix.lower() == ".svg" else exporter.export_png(settings.menu_url, path),
                "QR-Code exportiert",
            )

    def create_backup(self) -> None:
        self._run_user_action(lambda: BackupService().create_backup(DEFAULT_DB_PATH, PROJECT_ROOT / "exports" / "backups"), "Backup erstellt")

    def restore_backup(self) -> None:
        source, _ = QFileDialog.getOpenFileName(self, "Backup wiederherstellen", str(PROJECT_ROOT / "exports" / "backups"), "SQLite DB (*.db)")
        if not source:
            return
        if QMessageBox.question(self, "Backup wiederherstellen", "Aktuelle Datenbank durch dieses Backup ersetzen?") != QMessageBox.Yes:
            return
        try:
            self.session.close()
            BackupService().restore_backup(Path(source), DEFAULT_DB_PATH)
            self.session = self.session_factory()
            self.repo = MenuRepository(self.session)
            self.reload_categories()
            self.statusBar().showMessage("Backup wiederhergestellt", 4000)
        except Exception as exc:
            LOGGER.exception("Backup restore failed")
            QMessageBox.critical(self, "Fehler", str(exc))

    def export_json(self) -> None:
        target, _ = QFileDialog.getSaveFileName(self, "JSON exportieren", str(PROJECT_ROOT / "exports" / "menu.json"), "JSON (*.json)")
        if target:
            self._run_user_action(lambda: JsonService().export_menu(self.session, Path(target)), "JSON exportiert")

    def import_json(self) -> None:
        source, _ = QFileDialog.getOpenFileName(self, "JSON importieren", str(PROJECT_ROOT / "exports"), "JSON (*.json)")
        if source and QMessageBox.question(self, "Import", "Aktuelle Menudaten ersetzen?") == QMessageBox.Yes:
            self._run_user_action(lambda: JsonService().import_menu(self.session, Path(source)), "JSON importiert")
            self.reload_categories()

    def open_settings(self) -> None:
        QMessageBox.information(self, "Einstellungen", "Der Einstellungsdialog ist fuer die naechste UI-Iteration vorgesehen.")

    def select_image(self) -> None:
        source, _ = QFileDialog.getOpenFileName(self, "Bild auswaehlen", str(PROJECT_ROOT), "Bilder (*.png *.jpg *.jpeg *.webp)")
        if source:
            self.set_image_path(source)

    def remove_image(self) -> None:
        self.image_path_edit.clear()

    def set_image_path(self, path: str) -> None:
        self.image_path_edit.setText(path)

    def _apply_editor_to_item(self, item: MenuItem) -> None:
        item.name = self.name_edit.text().strip()
        item.description = self.description_edit.toPlainText().strip()
        item.price = self.price_spin.value()
        second_price = self.second_price_spin.value()
        item.second_price = second_price if second_price > 0 else None
        item.second_price_label = self.second_price_label_edit.text().strip() or None
        item.category_id = self.category_combo.currentData()
        item.active = self.active_check.isChecked()
        item.vegetarian = self.vegetarian_check.isChecked()
        item.vegan = self.vegan_check.isChecked()
        item.spicy_level = self.spicy_spin.value()
        item.allergens = self.allergens_edit.text().strip() or None
        item.additives = self.additives_edit.text().strip() or None
        item.image_path = self.image_path_edit.text().strip() or None
        item.notes = self.notes_edit.toPlainText().strip() or None

    def _search_query(self) -> str:
        return self.item_search_edit.text().strip()

    def _search_items(self, query: str) -> list[MenuItem]:
        needle = query.casefold()
        matches = []
        for category in self.repo.menu_tree(active_only=True):
            category_text = category.name.casefold()
            for item in category.items:
                searchable = " ".join(
                    [
                        item.name or "",
                        item.description or "",
                        category_text,
                        item.allergens or "",
                        item.additives or "",
                        item.notes or "",
                    ]
                ).casefold()
                if needle in searchable:
                    matches.append(item)
        return matches

    def _set_item_row(self, row: int, item: MenuItem, values: list[str], center_columns: set[int] | None = None) -> None:
        center_columns = center_columns or set()
        for col, value in enumerate(values):
            cell = QTableWidgetItem(value)
            cell.setData(ITEM_ID_ROLE, item.id)
            cell.setData(CATEGORY_ID_ROLE, item.category_id)
            if col in center_columns:
                cell.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(row, col, cell)

    def _autosave_if_dirty(self) -> bool:
        if self._loading or not self._dirty or not self.current_item_id:
            return True
        self._autosave_timer.stop()
        item = self.repo.get_item(self.current_item_id)
        if not item:
            return True
        try:
            previous_category_id = item.category_id
            self._apply_editor_to_item(item)
            self.repo.save_item(item)
            self._dirty = False
            if previous_category_id != item.category_id:
                self.current_category_id = item.category_id
                self.reload_categories(item.category_id)
                self.reload_items(item.id)
            else:
                self._update_current_item_row(item)
            self.statusBar().showMessage("Änderungen gespeichert", 2500)
            return True
        except (ValidationError, ValueError) as exc:
            QMessageBox.warning(self, "Eingabe pruefen", f"Die aktuellen Aenderungen koennen nicht gespeichert werden:\n{exc}")
            return False

    def _perform_autosave(self) -> None:
        if self._loading or not self._dirty or not self.current_item_id:
            return
        item = self.repo.get_item(self.current_item_id)
        if not item:
            return
        try:
            previous_category_id = item.category_id
            self._apply_editor_to_item(item)
            self.repo.save_item(item)
            self._dirty = False
            if previous_category_id != item.category_id:
                self.current_category_id = item.category_id
                self.reload_categories(item.category_id)
                self.reload_items(item.id)
            else:
                self._update_current_item_row(item)
            self.statusBar().showMessage("Änderungen gespeichert", 2500)
        except (ValidationError, ValueError) as exc:
            self.statusBar().showMessage(f"Autosave nicht möglich: {exc}", 5000)

    def _selected_category(self) -> Category | None:
        selected = self.category_table.selectedItems()
        return self.repo.get_category(selected[0].data(Qt.UserRole)) if selected else None

    def _select_category_by_id(self, category_id: int | None) -> None:
        if not category_id:
            return
        for row in range(self.category_table.rowCount()):
            item = self.category_table.item(row, 0)
            if item.data(Qt.UserRole) == category_id:
                self.category_table.selectRow(row)
                self.current_category_id = category_id
                return

    def _select_item_by_id(self, item_id: int | None) -> None:
        if not item_id:
            return
        for row in range(self.items_table.rowCount()):
            cell = self.items_table.item(row, 0)
            if cell and cell.data(Qt.UserRole) == item_id:
                self.items_table.selectRow(row)
                self.current_item_id = item_id
                item = self.repo.get_item(item_id)
                if item:
                    self._load_item(item)
                return

    def _update_image_preview(self) -> None:
        path = Path(self.image_path_edit.text().strip())
        if path.exists() and path.is_file():
            pixmap = QPixmap(str(path)).scaled(150, 92, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_preview.setPixmap(pixmap)
            self.image_preview.setText("")
        else:
            self.image_preview.setPixmap(QPixmap())
            self.image_preview.setText("Kein Bild")

    def _mark_dirty(self, *_args) -> None:
        if not self._loading and self.current_item_id:
            self._dirty = True
            self.statusBar().showMessage("Ungespeicherte Änderungen")
            self._autosave_timer.start()

    def _update_current_item_row(self, item: MenuItem) -> None:
        for row in range(self.items_table.rowCount()):
            cell = self.items_table.item(row, 0)
            if cell and cell.data(Qt.UserRole) == item.id:
                if self._search_query():
                    category = self.repo.get_category(item.category_id)
                    values = [
                        item.name,
                        category.name if category else "",
                        f"{float(item.price):.2f} EUR".replace(".", ","),
                    ]
                else:
                    values = [
                        f"{item.sort_order}.  {item.name}",
                        f"{float(item.price):.2f} EUR".replace(".", ","),
                        "Ja" if item.active else "Nein",
                        "Ja" if item.vegetarian else "",
                        "Ja" if item.vegan else "",
                        str(item.spicy_level) if item.spicy_level else "",
                    ]
                for col, value in enumerate(values):
                    table_item = self.items_table.item(row, col)
                    if table_item:
                        table_item.setText(value)
                break
        self._update_status()

    def _update_status(self) -> None:
        category_count = len(self.repo.list_items(self.current_category_id, active_only=False)) if self.current_category_id else 0
        total_count = len(self.repo.list_items(active_only=False))
        self.statusBar().showMessage(f"{category_count} Gerichte in dieser Kategorie        Gesamt: {total_count} Gerichte")

    def _update_buttons(self) -> None:
        self.actions["prices"].setEnabled(self.current_item_id is not None)

    def _run_user_action(self, action, success_message: str | None = None):
        try:
            result = action()
            if result:
                LOGGER.info("Action completed: %s", result)
            if success_message:
                self.statusBar().showMessage(success_message, 3000)
            return result
        except Exception as exc:
            LOGGER.exception("User action failed")
            QMessageBox.critical(self, "Fehler", str(exc))
            return None


def run_app(session_factory) -> int:
    app = QApplication([])
    apply_theme(app)
    window = MainWindow(session_factory)
    window.show()
    return app.exec()
