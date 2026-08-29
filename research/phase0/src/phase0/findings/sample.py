"""Draw a findings-correctness pack, audit it, and write the sheet and the labels file.

WHAT: `python -m phase0.findings.sample --harvest F --out DIR --seed N` writes a sheet of real
      published findings and a labels file with a VERDICT and a LINE to fill in per item.
WHY:  A6 measured 0.686 findings published per change and could not say how many were right.

      **THERE IS NO KEY, SO THERE IS NOTHING TO SEAL.** The planted-control arm this replaced
      needed one, and `PHASE0_PREREGISTRATION.md` A57 records a whole draw voided because a key
      reached a session transcript -- which then happened again here, to the tooling written
      after it. Removing the arm removed the hazard rather than guarding it: auditing this pack
      cannot burn the draw, because the pack contains no answers.

      What the sheet asks for is a verdict AND the line that decides it. That line is the
      attention check, and `scoring.py` refuses any verdict whose line is not in the code shown.
IMPORTS: stdlib, phase0.findings.{pack,audit}.
CONSUMED BY: `just findings-draw`. Its output is read by `phase0.findings.scoring`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase0.findings.audit import PackRejected, require_clean
from phase0.findings.pack import Finding, Pack, draw


def sheet_of(pack: Pack) -> str:
    """The sheet. Claim and code only -- no verdict, no anchor, nothing pre-decided."""
    n = len(pack.items)
    lines = [
        "# Findings correctness — labelling pack",
        "",
        f"**{n} items, each a finding this pipeline actually published.** For each: does the",
        "claim accurately describe a real problem in the code shown?",
        "",
        "Record two things per item in the labels file:",
        "",
        "- **VERDICT** — `TRUE`, `FALSE` or `UNKNOWN`.",
        "- **LINE** — for TRUE and FALSE, paste the one line from the diff that decides it.",
        "  It is checked against the code shown, and a verdict whose line is not there is not",
        "  scored. UNKNOWN needs no line.",
        "",
        "`UNKNOWN` is the right answer when deciding would need code, configuration or library",
        "behaviour that is not in the diff. It is not a failure to record it — a confident",
        "verdict resting on recalled facts is worse, and has already been wrong here.",
        "",
        "**Ten minutes per item, hard stop.** Judge from the diff shown and nothing else.",
        "",
    ]
    for item in pack.items:
        lines += [
            f"## item {item.label_id:02d}",
            "",
            "**Claim:**",
            "",
            "> " + item.claim.replace("\n", "\n> "),
            "",
            "**Code:**",
            "",
            "```diff",
            item.diff.rstrip(),
            "```",
            "",
        ]
    return "\n".join(lines)


def labels_of(pack: Pack) -> str:
    """The file the rater fills in. One block per item, parsed back by `scoring.py`."""
    lines = [
        "# Verdicts",
        "",
        "VERDICT: TRUE | FALSE | UNKNOWN.  LINE: the deciding line, pasted from the diff.",
        "",
    ]
    for item in pack.items:
        lines += [f"## item {item.label_id:02d}", "", "VERDICT:", "LINE:", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harvest", type=Path, required=True, help="JSON list of findings")
    parser.add_argument("--out", type=Path, required=True, help="directory for sheet and labels")
    parser.add_argument("--seed", type=int, required=True, help="no default, on purpose")
    parser.add_argument("--size", type=int, default=24)
    args = parser.parse_args()

    raw = json.loads(args.harvest.read_text())
    findings = [
        Finding(sha=r["sha"], path=r["path"], claim=r["claim"], quote=r["quote"], diff=r["diff"])
        for r in raw
    ]
    pack = draw(findings, size=args.size, seed=args.seed)

    try:
        seen = require_clean(pack)
    except PackRejected as rejected:
        print(f"PACK REJECTED: {rejected}. Nothing was written.")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "findings_pack.md").write_text(sheet_of(pack))
    (args.out / "findings_labels.md").write_text(labels_of(pack))

    print(f"considered {pack.considered} findings, {pack.unjudgeable} quoted outside their diff")
    print(
        f"pack: {seen['items']} items, {seen['distinct_diffs']} distinct diffs, "
        f"{seen['distinct_claims']} distinct claims, seed {pack.seed}"
    )
    print(
        f"audit: {seen['anchored']} of {seen['items']} items carry an anchor inside the code shown"
    )
    print(f"sheet  -> {args.out / 'findings_pack.md'}")
    print(f"labels -> {args.out / 'findings_labels.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
