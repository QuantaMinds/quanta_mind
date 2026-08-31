"""The pricing reversal, driven through `main()` on a document the test writes itself.

WHAT: Builds a miniature project holding the three documents `SCANNED` names, runs
      `check_decided_vocabulary.main()` over it, and asserts on the wording each rule must catch
      and the wording each must leave alone.
WHY:  **THE RULE THIS FILE COVERS WAS REVERSED, AND THE REVERSAL SHIPPED HALF-DONE.** On 2026-08-31
      the pricing axis moved from per repository to per developer. The pattern was rewritten; the
      EXEMPT list was not. An entry for `**per repository**`, written when that was the DECIDED
      side, went on exempting the most emphatic statement of the now-REJECTED side -- so
      `$99 **per repository** per month` reported ok while the unbolded sentence one character
      apart was caught. **A reversal has to move the exemptions, not only the pattern**, and
      nothing in the suite said so.

      **The narrow-pattern case is here for the same reason.** The first reversed pattern demanded
      the full phrase "per repository per month" and caught **one of five** realistic phrasings.
      A rule that is correct and too narrow reports identically to no rule at all.

      **And the honest cases matter as much as the failures.** Our cost of goods genuinely IS per
      repository -- a clone and an index -- and a guard that condemns a true cost sentence is one
      people disable. Three of these passed a broad first draft and had to be scoped out.
IMPORTS: scripts/guard/records/check_decided_vocabulary.py. No product imports.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "guard"))

from records.check_decided_vocabulary import main  # noqa: E402

# The guard scans by paragraph. Filler gives it a population without matching any rule.
FILLER = "\n\n".join(
    f"Paragraph {n} says nothing a decision has an opinion about." for n in range(8)
)


def _run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sentence: str, into: str = "pricing.md"
) -> int:
    """One sentence dropped into one of the three scanned documents."""
    product = tmp_path / "docs" / "product"
    product.mkdir(parents=True, exist_ok=True)
    for name in ("QUANTAMIND.md", "unit-economics.md", "pricing.md"):
        body = f"{FILLER}\n\n{sentence}\n" if name == into else f"{FILLER}\n"
        (product / name).write_text(body, encoding="utf-8")
    # **NO `AGENTS.md` AND NO `justfile` HERE, DELIBERATELY.** Those two are what `coverage.py`
    # uses to decide a tree is the project; writing them makes the 100-paragraph floor apply to a
    # fixture holding 25, and every case below fails on the floor rather than on its own assertion.
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    return main()


# Each is a phrasing a pricing page would actually use for the REJECTED axis.
REJECTED = [
    "Team is $99 per repository per month, billed annually.",
    "Team is $99 **per repository** per month, billed annually.",
    "Team is $99 per repository, billed annually.",
    "We charge per repository, so a bigger team costs the same.",
    "Team: $99/repo/mo.",
    "Pricing is per repository rather than per seat.",
    "| **Priced on** | — | **repository** | **repository** | contract |",
]


@pytest.mark.parametrize("sentence", REJECTED)
def test_the_rejected_pricing_axis_is_caught_however_it_is_phrased(
    sentence: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Five of these passed the first reversed pattern, and the bolded one passed the second."""
    assert _run(tmp_path, monkeypatch, sentence) == 1, (
        f"the guard reported ok on a sentence charging per repository: {sentence!r}"
    )
    assert "per DEVELOPER" in capsys.readouterr().out


# Each states a COST or a VOLUME per repository, which is true and decided and must not fire.
HONEST = [
    "What the shipped product actually costs is a clone and an index, per repository.",
    "Reviews per repository per month is unmeasured and spans two orders of magnitude.",
    "| Prefix — cached | repository conventions, index summary | per repository |",
    "Three candidate outcome rules, run on one population per repository.",
    "An earlier revision said we were priced per repository, and that is no longer true.",
]


@pytest.mark.parametrize("sentence", HONEST)
def test_a_true_cost_or_volume_sentence_is_not_condemned(
    sentence: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Our COST is per repository. Only the PRICE moved, and the rule has to know the difference.

    **The printed counts are asserted, not just the exit code.** A guard whose discovery collapsed
    would also return 0 here, and would go on returning 0 — passing for the reason that means it
    read nothing. That is the failure this whole file exists to make loud.
    """
    assert _run(tmp_path, monkeypatch, sentence) == 0, (
        f"the guard condemned a sentence that is true under the decision: {sentence!r}"
    )
    printed = capsys.readouterr().out
    assert "in 3 document(s) against 3 decision(s)" in printed, (
        f"the guard returned 0 without reading the three documents it was given: {printed!r}"
    )
    assert "ok" in printed, printed


def test_the_guard_reports_what_it_examined_rather_than_only_its_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ask what it prints when it is broken. Without this line, `ok` -- the same as a clean run.

    Emptying `RULES` or `SCANNED` used to print `ok` and exit 0. The counts are now asserted here
    and floored in the guard itself, so a mechanism that checks nothing cannot report success.
    """
    assert _run(tmp_path, monkeypatch, "Nothing contentious here at all.") == 0
    printed = capsys.readouterr().out
    assert "in 3 document(s)" in printed, printed
    assert "against 3 decision(s)" in printed, printed


def test_the_other_two_decisions_still_fire_after_the_pricing_reversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Rewriting one rule in a shared tuple is how the neighbours get broken silently."""
    assert _run(tmp_path, monkeypatch, "The allocator ranks every changed function.") == 1
    assert "FILES, not functions" in capsys.readouterr().out
    assert _run(tmp_path, monkeypatch, "The judge is the same model family as the reviewer.") == 1
    assert "DIFFERENT family" in capsys.readouterr().out
