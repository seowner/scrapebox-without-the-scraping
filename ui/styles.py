APP_STYLESHEET = """
QMainWindow {
    background-color: #efefef;
}

QGroupBox {
    border: 1px solid #bcbcbc;
    margin-top: 8px;
    padding: 8px;
    background-color: #f5f5f5;
    font-size: 12px;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px 0 4px;
    color: #2c2c2c;
}

QPlainTextEdit {
    background: #ffffff;
    border: 1px solid #b5b5b5;
    selection-background-color: #adc6f7;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12px;
}

QLabel {
    color: #222222;
    font-size: 12px;
}

QToolButton {
    background: #e1e1e1;
    border: 1px solid #9f9f9f;
    border-radius: 2px;
    color: #1f1f1f;
    padding: 6px 10px;
    text-align: left;
    min-height: 30px;
}

QToolButton::menu-indicator {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 8px;
}

QToolButton:hover {
    background: #ececec;
}

QToolButton:pressed {
    background: #d0d0d0;
}

QMenu {
    background-color: #f5f5f5;
    border: 1px solid #9f9f9f;
    padding: 4px 0;
}

QMenu::item {
    padding: 5px 24px 5px 10px;
}

QMenu::item:selected {
    background-color: #c5d8f6;
    color: #000000;
}
"""
