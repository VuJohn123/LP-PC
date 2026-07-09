# ui/styles.py

MATERIAL_DARK_STYLE = """
/* ==================== TOÀN CỤC ==================== */
QMainWindow {
    background-color: #0b0f19;
    color: #e1e4e8;
}
QWidget {
    font-family: "Segoe UI", "Roboto", "Helvetica Neue", sans-serif;
    font-size: 13px;
    color: #e1e4e8;
}

/* ==================== SIDEBAR ==================== */
QFrame#sidebar {
    background-color: #0d1117;
    border-right: 1px solid #21262d;
    min-width: 240px;
    max-width: 240px;
}
QFrame#sidebar QPushButton {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    color: #8b949e;
    font-weight: 600;
    font-size: 14px;
    margin: 2px 8px;
}
QFrame#sidebar QPushButton:hover {
    background-color: #161b22;
    color: #f0f6fc;
}
QFrame#sidebar QPushButton:checked {
    background-color: #238636;
    color: #ffffff;
}

/* ==================== TOOLBAR ==================== */
QToolBar {
    background-color: #0d1117;
    border-bottom: 1px solid #21262d;
    padding: 6px 12px;
    spacing: 10px;
}
QToolBar QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QToolBar QPushButton:hover {
    background-color: #30363d;
    border-color: #58a6ff;
}

/* ==================== SEARCH & COMBOBOX ==================== */
QLineEdit, QComboBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 14px;
    color: #c9d1d9;
    selection-background-color: #1f6feb;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #58a6ff;
}
QComboBox QAbstractItemView {
    background-color: #161b22;
    color: #c9d1d9;
    selection-background-color: #1f6feb;
    border-radius: 6px;
}

/* ==================== BUTTONS ==================== */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #58a6ff;
}
QPushButton:pressed {
    background-color: #0d1117;
}
QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
}

/* Action buttons màu sắc */
QPushButton[cssClass="green"] {
    background-color: #238636;
    border: 1px solid #2ea043;
    color: #ffffff;
}
QPushButton[cssClass="green"]:hover {
    background-color: #2ea043;
}
QPushButton[cssClass="blue"] {
    background-color: #1f6feb;
    border: 1px solid #388bfd;
    color: #ffffff;
}
QPushButton[cssClass="blue"]:hover {
    background-color: #388bfd;
}
QPushButton[cssClass="orange"] {
    background-color: #d29922;
    border: 1px solid #e3b341;
    color: #000000;
}
QPushButton[cssClass="orange"]:hover {
    background-color: #e3b341;
}
QPushButton[cssClass="yellow"] {
    background-color: #d29922;
    border: 1px solid #e3b341;
    color: #000000;
}
QPushButton[cssClass="yellow"]:hover {
    background-color: #e3b341;
}
QPushButton[cssClass="purple"] {
    background-color: #8957e5;
    border: 1px solid #a371f7;
    color: #ffffff;
}
QPushButton[cssClass="purple"]:hover {
    background-color: #a371f7;
}

/* ==================== LIST WIDGET ==================== */
QListWidget {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 12px 16px;
    border-bottom: 1px solid #161b22;
    color: #c9d1d9;
}
QListWidget::item:selected {
    background-color: #1f6feb;
    color: #ffffff;
    border-left: 3px solid #58a6ff;
}
QListWidget::item:hover {
    background-color: #161b22;
}

/* ==================== SCROLLBAR ==================== */
QScrollBar:vertical {
    background: #0d1117;
    width: 12px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 6px;
    min-height: 25px;
}
QScrollBar::handle:vertical:hover {
    background: #484f58;
}

/* ==================== PROGRESS BAR ==================== */
QProgressBar {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
}
QProgressBar::chunk {
    background-color: #238636;
    border-radius: 8px;
}

/* ==================== GROUP BOX ==================== */
QGroupBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 12px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: bold;
    color: #58a6ff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* ==================== TEXT EDIT (LOG) ==================== */
QTextEdit {
    background-color: #06080c;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 12px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    color: #b0b0b0;
}

/* ==================== STATUS BAR ==================== */
QStatusBar {
    background-color: #0d1117;
    color: #8b949e;
    border-top: 1px solid #21262d;
    padding: 4px 12px;
}

/* ==================== SPLITTER ==================== */
QSplitter::handle {
    background-color: #21262d;
    width: 3px;
}

/* ==================== TOOLTIP ==================== */
QToolTip {
    background-color: #161b22;
    color: #f0f6fc;
    border: 1px solid #58a6ff;
    border-radius: 6px;
    padding: 6px;
}

/* ==================== DIALOGS ==================== */
QDialog {
    background-color: #0d1117;
}

"""