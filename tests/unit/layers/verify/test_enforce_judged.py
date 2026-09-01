"""D1c end to end: the audit trail takes the parser's rows and not one model verdict.

WHAT: `verify/rule_check.enforce` against a REAL git clone with a REAL declared rules file.
WHY:  **THIS IS THE TEST THAT THE COMPLIANCE ARTEFACT IS UNCHANGED.** Everything else here checks a
      function; this checks the thing a customer shows an auditor. It builds a repository, commits
      it, runs the real enforcement, and reads the rows back out of the real store — no mock stands
      in for git or for SQLite, because a mock would pass whether or not the guarantee held.
IMPORTS: store.{schema,touches}, types.standards.{checked,judged,rule},
      verify.{judged_rule,rule_check}.
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

from quantamind.store import schema, touches
from quantamind.types.standards.checked import Outcome
from quantamind.types.standards.judged import Verdict
from quantamind.types.standards.rule import Rule
from quantamind.verify.judged_rule import JUDGE_CAP
from quantamind.verify.rule_check import enforce

SOURCE = '''"""A module."""


def total(rows):
    return sum(rows)


def deceptive(rows):
    return len(rows)
'''


def _saying(verdict: Verdict, quote: str = "", why: str = "said so"):
    """A judge that always answers the same thing."""

    def ask(rule: Rule, path: str, source: str) -> tuple[Verdict, str, str]:
        return verdict, quote, why

    return ask


def _repo(root: Path, rules: str, source: str) -> str:
    """A real repository with a real commit. **No mock stands in for git here.**"""
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    (root / ".quantamind").mkdir()
    (root / ".quantamind" / "rules.toml").write_text(rules, encoding="utf-8")
    (root / "app.py").write_text(source, encoding="utf-8")
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
    return done.stdout.strip()


DECLARED = """
[[rule]]
id = "explain-why"
description = "Every public function explains WHY it exists, not only what it does."
severity = "medium"
check = "model_judged"

[[rule]]
id = "no-print"
description = "Use the logger, not print."
severity = "low"
check = "forbid_call"
target = "print"
"""


def _seed_review(store: Path, repo: str, number: int, sha: str) -> None:
    """The review row `persist` writes its checks against.

    **WITHOUT THIS THE TEST PASSED VACUOUSLY THE OTHER WAY.** The first version asserted the rows
    landed and they had not — `enforce` printed "audit trail took 0 of 2 check(s)" and returned
    normally, which is correct behaviour and would have made a green test out of an empty table.
    """
    conn = schema.open_store(store)
    repo_id = touches.ensure_repo(conn, "github.com", repo)
    conn.execute(
        "INSERT INTO review (repo_id, pr_number, head_sha, created_at, fire_decision)"
        " VALUES (?, ?, ?, 1756600000, 1)",
        (repo_id, number, sha),
    )
    conn.commit()
    conn.close()


def test_enforce_stores_checks_and_never_stores_judgements(tmp_path: Path) -> None:
    """**The audit trail takes the parser's rows and not one model verdict.**

    The row count in `rule_check` must be identical whether or not a judge ran, or a model's
    opinion has entered the artefact a customer shows an auditor.
    """
    clone = tmp_path / "repo"
    sha = _repo(clone, DECLARED, SOURCE)
    store = tmp_path / "store"
    _seed_review(store, "acme/app", 1, sha)

    checks, judged = enforce(
        clone,
        sha,
        ["app.py"],
        store,
        "acme/app",
        1,
        _saying(Verdict.BROKEN, "def deceptive(rows):"),
    )

    assert judged and judged[0].verdict is Verdict.BROKEN
    assert any(c.rule_id == "explain-why" and c.outcome is Outcome.DEFERRED for c in checks)

    assert store.exists(), "the parser's half must have been persisted"
    conn = sqlite3.connect(store)
    rows = conn.execute("SELECT count(*) FROM rule_check").fetchone()[0]
    stored = {value[0] for value in conn.execute("SELECT DISTINCT outcome FROM rule_check")}
    conn.close()

    assert rows == len(checks), "every check ran must be on the record, and nothing else"
    assert stored <= {outcome.value for outcome in Outcome}

    # **THE ROW FOR THE MODEL-JUDGED RULE MUST STILL SAY `deferred`, AND THIS IS THE ASSERTION
    # THAT MATTERS.** Counting rows does not catch the dangerous case: `store/rule_checks.py`
    # writes with INSERT OR REPLACE, so a model verdict written over the parser's honest
    # "nobody decided this" leaves the COUNT unchanged and flips the outcome to `passed` — which
    # `counts_toward_compliance` accepts. A sabotage that persisted the judgements passed the
    # count check and was caught only by this line.
    conn = sqlite3.connect(store)
    outcomes = dict(conn.execute("SELECT rule_id, outcome FROM rule_check"))
    conn.close()
    assert outcomes["explain-why"] == "deferred", "a model verdict reached the audit trail"
    assert outcomes["no-print"] == "passed"


def test_enforce_without_a_judge_is_unchanged(tmp_path: Path) -> None:
    """**The deterministic half must be byte-identical with the model off.**"""
    clone = tmp_path / "repo"
    sha = _repo(clone, DECLARED, SOURCE)

    with_model, judged = enforce(
        clone, sha, ["app.py"], tmp_path / "a", "acme/app", 1, _saying(Verdict.MET)
    )
    without, none_judged = enforce(clone, sha, ["app.py"], tmp_path / "b", "acme/app", 1)

    assert without == with_model
    assert none_judged == ()
    assert len(judged) == 1


def test_the_file_cap_is_real(tmp_path: Path) -> None:
    """**A cap that does not hold is a cost bug; one that does not announce itself is a lie.**

    `serve/` reports the shortfall; this asserts the cap actually bounds the calls.
    """
    clone = tmp_path / "repo"
    sha = _repo(clone, DECLARED, SOURCE)
    seen: list[str] = []

    def ask(rule: Rule, path: str, source: str) -> tuple[Verdict, str, str]:
        seen.append(path)
        return Verdict.MET, "", ""

    paths = ["app.py"] * (JUDGE_CAP + 5)
    enforce(clone, sha, paths, tmp_path / "s", "acme/app", 1, ask)
    assert len(seen) == JUDGE_CAP
