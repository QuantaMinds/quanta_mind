# The command line

Every command this project ships, what it is for, what it returns, and what a healthy run looks
like. **A command that is not built says so and exits non-zero** — it never exits 0 having done
nothing, because that is how a runbook comes to report work it never did.

Exit codes are uniform: **0** success, **1** the command ran and something was wrong, **2** the
command is not built yet.

---

## `quantamind` — the product

### `quantamind --version`

Prints the package version and exits.

### `quantamind config`

**What:** prints the resolved configuration — every setting after environment variables are
applied — and exits 0.

**Why:** a misconfiguration should be visible *before* a run, not inferred from a strange result
afterwards. This is the command to run first on a new machine.

```
$ uv run quantamind config
database_path              quantamind.db
max_requests               50
threshold_percentile       0.9
inference_enabled          False
model                      claude-opus-5
subprocess_timeout_seconds 30

runs a model on a review:  False
```

**Settings** are read from the environment with a `QUANTAMIND_` prefix — `QUANTAMIND_DATABASE_PATH`,
`QUANTAMIND_MAX_REQUESTS`, `QUANTAMIND_MODEL`, `QUANTAMIND_SUBPROCESS_TIMEOUT_SECONDS`. A malformed
value raises `SettingsError` naming the variable and the value, and exits 1 — it never falls back
to a default silently.

> **`threshold_percentile` is printed and governs nothing.** No firing rule consumes it; setting it
> to 0.1 or 0.99 changes no output. It is listed here because it appears in the output, and a
> reader would otherwise reasonably assume it does something. See `CODEBASE.md`, "The firing rule".

### `quantamind retrospective <clone> [<clone> ...] [--repo NAME]`

**What:** replays the ranker over a repository's own history and reports what it would have said —
the ranker, the alphabetical control and exact hypergeometric chance, stratified.

**Why:** it is the first thing a sceptic runs. It needs a clone and nothing else: no App install,
no webhook, no token, and no code leaves the machine. With more than one clone it pools, which is
usually necessary — see the floors below.

**Arguments**

| | |
|---|---|
| `<clone>` | one or more paths to **full** git clones. Shallow and blob-filtered clones are refused, because both read wrong without failing |
| `--repo NAME` | `owner/name`, used for the report heading. With several clones it becomes a prefix: `NAME/<directory>` |

**How to read the output.** Three rows per repository:

```
$ uv run quantamind retrospective ~/clones/scrapy --repo scrapy/scrapy

Measured ELSEWHERE: on six repositories the method never saw, top-three-by-fix-history
missed 1.21% ... `just gate-2b` re-proves that this code reproduces it event for event.

THIS IS NOT THAT NUMBER. Below is a first measurement of one repository, unreplicated ...

scrapy/scrapy
-------------
  all events       n=  1351   ranker 4.74%  alphabetical 10.88%  chance  9.90%  ranker vs chance +5.16
  >3 files         n=   510   ranker 12.55% alphabetical 28.82%  chance 26.22%  ranker vs chance +13.67
  <=3 files        n=   841   ranker 0.00%  alphabetical  0.00%  chance  0.00%  ranker vs chance +0.00
  62.3% of events touch <=3 files, which a budget of three reads entirely ...
  discordant pairs: ranker 105, control 22; exact McNemar p = 0.00000
  alphabetical vs chance -0.98 — near zero means the control was genuinely uninformative here ...
  not admitted by the event definition — commit stamped before its predecessor: 13,
  every file scored the same: 96, file count outside 2..12: 3725, no later fix returned to it: 1364
```

- **`>3 files` is the headline.** A budget of three reads a three-file change entirely, so on the
  `<=3` rows no arm can miss and all three are 0.00% by construction. Those events decide nothing
  and pooling them dilutes the effect roughly threefold.
- **`ranker vs chance` is the number to quote**, not the gap to alphabetical. Alphabetical's
  strength depends on directory layout; chance depends only on the arithmetic of the change.
- **`alphabetical vs chance` is a diagnostic.** Near zero means the control was genuinely
  uninformative. Well above it means layout made it a poor control for this repository.
- **The rejection counts are part of the result.** If one clause starts rejecting everything, the
  run still "succeeds" — these counts are what tell you it happened.

**Expected exit codes:** 0 on success, 1 if any path is not a git clone.

**INCONCLUSIVE is a normal outcome and is not an error.** Below 500 events or 20 discordant pairs
the report refuses to give a rate and names the shortfall:

```
  INCONCLUSIVE — 414 events, 86 short of the 500 floor.
```

Measured on real projects, a single repository usually lands here — requests 551 events, fastapi
257, click 414. **Pass several clones to pool**, which is the same shape the published figure has:

```
$ uv run quantamind retrospective ~/clones/requests ~/clones/fastapi ~/clones/click --repo acme

POOLED across 3 repositories
  all events       n=  1222   ranker 0.74%  alphabetical  3.36%  chance  3.86%  ranker vs chance +3.12
  >3 files         n=   258   ranker 3.49%  alphabetical 15.89%  chance 18.28%  ranker vs chance +14.79
  discordant pairs: ranker 35, control 3; exact McNemar p = 0.00000
  repositories where the ranker beat chance on the informative stratum: 3 of 3
```

**Read the positivity count, always.** A pooled win carried by one repository is an artifact, and
that line is the only thing in the report that can say so.

### `quantamind review <pr>` — NOT BUILT <!-- documented-command:unbuilt -->

Exits **2** naming the stage that will deliver it. It parses so the argument shape is fixed; it
does nothing else.

### `quantamind serve [--port N]` — binds; authenticates; **does not review**

