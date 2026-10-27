"""Dark NOC Stylesheet and Colors for HarnessISP."""

NOC_STYLESHEET = """
QWidget {
    background-color: #12161f;
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Ubuntu', 'Roboto', sans-serif;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QTextEdit, QPlainTextEdit {
    background-color: #0b0e14;
    color: #38bdf8;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 8px;
    font-family: 'Fira Code', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
}

QLineEdit {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 12px;
}

QLineEdit:focus {
    border: 1px solid #06b6d4;
}

QPushButton {
    background-color: #1e293b;
    color: #f1f5f9;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #06b6d4;
}

QPushButton:pressed {
    background-color: #0f172a;
}

/* NOC Action Buttons */
QPushButton#action_btn {
    background-color: #0f2338;
    color: #38bdf8;
    border: 1px solid #0284c7;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}

QPushButton#action_btn:hover {
    background-color: #0284c7;
    color: #ffffff;
}

/* Risk Badges */
QLabel#risk_critical {
    background-color: #7f1d1d;
    color: #fca5a5;
    border: 1px solid #ef4444;
    border-radius: 4px;
    padding: 2px 6px;
    font-weight: bold;
}

QLabel#risk_medium {
    background-color: #78350f;
    color: #fde68a;
    border: 1px solid #f59e0b;
    border-radius: 4px;
    padding: 2px 6px;
    font-weight: bold;
}

QLabel#risk_low {
    background-color: #064e3b;
    color: #a7f3d0;
    border: 1px solid #10b981;
    border-radius: 4px;
    padding: 2px 6px;
    font-weight: bold;
}
"""
