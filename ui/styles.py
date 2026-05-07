MAIN_STYLESHEET = """
/* === Global === */
QWidget {
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #1D1D1F;
    background-color: #FAFAF8;
}

/* === Main Window === */
QMainWindow {
    background-color: #FAFAF8;
}

/* === Tab Widget === */
QTabWidget::pane {
    border: 1px solid #E5E5E7;
    border-radius: 12px;
    background-color: #FFFFFF;
    top: -1px;
}

QTabBar::tab {
    background-color: transparent;
    color: #86868B;
    padding: 10px 24px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #1D1D1F;
    border-bottom: 2px solid #0071E3;
    font-weight: 600;
}

QTabBar::tab:hover:!selected {
    color: #1D1D1F;
    background-color: #F5F5F7;
}

/* === Group Boxes (Section Cards) === */
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E7;
    border-radius: 12px;
    margin-top: 16px;
    padding: 20px 16px 16px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #1D1D1F;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    top: 4px;
    padding: 0 8px;
    background-color: #FFFFFF;
}

/* === Labels === */
QLabel {
    color: #1D1D1F;
    font-size: 13px;
}

QLabel[class="section-title"] {
    font-size: 15px;
    font-weight: 600;
    color: #1D1D1F;
}

QLabel[class="secondary"] {
    color: #86868B;
    font-size: 12px;
}

/* === Line Edits & Text Edits === */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #F5F5F7;
    border: 1px solid #E5E5E7;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: #1D1D1F;
    selection-background-color: #0071E3;
    selection-color: #FFFFFF;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #0071E3;
    background-color: #FFFFFF;
}

QLineEdit:disabled, QTextEdit:disabled {
    background-color: #F0F0F0;
    color: #AEAEB2;
}

/* === Spin Box & Double Spin Box === */
QDoubleSpinBox, QSpinBox {
    background-color: #F5F5F7;
    border: 1px solid #E5E5E7;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    color: #1D1D1F;
}

QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #0071E3;
    background-color: #FFFFFF;
}

/* === Combo Box === */
QComboBox {
    background-color: #F5F5F7;
    border: 1px solid #E5E5E7;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    color: #1D1D1F;
    min-width: 120px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border: none;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E7;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #F0F5FF;
    selection-color: #1D1D1F;
}

QComboBox:focus {
    border: 1px solid #0071E3;
}

/* === Buttons === */
QPushButton {
    background-color: #F5F5F7;
    border: 1px solid #E5E5E7;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
    color: #1D1D1F;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #EBEBED;
}

QPushButton:pressed {
    background-color: #DDDEE0;
}

QPushButton:disabled {
    background-color: #F0F0F0;
    color: #AEAEB2;
    border-color: #E5E5E7;
}

QPushButton[class="primary"] {
    background-color: #0071E3;
    color: #FFFFFF;
    border: none;
    font-weight: 600;
    font-size: 15px;
    padding: 12px 32px;
    border-radius: 10px;
}

QPushButton[class="primary"]:hover {
    background-color: #0077ED;
}

QPushButton[class="primary"]:pressed {
    background-color: #006EDB;
}

QPushButton[class="primary"]:disabled {
    background-color: #AEAEB2;
    color: #FFFFFF;
}

QPushButton[class="danger"] {
    background-color: #FF3B30;
    color: #FFFFFF;
    border: none;
    font-weight: 600;
}

QPushButton[class="danger"]:hover {
    background-color: #FF453A;
}

QPushButton[class="browse"] {
    padding: 8px 16px;
    min-width: 80px;
}

/* === Progress Bar === */
QProgressBar {
    background-color: #F0F0F0;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 11px;
    color: #86868B;
}

QProgressBar::chunk {
    background-color: #0071E3;
    border-radius: 6px;
}

/* === Scroll Bars === */
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #C7C7CC;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #AEAEB2;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #C7C7CC;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* === Tool Tips === */
QToolTip {
    background-color: #1D1D1F;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* === Splitter === */
QSplitter::handle {
    background-color: #E5E5E7;
    height: 1px;
}

/* === Console (Log area) === */
QTextEdit[class="console"] {
    background-color: #1E1E1E;
    color: #D4D4D4;
    border: none;
    border-radius: 12px;
    padding: 12px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", "SF Mono", monospace;
    font-size: 12px;
    selection-background-color: #264F78;
}
"""
