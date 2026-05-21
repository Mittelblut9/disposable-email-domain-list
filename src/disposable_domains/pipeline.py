from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import DEFAULT_RESOLVERS, Paths
from .dns_check import scan_domains
from .fetcher import fetch_all, read_sources
from .files import read_domain_file, write_domain_file, write_json_array

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateSummary:
    fetched: int
    skipped_cached_inactive: int
    allowlisted: int
    active: int
    newly_inactive: int
    unknown: int
    output: int


def run_update(paths: Paths, resolvers: tuple[str, ...] = DEFAULT_RESOLVERS, workers: int = 32) -> UpdateSummary:
    sources = read_sources(paths.sources)
    fetched_domains, source_results = fetch_all(sources)

    failed_sources = [result for result in source_results if result.error]
    if failed_sources:
        LOGGER.warning("%s source(s) failed and were skipped", len(failed_sources))

    allowlist = read_domain_file(paths.allowlist)
    inactive_cache = read_domain_file(paths.inactive_cache)
    skipped_cached_inactive = len(fetched_domains & inactive_cache)

    candidates = fetched_domains - allowlist - inactive_cache
    active, newly_inactive, unknown = scan_domains(candidates, resolvers=resolvers, workers=workers)

    output = active | unknown
    inactive_cache = inactive_cache | newly_inactive

    write_domain_file(paths.allowlist, allowlist)
    write_domain_file(
        paths.inactive_cache,
        inactive_cache,
        header=(
            "Domains below were confirmed inactive by consensus across all configured DNS\n"
            "resolvers. The updater keeps this sorted and reuses it to skip future scans."
        ),
    )
    write_domain_file(paths.domains_txt, output)
    write_json_array(paths.domains_json, output)

    return UpdateSummary(
        fetched=len(fetched_domains),
        skipped_cached_inactive=skipped_cached_inactive,
        allowlisted=len(fetched_domains & allowlist),
        active=len(active),
        newly_inactive=len(newly_inactive),
        unknown=len(unknown),
        output=len(output),
    )
