"""The two surfaces this product WRITES to on GitHub, kept apart from everything it reads.

`github_comments` posts a summary a human reads; `github_reviews` posts findings anchored to the
lines they concern, falling back to a comment when nothing anchors. They live together because they
answer one question -- how a verdict reaches the pull request -- and apart from the rest of
`ingest/` because every other module there only reads. A write is the side of this product a
customer's repository actually feels.

**GROUPING THEM DOES NOT GATE THEM, AND THIS LINE IS NOT A SAFETY CLAIM.** `POSTING_ENABLED`
is checked by the CALLER, at `serve/review_delivery.py:120` and `:191` -- nothing in this
package consults it, and a caller that forgets will post. What the grouping buys is that the
set needing a gate can be read off a directory listing instead of remembered.
"""
