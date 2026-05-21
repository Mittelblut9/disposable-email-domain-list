from disposable_domains.dns_check import DnsStatus, classify_domain


def test_classify_domain_active_when_any_resolver_finds_mx(monkeypatch):
    responses = {"1.1.1.1": "no_mx", "8.8.8.8": "mx"}
    monkeypatch.setattr("disposable_domains.dns_check.query_mx", lambda domain, resolver: responses[resolver])

    result = classify_domain("example.com", resolvers=("1.1.1.1", "8.8.8.8"))

    assert result.status is DnsStatus.ACTIVE


def test_classify_domain_inactive_only_on_conclusive_consensus(monkeypatch):
    responses = {"1.1.1.1": "no_mx", "8.8.8.8": "nxdomain"}
    monkeypatch.setattr("disposable_domains.dns_check.query_mx", lambda domain, resolver: responses[resolver])

    result = classify_domain("example.com", resolvers=("1.1.1.1", "8.8.8.8"))

    assert result.status is DnsStatus.INACTIVE


def test_classify_domain_unknown_when_resolvers_are_inconclusive(monkeypatch):
    responses = {"1.1.1.1": "no_mx", "8.8.8.8": "timeout"}
    monkeypatch.setattr("disposable_domains.dns_check.query_mx", lambda domain, resolver: responses[resolver])

    result = classify_domain("example.com", resolvers=("1.1.1.1", "8.8.8.8"))

    assert result.status is DnsStatus.UNKNOWN
