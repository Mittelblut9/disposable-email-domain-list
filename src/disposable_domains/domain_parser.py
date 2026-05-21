from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from urllib.parse import urlparse

DOMAIN_RE = re.compile(
    r"(?=.{1,253}\.?$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{1,62}\.?",
    re.IGNORECASE,
)


def normalize_domain(value: str) -> str | None:
    candidate = value.strip().lower()
    if not candidate or candidate.startswith("#"):
        return None

    candidate = candidate.split("#", 1)[0].strip()
    candidate = candidate.removeprefix("*.").removeprefix("@")

    if "://" in candidate:
        parsed = urlparse(candidate)
        candidate = parsed.hostname or ""

    candidate = candidate.strip(" .,\t\r\n'\"[]()<>")
    if not candidate:
        return None

    try:
        candidate = candidate.encode("idna").decode("ascii")
    except UnicodeError:
        return None

    if not DOMAIN_RE.fullmatch(candidate):
        return None

    return candidate.rstrip(".")


def parse_domains(content: str, content_type: str = "", source_url: str = "") -> set[str]:
    values: Iterable[object]
    looks_like_json = "json" in content_type.lower() or source_url.lower().endswith(".json")

    if looks_like_json:
        try:
            values = _flatten_json(json.loads(content))
        except json.JSONDecodeError:
            values = _split_text(content)
    else:
        values = _split_text(content)

    domains: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        domain = normalize_domain(value)
        if domain:
            domains.add(domain)
    return domains


def _flatten_json(value: object) -> Iterator[object]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _flatten_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_json(item)
    else:
        yield value


def _split_text(content: str) -> Iterator[str]:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for token in re.split(r"[\s,;]+", stripped):
            if token:
                yield token
