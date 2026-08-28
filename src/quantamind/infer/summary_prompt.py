"""The prompt the reviewer is given, and nothing else.

WHAT: `PROMPT`, a template of labelled FACT blocks and one TASK.
WHY:  **A PROMPT IS AN ARTEFACT, AND KEEPING IT SEPARATE IS HOW ITS CHANGES STAY VISIBLE.** It is
      the single largest determinant of what the review says, and buried among transport code its
      edits read as incidental. On its own, a diff to this file is unmistakably a change to the
      product's behaviour.

      **EVERY BLOCK IS A MEASURED FACT, NOT COMMENTARY.** An earlier version carried lines like
      "higher means this file has repeatedly needed correcting, so it deserves more suspicion" —
      an instruction to be suspicious, written by us and dressed as an input. The model was being
      led toward a conclusion and the output would have read as its own. The blocks now state what
      was measured and the task says answer only from them.

      **THE ABSENCES ARE WORDED, NOT LEFT BLANK.** An empty section reads to a model as "no
      information" and it will fill the gap; "no static Python import of these files was found"
      makes the absence itself the fact, which is what `parse/importers` can actually support.
IMPORTS: nothing. It is a string.
CONSUMED BY: `infer/change_summary.py`.
"""

from __future__ import annotations

PROMPT = """FACTS. Each block below is measured, not opinion. Do not restate them.

[PR_DESCRIPTION]
{goal}

[FILES_TOUCHED]
{files}

[PRIOR_FIXES] number of later commits that returned to each file
{history}

[STATIC_IMPORTERS] files whose Python imports resolve to the changed modules
{importers}

[TEAM_CONVENTIONS] documents this repository keeps about how its code is written
{conventions}

[DIFF]
{diff}

TASK. Answer only from the facts above. Reply with ONLY a JSON object, no markdown fence:
{{
  "what_changed": "one or two sentences, plain words, naming the function or file",
  "achieves_goal": true | false | null,
  "reasoning": "one sentence; if false name what is missing or contradicted",
  "impact": "one sentence on the files in STATIC_IMPORTERS",
  "breaks": true | false | null,
  "breaks_why": "one sentence; if true name what breaks and for whom",
  "convention": "one sentence, or empty. Name a TEAM_CONVENTIONS rule this diff contradicts and
                 quote the phrase. Empty if none is contradicted or no conventions were given.
                 Do not restate a convention the diff follows."
}}

achieves_goal is null when PR_DESCRIPTION is empty or states no purpose.
breaks is true when the diff shows something that fails for a file in STATIC_IMPORTERS: a changed
signature, a removed name, an altered return. It is false when those files are checked and the
change is additive or internal. It is null when the deciding fact is absent from the blocks above.
"""
