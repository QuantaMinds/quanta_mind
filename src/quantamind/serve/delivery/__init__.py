"""What one delivery produced, kept apart from the code that produces it.

`review_delivery.py` outgrew one file: it clones, ranks, allocates, consults a model, enforces
rules, banks a cost, renders and posts. The RESULT of all that is a separate concern from the
doing of it, and it is what callers and tests actually import.

**These types could not move to `types/`.** `Delivered` holds a `Reading`, which belongs to
`allocate` — to the RIGHT of `types` — and rule 7 forbids the import. The guard caught the
attempt; a subpackage under `serve/` keeps the dependency flowing left, the way `serve/http/`
already does for the socket layer.
"""
