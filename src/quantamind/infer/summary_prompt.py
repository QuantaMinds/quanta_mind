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

      **EVERY LABEL IS WORDED AS THE MODEL MAY REPEAT IT, BECAUSE IT DOES.** The blocks were named
      `[PR_DESCRIPTION]`, `[STATIC_IMPORTERS]`, `[TEAM_CONVENTIONS]` and the task asked for "one
      sentence on the files in STATIC_IMPORTERS". On `QuantaMinds/quanta_mind#101` the model wrote
      **"The test files in STATIC_IMPORTERS will need to be updated"** onto a real pull request --
      an internal identifier in a sentence a customer reads, which
      `docs/product/comment-golden-rules.md` forbids. A label is not private just because we think
      of it as structure; **it is vocabulary, and the model will use it.** Each one now reads as
      ordinary English if it is echoed.

      **AND `[FILE HISTORY]` IS DELIBERATELY VAGUE, WHICH IS THE OPPOSITE OF THE USUAL RULE HERE.**
      It read `[PRIOR_FIXES] number of later commits that returned to each file` -- an accurate
      description of the ranking signal, sitting in a prompt whose output is published.
      `docs/product/publishing-rules.md` puts *what the ranking is built from* first on the
      never-publish list, so the clearer label was the more dangerous one. **No output field uses
      this block**, which is worth knowing before anyone spends a measurement defending it.

      **THE ABSENCES ARE WORDED, NOT LEFT BLANK.** An empty section reads to a model as "no
      information" and it will fill the gap; "no static Python import of these files was found"
      makes the absence itself the fact, which is what `parse/importers` can actually support.
IMPORTS: nothing. It is a string.
CONSUMED BY: `infer/change_summary.py`.
"""

from __future__ import annotations

PROMPT = """FACTS. Each block below is measured, not opinion. Do not restate them.

[WHAT THE AUTHOR SAYS THIS IS FOR]
{goal}

[FILES CHANGED]
{files}

[FILE HISTORY]
{history}

[FILES THAT IMPORT THE CHANGED CODE] resolved by static Python import
{importers}

[CONVENTIONS THIS TEAM WROTE DOWN]
{conventions}

[DIFF]
{diff}

TASK. Answer only from the facts above. Reply with ONLY a JSON object, no markdown fence:
{{
  "what_changed": "one or two sentences, plain words, naming the function or file",
  "achieves_goal": true | false | null,
  "reasoning": "one sentence; if false name what is missing or contradicted",
  "impact": "one sentence on the files that import the changed code",
  "breaks": true | false | null,
  "breaks_why": "one sentence; if true name what breaks and for whom",
  "convention": "one sentence, or empty. Name a convention this team wrote down that this
                 diff contradicts, and quote the phrase. Empty if none is contradicted or
                 no conventions were given.
                 Do not restate a convention the diff follows."
}}

achieves_goal is null when the author's stated purpose is empty or says nothing.
breaks is true when the diff shows something that fails for a file that imports the changed
code: a changed signature, a removed name, an altered return. It is false when those files are
checked and the change is additive or internal. It is null when the deciding fact is absent from
the blocks above.
"""
