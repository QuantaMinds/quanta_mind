# A Vertex token without `gcloud`, and without a key on disk — G1

**Branch:** `feat/vertex-service-account`.

## What forced the design

`infer/gemini.py` shells out to `gcloud auth print-access-token`. There is no `gcloud` in the
container and there should not be: a 200 MB SDK to fetch a bearer token is exactly the dependency
`pyproject.toml`'s `dependencies = []` exists to refuse. The path was also a **Homebrew absolute
path compiled into the product**, correct on one laptop and absent everywhere else.

The plan was a service-account key, mirroring `app.pem`. **The GCP org policy refuses to issue
one** — `constraints/iam.disableServiceAccountKeyCreation`. That is good posture and is not routed
around: I have owner on the project and could disable it, and will not, because a long-lived
downloadable credential is worse than the inconvenience it removes.

**So there is no key, and that is the better answer.** A container on Cloud Run or GCE reads a
token from the metadata server, which means **zero credentials on disk anywhere** — a materially
stronger answer to "what do you do with our code?" than any key-handling policy could be.

## `ingest/google_auth.py`

`token()` tries, in order, and NAMES which one answered:

| source | when | credential on disk |
|---|---|---|
| metadata server | running on GCP | **none** |
| `gcloud` | a developer's laptop | gcloud's own store, never ours |
| — | neither | typed `Unavailable`, naming both attempts |

**The metadata probe must be fast and must not hang.** `metadata.google.internal` does not resolve
off GCP, and a DNS timeout on every review would make the product look broken rather than
unconfigured. A short timeout is a correctness requirement here, not a tuning preference.

**A failure names every source it tried.** "No access token" tells an operator nothing; "not on
GCP, and gcloud is not installed" tells them exactly which of the two deployments they are in and
what to fix.

## What must not change

- **No new dependency.** `urllib` reaches the metadata server; `google-auth` would be the first
  runtime dependency this product ever took.
- **`Settings.gcloud_path` stays**, because laptop development is a real case and PATH lookup
  already covers the container (where the binary is absent and the metadata server answers).

## What could still silently fail

- **The metadata server exists on GCP but the instance may lack the scope**, which returns a token
  that Vertex then rejects. That failure surfaces at the API call, not here.
- **Nothing has yet run this in a container on GCP.** Until G2 does, "the endpoint reviews with a
  model in production" remains a claim about a code path.
- **Token lifetime is not managed.** Each call fetches; caching is not built, so a very large
  review pays the fetch repeatedly.
