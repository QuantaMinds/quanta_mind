"""What does adding YAML to the ranked set cost the ranker? Measured before the scope changes.

WHAT: Replays the validated policy on the same six out-of-sample repositories twice — once over
      `.py` only, as it ships, and once over `.py` plus workflow YAML — and reports the miss rate,
      the alphabetical control, and how often a YAML file displaces source from the top three.
WHY:  **THE SHA ORACLE IS UNREACHABLE BECAUSE `.yml` IS NOT A REVIEWABLE SUFFIX, AND WIDENING THAT
      IS NOT FREE.** The ranker's whole evidence base — 1.21% against alphabetical's 3.12%, six
      unseen repositories, n = 2,400, p = 1.5e-07 — is measured over source files. Adding a suffix
      changes what gets ranked, and the validation does not automatically carry.

      **THE SPECIFIC RISK IS BUDGET DISPLACEMENT, AND IT HAS A DIRECTION.** Workflow files churn
      constantly and accumulate fix-word commits, so their prior is high. A change touching three
      source files and two workflows could see the workflows take top-three places from the source
      file a later fix actually returns to. **That is a cost to the half of the product that
      works, paid to reach a detector whose base rate is 0.24%.**

      **SO THE DISPLACEMENT IS COUNTED DIRECTLY, not inferred from the miss rate.** A miss rate that
      barely moves could still hide source files being pushed out and replaced by YAML files that
      happen to also be repaired.
IMPORTS: stdlib only. Local: `commit_stream` for the git read it reuses.
CONSUMED BY: read by a human; writes `results/yaml_scope.json`.
"""

from __future__ import annotations

import bisect
import collections
import json
import pathlib
import subprocess
import sys
from math import comb

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from commit_stream import ReadFailed

OUT = pathlib.Path(__file__).resolve().parent / "results" / "yaml_scope.json"
CLONES = pathlib.Path("/Users/dhanu/.claude/jobs/4cdada9b/tmp/churn-clones")
YEAR, WINDOW = 365 * 86400, 90 * 86400
FIXWORDS = ("fix", "bug", "revert", "hotfix", "regression", "broken")
MAX_FILES, MAX_EVENTS, BUDGET = 12, 400, 3
SOURCE = (".py",)
WIDENED = (".py", ".yml", ".yaml")


def stream(path: str, suffixes: tuple[str, ...]) -> list[tuple[int, str, frozenset[str]]]:
    """(timestamp, message, files) oldest-first, for whichever suffixes are in scope.

    A copy of `commit_stream.stream` with the suffix tuple lifted out. **Copied rather than the
    original parameterised**, because the original is what produced every published number here and
    editing it to run an experiment is how a validated read quietly becomes a different read.
    """
    done = subprocess.run(
        [
            "git",
            "-c",
            "core.commitGraph=false",
            "-C",
            path,
            "log",
            "--reverse",
            "--no-merges",
            "--name-only",
            "--format=%x00%ct%x01%s",
        ],
        capture_output=True,
        timeout=1800,
    )
    if done.returncode != 0:
        raise ReadFailed(f"{path}: git log exited {done.returncode}")
    out: list[tuple[int, str, frozenset[str]]] = []
    for chunk in done.stdout.decode("utf-8", errors="replace").split("\x00"):
        if not chunk.strip():
            continue
        head, _, body = chunk.partition("\n")
        ts, _, msg = head.partition("\x01")
        try:
            when = int(ts)
        except ValueError:
            continue
        files = frozenset(ln for ln in body.split("\n") if ln.strip() and ln.endswith(suffixes))
        if files:
            out.append((when, msg.lower(), files))
    return out


def prior(idx: dict[str, list[int]], unit: str, ts: int) -> int:
    lst = idx.get(unit, [])
    return bisect.bisect_left(lst, ts) - bisect.bisect_left(lst, ts - YEAR)


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / (2**n))


def score(commits: list, idx: dict) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for i, (ts, _msg, files) in enumerate(commits):
        if not (2 <= len(files) <= MAX_FILES):
            continue
        target: set[str] = set()
        for ts2, msg2, files2 in commits[i + 1 :]:
            if ts2 - ts > WINDOW:
                break
            if any(w in msg2 for w in FIXWORDS):
                target |= files2 & files
        if not target:
            continue
        counts = {f: prior(idx, f, ts) for f in files}
        if len(set(counts.values())) == 1:
            continue
        ranked = sorted(files, key=lambda f: (-counts[f], f))
        top = ranked[:BUDGET]
        events.append(
            {
                "hit": bool(set(top) & target),
                "alpha_hit": bool(set(sorted(files)[:BUDGET]) & target),
                "yaml_in_top": sum(1 for f in top if f.endswith((".yml", ".yaml"))),
                "source_pushed_out": sum(
                    1 for f in ranked[BUDGET:] if f.endswith(".py") and f in target
                ),
            }
        )
        if len(events) >= MAX_EVENTS:
            break
    return events


def main() -> int:
    out: dict[str, dict[str, list]] = {}
    for folder in sorted(CLONES.iterdir()):
        if not (folder / ".git").is_dir():
            continue
        out[folder.name] = {}
        for label, suffixes in (("source_only", SOURCE), ("with_yaml", WIDENED)):
            commits = stream(str(folder), suffixes)
            idx: dict[str, list[int]] = collections.defaultdict(list)
            for ts, _, files in commits:
                for f in files:
                    idx[f].append(ts)
            events = score(commits, idx)
            out[folder.name][label] = events
            miss = sum(1 for e in events if not e["hit"]) / max(1, len(events))
            print(
                f"  {folder.name:<28} {label:<12} n={len(events):<4} miss {miss:>6.2%}", flush=True
            )

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\n  {'scope':<14}{'events':>8}{'ours miss':>11}{'alpha miss':>12}{'p':>10}")
    for label in ("source_only", "with_yaml"):
        ev = [e for r in out.values() for e in r.get(label, [])]
        if not ev:
            continue
        miss = sum(1 for e in ev if not e["hit"]) / len(ev)
        am = sum(1 for e in ev if not e["alpha_hit"]) / len(ev)
        b = sum(1 for e in ev if e["hit"] and not e["alpha_hit"])
        c = sum(1 for e in ev if not e["hit"] and e["alpha_hit"])
        print(f"  {label:<14}{len(ev):>8}{miss:>11.2%}{am:>12.2%}{mcnemar(b, c):>10.2e}")

    wide = [e for r in out.values() for e in r.get("with_yaml", [])]
    if wide:
        took = sum(1 for e in wide if int(e["yaml_in_top"]) > 0)
        pushed = sum(1 for e in wide if int(e["source_pushed_out"]) > 0)
        yshare = f"{took}/{len(wide)} = {took / len(wide):.0%}"
        pshare = f"{pushed}/{len(wide)} = {pushed / len(wide):.1%}"
        print("\n  DISPLACEMENT, counted directly rather than inferred from the miss rate:")
        print(f"    events where YAML took a top-3 place : {yshare}")
        print(f"    events where a REPAIRED source file was pushed out : {pshare}")
    print(f"\n  -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
