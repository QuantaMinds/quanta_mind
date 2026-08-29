---
description: Rank this change by fix history and report what was read and what was not
allowed-tools: Bash(uv run quantamind review:*)
---

Run QuantaMind over the current working tree and act on the result.

```
!`uv run quantamind review . --repo local/working-tree --json`
```

The output above is one JSON object. Read these keys:

- **`not_reviewed_because`** — `null` when a ranking ran. Otherwise `nothing_pending` (clean
  tree) or `no_supported_language` (files changed, none we read). **If it is not null, say so
  and stop.** There is nothing to act on and inventing something would be worse than silence.
- **`files.reviewed`** — the files the ranker funded. These were looked at.
- **`files.unread`** — the files that changed and were **not** looked at.
- **`history`** — how often each file has needed a follow-up fix. This is the ranking signal.
- **`findings`** — usually empty. Present only if a model ran, which it does not by default.

## How to report this back

**Lead with what was not read.** Say `N of M files reviewed` and name the unread ones if there
are few. A change is not reviewed because this command ran; it is reviewed to the extent
`files.reviewed` says, and reporting otherwise is the one failure that makes the tool worse than
nothing. The residual is the product.

**Then, for each file in `files.reviewed`, actually read it and say whether the change looks
right.** The ranker decides *where* to look — it does not look. If you skip this step the
command has told the developer nothing they could not get from `git status`.

**Do not run with `--deep`.** That flag exists for measurement, is hidden from `--help`, and
turns on model findings that are 66.7–82.1% wrong. It is not part of this command.

If the command is not found, say that `quantamind` is not installed in this environment and
stop — do not fall back to reviewing the diff yourself and present it as this tool's output.
