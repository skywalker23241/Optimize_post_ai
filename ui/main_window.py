import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QProgressBar,
    QTabWidget, QGroupBox, QDoubleSpinBox, QSpinBox, QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from core.processor import SEOProcessor, ProcessorConfig
from core.worker import WorkerThread
from ui.console_widget import ConsoleWidget
from ui.styles import MAIN_STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OptimizePostAI")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        self.setStyleSheet(MAIN_STYLESHEET)

        self._worker: WorkerThread | None = None

        self._init_ui()
        self._connect_signals()

    # ------------------------------------------------------------------ UI
    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("OptimizePostAI")
        title.setProperty("class", "section-title")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        subtitle = QLabel("Batch SEO optimization for HTML articles powered by AI")
        subtitle.setProperty("class", "secondary")
        layout.addWidget(subtitle)

        layout.addSpacing(4)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_file_tab(), "  Files  ")
        self.tabs.addTab(self._build_api_tab(), "  API  ")
        self.tabs.addTab(self._build_prompt_tab(), "  Prompts  ")
        layout.addWidget(self.tabs)

        # Start button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.start_btn = QPushButton("  Start Optimization  ")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setProperty("class", "danger")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.stop_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%v%  (%p files)")
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Console
        console_label = QLabel("Console")
        console_label.setProperty("class", "secondary")
        layout.addWidget(console_label)

        self.console = ConsoleWidget()
        layout.addWidget(self.console)

    # ---- Tab 1: Files ----
    def _build_file_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # --- Input / Output ---
        io_group = QGroupBox("Folder Settings")
        io_layout = QGridLayout(io_group)
        io_layout.setSpacing(10)

        io_layout.addWidget(QLabel("Input Folder"), 0, 0)
        self.input_dir_edit = QLineEdit()
        self.input_dir_edit.setPlaceholderText("Select folder containing HTML files...")
        self.input_dir_edit.setReadOnly(True)
        io_layout.addWidget(self.input_dir_edit, 0, 1)

        self.input_browse_btn = QPushButton("Browse")
        self.input_browse_btn.setProperty("class", "browse")
        self.input_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        io_layout.addWidget(self.input_browse_btn, 0, 2)

        io_layout.addWidget(QLabel("Output Folder"), 1, 0)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Leave empty for auto-generated output folder")
        self.output_dir_edit.setReadOnly(True)
        io_layout.addWidget(self.output_dir_edit, 1, 1)

        self.output_browse_btn = QPushButton("Browse")
        self.output_browse_btn.setProperty("class", "browse")
        self.output_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        io_layout.addWidget(self.output_browse_btn, 1, 2)

        layout.addWidget(io_group)

        # --- Parse Rules ---
        rules_group = QGroupBox("Parse Rules")
        rules_layout = QGridLayout(rules_group)
        rules_layout.setSpacing(10)

        rules_layout.addWidget(QLabel("Content CSS Selector"), 0, 0)
        self.selector_edit = QLineEdit("div.product-main")
        self.selector_edit.setToolTip("CSS selector for the main content container")
        rules_layout.addWidget(self.selector_edit, 0, 1, 1, 2)

        rules_layout.addWidget(QLabel("Exclude / Include Rules"), 1, 0, Qt.AlignmentFlag.AlignTop)
        self.exclude_edit = QTextEdit()
        self.exclude_edit.setPlaceholderText(
            "CSS selector rules to exclude/include elements..."
        )
        self.exclude_edit.setMaximumHeight(80)
        self.exclude_edit.setPlainText(
            ":not(div.product-div):not(div.product-div *):"
            ":not(div.product-content):not(div.product-content *),\n"
            "h2, h3, p:not(:has(img))"
        )
        rules_layout.addWidget(self.exclude_edit, 1, 1, 1, 2)

        layout.addWidget(rules_group)
        layout.addStretch()
        return tab

    # ---- Tab 2: API ----
    def _build_api_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        api_group = QGroupBox("API Configuration")
        api_layout = QGridLayout(api_group)
        api_layout.setSpacing(10)

        api_layout.addWidget(QLabel("API Key"), 0, 0)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter your API key...")
        api_layout.addWidget(self.api_key_edit, 0, 1, 1, 2)

        api_layout.addWidget(QLabel("Base URL"), 1, 0)
        self.base_url_edit = QLineEdit("https://api.chatanywhere.tech/v1")
        api_layout.addWidget(self.base_url_edit, 1, 1, 1, 2)

        api_layout.addWidget(QLabel("Model"), 2, 0)
        self.model_edit = QLineEdit("deepseek-r1")
        api_layout.addWidget(self.model_edit, 2, 1, 1, 2)

        api_layout.addWidget(QLabel("Temperature"), 3, 0)
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(1.0)
        api_layout.addWidget(self.temp_spin, 3, 1)

        api_layout.addWidget(QLabel("Max Tokens"), 4, 0)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(256, 128000)
        self.max_tokens_spin.setSingleStep(256)
        self.max_tokens_spin.setValue(4000)
        api_layout.addWidget(self.max_tokens_spin, 4, 1)

        layout.addWidget(api_group)
        layout.addStretch()
        return tab

    # ---- Tab 3: Prompts ----
    def _build_prompt_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        prompt_group = QGroupBox("AI Instructions")
        prompt_layout = QVBoxLayout(prompt_group)
        prompt_layout.setSpacing(10)

        prompt_layout.addWidget(QLabel("System Prompt"))
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setMaximumHeight(80)
        self.system_prompt_edit.setPlainText("You are a helpful assistant that optimizes text.")
        prompt_layout.addWidget(self.system_prompt_edit)

        prompt_layout.addWidget(QLabel("User Prompt  (placeholders: {original_counts}, {cleaned_text})"))
        self.user_prompt_edit = QTextEdit()
        self.user_prompt_edit.setPlainText(
            "Strictly follow the requirements below to optimize the text:\n"
            "1. Keep the original number and order of h2/h3/p tags. "
            "Do not merge tags randomly. Only optimize the tag content.\n"
            "2. Role: SEO Optimization Specialist | Language: English | "
            "Expertise: SEO strategies & best practices | "
            "Skills: Technical SEO (audit, schema, sitemaps, speed), "
            "Content Optimization (keywords, on-page, quality, internal linking) | "
            "Rules: Ethical SEO, transparency, continuous learning, user experience focus | "
            "Workflows: Audit, keyword research, content optimization, performance monitoring | "
            "Goal: Improve website visibility & organic traffic.\n"
            "3. Return in JSON format: {{'h2': [...], 'h3': [...], 'p': [...]}}\n"
            "4. Do not add any explanatory text.\n"
            "5. Ensure that the number of elements in each array is exactly the same as the original data.\n\n"
            "Original content structure statistics:\n{original_counts}\n\n"
            "Content to be optimized:\n{cleaned_text}"
        )
        prompt_layout.addWidget(self.user_prompt_edit)

        layout.addWidget(prompt_group)
        layout.addStretch()
        return tab

    # ----------------------------------------------------------- Signals
    def _connect_signals(self):
        self.input_browse_btn.clicked.connect(self._browse_input)
        self.output_browse_btn.clicked.connect(self._browse_output)
        self.start_btn.clicked.connect(self._start_processing)
        self.stop_btn.clicked.connect(self._stop_processing)

    def _browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_dir_edit.setText(folder)

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_dir_edit.setText(folder)

    # -------------------------------------------------------- Processing
    def _build_config(self) -> ProcessorConfig:
        return ProcessorConfig(
            api_key=self.api_key_edit.text().strip(),
            base_url=self.base_url_edit.text().strip(),
            model=self.model_edit.text().strip(),
            temperature=self.temp_spin.value(),
            max_tokens=self.max_tokens_spin.value(),
            content_selector=self.selector_edit.text().strip(),
            exclude_rules=self.exclude_edit.toPlainText().strip(),
            system_prompt=self.system_prompt_edit.toPlainText().strip(),
            user_prompt=self.user_prompt_edit.toPlainText().strip(),
        )

    def _start_processing(self):
        input_dir = self.input_dir_edit.text().strip()
        if not input_dir or not os.path.isdir(input_dir):
            QMessageBox.warning(self, "Input Error", "Please select a valid input folder.")
            return

        if not self.api_key_edit.text().strip():
            QMessageBox.warning(self, "Input Error", "Please enter an API key.")
            return

        output_dir = self.output_dir_edit.text().strip()
        if not output_dir:
            current_time = datetime.now().strftime("%y%m%d_%H%M")
            output_dir = os.path.join(input_dir, f"optimized_{current_time}")

        config = self._build_config()
        processor = SEOProcessor(config)

        self.console.clear_console()
        self.progress_bar.setValue(0)
        self._set_running(True)

        self._worker = WorkerThread(processor, input_dir, output_dir)
        self._worker.log_message.connect(self.console.append_log)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.start()

    def _stop_processing(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self.console.append_log("[System] Cancelling...")

    def _on_progress(self, current: int, total: int):
        if total > 0:
            pct = int(current / total * 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"{pct}%  ({current}/{total} files)")

    def _on_finished(self, total: int, success: int, failed: int):
        self._set_running(False)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat(f"Done — {success} succeeded, {failed} failed")
        self._worker = None

    def _set_running(self, running: bool):
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        self.tabs.setEnabled(not running)
