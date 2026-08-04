"""Build the synthetic control corpus and measure it with the real pipeline.

WHAT: Constructs repositories where breakage IS caused by an unresolvable edge,
      plus matched controls where the caller is directly resolvable, then derives
      exposure and outcome by running the actual stages over them.
WHY:  This is the piece whose absence meant the RUNBOOK §2.1 gate could not run at
      all — `run_positive_control` computed a ratio *from* observations and nothing
      built them.

      Exposure and outcome are **derived, never assigned**. A control that writes
      its own answers tests the arithmetic and nothing else. So each synthetic PR
      goes through `run_pipeline.one_pr` for exposure and `scan_outcome.scan` for
      outcome, exactly as a corpus PR would.

      Deliberately **not perfectly separated** — see BREAK_FRACTION_EXPOSED and
      BREAK_FRACTION_CONTROL. Perfect separation makes the ratio unbounded and the
      GEE fit unidentified, so the control would pass for a reason that says nothing
      about a real corpus.

      A11: synthetic repositories guarantee `graph_status == OK`, so a failure to
      detect is unambiguously a *detection* failure. That is the only condition
      under which RR ≥ 5 carries meaning.
IMPORTS: GitPython, phase0.build_table, extract_prs, run_pipeline, scan_outcome,
      and controls.mechanisms.
CONSUMED BY: controls/gate.py; tests/test_controls_corpus.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from git import Actor, Repo

from phase0.controls.mechanisms import MECHANISMS, RESOLVABLE
from phase0.extract_prs import PRRecord

AUTHOR = Actor("Phase0 Control", "control@quantamind.invalid")
MERGED_AT = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)

# Strong but not perfect. A true RR of 8 clears the gate without making the fit
# unidentified, which perfect separation would.
# Expressed as a fraction and applied over the ACTUAL count. Writing this as
# `i % 10 < 8` over range(8) silently yields 8/8 -- perfect separation, an
# unbounded ratio, and a control that passes for a reason that says nothing.
BREAK_FRACTION_EXPOSED = 0.8
BREAK_FRACTION_CONTROL = 0.1


@dataclass(frozen=True, slots=True)
class SyntheticPR:
    """One built repository and the PR record describing it."""

    record: PRRecord
    repo_path: Path
    mechanism: str
    planted_break: bool


def _module_for(mechanism: str, index: int) -> str:
    """A distinct module name per synthetic PR.

    Every PR previously changed `mod.target`, so every symbol-derived nonsense
    variable was constant across the corpus and its 2x2 had an empty margin. A
    negative control with no variance tests nothing.
    """
    return f"{mechanism}_{index}"


def _stamp(when: datetime) -> str:
    """GitPython rejects an offset written '+00:00'; it wants '+0000'."""
    return when.strftime("%Y-%m-%dT%H:%M:%S%z")


def _commit(repo: Repo, rel: str, body: str, message: str, when: datetime) -> str:
    target = Path(repo.working_tree_dir or "") / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    repo.index.add([rel])
    stamp = _stamp(when)
    made = repo.index.commit(
        message, author=AUTHOR, committer=AUTHOR, author_date=stamp, commit_date=stamp
    )
    return made.hexsha


def build_one(
    root: Path, index: int, mechanism: str, exposed: bool, planted_break: bool
) -> SyntheticPR:
    """One repository: a package, a merged change to `target`, and maybe a fix."""
    path = root / f"{mechanism}-{'exp' if exposed else 'ctl'}-{index}"
    pkg = path / "acme"
    pkg.mkdir(parents=True)
    repo = Repo.init(path, initial_branch="main")

    source = MECHANISMS[mechanism] if exposed else RESOLVABLE
    _commit(repo, "acme/__init__.py", "", "chore: seed package", MERGED_AT - timedelta(days=2))
    _commit(
        repo,
        f"acme/{_module_for(mechanism, index)}.py",
        source,
        "chore: seed module",
        MERGED_AT - timedelta(days=1),
    )

    # The PR: a change to `target`, squash-shaped so A2 resolves it as SQUASH.
    merged = _commit(
        repo,
        f"acme/{_module_for(mechanism, index)}.py",
        source.replace("return r\n", "return r  # changed\n", 1),
        "feat: change target",
        MERGED_AT,
    )

    if planted_break:
        _commit(
            repo,
            f"acme/{_module_for(mechanism, index)}.py",
            source + "\n# hotfix\n",
            "fix: crash after target signature change",
            MERGED_AT + timedelta(days=2),
        )

    record = PRRecord(
        pr_id=f"{mechanism}-{'exp' if exposed else 'ctl'}-{index}",
        repo=f"synthetic/{mechanism}-{index}",
        language="python",
        parent_sha="",
        merged_sha=merged,
        merged_at=MERGED_AT.isoformat().replace("+00:00", "Z"),
        changed_files=(f"acme/{_module_for(mechanism, index)}.py",),
        changed_symbols=(f"{_module_for(mechanism, index)}.target",),
        arm="agent",
        task_type="refactor",
        repo_id=f"synthetic/{mechanism}-{index}-{'exp' if exposed else 'ctl'}",
    )
    return SyntheticPR(record, path, mechanism, planted_break)


def build_corpus(root: Path, per_mechanism: int = 8) -> list[SyntheticPR]:
    """Exposed and control arms across all four mechanisms, deterministically."""
    built: list[SyntheticPR] = []
    for mechanism in sorted(MECHANISMS):
        for i in range(per_mechanism):
            built.append(
                build_one(
                    root, i, mechanism, True, i < round(per_mechanism * BREAK_FRACTION_EXPOSED)
                )
            )
            built.append(
                build_one(
                    root, i, mechanism, False, i < round(per_mechanism * BREAK_FRACTION_CONTROL)
                )
            )
    return built
