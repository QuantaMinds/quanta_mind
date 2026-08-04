# qmctx — QuantaMind Context

**The layer that tells a coding agent what it does not know about your repository.**

Static analysis is unsound by design — every code-intelligence tool deliberately ignores
language features it cannot handle, and none of them says so. `qmctx` measures that
unsoundness per call site, labels every edge with how confident we are and why, and serves
the result over MCP so Claude Code, Codex and Cursor can **abstain instead of guessing.**

Your source code never leaves your network. We store derived facts, never code.

---

## The problem in one example

```python
class BasePaymentHandler:
    def validate(self, req): ...        # you change this

class StripeHandler(BasePaymentHandler):
    def validate(self, req):
        super().validate(req)           # invisible to static analysis
        ...
```

Your agent greps `validate`, finds three direct callers, edits them, and ships. Six
`super()` edges were never in the graph. The published measurement: state-of-the-art
static Python call graphs miss roughly half the edges observed at runtime, and `super()`
calls are absent entirely. Nothing in your toolchain tells you this happened.

With `qmctx`:

```
callers_of("BasePaymentHandler.validate")

  RESOLVED     3   direct call sites
  FRAMEWORK    6   super() chain — StripeHandler, PaypalHandler, +4
  AMBIGUOUS    2   flow-insensitive; candidates listed, not chosen
  UNRESOLVED   1   plugins/legacy.py:88 — getattr(mod, cfg["handler"])
                   → cannot be determined statically. Human review required.

  coverage(payments/) = 91%   pack a3f9c1
```

The agent now says: *"I updated 9 call sites, not 3. Two are ambiguous — I listed them
rather than editing. One I cannot resolve at all; someone should check it by hand."*

---

## Quick start

```bash
uv sync --all-extras
uv run qmctx index .                     # build the context pack (nothing leaves your machine)
uv run qmctx serve                       # MCP server on 127.0.0.1:7331

claude mcp add quantamind http://127.0.0.1:7331
```

Four tools become available to any MCP-speaking agent:

| Tool | Returns |
|---|---|
| `callers_of(symbol)` | every caller, each with a confidence label and provenance |
| `reaches(symbol)` | transitive callees, labeled |
| `coverage(path)` | resolved / total call sites for a region |
| `unresolved(path)` | every call site we could not resolve, with the construct that defeated us |

---

## What makes this different

Every competing tool reports what it **found**. None reports what it **missed**.

- A call site we cannot resolve produces `Unresolved(site, reason, construct)` — never
  silence. "No edge here" and "we failed here" are different values on the wire.
- Coverage is computed per directory, pinned to a commit SHA, and excludes builtin calls
  (which account for ~59% of the apparent static/dynamic gap and tell a developer nothing).
- We never build a "smarter" general analyzer. Soundness causes imprecision causes
  unscalability — that chain is documented and we do not fight it. We add narrow resolvers
  where framework semantics make the answer structurally guaranteed.

---

## Repository map

| Path | What lives there |
|---|---|
| `AGENTS.md` (`CLAUDE.md` →) | Agent memory file. Capped at 200 lines, every rule paired with an enforcer. |
| `ARCHITECTURE.md` | Layers, contracts, tech stack with justification, invariants |
| `CONTRIBUTING.md` | Branch / PR / review protocol |
| `docs/PROJECT_CONTEXT.md` | Full research record, business case, competitor table, corrections log |
| `docs/BUILD_PLAN.md` | Phased plan with gates and kill criteria |
| `docs/VALIDATION.md` | Why a green test is not verified data; the silent-failure suite |
| `docs/CODEBASE.md` | Folder-wise map, regenerated every PR |
| `scripts/guard/` | The enforcement layer — the rules that are real |

---

## Development

```bash
just check      # lint + types + guards + unit + property   (~60s, run constantly)
just verify     # check + live runs + golden diff           (~10min, before every PR)
```

`just check` green means the code is well-formed. **It does not mean the data is right.**
Only `just verify` claims that, and it claims it by running the real pipeline against real
repositories and diffing against golden files a human reviewed.

---

## Status

Pre-Phase-0. The founding measurement has not been taken yet — see
`docs/BUILD_PLAN.md#phase-0`, which can end this project in two days and should be run
before any product code is written.

Read `docs/PROJECT_CONTEXT.md#7-corrections-log` before repeating any number from this
README to anyone outside the team. Several early estimates were wrong and are recorded
there so nobody re-derives them.
