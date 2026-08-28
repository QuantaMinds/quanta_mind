"""Draw a blind findings-correctness pack, audit it, and write the sheet, labels and key.

WHAT: `python -m phase0.sample_findings --harvest F --out DIR --key PATH --seed N` writes a
      blind sheet, an empty labels file, and the sealed key -- the key wherever the caller
      says, so it can be put outside the working tree.
WHY:  A6 measured 0.686 findings published per change and could not say how many were right.
      This builds the instrument that asks a human, following the rules in
      `docs/findings/HAND_LABELLING_PROTOCOL.md` for a different unit of analysis.

      **THIS PROCESS NEVER PRINTS WHICH ARM AN ITEM IS IN.** `PHASE0_PREREGISTRATION.md` A57
      voided a whole draw because a key reached a session transcript, and notes that the
      protection which failed was an instruction rather than a check. So the reporting here is
      aggregate by construction: `require_clean` returns counts, and the per-item complaints
      from `audit` are deliberately NOT echoed -- a leak report names item numbers and arms,
      which is the key in another shape. A rejected pack prints how many leaks, not which.

      **THE SEED HAS NO DEFAULT**, for the reason `sample_for_labelling.py` gives: a draw must
      be reproducible and must not be quietly redrawn because somebody disliked the first one.
      Redrawing after arms have leaked is legitimate and is the one case that needs a NEW seed;
      it belongs in the preregistration, not in a default argument.
IMPORTS: stdlib, phase0.findings.{pack,audit}.
CONSUMED BY: an operator, by hand. Its output is read by `phase0.findings.scoring`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from phase0.findings.audit import PackRejected, require_clean
from phase0.findings.pack import Finding, Pack, draw


def sheet_of(pack: Pack) -> str:
    """The blind sheet. Claim and code only -- no path header, no verdict, no arm."""
    n = len(pack.blind)
    lines = [
        "# Findings correctness — labelling pack",
        "",
        f"**{n} items. For each: does the claim accurately describe a real problem in the code",
        "shown?** Write TRUE, FALSE or UNSURE in the labels file against the item id.",
        "",
        "- **Ten minutes per item, hard stop.** UNSURE is valid and is scored as disagreement.",
        "- **Judge from the diff shown and nothing else.** Do not open the repository.",
        f"- Some items are controls. Answering the same thing to all {n} scores 50%.",
        f"- The key is sealed outside this directory. Label all {n} before it is opened.",
        "- A claim can be about code that is not in the diff shown. That is a legitimate FALSE.",
        "",
    ]
    for item in pack.blind:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harvest", type=Path, required=True, help="JSON list of findings")
    parser.add_argument("--out", type=Path, required=True, help="directory for sheet and labels")
    parser.add_argument("--key", type=Path, required=True, help="where to seal the key")
    parser.add_argument("--seed", type=int, required=True, help="no default, on purpose")
    parser.add_argument("--real", type=int, default=12)
    parser.add_argument("--planted", type=int, default=12)
    args = parser.parse_args()

    raw = json.loads(args.harvest.read_text())
    findings = [
        Finding(sha=r["sha"], path=r["path"], claim=r["claim"], quote=r["quote"], diff=r["diff"])
        for r in raw
    ]
    pack = draw(findings, real=args.real, planted=args.planted, seed=args.seed)

    try:
        seen = require_clean(pack)
    except PackRejected as rejected:
        # Count only. The complaints name item numbers and arms; printing them here would be
        # the A57 failure again, committed by the tool that exists to prevent it.
        print(f"PACK REJECTED: {str(rejected).split(':')[0]}. Nothing was written.")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "findings_pack.md").write_text(sheet_of(pack))
    (args.out / "findings_labels.csv").write_text(
        "label_id,verdict\n" + "\n".join(f"item {i.label_id:02d}," for i in pack.blind) + "\n"
    )
    args.key.parent.mkdir(parents=True, exist_ok=True)
    args.key.write_text("\n".join(f"item {i:02d},{arm}" for i, arm in pack.key) + "\n")

    print(f"considered {pack.considered} findings, {pack.unjudgeable} quoted outside their diff")
    print(f"pack: {seen['real']} real, {seen['planted']} planted, seed {pack.seed}")
    print(f"audit: {seen['planted_examined']} of {seen['planted']} controls verified false")
    print(f"sheet -> {args.out / 'findings_pack.md'}")
    print(f"key   -> {args.key}  (do not open it, do not print it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
