import shutil
from pathlib import Path

from disposable_domains.config import Paths
from disposable_domains.pipeline import run_update


def test_run_update_writes_sorted_outputs_and_cache(monkeypatch):
    tmp_path = Path("tests/.tmp_pipeline").resolve()
    if tmp_path.exists():
        shutil.rmtree(tmp_path)
    tmp_path.mkdir(parents=True)

    paths = Paths(
        root=tmp_path,
        sources=tmp_path / "config" / "sources.txt",
        allowlist=tmp_path / "allowlist.txt",
        inactive_cache=tmp_path / "cache" / "inactive_domains.txt",
        domains_txt=tmp_path / "domains.txt",
        domains_json=tmp_path / "domains.json",
    )
    paths.sources.parent.mkdir()
    paths.sources.write_text("https://example.test/feed.txt\n", encoding="utf-8")
    paths.allowlist.write_text("legit.example\nlegit.example\n", encoding="utf-8")
    paths.inactive_cache.parent.mkdir()
    paths.inactive_cache.write_text("old-dead.example\n", encoding="utf-8")

    monkeypatch.setattr(
        "disposable_domains.pipeline.fetch_all",
        lambda sources: (
            {"active.example", "dead.example", "unknown.example", "legit.example", "old-dead.example"},
            [],
        ),
    )
    monkeypatch.setattr(
        "disposable_domains.pipeline.scan_domains",
        lambda domains, resolvers, workers: ({"active.example"}, {"dead.example"}, {"unknown.example"}),
    )

    summary = run_update(paths, workers=1)

    assert summary.output == 2
    assert paths.allowlist.read_text(encoding="utf-8") == "legit.example\n"
    assert paths.domains_txt.read_text(encoding="utf-8") == "active.example\nunknown.example\n"
    assert paths.domains_json.read_text(encoding="utf-8") == '["active.example","unknown.example"]\n'
    assert "dead.example" in paths.inactive_cache.read_text(encoding="utf-8")

    shutil.rmtree(tmp_path)
