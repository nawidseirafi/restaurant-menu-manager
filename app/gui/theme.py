from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication, QPushButton


COLORS = {
    "window": "#141619",
    "surface": "#1c1f22",
    "surface_alt": "#22262a",
    "field": "#282c31",
    "field_hover": "#30353b",
    "border": "#353a40",
    "border_focus": "#e58a1f",
    "text": "#f2f2f2",
    "muted": "#b8b8b8",
    "disabled": "#70757c",
    "red": "#c83228",
    "red_hover": "#df4338",
    "orange": "#e58a1f",
    "orange_hover": "#f09a32",
    "yellow": "#e2b632",
    "green": "#7fa337",
    "green_hover": "#91b742",
    "selection": "#3a2a1c",
}


def apply_theme(app: QApplication) -> None:
    available = set(QFontDatabase.families())
    family = next(
        (name for name in [".AppleSystemUIFont", "Segoe UI", "Inter", "Arial", "Helvetica"] if name in available),
        QFontDatabase.systemFont(QFontDatabase.GeneralFont).family(),
    )
    font = QFont(family)
    font.setPointSize(10)
    app.setFont(font)
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(COLORS["window"]))
    palette.setColor(QPalette.WindowText, QColor(COLORS["text"]))
    palette.setColor(QPalette.Base, QColor(COLORS["field"]))
    palette.setColor(QPalette.AlternateBase, QColor(COLORS["surface_alt"]))
    palette.setColor(QPalette.Text, QColor(COLORS["text"]))
    palette.setColor(QPalette.Button, QColor(COLORS["surface_alt"]))
    palette.setColor(QPalette.ButtonText, QColor(COLORS["text"]))
    palette.setColor(QPalette.Highlight, QColor(COLORS["orange"]))
    palette.setColor(QPalette.HighlightedText, QColor("#15110d"))
    palette.setColor(QPalette.ToolTipBase, QColor(COLORS["surface_alt"]))
    palette.setColor(QPalette.ToolTipText, QColor(COLORS["text"]))
    app.setPalette(palette)
    app.setStyleSheet(global_stylesheet())


def mark_button(button: QPushButton, role: str) -> None:
    button.setProperty("role", role)
    button.style().unpolish(button)
    button.style().polish(button)


