"""The Martian offline benchmark head-to-head.

WHAT: Runs our reviewer through `withmartian/code-review-benchmark`'s offline layer and scores it
      beside the rivals' checked-in candidates under one judge.
WHY:  Every competitor comparison has been refused on the grounds that their precision is
      behavioural and ours is truth. The offline layer is neither -- it is a fixed set of
      human-verified issues, so both can be scored on it.
IMPORTS: nothing.
CONSUMED BY: nobody.
"""
