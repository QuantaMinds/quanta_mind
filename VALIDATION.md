# Validation Doctrine

> A green test suite is the most convincing lie a codebase can tell.
>
> This document defines what we accept as evidence that the system works. Read it before
> writing your first test. Every rule here has a mechanical enforcer; where it does not,
> it is marked **ADVISORY** and you should treat it as an unfixed gap.

---

## 1. The core distinction

**A passing test proves the code did not crash. It does not prove the data is right.**

These are two different claims and we test them in two different places:

| Claim | Where | Command | What it actually proves |
|---|---|---|---|
| The code is well-formed | `tests/unit/`, `tests/property/` | `just check` | Types hold, invariants hold, units behave against controlled input |
| **The data is right** | `tests/live/` + golden diff | `just verify` | The real pipeline, on a real repository, produced output a human reviewed and approved |

`just check` being green means nothing about correctness of output. Say this out loud in
review when someone claims otherwise.

---

## 2. The five test tiers

### Tier 1 — Unit (`tests/unit/`, <10s)
Hermetic, fast, controlled input. Mocks permitted here and **only** here.
**Must assert on values, never on truthiness.** `assert result` is banned by
`check_assert_quality.py`; `assert result.confidence is Confidence.FRAMEWORK` is what we want.

### Tier 2 — Property (`tests/property/`, <2min)
Hypothesis. These encode the invariants from `ARCHITECTURE.md §6`. They are the only
tests that can find bugs nobody thought to look for.

```python
@given(pack=packs())
def test_no_edge_lacks_provenance(pack: Pack) -> None:
    """Invariant 1. The one bug that would destroy the product's reason to exist."""
    for edge in pack.edges:
        assert edge.provenance, f"unlabeled edge {edge.src}->{edge.dst}"
        assert edge.confidence in Confidence

@given(pack=packs())
def test_call_sites_are_conserved(pack: Pack) -> None:
    """Invariant 3. If a call site vanishes between parse and label, we lost data
    silently — the exact failure mode we sell against."""
    labeled = sum(pack.counts[c] for c in Confidence)
    assert labeled == pack.total_non_builtin_call_sites
```

### Tier 3 — Live (`tests/live/`, <10min)
The real pipeline against pinned real repositories. **Importing any mocking library in
this directory is a CI failure.** Fixtures are git submodules pinned to a SHA, chosen to
span the failure modes we know about:

| Fixture | Why it is in the suite |
|---|---|
| `django/django` | URL dispatch, signals, metaclasses — the framework-resolver target |
| `celery/celery` | string-dispatched tasks, the canonical invisible edge |
| `pallets/flask` | wrapper functions, the documented name-resolution mismatch |
| `sqlalchemy/sqlalchemy` | descriptors, ORM lazy relations |
| A ≥1M-line internal monorepo | the scale case where PyCG historically OOM'd |
| A repo with a deliberately broken test suite | proves graceful degradation when Tier 4 is unavailable |

### Tier 4 — Data verification (`just verify-data`)
Runs the pipeline, then **diffs the produced pack against a checked-in golden pack**.
Any change to the golden file requires a human reviewer to state, in the PR, why the
output changed and whether the new output is more correct.

This is the rule the whole doctrine turns on: **the golden file is reviewed, not
regenerated.** `--update-golden` exists, is logged, and any PR that uses it without a
reviewer comment explaining the delta is rejected.

### Tier 5 — Adversarial / silent-failure suite (`tests/adversarial/`)
See §4. This is the tier that separates us from every competitor.

---

## 3. What we log, and why logs are test output

Every pipeline run emits structured JSON at three points. Live tests assert on the logs,
not only on the return value — because the most dangerous failures produce a plausible
return value.

```json
{"stage":"resolve","resolver":"frameworks.celery","sites_seen":412,
 "sites_resolved":389,"sites_unresolved":23,"duration_ms":1840,"pack_sha":"a3f9c1"}
```

**Assertions live tests make on logs:**

- `sites_seen` at the input of a stage equals `sites_seen` at the output of the previous
  stage. A silent drop between stages is invisible in the final graph.
- No stage reports `sites_resolved == sites_seen` on a real repository. A resolver
  claiming 100% is a resolver that is lying — the soundiness literature says no analyzer
  achieves this, so 100% means our accounting is broken.
- `duration_ms` stays within 3× of the golden baseline. A 10× slowdown usually means an
  accidental full-repo walk, which will OOM on a customer's monorepo.
- Every `Unresolved` record carries a non-empty `construct`. "Unresolved for unknown
  reason" is useless to the customer and is treated as a bug.

---

## 4. The silent-failure suite

Small errors here cause large, invisible damage downstream. Each of these is a test
someone must write before the corresponding resolver ships.

| # | Silent failure | Blast radius | Detection |
|---|---|---|---|
| 1 | An edge is emitted with `confidence` defaulted rather than derived | Agent trusts a guess. Product's core claim is false. | Property test: no default is reachable — `Confidence` has no default in the dataclass |
| 2 | A call site is dropped between `parse` and `label` | Coverage looks *higher* than reality. Worst possible direction of error. | Log conservation assertion (§3) |
| 3 | Builtin calls counted in the coverage denominator | Coverage is deflated ~59% and the number becomes meaningless | Golden diff on a fixture with a known builtin count |
| 4 | Name resolution mismatch between two resolvers | Same function under two names → "0 callers" for a live function | Cross-resolver identity test: every symbol has exactly one canonical FQN |
| 5 | Framework resolver silently disabled by a version bump | Whole class of edges vanishes; no error | Live test asserts a minimum edge count per framework resolver |
| 6 | Stale pack served as fresh | Agent acts on a graph that predates the change it is making | Every response carries `pack_sha`; live test asserts it matches `git rev-parse HEAD` |
| 7 | Runtime tracer silently attaches to nothing | Runtime edges = 0, reported as "no dynamic edges found" | Assert tracer observed ≥1 edge before accepting a run as valid |
| 8 | Timeout on a subtree reported as "no edges" instead of `UNANALYZED` | Customer believes a region is clean when it was never looked at | Fault-injection test: force a timeout, assert label is `UNANALYZED` |
| 9 | Pack contains a fragment of source text | Contract and security-review breach | `verify-no-source-leak` (invariant 6) — proof, not assertion |
| 10 | Non-deterministic index → golden diffs become noise → people stop reading them | The entire review discipline collapses | `verify-determinism`, 3 runs byte-identical |

**Failure 10 is the one that kills the culture.** If golden diffs are noisy, reviewers
rubber-stamp them, and Tier 4 silently degrades into Tier 1. Determinism is not a nicety.

---

## 5. Fault injection

`tests/adversarial/` deliberately breaks the environment and asserts we degrade *loudly*:

- kill the LSP subprocess mid-run → expect `UNRESOLVED`, not a crash, not silence
- give the tracer a repo whose tests all fail → expect coverage reported without the
  runtime tier and a warning, not a zero-runtime pack presented as complete
- feed a file with a syntax error → expect `UNANALYZED` for that file only
- feed a 2M-line generated file → expect a timeout labelled `UNANALYZED`, not an OOM
- corrupt the pack on disk → expect a checksum failure, never a partial read

---

## 6. Before you open a PR

```bash
just verify              # must be green
just verify-determinism  # must be green if you touched store/ or label/
```

Then answer this in the PR description, in writing:

> **What could still silently fail after this change, and why do I believe it will not?**

A PR that answers "nothing" is sent back. Everything can silently fail; the question is
whether you looked.
