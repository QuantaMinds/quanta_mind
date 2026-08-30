"""Verification that warming a repository really indexes it, and that failing to is not fatal.

WHAT: Drives `serve/onboarding.warm` and `warm_all` against a REAL git repository and a REAL store,
      with only the network clone stubbed out.
WHY:  **`listener.py` CLAIMED THIS WAS ALREADY HANDLED AND IT WAS NOT.** The line beside the
      installation branch read "Provisioned here so a first review pays no cold index", but
      `tenancy.provision` creates the store FILE and nothing else — no clone, no touches, no
      watermark. The claim was true of nothing, so the first pull request paid a full clone plus a
      ~31s index build on a 115,776-commit repository, and Cloud Run's ephemeral disk means every
      new instance paid it again.

      **THE ROW COUNT IS ASSERTED, NOT THE ABSENCE OF AN EXCEPTION.** A warm-up that ran and
      indexed nothing is the failure this is meant to prevent, and it does not raise.

      **AND A FAILED WARM-UP MUST NOT FAIL THE INSTALLATION.** It runs after the endpoint has
      answered 200; an exception escaping would kill a worker thread over something that costs
      nothing worse than a slow first review.
IMPORTS: pytest, quantamind.serve.onboarding, quantamind.store.schema, quantamind.types.settings.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from quantamind.serve import onboarding as warm_module
from quantamind.serve.onboarding import warm, warm_all
from quantamind.store import tenancy
from quantamind.store.schema import open_store
from quantamind.types.settings import Settings

GIT_TIMEOUT_S = 30


def _repo(root: Path, commits: int) -> Path:
    """A real git repository with `commits` commits touching Python files."""
    root.mkdir(parents=True, exist_ok=True)

    def run(*args: str) -> None:
        subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, timeout=GIT_TIMEOUT_S
        )

    run("init", "--quiet", "-b", "main")
    run("config", "user.email", "t@example.com")
    run("config", "user.name", "t")
    for n in range(commits):
        (root / f"mod_{n % 3}.py").write_text(f"value = {n}\n")
        run("add", "-A")
        run("commit", "--quiet", "-m", f"change {n}")
    return root


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    (tmp_path / "stores").mkdir()
    return Settings(database_path=str(tmp_path / "stores"), clone_root=str(tmp_path / "clones"))


def test_warming_indexes_real_touches(tmp_path: Path, settings: Settings, monkeypatch) -> None:
    """The count comes back from a real git history through a real store, not from a stub."""
    clone = _repo(tmp_path / "src", commits=6)
    monkeypatch.setattr(warm_module, "ensure", lambda repo, root, token=None: clone)

    rows = warm("acme/payments", settings)

    assert rows > 0, "the warm-up reported no touches for a repository with six commits"
    store = tenancy.store_for(Path(settings.database_path), "acme", "payments")
    conn = open_store(store)
    try:
        assert int(conn.execute("SELECT COUNT(*) FROM touch").fetchone()[0]) == rows
        assert conn.execute("SELECT head_sha FROM touch_watermark").fetchone() is not None, (
            "the watermark was not moved, so the next review re-reads the whole history"
        )
    finally:
        conn.close()


def test_warming_twice_does_not_double_the_index(
    tmp_path: Path, settings: Settings, monkeypatch
) -> None:
    """A redelivered installation event must cost the remaining range, not the world."""
    clone = _repo(tmp_path / "src", commits=5)
    monkeypatch.setattr(warm_module, "ensure", lambda repo, root, token=None: clone)

    first = warm("acme/payments", settings)
    second = warm("acme/payments", settings)

    assert second == first, f"the index grew from {first} to {second} with no new commits"


def test_a_failure_is_collected_rather_than_raised(settings: Settings, monkeypatch) -> None:
    """warm_all runs after the endpoint answered 200; an escape would kill the worker thread."""

    def boom(repo: str, root: Path, token: str | None = None) -> Path:
        raise RuntimeError("clone refused")

    monkeypatch.setattr(warm_module, "ensure", boom)

    indexed, failed = warm_all(["acme/payments"], settings)

    assert indexed == {}
    assert "clone refused" in failed["acme/payments"]
    assert failed["acme/payments"].startswith("RuntimeError")


def test_one_failure_does_not_stop_the_others(
    tmp_path: Path, settings: Settings, monkeypatch
) -> None:
    """The second repository must still be warmed after the first fails."""
    clone = _repo(tmp_path / "src", commits=4)

    def sometimes(repo: str, root: Path, token: str | None = None) -> Path:
        if repo == "acme/broken":
            raise RuntimeError("clone refused")
        return clone

    monkeypatch.setattr(warm_module, "ensure", sometimes)

    indexed, failed = warm_all(["acme/broken", "acme/payments"], settings)

    assert list(failed) == ["acme/broken"]
    assert indexed["acme/payments"] > 0


def test_warming_nothing_returns_two_empty_maps(settings: Settings) -> None:
    """An installation selecting no repository is a real state, not an error."""
    assert warm_all([], settings) == ({}, {})
