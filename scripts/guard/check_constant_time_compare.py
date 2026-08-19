"""The signature comparison must stay constant-time, which no unit test can observe.

WHAT: Parses `serve/webhook_github.py` and fails unless the HMAC digest is compared with
      `hmac.compare_digest` and never with `==` or `!=`.
WHY:  **Swapping `compare_digest` for `==` leaves every test in the suite passing** — verified by
      doing it. A byte-by-byte compare returns False at the first mismatched byte, so an attacker
      who can measure response times can recover the expected signature one byte at a time. GitHub
      says so directly: *"Never use a plain `==` operator. Instead consider using a method like
      `secure_compare` or `crypto.timingSafeEqual`, which performs a 'constant time' string
      comparison to help mitigate certain timing attacks."*

      A timing test would be the direct check and is unreliable in CI — a loaded runner produces
      noise far larger than the signal, and a flaky security test gets deleted. This is crude by
      comparison: it checks the SHAPE of the code rather than its behaviour. But it fails when
      someone changes the comparison, which is the one thing the docstring could not do.
IMPORTS: stdlib only (ast, pathlib, sys).
CONSUMED BY: `just check` via the `guards` recipe.
"""

from __future__ import annotations

import ast
import pathlib
import sys

TARGET = pathlib.Path("src/quantamind/serve/webhook_github.py")
REQUIRED = "compare_digest"
# Names that hold a digest. An equality test against any of them is the defect.
DIGEST_NAMES = frozenset({"expected", "offered", "signature", "digest"})


def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[1] if len(argv) > 1 else ".").resolve()
    path = root / TARGET
    if not path.exists():
        print(f"[constant-time] {TARGET} not found — the guard is watching nothing")
        return 1

    tree = ast.parse(path.read_text())
    uses_compare_digest = any(
        isinstance(node, ast.Attribute) and node.attr == REQUIRED for node in ast.walk(tree)
    ) or any(isinstance(node, ast.Name) and node.id == REQUIRED for node in ast.walk(tree))

    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, ast.Eq | ast.NotEq) for op in node.ops):
            continue
        # Comparing len(digest) is a length check, not a value comparison: the length of a
        # fixed-width hex digest is not secret and leaks nothing. Only the value matters.
        inside_len = {
            n.id
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "len"
            for n in ast.walk(call)
            if isinstance(n, ast.Name)
        }
        touched = {
            n.id
            for n in ast.walk(node)
            if isinstance(n, ast.Name) and n.id in DIGEST_NAMES and n.id not in inside_len
        }
        if touched:
            offenders.append(f"line {node.lineno}: == or != against {sorted(touched)}")

    if not uses_compare_digest:
        print(f"[constant-time] {TARGET} no longer calls {REQUIRED}().")
        print("  A byte-by-byte compare leaks the expected signature through response timing, and")
        print(
            "  no test in this repository can see the difference. GitHub: 'Never use a plain =='."
        )
        return 1
    if offenders:
        print(f"[constant-time] {TARGET} compares a digest with == or !=:")
        for offender in offenders:
            print(f"    {offender}")
        print("  Use hmac.compare_digest. A timing side channel passes every test we have.")
        return 1
    print("[constant-time] ok — the signature comparison is constant-time")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
