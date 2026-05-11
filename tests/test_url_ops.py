import random

from core import url_ops


def test_dedupe_urls_preserves_first_seen_order() -> None:
    urls = ["https://a.com/x", "https://b.com", "https://a.com/x", "https://c.com"]
    filtered, removed = url_ops.dedupe_urls(urls)
    assert filtered == ["https://a.com/x", "https://b.com", "https://c.com"]
    assert removed == 1


def test_dedupe_domains_keeps_first_domain_occurrence() -> None:
    urls = [
        "https://www.example.com/a",
        "http://example.com/b",
        "https://other.com/z",
        "other.com/y",
    ]
    filtered, removed = url_ops.dedupe_domains(urls)
    assert filtered == ["https://www.example.com/a", "https://other.com/z"]
    assert removed == 2


def test_keep_only_duplicate_urls_keeps_all_duplicate_occurrences() -> None:
    urls = ["https://a.com", "https://b.com", "https://a.com", "https://c.com", "https://c.com", "https://c.com"]
    filtered, removed = url_ops.keep_only_duplicate_urls(urls)
    assert filtered == ["https://a.com", "https://a.com", "https://c.com", "https://c.com", "https://c.com"]
    assert removed == 1


def test_filter_by_phrases_remove_matches() -> None:
    urls = ["https://a.com/login", "https://a.com/about", "https://b.com/Login/help"]
    filtered, removed = url_ops.filter_by_phrases(urls, ["login"], keep_matches=False)
    assert filtered == ["https://a.com/about"]
    assert removed == 2


def test_filter_by_phrases_keep_matches() -> None:
    urls = ["alpha", "beta", "gamma"]
    filtered, removed = url_ops.filter_by_phrases(urls, ["a"], keep_matches=True)
    assert filtered == ["alpha", "beta", "gamma"]
    assert removed == 0


def test_clean_url_list_preserves_tabs_and_spaces() -> None:
    lines = ["col1\tcol2\t", "  padded value  ", "", "\tleading-tab"]
    cleaned = url_ops.clean_url_list(lines)
    assert cleaned == ["col1\tcol2\t", "  padded value  ", "\tleading-tab"]


def test_remove_under_length() -> None:
    urls = ["a", "abcd", "abcdef"]
    filtered, removed = url_ops.remove_under_length(urls, minimum_length=4)
    assert filtered == ["abcd", "abcdef"]
    assert removed == 1


def test_remove_over_length() -> None:
    urls = ["abc", "abcdef", "abcdefgh"]
    filtered, removed = url_ops.remove_over_length(urls, maximum_length=6)
    assert filtered == ["abc", "abcdef"]
    assert removed == 1


def test_trim_root() -> None:
    urls = ["https://example.com/a/b?x=1", "example.org/path/next"]
    trimmed = url_ops.trim_to_root(urls)
    assert trimmed == ["https://example.com/", "example.org/"]


def test_trim_first_folder() -> None:
    urls = ["https://example.com/a/b/c", "example.org/path/next"]
    trimmed = url_ops.trim_to_first_folder(urls)
    assert trimmed == ["https://example.com/a/", "example.org/path/"]


def test_trim_last_folder() -> None:
    urls = ["https://example.com/a/b/c", "example.org/path/next"]
    trimmed = url_ops.trim_to_last_folder(urls)
    assert trimmed == ["https://example.com/c/", "example.org/next/"]


def test_trim_domain_level() -> None:
    urls = ["https://forms.ygoc.org/", "blog.example.com/path", "https://example.net/keep"]
    trimmed = url_ops.trim_to_domain_level(urls)
    assert trimmed == ["ygoc.org", "example.com", "example.net"]


def test_trim_subdomain_level() -> None:
    urls = ["https://forms.ygoc.org/path/here", "http://blog.example.com/", "example.net/a"]
    trimmed = url_ops.trim_to_subdomain_level(urls)
    assert trimmed == ["forms.ygoc.org", "blog.example.com", "example.net"]


def test_trim_does_not_modify_plain_text_lines() -> None:
    lines = ["just a phrase", "keyword list item", "no-domain-slug"]
    assert url_ops.trim_to_root(lines) == lines
    assert url_ops.trim_to_first_folder(lines) == lines
    assert url_ops.trim_to_last_folder(lines) == lines
    assert url_ops.trim_to_domain_level(lines) == lines
    assert url_ops.trim_to_subdomain_level(lines) == lines


def test_spin_urls_combines_lines_into_spintax() -> None:
    lines = ["item1", "item2", "item3"]
    assert url_ops.spin_urls(lines) == "{item1|item2|item3}"


def test_spin_urls_empty_input() -> None:
    assert url_ops.spin_urls([]) == ""


def test_shuffle_urls_same_elements() -> None:
    urls = ["u1", "u2", "u3", "u4", "u5"]
    shuffled = url_ops.shuffle_urls(urls, rng=random.Random(123))
    assert sorted(shuffled) == sorted(urls)
    assert shuffled != urls