def global_stylesheet() -> str:
    c = COLORS
    return f"""
    * {{
        color: {c["text"]};
        selection-background-color: {c["orange"]};
        selection-color: #15110d;
    }}

    QMainWindow, QDialog, QWidget {{
        background-color: {c["window"]};
        color: {c["text"]};
    }}

    QToolTip {{
        background-color: {c["surface_alt"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        padding: 6px;
        border-radius: 4px;
    }}

    QStatusBar {{
        background: {c["surface"]};
        border-top: 1px solid {c["border"]};
        color: {c["muted"]};
    }}

    QMenuBar, QMenu {{
        background-color: {c["surface"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
    }}

    QMenu::item {{
        padding: 7px 22px;
        background: transparent;
        color: {c["text"]};
    }}

    QMenu::item:selected {{
        background: {c["selection"]};
        color: {c["text"]};
    }}

    QToolBar {{
        background: #181a1d;
        border: 0;
        border-bottom: 1px solid {c["border"]};
        spacing: 8px;
        padding: 10px 12px;
    }}

    QToolBar::separator {{
        background: {c["border"]};
        width: 1px;
        margin: 6px 8px;
    }}

    QLabel {{
        color: {c["text"]};
        background: transparent;
    }}

    QLabel[class="panelTitle"] {{
        color: {c["muted"]};
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0px;
        padding: 0 0 6px;
    }}

    QLabel[class="appTitle"] {{
        color: {c["text"]};
        font-size: 15px;
        font-weight: 700;
        padding: 0 12px 0 2px;
    }}

    QLabel[class="required"] {{
        color: {c["yellow"]};
        font-weight: 700;
    }}

    QFrame[class="panel"] {{
        background: {c["surface"]};
        border: 1px solid #2b3035;
        border-radius: 8px;
    }}

    QSplitter {{
        background: {c["window"]};
    }}

    QSplitter::handle {{
        background: {c["window"]};
        width: 8px;
    }}

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {c["field"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 7px;
        padding: 7px 9px;
        min-height: 32px;
    }}

    QTextEdit, QPlainTextEdit {{
        selection-background-color: {c["orange"]};
    }}

    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
        background-color: {c["field_hover"]};
        border-color: #454b52;
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {c["border_focus"]};
    }}

    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: #1d2023;
        color: {c["disabled"]};
        border-color: #2b2f34;
    }}

    QComboBox::drop-down {{
        background: {c["surface_alt"]};
        border-left: 1px solid {c["border"]};
        border-top-right-radius: 7px;
        border-bottom-right-radius: 7px;
        width: 30px;
    }}

    QComboBox::drop-down:hover {{
        background: {c["field_hover"]};
    }}

    QComboBox::down-arrow {{
        image: none;
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {c["text"]};
        margin-right: 9px;
    }}

    QComboBox::down-arrow:disabled {{
        border-top-color: {c["disabled"]};
    }}

    QSpinBox, QDoubleSpinBox {{
        padding-right: 28px;
    }}

    QSpinBox::up-button, QDoubleSpinBox::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        background: {c["surface_alt"]};
        border-left: 1px solid {c["border"]};
        border-bottom: 1px solid {c["border"]};
        border-top-right-radius: 7px;
        width: 24px;
    }}

    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        background: {c["surface_alt"]};
        border-left: 1px solid {c["border"]};
        border-bottom-right-radius: 7px;
        width: 24px;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover,
    QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
        background: {c["field_hover"]};
    }}

    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
        image: none;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 5px solid {c["text"]};
    }}

    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
        image: none;
        width: 0;
        height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {c["text"]};
    }}

    QSpinBox::up-arrow:disabled, QSpinBox::down-arrow:disabled,
    QDoubleSpinBox::up-arrow:disabled, QDoubleSpinBox::down-arrow:disabled {{
        border-top-color: {c["disabled"]};
        border-bottom-color: {c["disabled"]};
    }}

    QComboBox QAbstractItemView {{
        background: {c["surface_alt"]};
        color: {c["text"]};
        border: 1px solid {c["border"]};
        selection-background-color: {c["selection"]};
        selection-color: {c["text"]};
        outline: 0;
    }}

    QListWidget, QTableWidget, QTableView {{
        background: {c["surface_alt"]};
        alternate-background-color: #1d2023;
        color: {c["text"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        gridline-color: {c["border"]};
        outline: 0;
    }}

    QListWidget::item {{
        min-height: 38px;
        padding: 8px 10px;
        color: {c["text"]};
        border-bottom: 1px solid #282c31;
    }}

    QListWidget::item:hover {{
        background: {c["field_hover"]};
    }}

    QListWidget::item:selected {{
        background: {c["selection"]};
        color: {c["text"]};
        border-left: 3px solid {c["orange"]};
    }}

    QHeaderView::section {{
        background: #181b1e;
        color: {c["muted"]};
        border: 0;
        border-bottom: 1px solid {c["border"]};
        padding: 8px;
        font-weight: 700;
    }}

    QTableWidget::item {{
        padding: 7px;
        color: {c["text"]};
    }}

    QTableWidget::item:hover {{
        background: {c["field_hover"]};
    }}

    QTableWidget::item:selected {{
        background: {c["selection"]};
        color: {c["text"]};
    }}

    QTableWidget::item:disabled {{
        color: {c["disabled"]};
    }}

    QCheckBox {{
        color: {c["text"]};
        spacing: 8px;
        background: transparent;
        min-height: 28px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1px solid {c["border"]};
        background: {c["field"]};
    }}

    QCheckBox::indicator:hover {{
        border-color: {c["orange"]};
        background: {c["field_hover"]};
    }}

    QCheckBox::indicator:checked {{
        background: {c["green"]};
        border-color: {c["green"]};
    }}

    QPushButton, QToolButton {{
        background: #24282d;
        color: {c["text"]};
        border: 1px solid #333940;
        border-radius: 8px;
        padding: 7px 11px;
        min-height: 30px;
    }}

    QPushButton:hover, QToolButton:hover {{
        background: {c["field_hover"]};
        border-color: #4b5158;
    }}

    QPushButton:disabled, QToolButton:disabled {{
        background: #1a1d20;
        color: {c["disabled"]};
        border-color: #292d31;
    }}

    QPushButton[role="primary"] {{
        background: {c["green"]};
        border-color: {c["green"]};
        color: #10130d;
        font-weight: 700;
    }}

    QPushButton[role="primary"]:hover {{
        background: {c["green_hover"]};
    }}

    QPushButton[role="accent"] {{
        background: {c["orange"]};
        border-color: {c["orange"]};
        color: #18110a;
        font-weight: 700;
    }}

    QPushButton[role="accent"]:hover {{
        background: {c["orange_hover"]};
    }}

    QPushButton[role="danger"] {{
        background: {c["red"]};
        border-color: {c["red"]};
        color: #fff5f3;
        font-weight: 700;
    }}

    QPushButton[role="danger"]:hover {{
        background: {c["red_hover"]};
    }}

    QToolButton[class="addButton"], QToolButton[class="iconButton"] {{
        min-width: 28px;
        min-height: 28px;
        padding: 0;
        border-radius: 6px;
        font-weight: 700;
    }}

    QToolButton[class="addButton"] {{
        color: #18110a;
        background: {c["orange"]};
        border-color: {c["orange"]};
    }}

    QToolButton[class="addButton"]:hover {{
        background: {c["orange_hover"]};
    }}

    QToolButton[class="iconButton"] {{
        color: #fff5f3;
        background: #2a2221;
        border-color: #57312d;
    }}

    QToolButton[class="iconButton"]:hover {{
        background: {c["red"]};
        border-color: {c["red"]};
    }}

    QLabel[class="imagePreview"] {{
        border: 1px solid {c["border"]};
        border-radius: 6px;
        color: {c["muted"]};
        background: {c["field"]};
    }}

    QLabel[class="imagePreview"]:hover {{
        border-color: {c["orange"]};
        background: {c["field_hover"]};
    }}

    QDialogButtonBox QPushButton {{
        min-width: 92px;
    }}

    QSlider::groove:horizontal {{
        height: 5px;
        border-radius: 3px;
        background: #353a40;
    }}

    QSlider::sub-page:horizontal {{
        height: 5px;
        border-radius: 3px;
        background: {c["orange"]};
    }}

    QSlider::handle:horizontal {{
        width: 17px;
        height: 17px;
        margin: -7px 0;
        border-radius: 9px;
        background: #f4f4f4;
        border: 1px solid #ffffff;
    }}

    QSlider::handle:horizontal:hover {{
        background: #ffffff;
        border-color: {c["orange"]};
    }}

    QMessageBox {{
        background: {c["surface"]};
    }}

    QMessageBox QLabel {{
        color: {c["text"]};
    }}

    QTabWidget::pane {{
        border: 1px solid {c["border"]};
        background: {c["surface"]};
    }}

    QTabBar::tab {{
        background: {c["surface_alt"]};
        color: {c["muted"]};
        padding: 8px 12px;
        border: 1px solid {c["border"]};
    }}

    QTabBar::tab:selected {{
        background: {c["selection"]};
        color: {c["text"]};
    }}

    QScrollArea {{
        background: {c["surface"]};
        border: 0;
    }}

    QScrollBar:vertical, QScrollBar:horizontal {{
        background: {c["surface"]};
        border: 0;
        width: 12px;
        height: 12px;
    }}

    QScrollBar::handle {{
        background: #454b52;
        border-radius: 5px;
        min-height: 28px;
    }}

    QScrollBar::handle:hover {{
        background: #59616a;
    }}

    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0;
        height: 0;
    }}
    """
