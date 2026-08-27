# The webhook endpoint, containerised.
#
# WHAT:  A runtime image for `quantamind serve`. Builds nothing from source but the package itself.
# WHY:   **PACKAGING IS WHAT MADE THE DEPENDENCY LIST HONEST.** Before this file existed the
#        product also required a `gh` CLI authenticated as a PERSON -- `ingest/diff.py` read every
#        pull request through `gh api`. On a laptop that is invisible, because `gh auth login`
#        happened months ago. Here there is no `gh` and no login, so every delivery would have
#        failed after the image was declared working. The three binaries below are the real list.
# CONSUMED BY: any host that can run a container and give it a public URL.

FROM python:3.12-slim-bookworm

# **git**    -- `ingest/commits.py` is the only place the product runs `git log`, and the ranker is
#               a count over history. Without it there is nothing to rank.
# **openssl** -- signs the RS256 JWT that becomes an installation token. `pyproject.toml` declares
#               `dependencies = []`, and stdlib has no RSA; `ingest/app_auth.py` explains the trade.
# **ca-certificates** -- api.github.com over TLS. Its absence looks like a network outage.
#
# No `gh`. No build toolchain: there is nothing to compile, because there are no dependencies.
RUN apt-get update \
    && apt-get install --no-install-recommends -y git openssl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# **A NON-ROOT USER, AND THE CLONES BELONG TO IT.** The endpoint clones customer repositories and
# runs `git` over them. Running that as root means a `git` bug is a container-root bug.
RUN useradd --create-home --uid 10001 quantamind
WORKDIR /app

# The package only. Tests, research and docs are not runtime, and a research harness that imports
# pandas must never be reachable from a process that serves customers -- which is rule 11.
COPY --chown=quantamind:quantamind pyproject.toml README.md ./
COPY --chown=quantamind:quantamind src/ ./src/

RUN pip install --no-cache-dir . && rm -rf /root/.cache

# **THE ROOTS ARE CREATED HERE, AND ONLY HERE.** `serve/health.py` refuses to create a missing
# store root, so a typo in QUANTAMIND_DATABASE_PATH cannot produce a fresh empty root and a healthy
# verdict. That property is about the CONFIGURED path at runtime; provisioning a FIXED path at
# build time is the operator step the image performs on its own behalf. Without it a fresh
# container answers 503 forever and looks broken when it is merely unprovisioned.
RUN mkdir -p /data/stores /data/clones && chown -R quantamind:quantamind /data

USER quantamind

# **THE STORE ROOT AND THE CLONE ROOT ARE VOLUMES, NOT IMAGE LAYERS.** A tenant's touch index is
# the asset -- `store/schema.py` says the outcome history accumulates over months and there is no
# re-index path in production. Losing it on redeploy would silently cost every customer their
# history and the endpoint would look healthy afterwards.
ENV QUANTAMIND_DATABASE_PATH=/data/stores \
    QUANTAMIND_CLONE_ROOT=/data/clones \
    QUANTAMIND_APP_KEY_PATH=/run/secrets/app.pem \
    PYTHONUNBUFFERED=1
VOLUME ["/data"]

# **NOT SET HERE, ON PURPOSE:** QUANTAMIND_APP_ID, QUANTAMIND_WEBHOOK_SECRET, and the private key
# at /run/secrets/app.pem. A secret baked into an image is a secret in every registry that ever
# pulls it. `serve/listener.py` refuses to bind without the webhook secret, and `types/settings.py`
# refuses to construct when posting is enabled without an App -- so a container missing either
# fails loudly at startup rather than serving something that cannot work.
#
# **POSTING IS OFF UNLESS ASKED FOR.** With it off the endpoint runs the whole pipeline and prints
# the comment it would have posted, which is a complete rehearsal that touches nobody's repository.

EXPOSE 7331

# The liveness path `serve/health.py` answers. It opens EVERY tenant store rather than pinging,
# because a version mismatch in one tenant is a tenant this build must not write to.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:7331/health', timeout=5).status==200 else 1)"

ENTRYPOINT ["quantamind"]
# `--host 0.0.0.0` is asked for HERE and nowhere else: inside a container loopback is the
# container, so a default bind would time out every delivery against a healthy-looking process.
CMD ["serve", "--port", "7331", "--host", "0.0.0.0"]
