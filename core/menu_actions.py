from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMenu, QMessageBox, QWidget

from core import io_ops, url_ops


class MenuActionRouter:
    def __init__(
        self,
        parent: QWidget,
        read_urls: Callable[[], list[str]],
        write_urls: Callable[[list[str]], None],
        set_status: Callable[[str], None],
    ) -> None:
        self.parent = parent
        self.read_urls = read_urls
        self.write_urls = write_urls
        self.set_status = set_status

    def build_remove_filter_menu(self) -> QMenu:
        menu = QMenu(self.parent)
        menu.addAction("Remove Duplicate URLs", self.remove_duplicate_urls)
        menu.addAction("Remove Duplicate Domains", self.remove_duplicate_domains)
        menu.addSeparator()
        menu.addAction("Remove URL's containing...", self.remove_urls_containing_inline)
        menu.addAction("Remove URL's not containing...", self.keep_urls_containing_inline)
        menu.addAction("Remove URL's containing entries from...", self.remove_urls_containing_file)
        menu.addAction("Remove URL's not containing entries from...", self.keep_urls_containing_file)
        menu.addSeparator()
        menu.addAction("Remove URL's with less than xxx character", self.remove_under_length)
        menu.addAction("Remove URL's with more than xxx character", self.remove_over_length)
        menu.addSeparator()
        menu.addAction("Show Duplicates", self.show_duplicates)
        return menu

    def build_trim_menu(self) -> QMenu:
        menu = QMenu(self.parent)
        menu.addAction("Trim to Root", self.trim_domain_root)
        menu.addAction("Trim to First Folder", self.trim_domain_first_folder)
        menu.addAction("Trim to Last Folder", self.trim_domain_last_folder)
        menu.addAction("Trim URLs to Domain Level", self.trim_domain_level)
        menu.addAction("Trim URLs to Subdomain Level", self.trim_subdomain_level)
        return menu

    def build_import_menu(self) -> QMenu:
        menu = QMenu(self.parent)
        menu.addAction("Import From File (Replace Current List)...", self.import_from_file_replace)
        menu.addAction("Import From File (Add To Current List)...", self.import_from_file_add)
        menu.addSeparator()
        menu.addAction("Import From Clipboard (Replace Current List)", self.import_from_clipboard_replace)
        menu.addAction("Import From Clipboard (Add To Current List)", self.import_from_clipboard_add)
        return menu

    def build_export_menu(self) -> QMenu:
        menu = QMenu(self.parent)
        menu.addAction("Copy URLs To Clipboard", self.copy_urls_to_clipboard)
        menu.addAction("Save URLs To File...", self.save_urls_to_file)
        return menu

    def build_more_tools_menu(self) -> QMenu:
        menu = QMenu(self.parent)
        menu.addAction("Randomize URLs in List", self.shuffle_urls)
        menu.addAction("Spin URLs", self.spin_urls)
        return menu

    def remove_duplicate_urls(self) -> None:
        urls = self.read_urls()
        filtered, removed = url_ops.dedupe_urls(urls)
        self.write_urls(filtered)
        self.set_status(f"Removed {removed} duplicate URLs.")

    def remove_duplicate_domains(self) -> None:
        urls = self.read_urls()
        filtered, removed = url_ops.dedupe_domains(urls)
        self.write_urls(filtered)
        self.set_status(f"Removed {removed} duplicate domains.")

    def show_duplicates(self) -> None:
        urls = self.read_urls()
        filtered, removed = url_ops.keep_only_duplicate_urls(urls)
        self.write_urls(filtered)
        self.set_status(f"Removed {removed} non-duplicate URLs; showing duplicates only.")

    def remove_urls_containing_inline(self) -> None:
        phrases = self._prompt_inline_phrases()
        if phrases is None:
            return
        self._apply_phrase_filter(phrases, keep_matches=False)

    def keep_urls_containing_inline(self) -> None:
        phrases = self._prompt_inline_phrases()
        if phrases is None:
            return
        self._apply_phrase_filter(phrases, keep_matches=True)

    def remove_urls_containing_file(self) -> None:
        phrases = self._load_phrases_from_file()
        if phrases is None:
            return
        self._apply_phrase_filter(phrases, keep_matches=False)

    def keep_urls_containing_file(self) -> None:
        phrases = self._load_phrases_from_file()
        if phrases is None:
            return
        self._apply_phrase_filter(phrases, keep_matches=True)

    def remove_under_length(self) -> None:
        minimum, accepted = QInputDialog.getInt(
            self.parent,
            "Remove URLs Under Length",
            "Minimum characters:",
            value=10,
            minValue=1,
            maxValue=5000,
        )
        if not accepted:
            return
        urls = self.read_urls()
        filtered, removed = url_ops.remove_under_length(urls, minimum)
        if not self._confirm_large_removal(removed, "remove short URLs"):
            return
        self.write_urls(filtered)
        self.set_status(f"Removed {removed} URLs under {minimum} characters.")

    def remove_over_length(self) -> None:
        maximum, accepted = QInputDialog.getInt(
            self.parent,
            "Remove URLs Over Length",
            "Maximum characters:",
            value=200,
            minValue=1,
            maxValue=10000,
        )
        if not accepted:
            return
        urls = self.read_urls()
        filtered, removed = url_ops.remove_over_length(urls, maximum)
        if not self._confirm_large_removal(removed, "remove long URLs"):
            return
        self.write_urls(filtered)
        self.set_status(f"Removed {removed} URLs over {maximum} characters.")

    def trim_domain_root(self) -> None:
        urls = self.read_urls()
        self.write_urls(url_ops.trim_to_root(urls))
        self.set_status("Trimmed all URLs to domain root.")

    def trim_domain_first_folder(self) -> None:
        urls = self.read_urls()
        self.write_urls(url_ops.trim_to_first_folder(urls))
        self.set_status("Trimmed all URLs to first folder.")

    def trim_domain_last_folder(self) -> None:
        urls = self.read_urls()
        self.write_urls(url_ops.trim_to_last_folder(urls))
        self.set_status("Trimmed all URLs to last folder.")

    def trim_domain_level(self) -> None:
        urls = self.read_urls()
        self.write_urls(url_ops.trim_to_domain_level(urls))
        self.set_status("Trimmed all entries to domain level.")

    def trim_subdomain_level(self) -> None:
        urls = self.read_urls()
        self.write_urls(url_ops.trim_to_subdomain_level(urls))
        self.set_status("Trimmed all entries to subdomain level.")

    def import_urls_from_file(self) -> None:
        # Backward-compatible alias (used by existing shortcut wiring).
        self.import_from_file_replace()

    def import_from_file_replace(self) -> None:
        loaded_lines = self._pick_import_file_lines()
        if loaded_lines is None:
            return
        self._replace_imported_entries(loaded_lines, source_label="file")

    def import_from_file_add(self) -> None:
        loaded_lines = self._pick_import_file_lines()
        if loaded_lines is None:
            return
        self._append_imported_entries(loaded_lines, source_label="file")

    def import_urls_from_clipboard(self) -> None:
        # Backward-compatible alias.
        self.import_from_clipboard_replace()

    def import_from_clipboard_replace(self) -> None:
        imported_entries = self._read_clipboard_lines()
        if imported_entries is None:
            return
        self._replace_imported_entries(imported_entries, source_label="clipboard")

    def import_from_clipboard_add(self) -> None:
        imported_entries = self._read_clipboard_lines()
        if imported_entries is None:
            return
        self._append_imported_entries(imported_entries, source_label="clipboard")

    def _pick_import_file_lines(self) -> list[str] | None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Import URL List",
            "",
            "Text files (*.txt *.csv *.log);;All files (*.*)",
        )
        if not file_path:
            return None

        loaded_lines = io_ops.load_url_file(file_path)
        if not loaded_lines:
            self.set_status("No entries found in selected file.")
            return None
        return loaded_lines

    def _read_clipboard_lines(self) -> list[str] | None:
        clipboard_text = QApplication.clipboard().text()
        imported_entries = [line for line in clipboard_text.splitlines() if line != ""]
        if not imported_entries:
            self.set_status("Clipboard has no non-empty lines to import.")
            return
        return imported_entries

    def copy_urls_to_clipboard(self) -> None:
        urls = self.read_urls()
        QApplication.clipboard().setText(url_ops.urls_to_text(urls))
        self.set_status(f"Copied {len(urls)} URLs to clipboard.")

    def save_urls_to_file(self) -> None:
        urls = self.read_urls()
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Save URL List",
            "urls.txt",
            "Text files (*.txt);;All files (*.*)",
        )
        if not file_path:
            return
        saved_count = io_ops.save_url_file(file_path, urls)
        self.set_status(f"Saved {saved_count} URLs to file.")

    def shuffle_urls(self) -> None:
        urls = self.read_urls()
        shuffled = url_ops.shuffle_urls(urls)
        self.write_urls(shuffled)
        self.set_status(f"Shuffled {len(shuffled)} URLs.")

    def spin_urls(self) -> None:
        urls = self.read_urls()
        spun = url_ops.spin_urls(urls)
        if not spun:
            self.set_status("No lines available to spin.")
            return
        self.write_urls([spun])
        self.set_status(f"Spun {len(urls)} lines into spintax.")

    def _apply_phrase_filter(self, phrases: list[str], keep_matches: bool) -> None:
        urls = self.read_urls()
        filtered, removed = url_ops.filter_by_phrases(urls, phrases, keep_matches=keep_matches)
        if removed > 0 and not self._confirm_large_removal(removed, "apply phrase filter"):
            return
        self.write_urls(filtered)
        if keep_matches:
            self.set_status(f"Kept {len(filtered)} URLs matching {len(phrases)} phrase(s).")
        else:
            self.set_status(f"Removed {removed} URLs matching {len(phrases)} phrase(s).")

    def _prompt_inline_phrases(self) -> list[str] | None:
        raw_text, accepted = QInputDialog.getMultiLineText(
            self.parent,
            "Phrase Filter",
            "Enter phrase(s), one per line:",
        )
        if not accepted:
            return None
        phrases = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not phrases:
            self.set_status("No phrases provided.")
            return None
        return phrases

    def _load_phrases_from_file(self) -> list[str] | None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Load Phrase List",
            "",
            "Text files (*.txt *.csv *.log);;All files (*.*)",
        )
        if not file_path:
            return None
        phrases = io_ops.load_phrase_file(file_path)
        if not phrases:
            self.set_status("Selected phrase file is empty.")
            return None
        return phrases

    def _confirm_large_removal(self, removed_count: int, action_label: str) -> bool:
        if removed_count < 100:
            return True
        result = QMessageBox.question(
            self.parent,
            "Confirm Large Change",
            f"This action will remove {removed_count} URLs.\nContinue to {action_label}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return result == QMessageBox.Yes

    def _append_imported_entries(self, imported_entries: list[str], source_label: str) -> None:
        current_urls = self.read_urls()
        merged = current_urls + imported_entries
        self.write_urls(merged)
        self.set_status(f"Imported {len(imported_entries)} lines from {source_label} (added to current list).")

    def _replace_imported_entries(self, imported_entries: list[str], source_label: str) -> None:
        self.write_urls(imported_entries)
        self.set_status(f"Imported {len(imported_entries)} lines from {source_label} (replaced current list).")
