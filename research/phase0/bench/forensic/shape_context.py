"""Does telling the model what this change looks like against the repository help it review?

WHAT: Runs the shipped reviewer over the same 50 benchmark pull requests twice — once as it ships,
      once with the change's shape prepended as context — and scores both against the same 173
      human-verified defects with the same judge.
WHY:  **THE MODEL CANNOT COMPUTE ANY OF THIS FROM A DIFF.** "This repository's median change is two
      files; this one is fourteen", "these files carry 25 of the 33 commits this month", "four of
      the twelve people active this month have touched them" — none of it is in the text it reads.
      That makes it genuinely new information rather than more of the same code.

      **AND THE PRIOR IS BAD, WHICH IS EXACTLY WHY THIS IS MEASURED RATHER THAN ASSUMED.** Five
      prompt and context levers have moved nothing here — anchor repair, structured context, a
      rejection filter, hunk expansion, and three prompt-direction arms. An August 2026 result on
      Go code review found adding a THIRD context type *underperformed* two by 0.72 points, with
      the authors' own reading that "additional context can redirect attention away from
      recoverable issues". A second 2026 paper puts the mechanism plainly: context augmentation
      "is not merely a retrieval problem... even when useful context is successfully retrieved, the
      model may still fail to prioritize or exploit it."

      **SO THE HYPOTHESIS IS THAT SHAPE IS DIFFERENT IN KIND, AND THE BAR IS SET AGAINST THE
      MEASURED NOISE FLOOR RATHER THAN AGAINST ZERO.**

BARS, FIXED HERE BEFORE THE RUN:
      **PASS** — defects found rises by more than the judge's replicate spread of 2.1 points, AND
      comments emitted does not rise by more than 15%. Finding more by saying more is the trade
      this project has measured five times and does not count.
      **INCONCLUSIVE** — inside the 2.1-point spread.
      **FAIL** — defects found falls, or the comment count rises more than 15% for any gain.
IMPORTS: stdlib; local `martian_corpus`, `bench_reviewer`, `judge`; the product's `change_shape`.
CONSUMED BY: read by a human; writes `results/shape_context.json`.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "vertex"))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[3] / "src"))

import bench_reviewer as br  # noqa: E402
import judge  # noqa: E402
import martian_corpus as mc  # noqa: E402
from borrowed_clones import root as clone_root  # noqa: E402
from client import Client  # noqa: E402
from quantamind.ingest.change_shape import shape  # noqa: E402
from quantamind.serve.working_clone import CloneFailed, ensure  # noqa: E402

OUT = HERE.parent / "results" / "shape_context.json"


def context_for(clone: pathlib.Path, sha: str, changed: list[str]) -> str:
    """The shape sentence the model would be given. Facts only, no instruction on what to do."""
    got = shape(clone, sha, changed)
    parts = [
        f"This change touches {got.files} file(s) and {got.lines} line(s). "
        f"This repository's median change is {got.median_files} file(s) and "
        f"{got.median_lines} line(s)."
    ]
    if got.churn:
        parts.append(f"These files changed {got.churn} times in the last 30 days.")
    if got.hands:
        parts.append(f"{got.hands} other people have edited them in that time.")
    if got.unusual:
        parts.append("Unusual for this repository: " + "; ".join(got.unusual) + ".")
    return " ".join(parts)


def main() -> int:
    mc._assert_intact()
    client = Client("gemini-2.5-pro")
    pulls = [p for p in mc.pulls() if p.get("golden")]
    # **THE SHARED ROOT, NOT A FRESH ONE PER RUN.** A new mkdtemp every time is what put
    # 11 GB of duplicate clones on the disk; this reuses them and bounds the total.
    root = clone_root()
    arms: dict[str, dict[str, list[str]]] = {"PLAIN": {}, "WITH_SHAPE": {}}
    contexts: dict[str, str] = {}

    for pull in pulls:
        key = str(pull["key"])
        url = str(pull["original"])
        repo = "/".join(url.split("/")[3:5])
        try:
            diff = mc.diff(url)
        except mc.FetchFailed:
            continue
        note = ""
        try:
            clone = ensure(repo, root)
            sha = subprocess.run(
                ["git", "-C", str(clone), "log", "--format=%H", "-1"],
                capture_output=True,
                text=True,
                timeout=120,
            ).stdout.strip()
            changed = [
                x
                for x in subprocess.run(
                    ["git", "-C", str(clone), "show", "--name-only", "--format=", sha],
                    capture_output=True,
                    text=True,
                    timeout=120,
                ).stdout.split()
                if x.strip()
            ]
            note = context_for(clone, sha, changed)
        except (CloneFailed, subprocess.TimeoutExpired) as exc:
            print(f"  {repo}: {str(exc)[:60]}", flush=True)
        contexts[key] = note

        for arm in ("PLAIN", "WITH_SHAPE"):
            body = diff if arm == "PLAIN" or not note else f"{note}\n\n{diff}"
            try:
                issues, _ = br.review(client, str(pull["title"]), body)
            except br.ReviewFailed:
                continue
            arms[arm][key] = issues
        print(
            f"    {url[-26:]:>26}  plain {len(arms['PLAIN'].get(key, [])):>2}  "
            f"shape {len(arms['WITH_SHAPE'].get(key, [])):>2}",
            flush=True,
        )

    scored: dict[str, dict[str, int]] = {}
    for arm, cands in arms.items():
        covered = emitted = 0
        for pull in pulls:
            key = str(pull["key"])
            texts = cands.get(key, [])
            if not texts:
                continue
            got = judge.verdicts(client, list(pull["golden"]), texts)
            covered += len(got["tp"])
            emitted += len(texts)
        scored[arm] = {"defects_found": covered, "comments": emitted}
        print(f"\n  {arm:<12} {covered} of 173 defects, {emitted} comments", flush=True)

    OUT.write_text(json.dumps({"scored": scored, "contexts": contexts, "arms": arms}, indent=1))
    a, b = scored.get("PLAIN", {}), scored.get("WITH_SHAPE", {})
    if a and b:
        d = (b["defects_found"] - a["defects_found"]) / 173 * 100
        c = (b["comments"] - a["comments"]) / max(1, a["comments"]) * 100
        print(
            f"\n  defects found : {a['defects_found']} -> {b['defects_found']}  ({d:+.1f} points)"
        )
        print(f"  comments      : {a['comments']} -> {b['comments']}  ({c:+.0f}%)")
        print("\n  BAR: >+2.1 points AND comments up no more than 15%.")
        verdict = "PASS" if d > 2.1 and c <= 15 else ("FAIL" if d < 0 or c > 15 else "INCONCLUSIVE")
        print(f"  -> {verdict}")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
