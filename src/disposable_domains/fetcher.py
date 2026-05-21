from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

from .domain_parser import parse_domains

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceResult:
    url: str
    domains: set[str]
    error: str | None = None


def read_sources(path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            urls.append(stripped)
    return urls


def fetch_source(session: requests.Session, url: str, timeout: float = 30.0) -> SourceResult:
    try:
        response = session.get(url, timeout=timeout, headers={"User-Agent": "disposable-domain-updater/0.1"})
        response.raise_for_status()
    except requests.RequestException as exc:
        return SourceResult(url=url, domains=set(), error=str(exc))

    domains = parse_domains(
        response.text,
        content_type=response.headers.get("content-type", ""),
        source_url=url,
    )
    return SourceResult(url=url, domains=domains)


def fetch_all(urls: list[str]) -> tuple[set[str], list[SourceResult]]:
    results: list[SourceResult] = []
    domains: set[str] = set()

    with requests.Session() as session:
        for url in urls:
            result = fetch_source(session, url)
            results.append(result)
            if result.error:
                LOGGER.warning("Skipping source %s: %s", url, result.error)
                continue
            LOGGER.info("Fetched %s domains from %s", len(result.domains), url)
            domains.update(result.domains)

    return domains, results
