"""D6b follow-up: keep the candidate TEXTS, so the mechanism can be tested rather than asserted.

WHAT: re-runs both arms on a sample of the changes and writes every candidate finding to disk.
WHY:  **THE FIRST RUN SAVED COUNTS AND DISCARDED THE EVIDENCE.** Two rival explanations produce the
      identical table — (a) context makes the model report goal-achievement findings a DEFECT list
      scores as wrong, and (b) context is simply noise that degrades output quality — and nothing
      in `d6b_human_context.json` separates them, because the finding texts were never written
      down. An adversarial audit named that gap; this closes it.

      **IT ALSO TESTS THE JUDGE.** If the context arm's findings are systematically longer or more
      abstract, a judge that matches them to golden defects less reliably would depress the context
      arm's true positives for a reason that has nothing to do with the reviewer. Length is
      measured here so that confounder is a number rather than a worry.
IMPORTS: bench_reviewer, martian_corpus, client (research); quantamind.ingest.context.
CONSUMED BY: `docs/findings/reviewer/D6B_HUMAN_CONTEXT_NULL_2026-08.md`.
"""

from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "vertex"))

import bench_reviewer as reviewer
import martian_corpus as corpus
from client import Client
from d6b_population import context_for
from run_d6b import CONTEXT_BLOCK, MODEL

OUT = pathlib.Path(__file__).resolve().parent / "results" / "d6b_texts.json"

# The changes where the arms differed most in each direction, plus two where they tied. Chosen to
# span the range rather than to favour either explanation.
SAMPLE = {14740, 32918, 11059, 90045, 77754, 22345, 8330, 37038}


def main() -> int:
    client = Client(MODEL)
    out = []
    for pr in corpus.pulls():
        parts = str(pr["original"]).rstrip("/").split("/")
        if len(parts) < 5 or "pull" not in parts or not parts[-1].isdigit():
            continue
        number = int(parts[-1])
        if number not in SAMPLE:
            continue
        repo = f"{parts[3]}/{parts[4]}"
        context = context_for(repo, number)[0]
        diff = corpus.diff(str(pr["original"]))
        title = str(pr["title"])
        control, _ = reviewer.review(client, title, diff)
        armed, _ = reviewer.review(
            client, title, diff, template=reviewer.PROMPT + CONTEXT_BLOCK.format(context=context)
        )
        out.append(
            {
                "repo_file": str(pr["repo_file"]),
                "number": number,
                "golden": list(pr["golden"]),
                "control": control,
                "context": armed,
            }
        )
        print(
            f"  {repo.split('/')[-1][:12]:12s} #{number:<7} "
            f"control={len(control):2d} context={len(armed):2d}"
        )
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\n  wrote {len(out)} changes to {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
