# Why the signal is real and may be inert — the missing link, measured

**When the ranker is RIGHT about which file a later fix returns to, 74% of the time the fix
repairs code the reviewed change never touched.**

2,400 events, six repositories the ranker was never developed on, git history only.

## The chain, and which link this tests

`QUANTAMIND.md` states it: *we rank the risky file (**measured**) → the reviewer reads it
(**unmeasured**) → they find the defect (**unmeasured**) → it never reaches production
(**unmeasured**).*

**The second link has a testable failure mode.** If the later fix repairs code that was not in the
diff, then naming that file was correct and useless — no reviewer reading that change could have
found the defect, because the defect was not in front of them.

## Result

| | events | share |
|---|---|---|
| the ranker named the right file | 2,720 | — |
| both diffs readable | 2,400 | — |
| **the fix touched lines the change touched** | **623** | **26.0%** |
| **the fix touched only OTHER lines** | **1,777** | **74.0%** |

Per repository: scikit-learn 44.2%, scrapy 31.2%, celery 25.5%, django 22.5%, ansible 17.8%,
pandas 14.5%. **The spread is 3× and every repository is under half.**

## One case, read end to end

`scrapy` — the change is *"first functional version of pbcluster"*, three files.

```
1. [READ]  3 prior fixes  .../pbcluster/master/manager.py
2. [READ]  2 prior fixes  .../pbcluster/master/web.py   <-- the fix returned here
3. [READ]  2 prior fixes  .../pbcluster/worker/manager.py
```

**The ranking was right.** `web.py` was rank 2 and a fix came back to it the same day.

```
the change touched lines : 7, 8, 25, 26, 50, 54, 55, 58 …
the fix    touched lines : 236, 237
```

The fix added two lines at 236 — a loop over `self.nodes` in a method the reviewed change never
opened. **A reviewer given "read `web.py` first" would have read the right file and still missed
it, because it was not there yet.**

## The contrast, so the measurement is not one-sided

`django` — the change adds `ROOT_URLCONF` at lines 29–30 of `settings/main.py`. Three days later a
fix adds `SECRET_KEY` at lines 29–31, **overlapping**. Here the reviewer was looking at the exact
lines the fix repaired, and "this settings file has 5 prior fixes, read it first" would have put
them there.

## What this does and does not establish

**Does:** a floor on how much of the correct signal is *directly* reachable from the reviewed diff.
**26%.** Three quarters of what the ranker gets right is right about a file rather than about
anything a reviewer could act on in that review.

**Does not:** prove inertness. **A fix to a caller of the reviewed function is genuinely reachable
and will not overlap by line number**, and so is a fix to the same function after an intervening
edit shifts the line numbers. Line overlap undercounts reachability, and by how much is unmeasured.

**And it does not touch the queue-level claim.** *"This pull request should not be merged
unreviewed"* does not require the defect to be in the diff — it requires the change to be risky.
This measurement is about the file-level reading order, which was already dead on other evidence.

## Why it matters anyway

It supplies a **mechanism** for something that had only a pattern behind it. Five product framings
have failed with the signal intact, which permits *"the framing is not found yet"* or *"the signal
is real and inert."* **A 74% disjoint rate is the first direct evidence for the second**, and it
explains the anti-correlation with reviewer attention rather than merely restating it: reviewers do
not comment where fixes return partly because, at review time, there is nothing there to comment on.
