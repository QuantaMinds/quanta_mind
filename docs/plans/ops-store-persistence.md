# The audit trail does not survive a deploy — what to run, and what to build after

**Branch:** `ops/store-persistence`. **Status: PREPARED, NOT RUN.** Nothing here has been applied to
the running service. The commands are written out so somebody can read them before they execute
them, which is the point.

## What is actually wrong

Measured against the live service on 2026-09-11 with `gcloud run services describe
quantamind-reviewer`, which is the reader the `justfile` already names for service properties:

| | what is running |
|---|---|
| volumes | two **secret** volumes, both mounting `quantamind-app-key`; `quantamind-app-key-cev-cim` is **not mounted by the container** — an orphan from a redeploy |
| volume mounts | `/run/secrets` only. **No bucket, no disk** |
| `QUANTAMIND_DATABASE_PATH` | **not set**, so `types/settings.py` falls back to `"quantamind.db"` — a relative path in the container's working directory |
| `autoscaling.knative.dev/maxScale` | **3** |

**`database_path` is a ROOT, not a file.** `review_delivery.deliver()` calls
`tenancy.store_for(Path(settings.database_path), owner, name)`, so the default creates a
*directory* called `quantamind.db` holding `<owner>/<name>.db` per repository, plus the shared
accounts store. That is why the repository root has a `quantamind.db/` directory rather than a file.

**So the trail is destroyed on every deploy, and split across up to three instances while
running.** `docs/product/HOW_IT_WORKS.md` claimed it "now sits on a mounted bucket with a single
writer". Both halves were false. This is the defect that matters most, because
`docs/product/pricing.md` sells "full history" and "evidence you can hand to an auditor" on the
strength of it.

## The constraint that decides the design

**Neither Cloud Run volume type supports file locking**, and this is documented by Google rather
than inferred:

- **Cloud Storage FUSE** *"does not provide concurrency control for multiple writes (file locking)
  to the same file… the last write wins and all previous writes are lost."*
- **NFS / Filestore** — Cloud Run *"does not support NFS locking, and NFS volumes are automatically
  mounted in no-lock mode."*

SQLite on a filesystem with no locking is a corruption risk, not a performance one. `PRAGMA
journal_mode=WAL` also fails on these filesystems. **Any design that keeps SQLite on a mounted
volume is therefore a single-writer design or it is wrong.**

**One thing works in our favour and should not be over-read.** The store is one file per
*repository*, so two instances collide only on concurrent deliveries for the same repository —
which is a normal event on a busy repository, not a rare one. It narrows the blast radius; it does
not make multi-instance safe.

---

## Step one — stop the loss. Prepared, not run.

`just storage-setup`. Read it before running it; it changes a running service.

**`--update-env-vars`, never `--set-env-vars`.** The service carries `QUANTAMIND_APP_ID`,
`QUANTAMIND_APP_KEY_PATH`, `QUANTAMIND_INFERENCE_ENABLED`, `QUANTAMIND_INFERENCE_PROJECT`,
`QUANTAMIND_POSTING_ENABLED` and a secret reference for the webhook secret. `--set-env-vars`
replaces the whole set and would silently remove every one of them, which on this service means an
endpoint that authenticates nothing.

**`--max-instances=1` is not a performance decision.** It is what makes a lock-free filesystem safe
for SQLite, and it must move back only when step two lands.

**The deploy window is a real residual and is stated rather than hidden.** During a revision
rollout the old revision keeps serving until traffic moves, so two writers can exist briefly. Deploy
with `--no-traffic` and then `update-traffic --to-latest`, which narrows the overlap to in-flight
requests. It does not eliminate it. With zero customers this is acceptable; with customers it is
the argument for step two.

## Step two — the durable fix, which is a better auditor story anyway

**The trail is append-only by design** — `AGENTS.md` and the export both say nothing is ever
backfilled or edited. **Append-only is the one access pattern object storage is good at**, because
distinct objects need no locking at all.

Write each delivery's checks to the bucket as **one immutable object keyed by the
`X-GitHub-Delivery` GUID** that `store/deliveries.py` already keys replay protection on. Then:

- no locking, because two writers never touch one object;
- `--max-instances` goes back up, and the store stops being the thing that caps throughput;
- the SQLite file becomes a **rebuildable read model** rather than the system of record, so losing
  it on a deploy stops being a data-loss event;
- **object versioning plus a retention policy is tamper-evidence we cannot currently offer.** A
  SQLite file an operator can edit is a weaker claim than an object store that refuses to let them.
  `pricing.md` already promises "never backfilled, never edited"; this is what would make that
  checkable by the customer rather than asserted by us.

**This is a `store/` change and it needs its own plan before any code moves.** It is named here so
step one is understood as a stopgap rather than the answer.

## What could still silently fail

- **The mount succeeds and the path is wrong.** `/data/stores` must be the value of
  `QUANTAMIND_DATABASE_PATH` and the mount path must be its parent, or the service writes to the
  container filesystem exactly as it does today and nothing looks different. **The verification
  below is the check, and it must be run.**
- **The service account cannot write to the bucket.** The failure mode is a store that appears
  empty rather than an error, which is the shape this project refuses everywhere else.
- **`maxScale` is raised later by someone deploying normally.** `just deploy` does a source deploy
  that preserves service properties, so it will not undo this — but a hand-run `gcloud run deploy`
  with flags could.

## The known-answer test, which is the whole point

`HOW_IT_WORKS.md` says a review "has not yet been recorded, redeployed, and read back." That is the
test, and until it passes, persistence is a configuration claim rather than an observed one:

1. `quantamind compliance --repo <owner>/<name>` against the deployed service — note the row count.
2. `just deploy`.
3. Same command. **The count must be identical and the rows must be the same rows.**

A fresh empty store and a working one look the same on step three if nobody recorded step one.
