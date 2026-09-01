# Three deployment shapes, one container

D7f. The same image runs three ways. **The shape is configuration, not a build** — there is no
separate air-gapped artefact to keep in step with the cloud one, because a second artefact is a
second thing to drift.

| shape | who runs it | may reach |
|---|---|---|
| `cloud` | us | everything |
| `on_prem` | you, inside your network | everything except Google's instance metadata server |
| `air_gapped` | you, with no egress | **the clone, and nothing else** |

Set it with one variable:

```
QUANTAMIND_DEPLOYMENT_SHAPE=air_gapped
```

**A value that is not one of the three refuses at startup.** Reading a typo as `cloud` would turn a
misconfigured air-gapped deployment into one that reaches the network, which is the failure this
whole shape exists to prevent → `types/deployment.py:current`.

---

## What air-gapped actually means here

**It refuses. It does not merely fail to connect.**

A deployment that has no route produces timeouts, retries, and a review that is late rather than
declined — and you find the attempt in your egress logs while we never see it at all. **An outbound
call that fails quietly in a bank is a finding against us, not a bug.** So every destination is
asked about before a socket opens, and a forbidden one raises `NetworkRefused` naming the shape,
the destination, and what *is* permitted:

```
air_gapped deployment refuses inference: this instance is configured not to reach it.
Nothing was sent. Permitted here: git_remote.
```

**The clone is the boundary, not an exception to it.** With no repository there is nothing to
review, so refusing the clone would not be an air gap — it would be an off switch.

### What you get, and what you lose

**You get the whole deterministic half**, which is the half this product argues carries it:
the fix-history ranking, every declared rule in `.quantamind/rules.toml`, duplicate-body detection,
hardcoded-secret scanning, public-API break detection, and the audit trail with its export.

**You lose everything that needs a network:** the model's review, GitHub comments and statuses
(there is no API to post to), Jira and Slack context, and the release oracle's package-index checks.

**This is enforced, not documented.** `scripts/guard/runtime/check_network_chokepoint.py` fails the
build if any module in `src/` opens a socket or runs a networked git subcommand without asking
first — so a module added next month cannot quietly reintroduce an outbound call.

---

## Running it on premises

The image is the one built by `just deploy`; nothing about it is cloud-specific.

```bash
docker run --rm \
  -e QUANTAMIND_DEPLOYMENT_SHAPE=on_prem \
  -e QUANTAMIND_APP_ID=<your GitHub App id> \
  -e QUANTAMIND_APP_KEY_PATH=/run/secrets/app.pem \
  -e QUANTAMIND_WEBHOOK_SECRET=<from your App> \
  -e QUANTAMIND_DATABASE_PATH=/data/quantamind.db \
  -v /your/secrets/app.pem:/run/secrets/app.pem:ro \
  -v /your/data:/data \
  -p 7331:7331 \
  quantamind:latest serve
```

**On-prem loses the metadata server and nothing else.** `ingest/google_auth.py` reads a token from
an address that exists only inside Google's fabric; outside it, that read hangs until a timeout.
Configure your own inference credential instead, or leave `QUANTAMIND_INFERENCE_ENABLED=0` and run
the deterministic half.

**Storage is a volume you own.** `QUANTAMIND_DATABASE_PATH` is the audit trail; it must outlive the
container, and `quantamind compliance --repo <owner/name> --export trail.json` reads it back out
whole for an auditor.

### Air-gapped

Identical, with two changes:

```bash
docker run --rm \
  -e QUANTAMIND_DEPLOYMENT_SHAPE=air_gapped \
  -e QUANTAMIND_INFERENCE_ENABLED=0 \
  -e QUANTAMIND_POSTING_ENABLED=0 \
  ...
  quantamind:latest review /path/to/clone
```

`POSTING_ENABLED=0` is not required — posting would be refused anyway — but setting it means the
run reports "rehearsed" rather than raising, which is the honest output when there is nowhere to
post to.

**Verify the gap yourself**, rather than trusting this page:

```bash
QUANTAMIND_DEPLOYMENT_SHAPE=air_gapped python -c "
from quantamind.types.deployment import Destination, permit
permit(Destination.INFERENCE)"
# NetworkRefused: air_gapped deployment refuses inference ...
```

---

## What is still true and unpleasant

- **There is no scheduled export.** The audit trail is read out by a command somebody runs. A
  compliance team wanting a monthly artefact has to remember.
- **`just deploy` builds for Cloud Run.** The image runs anywhere, but the recipe that produces it
  is written for one target; an on-prem customer builds from the same Dockerfile with their own
  registry.
- **Air-gapped is untested against a real air-gapped network.** The refusals are tested, and the
  guard proves no module bypasses them, but nobody has run this inside a customer's isolated
  environment. That is the honest state of it.
