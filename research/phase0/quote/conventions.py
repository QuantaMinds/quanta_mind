"""Read the repository's own rules file, so a finding can cite the house rule it breaks.

WHAT: `select()` picks the conventions file from a repository's root listing and `render()` trims it
      to a prompt-sized block. Both are pure -- the caller supplies the bytes.
WHY:  Qodo ships `repo_context_files = ["AGENTS.md"]` at `repo_context_max_lines = 500` and leads
      Martian's offline layer. The reviewer currently reviews every repository against generic
      notions of good code, so it cannot tell a deliberate house convention from a defect, and it
      cannot cite the rule when there is one.

      THE PRE-REGISTERED RISK RUNS THE OTHER WAY, and it is the reason this is measured rather than
      simply shipped. A conventions file is mostly STYLE. Feeding one to a reviewer whose findings
      are already 30-35% wrong may buy convention-policing dressed as defect-finding -- a claim that
      quotes a real added line and cites a real rule, passes every gate we own, and is still not
      something a maintainer must fix before merging. `G-nit` catches the vocabulary of style, not
      its substance. So the harm shows up as a WRONG-RATE, and that is the number the run reports.

      WHAT IS SENT IS RECORDED WITH THE RUN. A prompt that varies per repository and is not stored
      is a run nobody can reproduce.
IMPORTS: stdlib only (hashlib).
CONSUMED BY: `run13.py` in this package.
"""

from __future__ import annotations

import hashlib

CANDIDATES = ("AGENTS.md", "CLAUDE.md", "CONVENTIONS.md", "CONTRIBUTING.md", ".cursorrules")
MAX_LINES = 500
MAX_CHARS = 20_000
# Below this a file states no rules. Three of the first six repositories sampled shipped a POINTER:
# pluggy's AGENTS.md is "See @CLAUDE.md", sanic's and trio's CONTRIBUTING.md are a bare URL -- 62,
# 72 and 98 characters. Real rules files in the same sample were 1,095 to 6,101. The cut sits in
# the empty middle and was fixed by INSPECTING THE FILES, before any model call and against no
# outcome. Without it the arm would have been a silent no-op on half the corpus and reported as
# though the rules had been supplied.
MIN_CHARS = 400


def names_to_try(names: list[str]) -> list[str]:
    """Candidate filenames present in a root listing, highest priority first."""
    have = {n.lower(): n for n in names}
    return [have[w.lower()] for w in CANDIDATES if w.lower() in have]


def select(bodies: dict[str, str]) -> str | None:
    """The highest-priority candidate that actually states rules, or None when none does.

    Priority order, skipping stubs -- not longest. Length is the wrong proxy for rule density:
    falcon ships a 6.1k AGENTS.md of coding rules beside a 14.8k CONTRIBUTING.md that is mostly
    how to open a pull request and sign a CLA, and longest picks the wrong one. Skipping stubs is
    what pluggy needs, whose AGENTS.md is a 62-character pointer at its real CLAUDE.md.

    None is a RESULT -- roughly half of repositories have no usable rules file, and the run reports
    how many so the arm is never averaged over repositories where it could not act.
    """
    lower = {n.lower(): n for n in bodies}
    for want in CANDIDATES:
        name = lower.get(want.lower())
        if name and len(bodies[name].strip()) >= MIN_CHARS:
            return name
    return None


def render(name: str, body: str) -> tuple[str, dict[str, object]]:
    """(prompt block, what was sent) -- trimmed to MAX_LINES then MAX_CHARS, whichever bites first.

    The digest is of the TRIMMED text, because the trimmed text is what the model saw.
    """
    lines = body.split("\n")
    kept = lines[:MAX_LINES]
    text = "\n".join(kept)[:MAX_CHARS]
    block = (
        f"This repository's own contributor rules follow, from {name}. A change breaking one of\n"
        f"these is a defect even if acceptable elsewhere; quote the rule in your claim.\n"
        f"Rules about formatting, naming or style are NOT defects and are still discarded.\n\n"
        f"```\n{text}\n```\n"
    )
    return block, {
        "file": name,
        "lines_total": len(lines),
        "lines_sent": len(kept),
        "chars_sent": len(text),
        "truncated": len(lines) > MAX_LINES or len("\n".join(kept)) > MAX_CHARS,
        "sha256": hashlib.sha256(text.encode()).hexdigest()[:16],
    }
