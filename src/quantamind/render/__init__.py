"""The render layer.

WHAT: The comment body, the coverage line, the weekly digest and the report.
WHY:  Coverage is rendered before findings, because the order is the argument: a reader should
      be able to weigh a finding before reading it.
IMPORTS: types through verify.
CONSUMED BY: serve.
"""

from __future__ import annotations
