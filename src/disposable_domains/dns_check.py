from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum

import dns.exception
import dns.resolver

from .config import DEFAULT_RESOLVERS

LOGGER = logging.getLogger(__name__)


class DnsStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DomainDnsResult:
    domain: str
    status: DnsStatus
    resolver_results: dict[str, str]


def query_mx(domain: str, resolver_ip: str, timeout: float = 4.0) -> str:
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [resolver_ip]
    resolver.timeout = timeout
    resolver.lifetime = timeout

    try:
        answers = resolver.resolve(domain, "MX")
    except dns.resolver.NXDOMAIN:
        return "nxdomain"
    except dns.resolver.NoAnswer:
        return "no_mx"
    except dns.resolver.NoNameservers:
        return "no_nameservers"
    except dns.exception.Timeout:
        return "timeout"
    except dns.exception.DNSException as exc:
        return f"error:{exc.__class__.__name__}"

    return "mx" if list(answers) else "no_mx"


def classify_domain(domain: str, resolvers: tuple[str, ...] = DEFAULT_RESOLVERS) -> DomainDnsResult:
    results: dict[str, str] = {}
    for resolver in resolvers:
        result = query_mx(domain, resolver)
        results[resolver] = result
        if result == "mx":
            return DomainDnsResult(domain=domain, status=DnsStatus.ACTIVE, resolver_results=results)

    status = DnsStatus.INACTIVE if results else DnsStatus.UNKNOWN

    return DomainDnsResult(domain=domain, status=status, resolver_results=results)


def scan_domains(
    domains: set[str],
    resolvers: tuple[str, ...] = DEFAULT_RESOLVERS,
    workers: int = 32,
) -> tuple[set[str], set[str], set[str]]:
    active: set[str] = set()
    inactive: set[str] = set()
    unknown: set[str] = set()

    max_workers = max(1, workers)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(classify_domain, domain, resolvers): domain for domain in sorted(domains)}
        for future in as_completed(futures):
            result = future.result()
            if result.status is DnsStatus.ACTIVE:
                active.add(result.domain)
            elif result.status is DnsStatus.INACTIVE:
                inactive.add(result.domain)
            else:
                LOGGER.info("DNS status unknown for %s: %s", result.domain, result.resolver_results)
                unknown.add(result.domain)

    return active, inactive, unknown
