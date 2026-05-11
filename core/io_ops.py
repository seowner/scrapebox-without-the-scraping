from __future__ import annotations

from pathlib import Path


def load_url_file(file_path: str) -> list[str]:
    path = Path(file_path)
    content = path.read_text(encoding="utf-8", errors="ignore")
    return [line for line in content.splitlines() if line != ""]


def load_phrase_file(file_path: str) -> list[str]:
    return load_url_file(file_path)


def load_multiple_url_files(file_paths: list[str]) -> tuple[list[str], int]:
    merged_lines: list[str] = []
    loaded_file_count = 0

    for file_path in file_paths:
        try:
            lines = load_url_file(file_path)
        except OSError:
            continue
        loaded_file_count += 1
        merged_lines.extend(lines)

    return merged_lines, loaded_file_count


def save_url_file(file_path: str, urls: list[str]) -> int:
    path = Path(file_path)
    payload = "\n".join(urls)
    if payload:
        payload += "\n"
    path.write_text(payload, encoding="utf-8")
    return len(urls)
