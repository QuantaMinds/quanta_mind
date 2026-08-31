"""The decisions this repository has taken, and the wording that contradicts each one.

WHAT: `SCANNED` -- the documents a decision can drift in. `EXEMPT` -- the markers that say a
      paragraph is DISCUSSING a decision rather than asserting the losing side. `RULES` -- one
      `Rule` per decision, carrying the pattern that contradicts it and where it is recorded.
WHY:  **SEPARATED FROM THE SCANNER SO A REVERSAL IS A DIFF IN ONE FILE.** Three decisions here
      have now been reversed -- the ranking unit, the reviewer's existence, and the pricing axis --
      and each reversal has to move the pattern AND the exemptions together. The 2026-08-31 pricing
      reversal moved only the pattern: an exemption for `**per repository**`, written when that was
      the DECIDED side, silently spared the most emphatic statement of the REJECTED side. Keeping
      the two lists adjacent and away from the scanning code is what makes that visible in review.

      **A REVERSED RULE IS REWRITTEN IN PLACE, WITH ITS HISTORY IN A COMMENT ABOVE IT.** A guard
      enforcing a withdrawn decision is worse than no guard: it turns the build red for saying the
      true thing. The comment is not decoration -- it is how the next reader tells a live rule from
      one that outlived its decision.
IMPORTS: stdlib re. No project imports.
CONSUMED BY: `records/check_decided_vocabulary.py`, which does the scanning.
"""

from __future__ import annotations

import re

SCANNED = (
    "docs/product/QUANTAMIND.md",
    # **THE PRICING DOCUMENTS WERE NOT SCANNED, AND THEY ARE WHERE PRICING VOCABULARY DRIFTS.**
    # Added 2026-08-31 after a known-answer test: a sentence charging per repository was pasted
    # into `pricing.md` and the guard reported ok, because it only ever read one file. The rule
    # was correct and looking in the wrong place, which reports identically to no rule at all.
    "docs/product/unit-economics.md",
    "docs/product/pricing.md",
)
# A line carrying any of these is discussing the decision rather than asserting the losing side.
EXEMPT = re.compile(
    # Marked as not shipping, or as the rejected side of a decision.
    r"~~|NOT BUILT|NOT SELLABLE|not built|closed on evidence|used to|no longer|superseded|"
    r"retired|road not taken|were written when|rejected|would\s+\w+|"
    # This document's own idiom for quoting what it previously said. Added 2026-08-31 with the
    # pricing reversal, which left six paragraphs whose job is to name the abandoned wording.
    r"an earlier (?:revision|draft|version)|this (?:section|document|paragraph|table) used to|"
    # Describing somebody else's product. A price range attributed to a vendor is about them.
    r"incumbent|competitor|CodeRabbit|Greptile|Qodo|Bugbot|Macroscope|Aikido|CodeScene|"
    r"Semgrep|SonarQube|Snyk|"
    r"\$[\d,]+[^ ]{1,3}[\d,]+ per seat|sold \*\*per seat\*\*|reviewer sold",
    # **AN EXEMPTION FOR `**per repository**` WAS REMOVED HERE ON 2026-08-31 AND THAT IS THE WHOLE
    # POINT OF THE REVERSAL.** It was written when per-repository was the DECIDED side, to spare a
    # comparison row carrying it in bold. Reversing the rule turned that line into an exemption for
    # the most emphatic statement of the REJECTED side -- the exact phrasing a pricing page uses.
    # Known-answer test: `$99 **per repository** per month` reported ok while the unbolded sentence
    # one character apart was caught. A reversal has to move the exemptions, not only the pattern.
    re.I,
)


class Rule:
    """One decision, the pattern that contradicts it, and where the decision is recorded."""

    __slots__ = ("decided", "pattern", "recorded")

    def __init__(self, decided: str, pattern: str, recorded: str) -> None:
        self.decided = decided
        self.pattern = re.compile(pattern, re.I)
        self.recorded = recorded


