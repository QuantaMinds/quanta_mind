"""Statistics used by `verify_claims.py`, separated at the file-length cap.

WHAT: Wilson intervals, exact McNemar, Cohen's kappa and the hypergeometric chance baseline.
WHY:  These are the instruments every number in this project is expressed in, and keeping them in
      one place means a claim and its recomputation cannot drift apart through two copies of a
      formula. Split from the checker itself because the checker is a list of assertions and this
      is arithmetic -- one public concern each.
IMPORTS: stdlib only (math).
CONSUMED BY: `verify_claims.py`.
"""

from __future__ import annotations

from math import comb, sqrt


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mcnemar(b: int, c: int) -> float:
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2**n)


def kappa(a: dict[str, str], b: dict[str, str], cats: tuple[str, ...]) -> float:
    n = len(a)
    po = sum(1 for k in a if a[k] == b[k]) / n
    pe = sum(
        (sum(1 for k in a if a[k] == c) / n) * (sum(1 for k in b if b[k] == c) / n) for c in cats
    )
    return (po - pe) / (1 - pe)


def chance(n: int, t: int, budget: int = 3) -> float:
    """Exact hypergeometric probability that a random pick of `budget` hits one of `t` targets."""
    return 1.0 if n - t < budget else 1 - comb(n - t, budget) / comb(n, budget)
