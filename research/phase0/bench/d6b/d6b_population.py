"""The D6b population and its statistic, kept apart from the arms that use them.

WHAT: `context_for(repo, number)` returns (context, why_not) via the product's own reader, and
      `mcnemar(better, worse)` is the exact two-sided sign test on discordant pairs.
WHY:  **SPLIT OUT AT THE 200-LINE CAP, AND IT IS A REAL SEAM.** `run_d6b.py` runs arms;
      deciding who is IN the population and how a difference is tested are separate questions, and
      `run_d6b_noise.py` needs both without needing the arms.

      **`context_for` RETURNS A REASON, NOT JUST TEXT.** Returning only the text dropped
      `behind()`'s `unreadable` and `skipped`, so a GitHub outage, a 403 or a rate limit was filed
      under "the author wrote little" — the distinction `ingest/context/tickets.py` exists to
      preserve, destroyed by its caller. It made the first run's "too thin = 4" untrustworthy.
IMPORTS: quantamind.ingest.context.tickets; stdlib math.
CONSUMED BY: `run_d6b.py`, `run_d6b_noise.py`.
"""

from __future__ import annotations

from math import comb

MIN_CONTEXT_CHARS = 120
"""Copied from `scripts/measure/context/exposure.py`, fixed before any outcome was seen."""


def context_for(repo: str, number: int) -> tuple[str, str]:
    """(context, why_not). **A READ FAILURE IS NOT "THE AUTHOR WROTE LITTLE".**

    The first version returned only the text, so `behind()`'s `unreadable` and `skipped` were
    dropped and a GitHub outage, a 403 or a rate limit landed in the "too thin" bucket beside a
    change whose author really had said nothing. That is the distinction
    `ingest/context/tickets.py` exists to preserve, destroyed by its own caller — and it means the
    original run's "too thin = 4" was not a trustworthy count. `why_not` is empty when the read
    succeeded, and carries the reason when it did not.
    """
    from quantamind.ingest.context.tickets import behind

    got = behind(repo, number)
    if got.unreadable:
        return "", f"unreadable: {got.unreadable}"
    stated = " ".join(got.stated.text().split())
    titles = " ".join(" ".join(t.title.split()) for t in got.tickets)
    text = (stated + (" " if stated and titles else "") + titles).strip()
    # **BRACES IN REAL PROSE COLLIDE WITH `str.format`.** `bench_reviewer.review` formats the
    # template, so a pull request body containing `{ init }` raised KeyError -- and a body
    # containing `{title}` would have been SILENTLY SUBSTITUTED, corrupting the arm without
    # raising at all. Escaping here is what makes the arm's text the author's text.
    declined = "; ".join(s.why.value for s in got.skipped)
    return text.replace("{", "{{").replace("}", "}}"), (
        f"declined: {declined}" if declined and not text else ""
    )


def mcnemar(better: int, worse: int) -> float:
    total = better + worse
    if total == 0:
        return 1.0
    smaller = min(better, worse)
    return float(min(1.0, 2 * sum(comb(total, i) for i in range(smaller + 1)) / 2**total))
