"""The Martian offline corpus: golden comments, rival candidates, and the diffs under review.

WHAT: Loads the 50 pull requests and their human-verified issue lists from a checked-out copy of
      `withmartian/code-review-benchmark`, loads the candidates every other tool produced, and
      fetches each pull request's diff from its ORIGINAL repository.
WHY:  The comparison is only like-for-like if every arm is scored against the same ground truth on
      the same changes. Reading the golden comments and the rivals' candidates from their
      repository rather than transcribing them is what makes that checkable by someone else.

      THE DIFF COMES FROM `original_url`, NOT `url`. The golden file's `url` points at a fork in
      `ai-code-review-evaluation/` created so the tools could be run; several carry an
      `az_comment` saying the reviewed commit is not in the repo. The original pull request is the
      change the golden comments describe.
IMPORTS: stdlib only (json, pathlib, subprocess).
CONSUMED BY: `run.py` in this package.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

# **IN THE REPOSITORY, NOT IN /private/tmp.** This pointed at a scratchpad belonging to a dead
# session. Such a path does not fail loudly when the OS clears it -- the file is simply gone and the
# run reports a smaller denominator or a clean skip. `_assert_intact()` below refuses instead.
BENCH = pathlib.Path(__file__).resolve().parent / "martian" / "data"
CACHE = pathlib.Path(
    "/private/tmp/claude-501/-Users-dhanu-Documents-SaaS-quanta-mind/"
    "6063c1dc-2654-4975-b12a-47677aad0026/scratchpad/bench/diffs"
)
JUDGE_DIR = "anthropic_claude-opus-4-5-20251101"
MAX_DIFF_CHARS = 180_000


def _assert_intact() -> None:
    """Refuse to read a corpus that has moved, vanished or changed since it was checksummed."""
    root = BENCH.parent
    stamp = root / "CHECKSUM"
    if not BENCH.is_dir() or not stamp.is_file():
        raise CorpusMissing(f"{BENCH} or its CHECKSUM is absent; the benchmark data is not here")
    files = sorted(p for p in BENCH.rglob("*") if p.is_file() and p.suffix in (".json", ".py"))
    digest = hashlib.sha256()
    for f in files:
        digest.update(hashlib.sha256(f.read_bytes()).hexdigest().encode() + b"  " + str(f).encode())
    # The recipe in martian/README.md hashes `shasum` output lines; reproduce it exactly.
    lines = "".join(
        f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(root)}\n" for f in files
    )
    got = hashlib.sha256(lines.encode()).hexdigest()
    want = stamp.read_text().strip()
    if got != want:
        raise CorpusChanged(
            f"benchmark data does not match {stamp}: {got[:12]} vs {want[:12]}. "
            f"Regenerate the checksum only if the change was deliberate."
        )


class CorpusMissing(RuntimeError):
    """The benchmark data is not where it is supposed to be."""


class CorpusChanged(RuntimeError):
    """The benchmark data changed under a run that depends on it."""


class FetchFailed(RuntimeError):
    """A diff that could not be read. Never silently an empty diff."""


def pulls() -> list[dict[str, object]]:
    """The 50 pull requests, each with its golden comments and its original URL."""
    out: list[dict[str, object]] = []
    for f in sorted((BENCH / "golden_comments").glob("*.json")):
        for pr in json.loads(f.read_text()):
            out.append(
                {
                    "repo_file": f.stem,
                    "key": pr["url"],  # the benchmark's own identifier, used to join to rivals
                    "original": pr.get("original_url") or pr["url"],
                    "title": pr.get("pr_title", ""),
                    "golden": [c["comment"] for c in pr["comments"]],
                }
            )
    return out


def rival_candidates(tool: str) -> dict[str, list[str]]:
    """{benchmark pull-request url: [candidate text]} for one already-evaluated tool."""
    data = json.loads((BENCH / "results" / JUDGE_DIR / "candidates.json").read_text())
    out: dict[str, list[str]] = {}
    for url, tools in data.items():
        if tool in tools:
            out[url] = [c["text"] for c in tools[tool] if c.get("text")]
    return out


def published(tool: str) -> tuple[int, int, int]:
    """(true positives, false positives, false negatives) as THEIR judge scored this tool.

    Used only for the calibration bar. If our judge disagrees with this wildly, the run measures
    our judge and not our reviewer, and the comparison is void rather than interesting.
    """
    ev = json.loads((BENCH / "results" / JUDGE_DIR / "evaluations.json").read_text())
    tp = fp = fn = 0
    for _url, tools in ev.items():
        r = tools.get(tool)
        if not r or r.get("skipped"):
            continue
        tp += len(r.get("true_positives", []))
        fp += len(r.get("false_positives", []))
        fn += len(r.get("false_negatives", []))
    return tp, fp, fn


def diff(original_url: str) -> str:
    """The unified diff, cached on disk. Raises rather than returning an empty string."""
    CACHE.mkdir(parents=True, exist_ok=True)
    slug = original_url.replace("https://github.com/", "").replace("/", "_")
    path = CACHE / f"{slug}.diff"
    if path.exists() and path.stat().st_size > 0:
        return path.read_text()[:MAX_DIFF_CHARS]

    # Discourse's golden file identifies its changes by COMMIT, not by pull request -- all ten of
    # its entries are /commit/<sha>. Splitting every URL on "/pull/" produced a nonsense endpoint
    # and ten fetch failures that looked like the reviewer declining to review.
    bare = original_url.replace("https://github.com/", "")
    if "/pull/" in bare:
        repo, _, tail = bare.partition("/pull/")
        endpoint = f"repos/{repo}/pulls/{tail}"
    elif "/commit/" in bare:
        repo, _, tail = bare.partition("/commit/")
        endpoint = f"repos/{repo}/commits/{tail}"
    else:
        raise FetchFailed(f"{original_url}: neither a pull request nor a commit URL")

    p = subprocess.run(
        ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.v3.diff"],
        capture_output=True,
        timeout=180,
    )
    if p.returncode != 0:
        raise FetchFailed(f"{original_url}: gh exited {p.returncode}: {p.stderr[:160]!r}")
    text = p.stdout.decode("utf-8", "replace")
    if not text.strip():
        raise FetchFailed(f"{original_url}: gh returned an empty diff at exit 0")
    path.write_text(text)
    return text[:MAX_DIFF_CHARS]
