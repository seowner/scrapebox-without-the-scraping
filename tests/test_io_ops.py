from core import io_ops


def test_load_multiple_url_files_merges_in_order(tmp_path) -> None:
    file_one = tmp_path / "one.txt"
    file_two = tmp_path / "two.txt"
    file_one.write_text("a\nb\n", encoding="utf-8")
    file_two.write_text("c\n\nd\n", encoding="utf-8")

    lines, loaded_count = io_ops.load_multiple_url_files([str(file_one), str(file_two)])

    assert loaded_count == 2
    assert lines == ["a", "b", "c", "d"]


def test_load_multiple_url_files_skips_unreadable(tmp_path) -> None:
    good_file = tmp_path / "ok.txt"
    missing_file = tmp_path / "missing.txt"
    good_file.write_text("alpha\nbeta\n", encoding="utf-8")

    lines, loaded_count = io_ops.load_multiple_url_files([str(missing_file), str(good_file)])

    assert loaded_count == 1
    assert lines == ["alpha", "beta"]
