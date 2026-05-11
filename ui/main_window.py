from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QDragEnterEvent, QDropEvent, QGuiApplication, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core import io_ops
from core.menu_actions import MenuActionRouter
from core.url_ops import clean_url_list, urls_to_text
from ui.styles import APP_STYLESHEET


class FileDropPlainTextEdit(QPlainTextEdit):
    def __init__(self, on_files_dropped, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._on_files_dropped = on_files_dropped
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._extract_local_paths(event):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        local_paths = self._extract_local_paths(event)
        if local_paths:
            self._on_files_dropped(local_paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def _extract_local_paths(self, event) -> list[str]:
        mime = event.mimeData()
        if not mime.hasUrls():
            return []
        paths: list[str] = []
        for url in mime.urls():
            if url.isLocalFile():
                paths.append(url.toLocalFile())
        return paths


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._urls: list[str] = []
        self.setWindowTitle("ScrapeBox URL Utility")
        self.resize(1050, 700)
        self.setStyleSheet(APP_STYLESHEET)

        self._build_layout()
        self._wire_router()
        self._wire_shortcuts()
        self._update_status_count()
        self._position_on_left_monitor()
        self.set_status("Ready.")

    def _build_layout(self) -> None:
        container = QWidget(self)
        self.setCentralWidget(container)

        root_layout = QHBoxLayout(container)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(12)

        left_group = QGroupBox("Urls Harvested", container)
        left_layout = QVBoxLayout(left_group)
        left_layout.setSpacing(8)

        self.urls_edit = FileDropPlainTextEdit(self._handle_dropped_files, left_group)
        self.urls_edit.setPlaceholderText("Paste or import URLs, one per line...")
        self.urls_edit.textChanged.connect(self._sync_urls_from_editor)
        left_layout.addWidget(self.urls_edit, stretch=1)

        self.count_label = QLabel("Urls in List: 0", left_group)
        left_layout.addWidget(self.count_label)

        self.status_label = QLabel("", left_group)
        self.status_label.setWordWrap(True)
        left_layout.addWidget(self.status_label)

        sidebar_group = QGroupBox("Manage Lists", container)
        sidebar_layout = QVBoxLayout(sidebar_group)
        sidebar_layout.setSpacing(8)
        sidebar_layout.setAlignment(Qt.AlignTop)

        self.remove_filter_button = self._build_menu_button("Remove / Filter")
        self.trim_button = self._build_menu_button("Trim")
        self.import_button = self._build_menu_button("Import URL List")
        self.export_button = self._build_menu_button("Export URL List")
        self.more_tools_button = self._build_menu_button("More List Tools")

        sidebar_layout.addWidget(self.remove_filter_button)
        sidebar_layout.addWidget(self.trim_button)
        sidebar_layout.addWidget(self.import_button)
        sidebar_layout.addWidget(self.export_button)
        sidebar_layout.addWidget(self.more_tools_button)
        sidebar_layout.addStretch()

        left_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sidebar_group.setFixedWidth(260)

        root_layout.addWidget(left_group, stretch=1)
        root_layout.addWidget(sidebar_group)

    def _build_menu_button(self, title: str) -> QToolButton:
        button = QToolButton(self)
        button.setText(title)
        button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        button.setPopupMode(QToolButton.InstantPopup)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        return button

    def _wire_router(self) -> None:
        router = MenuActionRouter(
            parent=self,
            read_urls=self.read_urls,
            write_urls=self.write_urls,
            set_status=self.set_status,
        )
        self.router = router
        self.remove_filter_button.setMenu(router.build_remove_filter_menu())
        self.trim_button.setMenu(router.build_trim_menu())
        self.import_button.setMenu(router.build_import_menu())
        self.export_button.setMenu(router.build_export_menu())
        self.more_tools_button.setMenu(router.build_more_tools_menu())

    def _wire_shortcuts(self) -> None:
        import_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        import_shortcut.activated.connect(self.router.import_urls_from_file)

        export_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        export_shortcut.activated.connect(self.router.save_urls_to_file)

        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self.router.copy_urls_to_clipboard)

        # Keep references alive.
        self._shortcuts = [import_shortcut, export_shortcut, copy_shortcut]

        # Disable default QTextEdit copy action from stealing global behavior.
        no_op = QAction(self)
        self.urls_edit.addAction(no_op)

    def _sync_urls_from_editor(self) -> None:
        raw_lines = self.urls_edit.toPlainText().splitlines()
        self._urls = clean_url_list(raw_lines)
        self._update_status_count()

    def _update_status_count(self) -> None:
        self.count_label.setText(f"Urls in List: {len(self._urls)}")

    def read_urls(self) -> list[str]:
        raw_lines = self.urls_edit.toPlainText().splitlines()
        self._urls = clean_url_list(raw_lines)
        return self._urls[:]

    def write_urls(self, urls: list[str]) -> None:
        self._urls = clean_url_list(urls)
        self.urls_edit.blockSignals(True)
        self.urls_edit.setPlainText(urls_to_text(self._urls))
        self.urls_edit.blockSignals(False)
        self._update_status_count()

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _position_on_left_monitor(self) -> None:
        screens = QGuiApplication.screens()
        if not screens:
            return

        left_screen = min(screens, key=lambda screen: screen.availableGeometry().x())
        bounds = left_screen.availableGeometry()

        target_width = min(self.width(), bounds.width())
        target_height = min(self.height(), bounds.height())
        offset_x = max(0, (bounds.width() - target_width) // 2)
        offset_y = max(0, (bounds.height() - target_height) // 2)
        self.setGeometry(bounds.x() + offset_x, bounds.y() + offset_y, target_width, target_height)

    def _handle_dropped_files(self, file_paths: list[str]) -> None:
        imported_lines, loaded_file_count = io_ops.load_multiple_url_files(file_paths)
        if loaded_file_count == 0:
            self.set_status("No readable files were dropped.")
            return

        if not imported_lines:
            self.set_status(f"Dropped {loaded_file_count} file(s), but found no non-empty lines.")
            return

        current_lines = self.read_urls()
        self.write_urls(current_lines + imported_lines)
        self.set_status(f"Imported {len(imported_lines)} lines from {loaded_file_count} dropped file(s).")
