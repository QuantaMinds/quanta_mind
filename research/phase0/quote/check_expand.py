"""Known-answer and sabotage tests for `expand.py` and `conventions.py`.

WHAT: Asserts each mechanism produces the right answer, then BREAKS each mechanism and asserts the
      same assertions now fail. Prints a table and exits non-zero if any check is wrong.
WHY:  "Ask what a check outputs when the thing it checks is broken. If the answer is 'the same
      thing', it is not a check." A previous sabotage of `G-fix` was a dud -- it broke `_norm` in a
      way that preserved the equality being tested, so the test stayed green against a broken
      mechanism and was read as coverage.

      SO EACH SABOTAGE HERE BREAKS THE WHOLE MECHANISM, not its entry point. For expansion that is
      the backwards search that finds the declaration, not `section()` which merely reads the header
      -- a run with `section()` stubbed would still be caught by the header regex upstream.
IMPORTS: stdlib only (sys). Local: `conventions`, `expand`, `gate`.
CONSUMED BY: nobody -- it prints and exits.
"""

from __future__ import annotations

import sys

import conventions
import expand
import gate

FILE = [
    "import os",
    "from decimal import Decimal",
    "",
    "",
    "class Ledger:",
    "    def settle(self, order):",
    "        total = order.amount",
    "        validate(order)",
    "        self.write(order.id, total)",
    "        return total",
]

DIFF = """diff --git a/pay.py b/pay.py
--- a/pay.py
+++ b/pay.py
@@ -8,2 +8,4 @@ def settle(self, order):
         self.write(order.id, total)
+        if order.refunded:
+            return None
         return total
"""

RULES = "\n".join(f"rule {i}" for i in range(900))
results: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    results.append((name, passed, detail))


def anchors(d: str) -> list[tuple[str, int, str]]:
    added, _ = gate.added_lines(d)
    return [(p, ln, t) for p, ln, t, _h in added]


# --- known answers -------------------------------------------------------------------------
out, stats = expand.expand(DIFF, lambda p: FILE)
record("expand finds the declaration", "    def settle(self, order):" in out.split("@@")[-1])
record("expand changed the diff at all", out != DIFF)
record("expand reports it expanded", stats["expanded"] == 1, str(stats))
record("expand does not move anchors", anchors(out) == anchors(DIFF), str(anchors(out)))
record("expand is inert without the file", expand.expand(DIFF, lambda p: None)[0] == DIFF)
record(
    "expand counts a headerless hunk",
    expand.expand(DIFF.replace(" @@ def settle(self, order):", " @@"), lambda p: FILE)[1][
        "no_header"
    ]
    == 1,
)
BIG = "x" * 2000
record(
    "conventions lists candidates by priority",
    conventions.names_to_try(["CONTRIBUTING.md", "README.md", "AGENTS.md"])
    == ["AGENTS.md", "CONTRIBUTING.md"],
)
record("conventions returns None when absent", conventions.select({}) is None)
record(
    "conventions rejects a pointer stub",
    conventions.select({"AGENTS.md": "See @CLAUDE.md for instructions."}) is None,
)
record(
    "conventions skips a stub to the real file",
    conventions.select({"AGENTS.md": "See @CLAUDE.md.", "CLAUDE.md": BIG}) == "CLAUDE.md",
)
record(
    "conventions keeps priority over length",
    conventions.select({"AGENTS.md": BIG, "CONTRIBUTING.md": BIG * 4}) == "AGENTS.md",
)
_, sent = conventions.render("AGENTS.md", RULES)
record("conventions truncates at the cap", sent["lines_sent"] == conventions.MAX_LINES, str(sent))
record("conventions reports truncation", sent["truncated"] is True)

# --- sabotage: break the WHOLE mechanism, then require the same checks to FAIL ---------------
real_max = expand.MAX_BACK
expand.MAX_BACK = 0  # the backwards search can no longer reach any declaration
sab, sab_stats = expand.expand(DIFF, lambda p: FILE)
record("SABOTAGE expansion -> the diff is now unchanged", sab == DIFF, sab_stats and "")
record(
    "SABOTAGE expansion -> expanded count drops to 0", sab_stats["expanded"] == 0, str(sab_stats)
)
expand.MAX_BACK = real_max

real_cands = conventions.CANDIDATES
conventions.CANDIDATES = ()  # no candidate can ever be listed
record(
    "SABOTAGE candidates -> AGENTS.md no longer found",
    conventions.names_to_try(["CONTRIBUTING.md", "AGENTS.md"]) == [],
)
conventions.CANDIDATES = real_cands

real_min = conventions.MIN_CHARS
conventions.MIN_CHARS = 0  # every stub now counts as rules
record(
    "SABOTAGE stub cut -> the pointer is accepted again",
    conventions.select({"AGENTS.md": "See @CLAUDE.md for instructions."}) == "AGENTS.md",
)
conventions.MIN_CHARS = real_min

real_lines = conventions.MAX_LINES
conventions.MAX_LINES = 10**9  # the cap can no longer bite
_, sab_sent = conventions.render("AGENTS.md", RULES)
record(
    "SABOTAGE cap -> truncation check now fails",
    sab_sent["lines_sent"] != real_lines and sab_sent["truncated"] is False,
    str(sab_sent),
)
conventions.MAX_LINES = real_lines

bad = 0
for name, ok, detail in results:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"   {detail[:70]}" if not ok else ""))
    bad += not ok
print(f"\n  {len(results) - bad}/{len(results)} checks correct")
sys.exit(1 if bad else 0)
