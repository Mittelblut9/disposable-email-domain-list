# Disposable Email Domain List

This repository builds a slim, DNS-validated list of domains associated with
disposable email services.

The updater aggregates public disposable-domain feeds, normalizes messy source
formats, removes known legitimate mail providers from `allowlist.txt`, and keeps
only domains that either still have MX records or could not be conclusively
classified as inactive. Domains that every configured public DNS resolver agrees
are inactive are written to `cache/inactive_domains.txt` and skipped on future
runs.

## Download

[TXT format](https://github.com/groundcat/disposable-email-domain-list/raw/master/domains.txt)

[JSON format](https://github.com/groundcat/disposable-email-domain-list/raw/master/domains.json)

## How It Works

1. Read source URLs from `config/sources.txt`.
2. Fetch JSON, plain text, conf-style, whitespace-delimited, or mixed-format domain lists.
3. Normalize domains, remove duplicates, and discard invalid entries.
4. Sort and deduplicate `allowlist.txt`, then exclude allowlisted legitimate providers.
5. Skip domains already recorded in `cache/inactive_domains.txt`.
6. Query MX records across multiple public DNS resolvers.
7. Keep domains with any confirmed MX record.
8. Keep inconclusive domains to avoid false removals.
9. Cache only domains where every resolver returns a conclusive inactive result.

## Local Development

Always use a virtual environment for local Python commands:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e .[dev]
```

Run tests:

```powershell
.\.venv\Scripts\python -m pytest
```

Update the generated lists:

```powershell
.\.venv\Scripts\update-disposable-domains --workers 32
```

## Automation

GitHub Actions runs the updater weekly on Mondays and can also be triggered
manually. If the generated output passes tests and sanity checks, the workflow
commits updates to:

- `allowlist.txt`
- `cache/inactive_domains.txt`
- `domains.txt`
- `domains.json`

## Sources

The raw data is compiled from the active feeds in `config/sources.txt`. Sources
that are unavailable, access-blocked, or no longer maintained should be removed
from that file instead of being carried forward silently.

## Contribution

This repository does not accept direct contributions of new disposable domains;
it gathers and cleans public source lists. If a legitimate provider appears in
the output, add it to `allowlist.txt`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
