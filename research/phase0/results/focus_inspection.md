# Blind inspection of what MIN_COMMIT_FOCUS removed

Verdicts written before the variant counts were read. The dropped set was extracted from
`rule_attribution.json` by field, so the counts stayed unseen.

## AgentOps-AI/agentops#818 — "fix: checks for `dev` before release"

Merged 2025-03-13, 100 files. Commits in its seven-day window whose subject matches the
breakage pattern:

| commit | files | subject |
|---|---|---|
| `ad3c9fab6` | 1 | fix: Remove `X-API-Key` from headers to fix auth (#840) |
| `e47b8949f` | **71** | fix-a-lot (#830) |

`ad3c9fab6` touches one file, so its focus is 1.0 and it is kept either way. The dropped
verdict therefore comes from `e47b8949f`.

**Verdict: correctly dropped.** `fix-a-lot` is a 71-file omnibus sweep landing the day
after, in the middle of a 0.4.0 release — the same window contains a 158-file
`[RELEASE] v0.4.0` and a 26-file `0.4.4`. PR 818 changed a release-time guard for `dev`
versions. A 71-file commit named "fix-a-lot" is not a targeted repair of that guard; it
overlaps by breadth, which is exactly what the threshold exists to exclude.

**This is the sweep case, not the "real repair plus unrelated cleanup" case.** The metric
is doing what it was written to do, and 0.25 stands.

**One caveat recorded against my own verdict.** The whole window is release churn, so this
repository is a favourable example for the threshold. A single instance cannot show that
the metric is right in general — only that it was right here. If a later run drops more,
the same inspection is repeated rather than assumed to have been settled by this one.
