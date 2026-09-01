from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication, QPushButton


COLORS = {
    "window": "#111315",
    "surface": "#171A1D",
    "surface_alt": "#1D2125",
    "field": "#20252A",
    "field_hover": "#262C31",
    "border": "#2B3137",
    "border_focus": "#D98B2B",
    "text": "#F2F4F5",
    "muted": "#9CA3AA",
    "disabled": "#676E75",
    "red": "#D64B43",
    "red_hover": "#E15B53",
    "orange": "#D98B2B",
    "orange_hover": "#E7A24D",
    "yellow": "#E1B85B",
    "green": "#7FA63A",
    "green_hover": "#91B64C",
    "selection": "#272D32",
}


def apply_theme(app: QApplication) -> None:
    available = set(QFontDatabase.families())
    family = next(
        (name for name in [".AppleSystemUIFont", "SF Pro Text", "Segoe UI", "Inter", "Arial", "Helvetica"] if name in available),
        QFontDatabase.systemFont(QFontDatabase.GeneralFont).family(),
    )
    font = QFont(family)
    font.setPointSize(10)
    app.setFont(font)

    c = COLORS
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(c["window"]))
    palette.setColor(QPalette.WindowText, QColor(c["text"]))
    palette.setColor(QPalette.Base, QColor(c["field"]))
    palette.setColor(QPalette.AlternateBase, QColor(c["surface_alt"]))
    palette.setColor(QPalette.Text, QColor(c["text"]))
    palette.setColor(QPalette.Button, QColor(c["surface_alt"]))
    palette.setColor(QPalette.ButtonText, QColor(c["text"]))
    palette.setColor(QPalette.Highlight, QColor(c["selection"]))
    palette.setColor(QPalette.HighlightedText, QColor(c["text"]))
    palette.setColor(QPalette.ToolTipBase, QColor(c["surface_alt"]))
    palette.setColor(QPalette.ToolTipText, QColor(c["text"]))
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
        color: {c['text']};
        selection-background-color: {c['selection']};
        selection-color: {c['text']};
    }}

    QMainWindow, QDialog, QWidget {{
        background-color: {c['window']};
        color: {c['text']};
    }}

    QToolTip {{
        background-color: #252A2F;
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 6px 8px;
        border-radius: 6px;
    }}

    QStatusBar {{
        background: {c['window']};
        border-top: 1px solid #22272C;
        color: {c['muted']};
        min-height: 24px;
    }}

    QMenu {{
        background-color: #1B1F23;
        color: {c['text']};
        border: 1px solid #30363C;
        border-radius: 8px;
        padding: 6px;
    }}
    QMenu::separator {{
        height: 1px;
        background: #30363C;
        margin: 6px 8px;
    }}
    QMenu::item {{
        padding: 8px 30px 8px 12px;
        border-radius: 5px;
        background: transparent;
    }}
    QMenu::item:selected {{
        background: #2A3035;
    }}
    QMenu::item:disabled {{ color: {c['disabled']}; }}

    QToolBar {{
        background: {c['window']};
        border: 0;
        border-bottom: 1px solid #22272C;
        spacing: 6px;
        padding: 8px 14px;
        min-height: 48px;
    }}
    QToolBar::separator {{ background: #2B3035; width: 1px; margin: 8px; }}

    QLabel {{ color: {c['text']}; background: transparent; }}
    QLabel[class="panelTitle"] {{
        color: #CDD1D5;
        font-size: 12px;
        font-weight: 650;
        padding: 0;
    }}
    QLabel[class="appTitle"] {{
        color: {c['text']};
        font-size: 15px;
        font-weight: 650;
        padding: 0 10px 0 0;
    }}
    QLabel[class="required"] {{ color: {c['muted']}; font-weight: 600; }}
    QLabel[class="fieldLabel"] {{ color: {c['muted']}; font-size: 11px; font-weight: 600; padding-bottom: 2px; }}
    QLabel[class="sectionLabel"] {{ color: #C7CCD1; font-size: 11px; font-weight: 650; }}
    QLabel[class="hint"] {{ color: #747C84; font-size: 10px; }}
    QLabel[class="dialogTitle"] {{ color: #F2F3F4; font-size: 19px; font-weight: 650; }}
    QLabel[class="eyebrow"] {{ color: #7F878F; font-size: 10px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; }}
    QLabel[class="statusMeta"] {{ color: #858D95; font-size: 11px; font-weight: 600; }}

    QFrame[class="panel"] {{
        background: {c['surface']};
        border: 0;
        border-radius: 10px;
    }}
    QFrame[class="softGroup"] {{
        background: #1A1E22;
        border: 1px solid #262C31;
        border-radius: 8px;
    }}
    QFrame[class="statusGroup"] {{
        background: #181C1F;
        border: 1px solid #272D32;
        border-radius: 9px;
    }}

    QSplitter {{ background: {c['window']}; }}
    QSplitter::handle {{ background: {c['window']}; width: 7px; }}
    QSplitter::handle:hover {{ background: #24292E; }}

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {c['field']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 7px;
        padding: 7px 10px;
        min-height: 30px;
    }}
    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
        background-color: {c['field_hover']};
        border-color: #394149;
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border-color: {c['border_focus']};
    }}
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
        background-color: #1A1D20;
        color: {c['disabled']};
        border-color: #262B30;
    }}

    QLineEdit[class="settingsUrlField"] {{
        min-height: 40px; max-height: 40px;
        padding: 0 12px;
        font-size: 12px;
        background: #20252A;
        border: 1px solid #31383E;
        border-radius: 8px;
    }}
    QLineEdit[class="settingsUrlField"]:focus {{
        border-color: {c['orange']};
        background: #23292E;
    }}

    QLineEdit[class="searchField"] {{
        min-height: 28px;
        padding: 5px 10px;
        border-radius: 7px;
        background-color: #1E2327;
        border: 1px solid #2D343A;
    }}
    QLineEdit[class="searchField"]:focus {{ border-color: {c['border_focus']}; background: #22282D; }}

    QComboBox {{ padding-right: 28px; }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 26px;
        border: 0;
        background: transparent;
    }}
    QComboBox::down-arrow {{
        image: none;
        width: 7px;
        height: 7px;
        border-right: 1.5px solid {c['muted']};
        border-bottom: 1.5px solid {c['muted']};
        transform: rotate(45deg);
        margin: 0 10px 5px 0;
    }}
    QComboBox QAbstractItemView {{
        background: #20252A;
        color: {c['text']};
        border: 1px solid #353C43;
        border-radius: 6px;
        padding: 4px;
        selection-background-color: #30373D;
        selection-color: {c['text']};
        outline: 0;
    }}

    QSpinBox, QDoubleSpinBox {{ padding-right: 10px; }}
    QSpinBox[class="compactSpin"] {{
        min-width: 52px; max-width: 52px;
        min-height: 34px; max-height: 34px;
        padding: 0;
        background: #20252A;
        border: 1px solid #30373D;
        border-radius: 7px;
        font-size: 12px;
        font-weight: 650;
    }}
    QSpinBox[class="compactSpin"]:focus {{ border-color: {c['orange']}; }}
    QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        width: 0px; height: 0px; border: 0; background: transparent;
    }}

    QTableWidget, QTableView {{
        background: {c['surface_alt']};
        alternate-background-color: #1C2024;
        color: {c['text']};
        border: 0;
        border-radius: 8px;
        gridline-color: transparent;
        outline: 0;
    }}
    QHeaderView::section {{
        background: #181C1F;
        color: #AAB0B6;
        border: 0;
        border-bottom: 1px solid #2B3137;
        padding: 9px 10px;
        font-weight: 600;
    }}
    QTableWidget::item {{
        padding: 8px 10px;
        border: 0;
        border-bottom: 1px solid #282E33;
    }}
    QTableWidget::item:hover {{ background: #242A2F; }}
    QTableWidget::item:selected {{ background: {c['selection']}; color: {c['text']}; }}
    QTableWidget::item:disabled {{ color: {c['disabled']}; }}

    QCheckBox {{ color: #D9DDE0; spacing: 7px; background: transparent; min-height: 26px; }}
    QCheckBox[class="statusChip"] {{
        color: #B7BDC3;
        background: #1D2226;
        border: 1px solid #2D343A;
        border-radius: 7px;
        padding: 5px 10px 5px 8px;
        spacing: 7px;
        min-height: 22px;
        font-size: 11px;
        font-weight: 550;
    }}
    QCheckBox[class="statusChip"]:hover {{
        background: #242A2F;
        border-color: #3A4249;
        color: #E6E8EA;
    }}
    QCheckBox[class="statusChip"]:checked {{
        background: #20271E;
        border-color: #465B2B;
        color: #E2EAD8;
    }}
    QCheckBox[class="statusChip"]::indicator {{
        width: 11px; height: 11px;
        border-radius: 6px;
        border: 1px solid #4A5259;
        background: #252B30;
    }}
    QCheckBox[class="statusChip"]::indicator:hover {{ border-color: #737C84; }}
    QCheckBox[class="statusChip"]::indicator:checked {{
        background: {c['green']};
        border-color: {c['green']};
    }}
    QCheckBox::indicator {{
        width: 16px; height: 16px; border-radius: 4px;
        border: 1px solid #3B4249; background: #22272C;
    }}
    QCheckBox::indicator:hover {{ border-color: #69717A; background: #292F34; }}
    QCheckBox::indicator:checked {{ background: {c['green']}; border-color: {c['green']}; }}

    QPushButton, QToolButton {{
        background: #20252A;
        color: {c['text']};
        border: 1px solid #30373D;
        border-radius: 7px;
        padding: 7px 11px;
        min-height: 28px;
    }}
    QPushButton:hover, QToolButton:hover {{ background: #292F34; border-color: #404850; }}
    QPushButton:disabled, QToolButton:disabled {{ background: #191D20; color: {c['disabled']}; border-color: #242A2F; }}
    QPushButton[role="primary"] {{ background: {c['green']}; border-color: {c['green']}; color: #11150D; font-weight: 650; }}
    QPushButton[role="primary"]:hover {{ background: {c['green_hover']}; }}
    QPushButton[role="accent"] {{ background: {c['orange']}; border-color: {c['orange']}; color: #16110B; font-weight: 650; }}
    QPushButton[role="accent"]:hover {{ background: {c['orange_hover']}; }}
    QPushButton[role="danger"] {{ background: #362120; border-color: #59302D; color: #F3C8C5; }}
    QPushButton[role="danger"]:hover {{ background: {c['red']}; border-color: {c['red']}; color: white; }}

    QToolButton[class="addButton"] {{
        min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px;
        padding: 0; border-radius: 6px; font-size: 18px; font-weight: 500;
        color: {c['orange']}; background: transparent; border: 0;
    }}
    QToolButton[class="addButton"]:hover {{ background: #292F34; color: {c['orange_hover']}; }}
    QToolButton[class="iconButton"] {{
        min-width: 26px; max-width: 26px; min-height: 26px; max-height: 26px;
        padding: 0; border-radius: 6px; font-size: 15px;
        color: #929AA2; background: transparent; border: 0;
    }}
    QToolButton[class="iconButton"]:hover {{ color: #F0B0AA; background: #352321; }}
    QToolButton[class="menuButton"] {{ background: transparent; border: 0; padding: 6px 9px; }}
    QToolButton[class="menuButton"]:hover {{ background: #252B30; }}
    QToolButton[class="menuButton"]::menu-indicator {{ image: none; width: 0px; }}

    QLabel[class="imagePreview"] {{
        border: 1px dashed #3A4249;
        border-radius: 8px;
        color: {c['muted']};
        background: #1D2226;
    }}
    QLabel[class="imagePreview"]:hover {{ border-color: {c['orange']}; background: #22282D; }}

    QScrollArea {{ background: transparent; border: 0; }}
    QScrollBar:vertical {{ background: transparent; border: 0; width: 7px; margin: 0; }}
    QScrollBar:horizontal {{ background: transparent; border: 0; height: 7px; margin: 0; }}
    QScrollBar::handle {{ background: #3A4249; border-radius: 3px; min-height: 28px; min-width: 28px; }}
    QScrollBar::handle:hover {{ background: #505A63; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

    QMessageBox {{ background: {c['surface']}; }}
    QMessageBox QLabel {{ color: {c['text']}; }}
    """
