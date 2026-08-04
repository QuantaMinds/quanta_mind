"""The exposure variable: could the instrument resolve callers of the changed symbol?

WHAT: Joins the census (denominator) against PyCG's edges (numerator) at the
      PARENT commit and assigns each changed symbol to an arm.
WHY:  Three design decisions carry the study, and each is pre-registered.

      1. Parent commit only. Classifying against the merged state leaks the
         outcome into the exposure and manufactures a correlation. RUNBOOK section
         1.2 calls it "the single most likely way to fake a positive result by
         accident". This module never sees a merged tree — run_pipeline.py checks
         out the parent and nothing here can override that.

      2. Amendment A6 — granularity. PyCG emits a SET of callees per caller, so a
         function calling S both directly and through getattr yields ONE edge and
         both sites read as resolved. Call-site granularity is therefore not
         measurable with this instrument; on single-site (caller, symbol) pairs it
         is measurable exactly. The primary analysis uses only those. Multi-site
         pairs go to a bounded sensitivity analysis, coded both ways.

      3. Amendment A7 — a parse failure is attrition, not an arm. Only TIMEOUT and
         OOM reach UNANALYZED_RESOURCE, which RUNBOOK section 4.4 reads to decide
         whether this is a scalability product.

      Matching is deliberately LENIENT about the package prefix. PyCG names the
      same function two ways — `sub.deep.helper_fn` at its definition site and
      `acme.sub.deep.helper_fn` where an import resolved it — which is DyPyBench's
      name-resolution mismatch, measured at ~12%. Strict equality would mark
      nested-package callers unresolved wholesale and inflate exposure. Leniency
      errs toward UNEXPOSED, i.e. toward the null, which is the conservative
      direction and the same one A6 already documents.
IMPORTS: phase0.census, phase0.run_graph, phase0.pycg_failure, phase0.scope,
      phase0.syntax. Never phase0.scan_outcome — see run_pipeline.py.
CONSUMED BY: run_pipeline.py, build_table.py; tests/test_classify_exposure.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from phase0.census import CallSite
from phase0.pycg_failure import GraphStatus


class Exposure(Enum):
    """Three arms. Never two, and never four."""

    EXPOSED = "exposed"  # a single-site pair whose edge PyCG did not emit
    UNEXPOSED = "unexposed"  # every single-site pair has its edge
    UNANALYZED_RESOURCE = "unanalyzed_resource"  # timeout or OOM, per A7


class Cardinality(Enum):
    """Whether a (caller, symbol) pair is measurable exactly. Amendment A6."""

    SINGLE = "single"  # one matching site: edge presence settles it
    MULTI = "multi"  # two or more: PyCG's set collapses them


@dataclass(frozen=True, slots=True)
class PairVerdict:
    """One caller/symbol pair, and whether the instrument could speak to it."""

    caller: str
    symbol: str
    site_count: int
    edge_present: bool

    @property
    def cardinality(self) -> Cardinality:
        return Cardinality.SINGLE if self.site_count == 1 else Cardinality.MULTI


@dataclass(frozen=True, slots=True)
class SymbolExposure:
    """The arm for one changed symbol, plus the diagnostics A6 requires."""

    symbol: str
    primary: Exposure | None  # None: no single-site pair, so outside the primary table
    sensitivity_low: Exposure | None  # multi-site coded UNEXPOSED
    sensitivity_high: Exposure | None  # multi-site coded EXPOSED
    single_site_pairs: int
    multi_site_pairs: int
    matched_sites: tuple[CallSite, ...]  # sampled for the false-match hand-check

    @property
    def in_primary_table(self) -> bool:
        return self.primary is not None

    @property
    def bounds_agree(self) -> bool:
        """When both bounds agree, A6's collapse provably changed no conclusion."""
        return self.sensitivity_low is self.sensitivity_high


def _matches(edge_target: str, symbol_fqn: str) -> bool:
    """True if an edge target names this symbol, allowing for package-prefix drift.

    Accepts `a.b.validate` against `b.validate` and the reverse, because PyCG
    names a function differently at its definition site than where an import
    resolved it. Requires a dot boundary so `revalidate` never matches `validate`.
    """
    if edge_target == symbol_fqn:
        return True
    return edge_target.endswith(f".{symbol_fqn}") or symbol_fqn.endswith(f".{edge_target}")


def _pairs(
    symbol_fqn: str,
    short_name: str,
    sites: list[CallSite],
    edges: dict[str, set[str]],
) -> list[PairVerdict]:
    """Group matching call sites by caller and ask the graph about each group."""
    grouped: dict[str, list[CallSite]] = {}
    for site in sites:
        if site.is_builtin or site.callee_name != short_name:
            continue
        grouped.setdefault(site.enclosing, []).append(site)

    verdicts: list[PairVerdict] = []
    for caller, group in grouped.items():
        targets = edges.get(caller, set())
        verdicts.append(
            PairVerdict(
                caller=caller,
                symbol=symbol_fqn,
                site_count=len(group),
                edge_present=any(_matches(t, symbol_fqn) for t in targets),
            )
        )
    return verdicts


def _arm(verdicts: list[PairVerdict], include_multi_as_exposed: bool | None) -> Exposure | None:
    """Reduce pair verdicts to one arm.

    include_multi_as_exposed: None restricts to single-site pairs (the primary
    analysis); True and False code multi-site pairs as the two sensitivity bounds.
    """
    considered = [
        v
        for v in verdicts
        if v.cardinality is Cardinality.SINGLE or include_multi_as_exposed is not None
    ]
    if not considered:
        return None

    for verdict in considered:
        if verdict.cardinality is Cardinality.MULTI and include_multi_as_exposed:
            return Exposure.EXPOSED
        if verdict.cardinality is Cardinality.SINGLE and not verdict.edge_present:
            return Exposure.EXPOSED
    return Exposure.UNEXPOSED


def classify(
    symbol_fqn: str,
    short_name: str,
    sites: list[CallSite],
    edges: dict[str, set[str]],
    status: GraphStatus,
    sample: int = 5,
) -> SymbolExposure:
    """Assign one changed symbol to an arm, using parent-commit state only.

    A7: a syntax failure must never reach here — run_pipeline.py excludes it as
    corpus attrition before classification, so this asserts rather than guesses.
    """
    if status.is_attrition:
        raise ValueError(
            f"{symbol_fqn}: SYNTAX_UNSUPPORTED is corpus attrition (A7) and has no arm. "
            f"Exclude it in run_pipeline.py rather than classifying it."
        )

    if status.is_resource_exhaustion:
        return SymbolExposure(
            symbol=symbol_fqn,
            primary=Exposure.UNANALYZED_RESOURCE,
            sensitivity_low=Exposure.UNANALYZED_RESOURCE,
            sensitivity_high=Exposure.UNANALYZED_RESOURCE,
            single_site_pairs=0,
            multi_site_pairs=0,
            matched_sites=(),
        )

    verdicts = _pairs(symbol_fqn, short_name, sites, edges)
    matched = tuple(s for s in sites if not s.is_builtin and s.callee_name == short_name)

    return SymbolExposure(
        symbol=symbol_fqn,
        primary=_arm(verdicts, include_multi_as_exposed=None),
        sensitivity_low=_arm(verdicts, include_multi_as_exposed=False),
        sensitivity_high=_arm(verdicts, include_multi_as_exposed=True),
        single_site_pairs=sum(1 for v in verdicts if v.cardinality is Cardinality.SINGLE),
        multi_site_pairs=sum(1 for v in verdicts if v.cardinality is Cardinality.MULTI),
        matched_sites=matched[:sample],
    )
