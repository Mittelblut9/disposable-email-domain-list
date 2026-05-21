from __future__ import annotations

import json
from pathlib import Path

from .domain_parser import normalize_domain


def read_domain_file(path: Path) -> set[str]:
    if not path.exists():
        return set()

    domains: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        domain = normalize_domain(line)
        if domain:
            domains.add(domain)
    return domains


def write_domain_file(path: Path, domains: set[str], header: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = sorted(domains)
    body = "\n".join(lines)
    if body:
        body += "\n"

    if header:
        header_text = "\n".join(f"# {line}" for line in header.splitlines())
        path.write_text(f"{header_text}\n{body}", encoding="utf-8")
    else:
        path.write_text(body, encoding="utf-8")


def write_json_array(path: Path, domains: set[str]) -> None:
    path.write_text(
        json.dumps(sorted(domains), ensure_ascii=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
