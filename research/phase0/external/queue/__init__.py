"""The change-level questions, as opposed to the file-level ones the rest of this package answers.

`actionability` asks whether a correct file-level prediction is reachable from the reviewed diff —
26% of the time. `queue_triage` and `queue_triage_tight` ask whether the firing gate concentrates
the changes that later need repair, which is the queue-level product claim: 1.35x against a
pre-registered 2.03x, so it fails. `one_example` prints a single case end to end, because a rate is
not a mechanism until someone reads one.
"""
