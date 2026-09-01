"""D1c: what the commit status is computed from, and what it must never be computed from.

WHAT: `serve/standards_step.applied` — the step that runs the declared standards and posts the
      status, with the network call intercepted.
WHY:  **A STATUS BLOCKS A MERGE.** Our raw model findings measure 66.7-82.1% wrong across four
      blind pools, so a status that moved on a model verdict would turn the product into an
      obstacle rather than a check. Written after a sabotage forcing `enabled=True` passed with
      nothing failing: the module was new and had no test at all, so both of its guarantees — the
      status sees only `checks`, and posting obeys the setting — were unenforced prose.
IMPORTS: serve.standards_step, types.settings, types.standards.checked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from quantamind.serve.review import standards_step
from quantamind.types.settings import Settings

DECLARED = """
[[rule]]
id = "explain-why"
description = "Every public function explains why it exists."
severity = "medium"
check = "model_judged"

[[rule]]
id = "no-print"
description = "Use the logger, not print."
severity = "low"
check = "forbid_call"
target = "print"
"""

SOURCE = "def total(rows):\n    print(rows)\n    return sum(rows)\n"


@pytest.fixture
def clone(tmp_path: Path) -> tuple[Path, str]:
    """A real repository with a real commit. **No mock stands in for git.**"""
    root = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    (root / ".quantamind").mkdir()
    (root / ".quantamind" / "rules.toml").write_text(DECLARED, encoding="utf-8")
    (root / "app.py").write_text(SOURCE, encoding="utf-8")
    for command in (
        ["git", "-C", str(root), "config", "user.email", "t@example.com"],
        ["git", "-C", str(root), "config", "user.name", "t"],
        ["git", "-C", str(root), "add", "-A"],
        ["git", "-C", str(root), "commit", "-qm", "one"],
    ):
        subprocess.run(command, check=True, timeout=30)
    done = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return root, done.stdout.strip()


def test_the_status_is_computed_from_the_parsers_rows_alone(
    clone: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**NO MODEL VERDICT MAY REACH `announce`.** A status blocks a merge."""
    root, sha = clone
    seen: dict[str, Any] = {}

    def spy(repo: str, head: str, rows: Any, *, enabled: bool) -> None:
        seen["rows"] = rows
        seen["enabled"] = enabled

    monkeypatch.setattr(standards_step, "announce", spy)
    settings = Settings(posting_enabled=False, inference_enabled=False)

    checks, judged, merged = standards_step.applied(
        root, sha, ["app.py"], tmp_path / "s", "acme/app", 1, settings
    )

    assert seen["rows"] == checks
    assert judged == (), "inference was off, so nothing may have been judged"
    # **NO ORGANISATION CLONE WAS INJECTED**, so nothing was inherited and nothing was dropped —
    # and `org_read` is True, because "no organisation" is not "we could not read one".
    assert merged.org_read is True
    assert merged.changed() is False
    # Every row handed to the status must be a parser's verdict — none may be model-provenance.
    assert all(type(row).__name__ == "Checked" for row in seen["rows"])


def test_posting_disabled_is_passed_through_not_overridden(
    clone: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**`POSTING_ENABLED=0` REHEARSES.** A step ignoring it would write to a real repository."""
    root, sha = clone
    seen: dict[str, Any] = {}
    monkeypatch.setattr(
        standards_step,
        "announce",
        lambda repo, head, rows, *, enabled: seen.update(enabled=enabled),
    )

    standards_step.applied(
        root,
        sha,
        ["app.py"],
        tmp_path / "s",
        "acme/app",
        1,
        Settings(posting_enabled=False, inference_enabled=False),
    )
    assert seen["enabled"] is False

    standards_step.applied(
        root,
        sha,
        ["app.py"],
        tmp_path / "t",
        "acme/app",
        1,
        # **`Settings` REFUSES posting without an App configured**, which is why these are set.
        Settings(
            posting_enabled=True,
            inference_enabled=False,
            app_id="1",
            app_key_path="/tmp/unused-in-this-test.pem",
        ),
    )
    assert seen["enabled"] is True


def test_an_unreachable_organisation_repository_inherits_nothing(
    clone: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D1e: A FAILED FETCH MUST NOT READ AS "THE ORGANISATION DECLARES NOTHING".**

    Falling back to the repository's own file would report it as fully compliant at the exact
    moment its inherited standards stopped arriving — the confusion `rules_file.py` was built to
    prevent, one level up.
    """
    root, sha = clone
    monkeypatch.setattr(standards_step, "announce", lambda *a, **k: None)

    _checks, _judged, merged = standards_step.applied(
        root,
        sha,
        ["app.py"],
        tmp_path / "s",
        "acme/app",
        1,
        Settings(posting_enabled=False, inference_enabled=False),
        clone_org=lambda repo: None,
    )

    assert merged.org_read is False, "an unreachable org file was read as an empty one"
    assert merged.inherited_ids == frozenset()


def test_the_organisation_repository_asked_for_is_the_owners(
    clone: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**NAMES ITS ARTEFACT.** `acme/app` must look in `acme/.quantamind`, not anywhere else."""
    root, sha = clone
    monkeypatch.setattr(standards_step, "announce", lambda *a, **k: None)
    asked: list[str] = []

    def opener(repo: str) -> None:
        asked.append(repo)
        return None

    standards_step.applied(
        root,
        sha,
        ["app.py"],
        tmp_path / "s",
        "acme/app",
        1,
        Settings(posting_enabled=False, inference_enabled=False),
        clone_org=opener,
    )
    assert asked == ["acme/.quantamind"]
