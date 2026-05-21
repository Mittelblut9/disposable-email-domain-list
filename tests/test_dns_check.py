import threading
import time

from disposable_domains.dns_check import DnsStatus, classify_domain, scan_domains


def test_classify_domain_active_when_any_resolver_finds_mx(monkeypatch):
    queried = []
    responses = {"1.1.1.1": "no_mx", "8.8.8.8": "mx"}

    def fake_query(domain, resolver):
        queried.append(resolver)
        return responses[resolver]

    monkeypatch.setattr("disposable_domains.dns_check.query_mx", fake_query)

    result = classify_domain("example.com", resolvers=("1.1.1.1", "8.8.8.8"))

    assert result.status is DnsStatus.ACTIVE
    assert queried == ["1.1.1.1", "8.8.8.8"]


def test_classify_domain_inactive_only_on_conclusive_consensus(monkeypatch):
    responses = {"1.1.1.1": "no_mx", "8.8.8.8": "nxdomain"}
    monkeypatch.setattr("disposable_domains.dns_check.query_mx", lambda domain, resolver: responses[resolver])

    result = classify_domain("example.com", resolvers=("1.1.1.1", "8.8.8.8"))

    assert result.status is DnsStatus.INACTIVE


def test_classify_domain_inactive_when_resolvers_have_no_mx_even_with_errors(monkeypatch):
    responses = {"1.1.1.1": "no_mx", "8.8.8.8": "timeout"}
    monkeypatch.setattr("disposable_domains.dns_check.query_mx", lambda domain, resolver: responses[resolver])

    result = classify_domain("example.com", resolvers=("1.1.1.1", "8.8.8.8"))

    assert result.status is DnsStatus.INACTIVE


def test_scan_domains_uses_bounded_concurrency(monkeypatch):
    active_threads = 0
    peak_threads = 0
    lock = threading.Lock()

    def fake_classify(domain, resolvers):
        nonlocal active_threads, peak_threads
        with lock:
            active_threads += 1
            peak_threads = max(peak_threads, active_threads)
        time.sleep(0.01)
        with lock:
            active_threads -= 1
        return type(
            "Result",
            (),
            {"domain": domain, "status": DnsStatus.INACTIVE, "resolver_results": {}},
        )()

    monkeypatch.setattr("disposable_domains.dns_check.classify_domain", fake_classify)

    active, inactive, unknown = scan_domains({f"d{i}.example" for i in range(20)}, workers=4)

    assert active == set()
    assert len(inactive) == 20
    assert unknown == set()
    assert peak_threads <= 4
    assert peak_threads > 1