RULES = (
    Rule(
        "allocation ranks FILES, not functions",
        r"rank(?:s|ing|ed)?\s+(?:the\s+)?functions?\b|top-ranked function|"
        r"every changed function|names?\s+(?:the\s+)?(?:one\s+)?function\b|"
        r"for every function|ranked function",
        "rank/order.py — `Site(path, line=0)`; docs/plans/delivered/feat-rank-fix-history.md",
    ),
    # **THIS RULE IS THE REVERSAL OF ONE THAT ENFORCED THE OPPOSITE, RECORDED RATHER THAN QUIETLY
    # APPLIED** -- the same handling as the `infer/`/`verify/` rule below, and for the same reason.
    # It used to read "pricing is per REPOSITORY, not per seat", on the argument that our costs
    # scale with repositories rather than headcount. That cost claim is still true and stopped
    # being the deciding one on 2026-08-31, when inference was measured at $1.20-$2.00 per
    # developer per month against a $29 price: a 4-7% input should not choose the pricing axis.
    # Three things decided it instead. The category prices per seat -- Semgrep $30/contributor,
    # SonarQube $40-50/developer, CodeRabbit $24 -- and a buyer who cannot compare like-for-like
    # assumes the worst. Per-repository pricing punishes microservice teams, who are the best fit.
    # And a repository count is gameable by merging repositories, which turns a pricing
    # conversation into an architecture argument.
    # **THE PATTERN NAMES A PRICE, NEVER A COST, AND THE DISTINCTION IS THE RULE.** Our cost of
    # goods genuinely IS per repository -- a clone and an index -- and saying so is true and
    # decided. What was reversed is the axis we CHARGE on. A first draft matched bare
    # "per repository" and condemned the cost-of-goods row, the cache-scope table and
    # "reviews per repository is unmeasured"; a second demanded the full "per repository per
    # month" and caught one of five realistic phrasings of the rejected side.
    Rule(
        "pricing is per DEVELOPER, not per repository",
        # $12/repo/mo, and the `**$12**/repo/mo` the tier table wrote it in.
        r"\$\s*[\d.,]+\s*(?:\*\*)?\s*/\s*repo(?:sitory)?\s*/\s*mo"
        # $10 per repository, $99 a repository.
        r"|\$\s*[\d.,]+\s*(?:\*\*)?\s*(?:per|a|/)\s*repositor(?:y|ies)\b"
        # priced / charged / billed per repository, across table cells as well as prose.
        r"|\b(?:pric(?:e|ed|es|ing)|charg(?:e|ed|es|ing)|bill(?:ed|ing|s)?)\b"
        r"[^.]{0,60}\bper repositor(?:y|ies)\b"
        # The tier table's own axis row: `| **Priced on** | ... | **repository** |`.
        r"|\bpriced on\b[^.]{0,60}\brepositor",
        "docs/product/unit-economics.md — the tier table; reversed from per-repository 2026-08-31",
    ),
    # **THIS RULE REPLACES ONE THAT ENFORCED THE OPPOSITE, AND THE REVERSAL IS RECORDED RATHER
    # THAN QUIETLY APPLIED.** It used to read "no model reads the code -- `infer/` and `verify/`
    # ship nothing", which was true of the product until 2026-08-20, when the reviewer half was
    # brought back in as a product decision. A guard enforcing a withdrawn decision is worse than
    # no guard: it turns the build red for saying the true thing.
    #
    # What is worth protecting NOW is the mechanism that makes shipping a model defensible, and it
    # is the part a summary drops first: findings are published only after an isolated judge in a
    # DIFFERENT model family clears them. Measured 2026-08-20 -- a same-family judge agreed with a
    # careful rater on 34.9% of findings and certified the reviewer's own invented facts.
    Rule(
        "raw model findings are never published, and the judge is a DIFFERENT family",
        r"publish(?:es|ed)? (?:the )?(?:raw |model )?findings? (?:directly|unverified|as[- ]is)|"
        r"same model (?:family|as the reviewer)|"
        r"no judge|without (?:a|the) judge|judge is the same",
        'docs/product/QUANTAMIND.md — "THE JUDGE IS THE RELIABILITY MECHANISM"',
    ),
)
