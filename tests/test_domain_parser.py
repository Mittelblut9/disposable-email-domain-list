from disposable_domains.domain_parser import normalize_domain, parse_domains


def test_normalize_domain_handles_noise_and_idna():
    assert normalize_domain(" *.Example.COM, ") == "example.com"
    assert normalize_domain("https://mail.example.com/path") == "mail.example.com"
    assert normalize_domain("bücher.example") == "xn--bcher-kva.example"
    assert normalize_domain("not a domain") is None


def test_parse_domains_handles_json_and_messy_text():
    assert parse_domains('["A.example", {"nested": ["b.example"]}]', source_url="feed.json") == {
        "a.example",
        "b.example",
    }

    assert parse_domains("a.example b.example\n# comment\n*.C.example # inline") == {
        "a.example",
        "b.example",
        "c.example",
    }
