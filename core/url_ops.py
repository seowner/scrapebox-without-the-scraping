from __future__ import annotations

import random
from urllib.parse import urlsplit


def clean_url_list(lines: list[str]) -> list[str]:
    return [line for line in lines if line != ""]


def urls_to_text(urls: list[str]) -> str:
    return "\n".join(urls)


def dedupe_urls(urls: list[str]) -> tuple[list[str], int]:
    seen: set[str] = set()
    output: list[str] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        output.append(url)
    return output, len(urls) - len(output)


def keep_only_duplicate_urls(urls: list[str]) -> tuple[list[str], int]:
    occurrence_count: dict[str, int] = {}
    for url in urls:
        occurrence_count[url] = occurrence_count.get(url, 0) + 1

    output = [url for url in urls if occurrence_count.get(url, 0) > 1]
    return output, len(urls) - len(output)


def dedupe_domains(urls: list[str]) -> tuple[list[str], int]:
    seen_domains: set[str] = set()
    output: list[str] = []
    for url in urls:
        domain_key = _domain_key(url)
        if domain_key in seen_domains:
            continue
        seen_domains.add(domain_key)
        output.append(url)
    return output, len(urls) - len(output)


def filter_by_phrases(urls: list[str], phrases: list[str], keep_matches: bool) -> tuple[list[str], int]:
    normalized_phrases = [phrase.casefold() for phrase in phrases if phrase.strip()]
    if not normalized_phrases:
        return urls[:], 0

    output: list[str] = []
    for url in urls:
        lowered = url.casefold()
        has_match = any(phrase in lowered for phrase in normalized_phrases)
        if keep_matches and has_match:
            output.append(url)
        elif not keep_matches and not has_match:
            output.append(url)
    return output, len(urls) - len(output)


def remove_under_length(urls: list[str], minimum_length: int) -> tuple[list[str], int]:
    output = [url for url in urls if len(url) >= minimum_length]
    return output, len(urls) - len(output)


def remove_over_length(urls: list[str], maximum_length: int) -> tuple[list[str], int]:
    output = [url for url in urls if len(url) <= maximum_length]
    return output, len(urls) - len(output)


def trim_to_root(urls: list[str]) -> list[str]:
    return [_trim_url(url, "root") for url in urls]


def trim_to_first_folder(urls: list[str]) -> list[str]:
    return [_trim_url(url, "first") for url in urls]


def trim_to_last_folder(urls: list[str]) -> list[str]:
    return [_trim_url(url, "last") for url in urls]


def trim_to_domain_level(urls: list[str]) -> list[str]:
    return [_trim_url(url, "domain") for url in urls]


def trim_to_subdomain_level(urls: list[str]) -> list[str]:
    return [_trim_url(url, "subdomain") for url in urls]


def spin_urls(urls: list[str]) -> str:
    if not urls:
        return ""
    return "{" + "|".join(urls) + "}"


def shuffle_urls(urls: list[str], rng: random.Random | None = None) -> list[str]:
    output = urls[:]
    if rng is None:
        random.shuffle(output)
    else:
        rng.shuffle(output)
    return output


def _domain_key(url: str) -> str:
    parsed, _ = _parse_url_like(url)
    if parsed is None:
        return url.casefold()

    domain = (parsed.hostname or parsed.netloc or "").casefold()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain or url.casefold()


def _prepare_url(url: str) -> tuple[str, bool]:
    candidate = url.strip()
    had_scheme = "://" in candidate
    if had_scheme:
        return candidate, True
    return f"http://{candidate}", False


def _trim_url(url: str, mode: str) -> str:
    parsed, had_scheme = _parse_url_like(url)
    if parsed is None:
        return url

    netloc = parsed.netloc
    if not netloc:
        return url

    path_parts = [part for part in parsed.path.split("/") if part]
    if mode == "root":
        trimmed_path = "/"
    elif mode == "first":
        trimmed_path = f"/{path_parts[0]}/" if path_parts else "/"
    elif mode == "last":
        trimmed_path = f"/{path_parts[-1]}/" if path_parts else "/"
    elif mode == "domain":
        host = parsed.hostname or netloc
        if not host:
            return url
        return _to_domain_level(host)
    elif mode == "subdomain":
        host = parsed.hostname or netloc
        if not host:
            return url
        return host
    else:
        return url

    if had_scheme:
        return f"{parsed.scheme}://{netloc}{trimmed_path}"
    return f"{netloc}{trimmed_path}"


def _to_domain_level(host: str) -> str:
    lower_host = host.casefold()
    if lower_host == "localhost":
        return host

    labels = [label for label in host.split(".") if label]
    if len(labels) <= 2:
        return ".".join(labels) if labels else host

    return ".".join(labels[-2:])


def _parse_url_like(value: str):
    candidate = value.strip()
    if not candidate:
        return None, False

    has_scheme = "://" in candidate
    if not has_scheme:
        if " " in candidate:
            return None, False
        first_token = candidate.split("/")[0]
        if "." not in first_token:
            return None, False

    prepared_url, had_scheme = _prepare_url(candidate)
    parsed = urlsplit(prepared_url)
    if not parsed.netloc:
        return None, False
    return parsed, had_scheme