Serves two routes on `127.0.0.1` (default port **7331**) using the standard library, so the
project's runtime dependency count is still zero.

**The secret comes from the environment and nowhere else.** `QUANTAMIND_WEBHOOK_SECRET` is read at
serve time and is deliberately absent from `Settings`, so `quantamind config` cannot print it into a
scrollback or a CI log. With no secret set the command refuses to bind and exits **1** — an endpoint
that verifies nothing is an open command channel, and it would pass every test that supplies one.

```bash
QUANTAMIND_WEBHOOK_SECRET=... uv run quantamind serve --port 7331
```

Healthy startup — and read the third line, because it is the honest part:

```
[serve] listening on 127.0.0.1:7331
[serve] POST /webhook  — verifies the signature, refuses a replay, answers 202
[serve] GET  /health   — opens the store and reports what is wrong, never raises
[serve] GET  /         — the dashboard: sign in, then a repository's reports
[serve] GET  /r/<owner>/<name> — compliance, outcomes and cost for one repository
[serve] IT DOES NOT REVIEW. The work callback logs and returns; see run_endpoint.py.
[serve] http.server is not a hardened edge — run it behind a TLS-terminating proxy.
```

**Nothing is wired to the work callback.** A delivery is authenticated, de-duplicated, acknowledged
and logged; no repository is cloned and no comment is posted, because `review` is not built. The
banner says so on every start rather than leaving an operator to infer it from an empty output
directory — an endpoint that quietly accepted and dropped the work would look identical to one
doing its job.

| Exit | Meaning |
| --- | --- |
| **0** | stopped by Ctrl-C after serving |
| **1** | no `QUANTAMIND_WEBHOOK_SECRET`, or the port could not be bound |

Responses, all JSON:

| Request | Status | Body |
| --- | --- | --- |
| signed, actionable | **202** | `{"accepted": <guid>, "repo": ..., "pr": ...}` — answered **before** the work runs, because GitHub requires a 2XX within ten seconds |
| signed, already completed | **200** | `{"replay": <guid>, "note": "already completed, not repeated"}` |
| signed ping, draft, label change | **200** | `{"ignored": <reason>}` |
| wrong or absent signature | **401** | `{"error": "signature does not match the body"}` and the other two rejection reasons, kept distinct |
| no `X-GitHub-Delivery` | **400** | replay protection has nothing to key on, so the delivery is refused rather than processed unprotected |
| absent or unusable `Content-Length` | **411** | three distinct messages — absent, unparseable, over the 25 MB ceiling |
| a fault inside the handler | **500** | `{"error": "<Type>: <message>"}` — an unhandled exception would otherwise close the socket with **no status at all**, which GitHub records as a failed delivery nobody can diagnose. A missing secret cannot appear here: it is refused at bind time, above |

`GET /health` returns **200** or **503** with the same verdict `serve/health.py` produces — it opens
the store, so a version mismatch fails the probe rather than passing it.

---

## `just` — the development commands

### `just check` — before every commit

Runs ruff, mypy, the guards, and the unit, property and research suites. **This is the gate; if it
is red, nothing else matters.** Takes about a minute.

```
✅ check passed — code is well-formed. This does NOT mean the data is right.
```

Read that second line literally: `check` proves the code is well-formed, not that any number it
produces is correct.

### `just verify` — before every PR

`check`, plus the live tests against real repositories, plus two proofs about the pack. Takes about
four minutes and clones a repository into `.verify-clone` itself — no setup needed.

Healthy tail:

```
[no-source-leak] ok — no stored value appears in any source file
[determinism] excluded as wall-clock, not data: delivery.completed_at, delivery.started_at, repo.first_seen
[determinism] exclusion proven live: mutating those columns did not move the digest
✅ verify passed — the pipeline ran against real repositories and the pack holds no source.
   NOT covered: golden-pack comparison.
```

**The "exclusion proven live" line matters.** The determinism check once declared its wall-clock
exclusion list and never applied it, passing for as long as three runs landed inside one second.
That line is the tool proving to you that the exclusion is doing something.

### `just fixtures` — once, before `just gate-2b`

Clones the six repositories that produced the ranker's validated result, at the exact commits it
was measured at (`tests/fixtures/pinned.json`). **About 1.3 GB.** Idempotent — a clone already at
its pinned commit is left alone.

```
  cloned   ansible_ansible            9cf16a4aca78
  present  celery_celery              1fcbf6fa4fb3
  ...
  6 repositories at their pinned commits in tests/fixtures/repos
```

Exits 1 and names the repository if a pinned commit is unreachable — it never falls back to
whatever the branch points at today.

### `just gate-2b` — the ranker's strongest check

Replays the product over the pinned corpus and requires it to reproduce
`research/phase0/external/defect_return_external.json` **event for event**.

```
  events 2400  hits 2371  alpha hits 2325
  miss 0.0121  alphabetical 0.0312
  1 passed
```

**Anything other than 2,400 events at 1.21% / 3.12% is a regression** and worth stopping on. It is
kept out of `just verify` because of the 1.3 GB, which means it can rot if nobody runs it.

### The narrower recipes

| command | what it runs |
|---|---|
| `just install` | `uv sync --all-extras`, plus the research project on its own interpreter |
| `just lint` / `just types` | ruff / mypy alone |
| `just guards` | the structural, layering, citation and provenance guards |
| `just test-unit` | `tests/unit`, about 5s |
| `just test-property` | `tests/property` — the conservation and layer-order invariants |
| `just test-live` | live runs against real repositories, not mocked; excludes the pinned corpus |
