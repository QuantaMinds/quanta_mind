"""The admission limit and the research's cap count DIFFERENT populations.

WHAT: Builds a history where one admissible event is flat-scored, so limiting admissions and
      capping survivors give different answers, and asserts both.
WHY:  `defect_return.py` appends an event and only THEN checks `len(events) >= 400`, so its cap
      counts survivors of the flat-score skip. `admissible()` cannot evaluate that skip -- it
      needs scores, which need the store, which `rank/` may not reach.

      Measured on the pinned corpus, capping admissions at 400 yields 2,278 events against 2,400,
      and the shortfall runs from 0.75% (pandas) to 10% (scikit-learn) because each repository has
      its own flat-score rate. **It does not merely shrink the sample, it REWEIGHTS the
      repositories inside a pooled figure**, and it stops five weeks earlier in scrapy's history.
      `serve/retrospective.replay()` defaulted to those semantics under the research's name.
IMPORTS: quantamind.ingest.commits, quantamind.rank.events, quantamind.serve.retrospective.
CONSUMED BY: `just check`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from test_retrospective_bound import BASE, DAY, _commit

from quantamind.ingest.commits import read_commits
from quantamind.serve import retrospective


def test_the_admission_limit_is_not_the_research_cap(tmp_path: Path) -> None:
    """`limit` counts admissions; the research's 400 counts survivors of the flat-score skip.

    Capping admissions loses events UNEVENLY — 0.75% of pandas against 10% of scikit-learn on the
    pinned corpus — because each repository has its own flat-score rate. That reweights the
    repositories inside a pooled figure, which is the one thing a pooled comparison must not do.

    The fixture below makes the difference visible in miniature: three admissible events, of which
    the FIRST is flat-scored and dropped. Limiting admission to 2 therefore yields ONE survivor,
    while an uncapped walk yields two. A `limit` that silently meant the research's cap would make
    those the same number under the same name.
    """
    from quantamind.rank.events import SURVIVOR_CAP, admissible

    repo = tmp_path / "uneven"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, capture_output=True, timeout=60)
    # a.py and b.py tie at zero on the first event, so it is flat and the scorer drops it.
    _commit(repo, BASE, {"a.py": "1", "b.py": "1"}, "first change")
    _commit(repo, BASE + DAY, {"a.py": "2"}, "fix the first")
    for n in range(2):
        _commit(repo, BASE + (10 + n * 30) * DAY, {"a.py": f"x{n}", "b.py": f"y{n}"}, f"change {n}")
        _commit(repo, BASE + (11 + n * 30) * DAY, {"a.py": f"f{n}"}, f"fix change {n}")

    commits = read_commits(repo, pathspec="*.py")
    assert len(list(admissible(commits))) == 3, "the fixture must admit three events"
    assert len(list(admissible(commits, limit=2))) == 2, "limit counts ADMISSIONS"

    capped = retrospective.replay(repo, "t/t", tmp_path / "capped.db", cap=1)
    whole = retrospective.replay(repo, "t/t", tmp_path / "whole.db")
    assert capped.whole.events == 1, "cap counts SURVIVORS, applied after the flat-score skip"
    assert whole.whole.events > capped.whole.events, (
        f"uncapped produced {whole.whole.events}, capped {capped.whole.events} — the survivor cap "
        f"is not being applied where the skip happens"
    )
    assert SURVIVOR_CAP == 400, "the research's cap is 400 survivors, not 400 admissions"
