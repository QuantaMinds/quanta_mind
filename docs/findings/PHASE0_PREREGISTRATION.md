# the correlation test Pre-Registration — Does Unresolved Predict Breakage?

> **Status: PRE-REGISTERED. Not yet run.**
>
> This file is committed **before** any data is touched. Its purpose is to remove our own
> discretion from the result. Everything below — the outcome variable, the exposure
> variable, the threshold, and the stop rule — is fixed at commit time.
>
> **Amending this file after data collection begins requires a PR that states what was
> changed, why, and who approved it.** An unamended, unexplained change to the threshold
> is research misconduct on ourselves.
>
> Commit this file. Note the SHA. Then follow `PHASE0_RUNBOOK.md` — the executable
> protocol with harness tests, controls, expected outputs and the failure tree.
>
> **Languages in scope: Python and TypeScript/JavaScript.** The Python arm runs first;
> TS/JS repeats the identical protocol only after Python reports, so that a broken
> harness is diagnosed once rather than twice. No other language until both report.

---

## 0. Amendment log

Every change to this file after its first commit is recorded here. All amendments below
were made **before any data was touched** — the harness existed but had not been run, and
``PHASE0_PREREGISTRATION.md` “Results” Results` was and is empty. They arise from reading the corpus schema and the source
papers, and from review of the execution plan.

**No amendment moves a decision boundary.** The RR thresholds (3.0 / 1.5), the CI rules,
the 7-day window, the `a ≥ 20` floor and the stop rule in `PHASE0_PREREGISTRATION.md` “If the result is null” are byte-identical to the
first commit. A1–A5 are factual corrections or newly discovered prerequisites; A6–A18
change *what is measured* (A6), *how it is matched* (A9), *what is excluded* (A7), *how it
is estimated* (A8), or *what may be claimed from the result* (A10), so that all of them
match what the instrument can actually deliver.

**Every one of A6, A7, A9 and A10 was forced by a property established by running the
instrument, not by reading about it** — the set-valued edge map, the 3.10 parse ceiling,
two distinct naming defects, and a capability profile of one mechanism in four. Each is
recorded with its bias direction, and in every case the direction is toward the null. An
amendment that made a positive result *easier* would deserve far more scepticism than
these do.

**One amendment does touch the outcome definition, and it is A4.** The third of `PHASE0_PREREGISTRATION.md` “Outcome variable”'s
three BROKE criteria — the issue link — becomes conditional on API quota. The first two,
which do the overwhelming majority of the work and need no quota, are unchanged. This is
recorded here rather than filed under "factual correction" because a criterion that may or
may not execute is a real change to the outcome variable, and `PHASE0_PREREGISTRATION.md` “Outcome variable” now requires Results to
state whether it ran. Calling that a clarification would be exactly the kind of quiet
reclassification this log exists to prevent.

| # | Section | Change | Why |
|---|---|---|---|
| **A1** | 3 | Population restated: 7,191 → 4,798 structural → ~3,300 merged. Human arm runs in the same pass. | 7,191 was the pre-filter count. The analysed population is 2.2× smaller and saying so is cheaper than discovering it at Day 6. **A32: "in the same pass" is what actually happened, and only the human half ran.** These counts are the AGENT arm's. The pilot that has been executed — 90 repositories, 236 attempts, 139 admitted — drew from the figshare human package and is the human arm end to end. The agent population above has not been built yet. |
| **A2** | 3.1 | Parent commit is `merge_commit_sha^1`, obtained from the GitHub API, with a diff-coverage rule for rebase merges. | AIDev carries no base, head or merge SHA. `base.sha` would be the commit the PR was *opened against*, potentially weeks stale. |
| **A3** | 3.1 | Census scope ≡ PyCG scope, as a rule with the failure mode named. | A wider census makes every out-of-scope site look unresolved and inflates exposure toward 100%. |
| **A4** | 3.2 | Issue-link outcome criterion marked optional and API-dependent; whether it ran is stated in Results. | It needs quota the other two criteria do not. Silent non-execution would give two runs different outcome variables under one name. |
| **A5** | 7 | Pilot added as Day 2.5, with its gate table. | The Day 1–2 gates test the harness against fixtures, never against the corpus. |
| **A6** | 3.1 | Primary analysis restricted to single-site (caller, callee) pairs; multi-site pairs to a bounded sensitivity analysis; fallback pre-specified. | PyCG resolves at pair granularity, so call-site granularity is not measurable. Bias ran toward the null — toward the stop rule. |
| **A7** | 3.1 | `EXCLUDED_SYNTAX` split out of `UNANALYZED` and excluded from the study. | PyCG parses on CPython 3.10; 3.11+ syntax fails because our toolchain is behind, not because the code is dynamic. `PHASE0_PREREGISTRATION.md` “Agent composition” reads that arm to decide what company this is. |
| **A8** | 3.4, 4 | Primary inference is cluster-robust at repository level; naive Katz CI reported alongside; power restated in clustered terms. | Symbols cluster in PRs, PRs cluster in repos. Katz assumes independence and understates variance at exactly the boundary `PHASE0_PREREGISTRATION.md` “Decision thresholds” turns on. |
| **A9** | 3.1 | Edge matching normalises PyCG's path separators and is lenient about the package prefix, requiring a dot boundary. | PyCG names the same function two ways and leaks path separators into module names. Strict equality would mark nested-package callers unresolved wholesale. |
| **A10** | 3.1, 6 | The exposure variable's **capability profile** is recorded, and the scope of a null is narrowed to match it. | Measured: the variable detects 1 of 4 unresolvable-caller mechanisms. Value-dispatched calls carry no callee name, so they produce no pair and read UNEXPOSED. A null therefore cannot be reported as a null about unresolvability in general. |
| **A11** | 4.1 | Control corpus is synthetic repositories plus one real repository, not a Django fixture; per-mechanism detection reported against a fixed reading table; gate unchanged at pooled RR ≥ 5. | A control that times out measures our timeout, not our instrument. Synthetic repos guarantee `graph_status == OK`, so a non-detection is unambiguously a detection failure. |
| **A12** | 4.2 | Control corpus: **if an exposed unit is excluded, its matched control twin is excluded with it.** Unseeable mechanisms go to the capability table only; the firing mechanism scales to 40/40. Gate unchanged. | The first run computed RR = 8.0 from 50 of 80 units, with all 30 exclusions in the exposed arm and none in the control arm. Coding them the other way gives 2.0 — a 4× swing from asymmetric absence alone. |
| **A13** | 4.3 | **Differential exclusion by arm**, for the main study: exclusions reported by arm and reason; pooled RR demoted if the exposed-arm rate exceeds the control arm's by >10pp or the bounds diverge; every exclusion category bounded both ways, or declared unbounded. | Every exclusion category plausibly removes exposed units faster than unexposed ones. The control measured the magnitude at 4×; on the real corpus nobody plants it deliberately. |
| **A14** | 4.4 | RR reported **by agent**; `PHASE0_PREREGISTRATION.md` “If the result is null” scopes the finding; non-identical arm time windows recorded. | Computed: Codex is 64.9% of the corpus and Claude Code 1.4% (459 PRs). A general-sounding claim would rest on one agent — and the product targets the agent with 1.4% of the evidence. |
| **A15** | 4.5 | Human-arm star-band mismatch confirmed by **joining `human_pull_request` to `repository`**, not by a superset statistic; handled by stratifying on star band. | The human arm's true floor is 503 stars with 0% below 500; the agent arm has 47.3% below 500 and a median of 564 against the human Python slice's 14,933. A 26× popularity gap. |
| **A16** | 4.6 | **Supersedes A13's mechanism.** Distinguishes the control's *restricted estimand* (no measurement to be missing) from the study's genuine, likely **MNAR** loss to follow-up. Primary labelled complete-case; worst-case bounds; **tipping-point multiplier** run only if the primary is positive; IPCW as supporting. | The `PHASE0_PREREGISTRATION.md` “The table” 2×2 is a complete-case analysis, unbiased only under MCAR. The bias is not identifiable, so the question is how much of it the conclusion survives — which is a number, not a caveat. |
| **A17** | 4.7, 6 | Agent-stratified RR **reportable for Codex only**; Claude Code descriptive at best; corpus composition recorded in `PHASE0_PREREGISTRATION.md` “If the result is null” as *conservative*; retrieval-strategy moderation **pre-registered as a prediction**. | Codex is 64.9% of the corpus and has the lowest breaking rate (2.62%) of the five, so a positive appears under unfavourable conditions. Claude Code is 459 PRs — below the power floor before the filters. A moderation found post-hoc is a story; predicted, it is mechanism evidence. |
| **A18** | 4.8 | Prior-work scan recorded: terms, date, coverage (~23 of 62+), and the precise novelty claim. | Three adjacent literatures exist — call-graph *accuracy*, call-graph *defect prediction*, and AIDev empirical studies — and none uses the analyzer's failure to resolve as an exposure. Also found: InferCG beats PyCG by 13.9% recall, which is a the MRO and framework resolvers option, not a threat to a deliberately crude instrument. |

| **A19** | 4.9 | Human-arm commit data is **sourced from the AIDev_BC_Analyser replication package**, not mined. Coverage measured, not assumed: 1,009 of 1,042 merged human Python PRs (96.8%). The 3.2% without commits are attrition under A2, counted by resolution case. | AIDev ships no `pr_commits` for human PRs, so A2's parent resolution could not run on that arm at all. The package supplies commit SHAs for effectively all of it, removing a GitHub-API mining workstream whose quota cost was the human arm's largest unknown. Sourcing beats mining: it is fixed, citable, and re-runnable without a token. |

| **A20** | 4.10 | Traces missing patch text through to A16's confounder. Link 1 **fails, in our favour** — shape detection reads filenames, which are complete. Link 2 holds but is an **outlier, not a gradient**. Adds one pilot metric: **file-set disagreement rate by changed-lines quartile**. Corrects A19's patch-weighted 31.1%. | The chain is real — text is missing precisely for the largest changes, so the tertiary outcome loses big patches differentially, on exactly the variable that achieves AUC 0.957 on its own. It needed measuring rather than asserting, and measuring changed the shape of the answer twice. |

| **A21** | 4.11 | Fixes `PHASE0_PREREGISTRATION.md` “Timeline”'s day-2 gate protocol before it runs: **human arm**, eligibility, a **stride draw** across the id range, a manifest hash binding labelling to scoring, and **Cohen's kappa reported as a diagnostic beside the unchanged ≥16/20 threshold**. A PR whose history is unreadable is **not labellable** and invalidates the gate. | The gate's validity is entirely an ordering property, and ordering is the one thing a green test does not check. Also: raw agreement on an all-clean sample is 20/20 for a classifier that always answers "clean" — the same degeneracy `controls/analysis.py` already refuses in the negative controls, reappearing a layer up. |

| **A22** | 4.12 | **Blind stratified sampling.** The sample is 10 PRs the classifier called BROKE and 10 it called CLEAN, shuffled, exported as URLs only; the answers are sealed in a gitignored key. Supersedes A21's stride draw. | At the corpus base rate a random twenty holds about two broken PRs, so labelling everything CLEAN scores ~18/20 and passes a gate that proved nothing. Balanced, always-CLEAN scores 10/20 and fails. The cost is representativeness: agreement now estimates the mean of sensitivity and specificity, not agreement in the wild. |
| **A23** | 4.12 | **The human judges breakage, not the rule.** The rendered seven-day commit window is withdrawn; the labeller works from the pull request and may use any evidence, including linked issues and CI runs the classifier cannot see. `UNSURE` becomes a first-class verdict, scored as disagreement. | The withdrawn sheet showed exactly the classifier's own input, so agreement would have been partly true by construction — it tested whether a human can apply the regex, not whether the regex captures breakage. The gate only means something if the two sources of evidence can differ. |

| **A24** | 4.13 | Records an **agent-labelled dry run** of the 20-PR gate (11/20, kappa 0.10) and the two defects it exposed: `FIX_PATTERN` matching **squash-merge bodies**, and the replication package **over-attributing files to a PR** (92 `.py` files on a PR that changed 2; 15.9% of PRs get more than 30). Makes the file-set consistency gate **blocking**, not precautionary. | Both defects manufacture BROKE, both scale with PR size, and so both re-enter as A16's confounder through a third door. A dry run is not the gate and does not satisfy it — but it found two corpus-level faults that would have inflated the outcome variable silently. |

| **A25** | 4.14 | A PR with **no changed function body** is excluded as a **restricted estimand**, counted apart from resource attrition and carried into the bounds. Attrition is reported **cross-tabulated by commit count and corpus file count**, never pooled; if it tracks either, A17's bounds must cover `parent_commit` failures and not only the file-set gate. The estimand is stated as **function-body changes only**. | A smoke run lost 32% of PRs with `parent_commit` dominating — shape detection failing when the corpus file list does not match the change, which tracks patch size. That is differential exclusion on the study's own confounder, and a single attrition percentage cannot show it. Coding zero-symbol PRs as UNEXPOSED would put real breakage (import and constant edits do break callers) into the unexposed arm — the error that manufactured RR 8.0, arriving from the other side. |

| **A26** | 4.15 | **Tightens the outcome rule on its two named defects, before the labels are drawn.** The breakage pattern matches the commit **subject** only, not the squash body; and a later commit counts as a repair only if the PR's files are at least a quarter of what that commit touched. Adds **clone timeout** as a named exclusion in A17's bounds. | The pilot's rate came back at **27.3%** against the published PR-level figure of 11.3% — 2.4x the reference, on a corpus skewed toward small single-commit changes that should sit *below* it. Both causes were already diagnosed, so fixing them after labelling would burn an iteration of the gate on a rule known to be broken. Both changes can only remove verdicts, never add them. **CORRECTED by A32: the reference was the wrong arm.** The pilot is human-arm, whose published PR-level rate is 21.18% (`136/642`), not 11.3%. The excess was 1.29x, not 2.4x. **The two mechanical fixes stand** — subject-vs-body matching was diagnosed on pruna `017dc9a144` and the focus threshold on its own logic; neither argument mentions a rate. What does not stand is the calibration story that motivated the timing, which rested on a comparison against the arm this pilot was not measuring. **CORRECTED a third time by A38, and the rate justification is now WITHDRAWN rather than restated.** A26 was timed against a 1.29× excess over the human reference; the uncontaminated excess is **1.66×**, and the commit-count cap was suppressing it from the other side while A26 tightened the rule to reduce it. **The two mechanical fixes stand on their own arguments** — subject-vs-body matching was diagnosed on `pruna 017dc9a144`, the focus threshold on its own logic; neither cites a rate, and both can only remove verdicts, never add them. **The calibration story is struck, not re-derived.** It has been withdrawn twice already, and re-deriving it would tie it to a third number that is itself provisional (A38's 35.08% is a partial re-scan, not a clean walk). Stated plainly: **the outcome rule has never been calibrated against an uncontaminated measurement, and its justification does not depend on one.** **ADVISORY — no mechanism, and the reason is stated rather than the tag being a shrug.** What is withdrawn here is a JUSTIFICATION, not a behaviour: no code implements a calibration argument, so there is no call site a guard could reject, and `check_no_partial_clone`'s equivalent does not exist for a sentence. The two mechanical fixes remain enforced by their own tests. What would make this checkable is the thing to watch for: any future text that re-derives a calibration claim for A26 must cite a walk that postdates A38 and A39, and there is none yet. |

| **A27** | 4.16 | **The outcome scan must walk the PR's own base branch, not the clone's default.** 15.5% of PRs merge into `dev`, `develop` or a feature branch; `scan_outcome` walks from HEAD, so their post-merge history is invisible and every one of them reads CLEAN. Also: `merged_at` asserted before `merge_commit_sha` is read, a merged PR with a null merge sha becomes `no_merge_sha`, and file-set verification requires **exact equality** rather than a ratio. | A superset passes a ratio gate. When a PR's commits land via another pull request the merge sha belongs to that other PR, shape detection resolves a parent confidently, and if the other PR carried nothing else the file sets differ only by what they share — a wrong parent that passes verification, which is the one failure surviving every downstream check. And a false CLEAN on 15.5% of the corpus biases the outcome toward the null in a way no bound would show. |

| **A28** | 4.17 | **Supersedes A2's detection rule.** Shape is decided by the SEQUENCE of the PR's commit subjects — at least two consecutive matches walking back from the merge — with the diff-coverage rules kept only as a fallback when the API returns no subjects. Records the hand-verification: 19 of 20 resolved parents agree with `merge_commit_sha`'s first parent, all five of the 21+ band among them — which over a sample of 16 squashes and 3 merge commits confirms that **none was misrouted to rebase**, and, since the resolver returns `merge^1` for both those shapes by construction, is not independent evidence of anything more. The sample contained **no rebases**, so that branch was measured and verified separately: it fires on **4 of 88 multi-commit PRs (4.5%)** across three repositories, its shape is confirmed by a committer-timestamp test that reads no message text, and **all 4 of its parents are correct** against that structural truth — each differing from `merge^1`, which is what makes the check meaningful there and near-tautological everywhere else. Also makes `UNSCANNABLE` a **counted exclusion at every consumer**, not only at the scan, and adds the unreachable-merge prevalence **measured at admission**. | A2 detected shape by diff coverage against a file list the corpus supplies, and the corpus attributes 92 files to some three-file PRs — so detection failed on exactly the PRs whose file lists were wrong, at 17–70% across commit-count bands, differentially on patch size. Subjects come from the API and are independent of the corpus, which removes the file list from detection entirely. A single-subject match would not do: GitHub's default squash message reuses the title on a one-commit PR, so only a sequence of two distinguishes the shapes. **This changes which units are admitted, never a decision boundary** — no threshold, arm coding or verdict rule moves. **A28's FAILURE MODE DOES NOT OCCUR IN THIS CORPUS, AND THAT IS NOT THE SAME AS A28 BEING UNNECESSARY.** With A42's reclassification, `parent_commit` is zero in both arms — every parent-resolution failure here was a force-push — so the commit-count gradient has nothing left to measure, and the 25.0% top band that prompted the hand-verification was one repository's rewritten history throughout. A28's replacement of the file-set detection rule, A24's measurement behind it, and `pilot/gradient.py` all remain correct as written; they simply have no cases here. **A later corpus may have them, and these checks are what would show it.** |

| **A29** | 4.18 | **Clones are blobless.** `worktree.cloned` passes `--filter=blob:none` and asserts the server honoured it by reading back `remote.origin.partialclonefilter`; a denied filter is a failure, not a full clone served quietly. Supersedes A26's addition of **clone timeout** as a named exclusion in A17's bounds: the exclusion is not removed from the bounds but its measured incidence goes to zero on the eight repositories that defined it. The probe is reported per repository, and **"zero lazy fetches" is recorded as an artefact, not a property** — seven targets showed 0 and the one whose scan returned BROKE showed 20, because a BROKE verdict is what makes the scan call `commit.stats.files`, which needs contents. 20 is the figure to carry, not 0. | Nine repositories exceeded the clone timeout and they were the largest — an 11.5x median size difference against those that cloned — so a resource exclusion selected on repository size, which is A16's confounder arriving through the one door that was a property of our command rather than of the data. Measured: `blob:none` resolved 8/8 within budget, worst case 343.9s of 900s, every parent resolved and every pipeline completed; `blob:limit=1m` managed 4/8 and was eliminated under the rule fixed before the probe ran. **This changes which units are admitted, never a decision boundary.** Recovering eight repositories is not eight usable PRs — two carry no `.py` files at all. **UNSIGNED, and conditional.** This strategy FAILED its first live use: blobless clones supply file contents only by lazy fetch, and a diff over blobs that never arrived is empty rather than wrong, so twelve rejections came back at `derived=0` and seventeen of seventeen scored PRs read CLEAN. It is safe only with the contents assertion in `pipeline/assemble.py`, which raises `HarnessError` when the derived `.py` count falls short of GitHub's list — that assertion is the reason this amendment is signable at all, and removing it silently restores the defect. A31 fixes the stop rule that governs whether this amendment survives. **WITHDRAWN 2026-08-05 — A31 triggered.** The re-run with the contents assertion reproduced the first result exactly: `ingestr#2532214135` still derives zero symbols where the probe scored it BROKE, the three `no_python` rejections still derive zero against GitHub lists of 104, 65 and 40, and the recovered scored set is again 0 broke of 17 (p = 0.0049). The assertion never fired, because `api_files` truncates at `API_FILE_PAGE` and the guard therefore skips exactly the largest PRs — the same size selection this amendment existed to remove, relocated into its own safeguard. Blobless cloning is NOT adopted. The eight repositories stay excluded, A17 keeps the clone-timeout bound, and the 21+ band stays unresolved. **Enforced by `guard:check_no_partial_clone`.** The withdrawal below was recorded in this log while the flag stayed in `pipeline/worktree.py`; the guard is what makes the reversal real. |

| **A30** | 4.19 | **A harness failure is not a graph status.** PyCG's memory cap is probed against the kernel rather than inferred from `sys.platform`, the bound that actually applied travels on the result (`GraphResult.mem_cap`), and a subprocess that never launched raises `HarnessError` — re-raised ahead of `run_pipeline.one_pr`'s per-PR handler — instead of being recorded as `CRASHED`. | Found by running the harness on a third platform. `RLIMIT_AS` cannot be lowered on darwin under an unlimited hard limit, the `ValueError` fired inside `preexec_fn`, and **100% of invocations returned `CRASHED`** — a status that asserts the analysed repository defeated the analyser. The run would have completed and reported total attrition as a finding, which is ENVIRONMENT.lock Finding 4's shape one platform over. Every `GraphStatus` member is a claim about the corpus; "our environment failed" is a claim about us, and the two must not share a value. **No threshold, verdict rule or arm coding changes. Admission DOES change on darwin** — units that were becoming `CRASHED` now receive real classifications, because a harness failure stopped occupying a corpus label. Saying "no decision boundary moved" was strictly true of the thresholds and misleading about the consequence. **Platform equivalence is a CONDITION, not a claim:** the controls gate must be run on any platform before the corpus runs there, and `RR 8.0 / 80-of-80 / super_chain 40-of-40` is the known-answer result it must reproduce. That converts an inference about `RLIMIT_AS` behaviour into a procedure that would have caught this defect in minutes. |

| **A31** | 4.20 | **A pre-fixed stop rule for A29's clone strategy, written before the re-run and before any result is seen.** The first live use of `--filter=blob:none` produced 17 of 17 scored PRs CLEAN (p = 0.0049 against the corpus base rate), twelve rejections with `derived=0` including three labelled `no_python` at `corpus_py` 104, 65 and 40, and — decisively — `bruin-data/ingestr#2532214135` derived zero symbols where the probe had scored it BROKE with 20 lazy fetches. Derivation and the outcome scan both need blob CONTENTS, which a blobless clone supplies only by lazy fetch; when that yields nothing the harness recorded it as a property of the repository. **The known-answer test is `ingestr#2532214135`, whose correct answer the probe already fixed at BROKE.** After the contents assertion lands, the re-run must satisfy all three: (a) that PR reads BROKE; (b) the three `no_python` rejections derive a non-zero file count; (c) the broke rate across the recovered scored set is non-zero and not extreme against 26.87%. **If (a) fails, `blob:none` is ABANDONED, not patched** — the eight stay excluded, A17 keeps the clone-timeout bound, and the 21+ band stays unresolved. | A29 adopted blobless cloning to close a size-selection door and opened a worse one onto the same eight largest repositories — the study's own confounder, entered from the other side, and biased toward the null in a way no bound would show. A recovered corpus resting on a clone strategy whose failure mode is not fully understood is worse than the smaller corpus it replaced: the original exclusion is visible and bounded, this one is invisible and reads as data. Fixing the mechanism blind and re-running until it passes would be tuning the instrument against the answer, so the abandon condition is fixed here while the result is still unknown. **Enforced by `guard:check_no_partial_clone`.** ABANDONED was honoured in prose for a day and not in code: the commit recording it touched thirteen files, none of them source, and both pilot arms were then walked under the withdrawn strategy. The guard rejects any `--filter` on a git clone, in any form. **DIAGNOSIS WITHDRAWN 2026-08-09. Strategy UNEVALUATED, not disproven. NOT re-adopted. Motivating problem UNREPRODUCED on the current platform.** Both evidence pieces are now non-defects. **(a)** "17 of 17 scored PRs CLEAN at p = 0.0049" is the signature A38 shows `MAX_COMMITS = 2000` produces, and the eight recovered repositories are exactly the high-velocity ones the cap silenced. **(b)** "three `no_python` rejections derive zero against GitHub lists of 104, 65 and 40" — **those numbers are `corpus_py_files`, the corpus's claim, not GitHub's.** GitHub's own `changed_files` for those PRs is **2, 9 and 2, with zero `.py` among them**; `mlflow/mlflow#14364` is "Fix API reference link in preview" and touches a CircleCI config and a docs sidebar. Derivation was CORRECT and those rejections were RIGHT. Neither piece is attributable to the clone filter, so blobless was never tested against — it is unevaluated rather than disproven. It is **not re-adopted**, and re-evaluating it has no payoff: the clone-timeout bound it existed to close measured **0 of 8** under full clones on darwin arm64 at a 900s budget, worst case 617.5s (68.6%), so the motivating problem is itself unreproduced here. A17's clone-timeout bound and the 21-plus band rest on this chain and may no longer cite A31 as settled. |
| **A32** | 4.5, 4.15, 6 | **The 90-repository pilot is the HUMAN arm, and every row now carries the arm it came from.** `handlabel/select.py` draws from the figshare replication package, which ships `human_pr_python`, `human_commit` and `human_commit_detail` and **no agent table at all**; `pilot/run.py` imported it as its population and inherited the arm silently. Confirmed four ways: the package's members; `eligible_prs` returning 608 ids, **608 in `human_pull_request` and 0 in `pull_request`**; all **236** canonical journal ids and all **139** admitted rows human, 0 agent; and the journal's repositories flooring at **528 stars**. `phase0/arm.py` now reads `pr_id -> arm` from AIDev's own `agent` column and `pilot/run.py` verifies the whole population **before the first clone**; `Candidate`, `Attempt` and the journal carry `arm`, appended last so older journals read `""` — NOT MEASURED, never back-filled. **Consequence: the pilot is a complete pilot of the COMPARISON arm, not the primary one.** Every shape metric it produced — 26.87% breakage, exposure rate, multi-site fraction, no-static-callee share, the commit-count gradient, the attrition split — is a human-arm number and none transfers. The agent arm needs its own population (AIDev `pr_commits`, 4,798 structural PRs, star floor 101 with 47.3% below 500, a different repository set) **and its own pilot** before its full run. | **A15 already contained the falsifying evidence and it was read the favourable way.** A15 records the human arm's floor as *503 stars with 0% below 500* against the agent arm's *101 and 47.3% below*. The pilot's own ≥500 floor was measured, matched that filter exactly, and was read as the agent arm self-selecting into the human band through attrition. The alternative was not merely untested — it was pre-registered, quantified, and in this file. Nothing lied at any point: `select.py`'s docstring says *"Every merged **human** Python PR"* and *"The human arm is used because it needs no GitHub token"*. The defect was a consumer treating "the population function" as arm-neutral, and **no record, row or report naming an arm to disagree with**. This is the thirteenth instance this session of one shape — a stage produced a complete, plausible, wrong result rather than an error — and the first where the field existed and was hardcoded, which is what made it read as a bug in the exposure pass rather than as the truth about the whole corpus. |
| **A33** | 4.19 | **Closes the two gaps A30's signature left open, and corrects one claim A30 made.** (1) **`mem_cap` never reached disk.** A30 states the applied bound "travels on the result"; it travelled as far as the in-memory `GraphResult` and was dropped at `measure.py` — zero reads outside the two defining files, no field on `PRAudit`, nothing in `Provenance`. **No record on disk stated whether its run was bounded.** `PRAudit.mem_cap` and `Provenance.platform` now persist; empty `mem_cap` means UNRECORDED, never "bounded". (2) **The probe authorised a call it never made.** `_probe` tested `(limit, hard)`; the hook applied `(limit, limit)`. Both now go through one function, `_lower_soft`, soft-only. (3) **Enforcement is now proven, on linux.** Two tests spawn a real child: one reads its actual limits back, one allocates past the bound and follows it through `classify()` to `OOM`. They SKIP where the cap is unenforceable, so **darwin reports enforcement as untested rather than green**. | **Observed, not inferred — A30's uncovered path (1) is now closed.** Run under docker on linux: `RLIMIT_AS` as found is `(-1, -1)`, the soft-only probe is accepted and restorable, the child dies with `MemoryError` and classifies as `OOM`, and the full `test_memory_cap.py` runs **7 passed** where darwin skips 2. Also observed: lowering the HARD limit is irreversible **even as uid 0** (`ValueError: not allowed to raise maximum limit`), which is why the divergence is resolved by sharing the soft-only call rather than widening the probe to match the hook — a probe of `(limit, limit)` cannot undo itself. The old hook's call is accepted on linux, so the divergence was **latent, not live**, there. The enforcement assertion was sabotaged twice to confirm it discriminates: a 1KB allocation and a cap-absent run both leave the child at returncode 0 and fail it. **Why this mattered beyond documentation:** on darwin `enforceable=False` means `preexec_for` returns `None`, so PyCG runs **unbounded** and `GraphStatus.OOM` cannot fire via `RLIMIT_AS` at all — leaving `UNANALYZED_RESOURCE`, the arm section 4.4 reads to decide *scalability product vs unsoundness product*, structurally empty with nothing on disk saying so. **The run platform must be decided before the full run**; if it is darwin, that arm needs a stated caveat. |
| **A34** | 4.4, 4.7, 6 | **Agent-stratified RR is reportable for CODEX ONLY, and the retrieval-strategy moderation is WITHDRAWN on power grounds — both fixed before any agent-arm number exists.** The agent population is now built (A32) and counted: **3,566 PRs across 389 repositories** — Codex 2,815, Devin 301, Copilot 271, Cursor 132, **Claude Code 47**. A17 called 459 Claude Code PRs "below the power floor"; **47 is not underpowered, it is absent** — before merge-status filtering, before admission, before exposure. Every non-Codex cell is DESCRIPTIVE and is labelled as such in Results; no relative risk is computed for one. The moderation hypothesis ("RR differs by agent retrieval strategy") required four contrastable strata and has 47 / 132 / 271 / 301 against 2,815. It is **withdrawn**, not quietly unreported, and not folded into a Codex-vs-rest contrast — that contrast is not the hypothesis, since "the rest" mixes three retrieval strategies and would answer a question nobody asked. | **Withdrawing a pre-registered hypothesis before seeing data is clean; leaving it in and not reporting it is not.** That is the entire reason this is written now rather than at analysis time. **A second finding, and the one that was not expected: the population filters are NOT agent-neutral.** Against A17's pre-filter shares, the structural + merged + `.py` filters move Codex **64.9% → 78.9% (+14.0pp)**, Copilot **14.8% → 7.6% (−7.2pp)**, Devin **14.4% → 8.4% (−6.0pp)**, Cursor −0.9pp, Claude Code −0.1pp. So the corpus is *more* Codex-dominated than A17's table implies, and the differential runs along the same axis A13 and A16 already treat as the study's exposure-side threat — this time entering at population construction rather than at admission. A14's "two-thirds the safest agent" is now **four-fifths**, which strengthens the conservatism argument for a positive and narrows the null further. **The briefing line gets sharper, not softer: the evidence is Codex evidence, the product's first integration is Claude Code, and this study does not close that gap.** Stated here so it is a scope statement written before the result rather than a limitation discovered after it. **ADVISORY — no mechanism, and the reason is stated rather than the tag being a shrug.** A withdrawn HYPOTHESIS is not a code change: nothing in the repository computes a retrieval-strategy moderation today, so there is no call site a guard could reject. What enforces it is that the analysis is not yet written and this row precedes it. If a per-agent RR is ever computed, that code must cite this row. |
| **A35** | 4.19, 4.4 | **The corpus runs on LINUX, and A30's platform-equivalence condition is now SATISFIED rather than pending.** Run under docker on linux/aarch64: the controls gate reproduces the known answer exactly — `gate_passed: true`, positive control **RR 7.999999999999995**, cluster-robust CI **[3.117, 20.531]**, **80** synthetic repositories, `super_chain` **40/40**, 1 of 4 mechanisms firing, all three negative controls passing (RR 1.077, 1.000, 1.000). `resolve(16)` returns `enforceable=True` there, so `RLIMIT_AS` applies, the child dies at the bound and `classify()` returns `OOM`. Artefact: `research/phase0/results/controls_linux.json`, carrying its own platform stamp. | **This is the decision the OOM arm was blocked on.** On darwin `preexec_for` returns `None`, PyCG runs unbounded, and `GraphStatus.OOM` cannot fire via `RLIMIT_AS` at all — leaving `UNANALYZED_RESOURCE` structurally empty. That arm is what section 4.4 reads to decide *scalability product vs unsoundness product*, so on darwin the question is not answered NEGATIVELY, it is **unanswerable**, which is a worse artefact than either verdict. Choosing linux converts it back into a measurement. **A patch-version discrepancy was raised and is CLOSED, not carried.** The container resolves CPython **3.10.19** where `ENVIRONMENT.lock` pins **3.10.20**. Checked rather than assumed: both are security-only releases — 3.10.19 covers libexpat, expat GC, tarfile offsets, zip64 and `html.parser`; 3.10.20 covers `email.generator`, `email.message`, `wsgiref.headers`, `http.cookies`, `data:` URLs and libexpat. **Neither touches `ast`, the tokenizer or the grammar,** and structurally neither could: the 3.10 branch accepts security fixes only. **A7's `SYNTAX_UNSUPPORTED` arm is therefore defined against the MINOR version, not the patch** — which is a stronger statement than the one this amendment first made, and it closes the thread instead of carrying it. The container is still pinned by digest for reproducibility, which is a different concern; see `ENVIRONMENT.lock`. |
| **A36** | 4.4, 4.7 | **A34's composition shift is inherited from the population, not manufactured by our filters — attributed to the stage that causes it.** Measured across the three filters in order: **merged-only** moves Codex 64.9% -> **75.0% (+10.1pp)** and costs Copilot 5.9pp and Devin 3.6pp; **requiring a mined commit** moves it **0.0pp** (every merged agent PR already has one); **requiring a `.py` file** adds the remaining +3.9pp and is close to agent-neutral (11.6%-17.3% of merged PRs qualify, and **Claude Code is the HIGHEST at 17.3%**). The cause is the merge rate itself: **Codex 82.6%, Cursor 65.2%, Claude Code 59.0%, Devin 53.8%, Copilot 43.0%** of each agent's PRs are merged. | **This is the difference between a property of the world and an artefact of ours, and it was worth the ten minutes to tell them apart.** Maintainers merge Codex PRs at nearly twice Copilot's rate; that is a documented feature of the corpus, consistent with the agent-fix rejection rate the source paper reports, and it would be present in any study of merged agent PRs. Our `.py` requirement contributes almost nothing and does not disadvantage the agent with the least data. So the +14pp is **not** a selection effect introduced by this instrument, and A13/A16's differential-exclusion machinery does not need to widen to cover it. What it does change is scope: the estimand is *merged* agent PRs, and merging is not independent of the agent. **A14's conservatism argument strengthens** — Codex is the lowest-breaking agent at 2.62% and the corpus holds more of it than AIDev does — and any null is correspondingly narrower. Recorded because "we checked and it is the data, not us" is only worth anything if the check is on record. |
| **A37** | 4.20 | **The contents assertion is REMOVED. Its premise died with A29 and it had begun inverting the bug it was written for.** `assemble.build_record` raised `HarnessError` when the derived `.py` count fell short of GitHub's, reasoning that contents must have failed to arrive. That holds only under `--filter=blob:none`, where a diff over blobs that never fetched is empty rather than wrong. With the filter removed (`guard:check_no_partial_clone`) a shortfall is an ordinary corpus condition, and it now falls through to `verify_files`, which labels it `file_set/integrity` and lets the walk continue. | **Caught by running it: the first full-clone human re-walk died at repository 6 of 90** on `BerriAI/litellm#2313919432`, deriving 2 of 4. The canonical pre-blobless journal rejects that same PR as `file_set/integrity` — a legitimate exclusion produced by the check built to produce it. The assertion had converted a fact about the repository into a claim about us, which is precisely the failure it was added to prevent, arriving from the other side. **The generalisable rule: a check whose claim holds only under one configuration must be REMOVED when that configuration goes, not left asserting something it can no longer know.** Its message still read "with --filter=blob:none that means a lazy fetch returned nothing" while no clone used that filter. Removing it loses nothing — `verify_files` compares the same two lists and, unlike the assertion, claims no cause. |

| **A38** | 4.15 | **The outcome walk is bounded by DATE, never a commit count, and an unreadable walk raises rather than reading as an empty window. THE CROSS-ARM COMPARISON WAS AN ARTEFACT OF UNEQUAL TRUNCATION. Both arms' breakage numbers are VOID; the next walk is the baseline, not a comparison to one.** `window.candidates` passed `max_count=2000` and walked newest-first from the tip; commits landing AFTER the window end hit `continue` but still spent that budget, so a repository that had since landed more than 2,000 commits exhausted the walk before reaching the window, returned `[]`, and scored CLEAN with `commits_examined = 0`. An absent authority is now `WindowUnreadable` → `Exclusion.WINDOW_UNREADABLE`, because returning `[]` for both "nothing landed" and "we could not look" is what kept this invisible. | **The arms were truncated at DIFFERENT rates — human 31.4% (60/191), agent 20.2% (20/99), Fisher p = 0.052 — and that manufactured the entire arm difference.** As published: human 23.04%, agent 26.26%. On PRs the scan could actually see: **33.59% and 32.91%, Fisher p = 1.000.** More of the human arm was blanked to CLEAN, so it read as the less breakage-prone arm. Truncated PRs broke at **0.00% in both arms** (0/60 and 0/20); P(0 in 60 \| p = 0.3359) ≈ 2×10⁻¹¹. Re-scanned with only the walk's bound changed — same `signals`, same `_touches_pr_files`, same A26 subject matching — **23 of the 60 came back BROKE**, all on `fix_touching_same_file`, `commits_examined` going from 0 on every one to a median of 62, and truncated vs reachable became statistically indistinguishable (Fisher p = 0.519). The cap accounted for the whole gap. A count cap selects on repository **VELOCITY**, which tracks size — A16's confounder entering through our command rather than the data, biased toward the null. Corrected human-arm rate **35.08%, not 23.04%** — 1.66× the published 21.18% reference rather than 1.09×. **That figure is PROVISIONAL**: it is 60 re-scanned PRs grafted onto 131 unchanged ones, not a clean end-to-end run. `scan.py` also held a dead duplicate `MAX_COMMITS` that nothing read, so the constant that looked authoritative could be edited with no effect and no failing test. **THE BASELINE WALK NAMED ABOVE NOW EXISTS: `agent_rewalk` and `human_rewalk`, both arms walked under this amendment and A39.** Both reproduce their original corpora exactly — agent 72 repos / 205 attempts, human 90 / 310, same repositories and the same per-repo distribution — so the comparison is pipeline-to-pipeline, not corpus-to-corpus. **The prediction this amendment made is confirmed: the arms are indistinguishable, agent 32.04% (33/103) against human 34.22% (64/187), Fisher p = 0.795.** The published 3.2pp arm difference was the unequal truncation and nothing else. Both arms also landed near the estimates made from partial data before the walk existed — agent 32.04% against 32.91% predicted from reachable PRs only, human 34.22% against the 35.08% partial re-scan — so 35.08% ceases to be provisional and is superseded by a measured 34.22%. Against the published human reference of 21.18%: agent 1.51x, human 1.62x. |
| **A40** | 4.14, 6 | **A deleted base branch resolves four ways, two of which are counted exclusions, and the threshold at which they become a scope limit is fixed HERE, before the numbers exist.** `base_ref` resolves → walk it. Gone, but the merge is in the default branch and arrived **inside** this PR's window → walk default and record the substitution per PR. Gone, merge in default, arrived **after** the window → `BASE_REF_WINDOW_SHIFTED`. Gone, merge not in default at all → `BASE_REF_UNRESOLVABLE`. **Both are reported separately AND combined.** If the combined share of scannable attempts exceeds **5%**, it gets its own line in Results as a **scope limit on the estimand**, not an entry in A17's bounds — bounds are for units whose outcome is unknown, and these are units the outcome variable cannot reach. Below 5% it is a footnote in the attrition table. | The threshold is pre-specified because the alternative is choosing it after seeing whether the number is inconvenient. Reported separately because they shrink the estimand for different reasons and a dominant one is information about which mechanism is doing the work: `WINDOW_SHIFTED` is a fact about the DATA, `UNRESOLVABLE` a fact about US. **They are not merged into a single "unreachable" count**, which would be the same collapse non-negotiable 3 forbids and that this study has now removed from the graph layer, the file list, the commit walk, the outcome table and the covariates. **No fifth category for squash-merged-and-deleted.** A squash writes a new commit, so the PR's own merge sha is absent whether the branch was squashed or abandoned, and separating them needs a content match on a diff that may have been modified in the squash, introduced independently, or arrived by another path — a heuristic dressed as a measurement. A category that could never fire while implying coverage is worse than an honest merge of two facts, which is the argument already made for tagging things ADVISORY. **`UNRESOLVABLE` is expected to be non-random**: it is decided by repository merge policy, and policy correlates with size, age and release discipline — the same axis as the clone timeouts, the commit-count gradient and the file-list truncation. So the repository's observed merge-strategy distribution is recorded beside the exclusion, converting "we could not measure these" into "we could not measure these, and here is what they have in common". **Measured before this row was written, and it contradicted the expectation that motivated the fourth arm:** on the four known deleted-base PRs the merge arrived in default after 1 minute, 3 minutes, 10 minutes and 3 days 12 hours — all INSIDE the window, so `WINDOW_SHIFTED` fired on none of them. That claim had been stated as a measurement and built upon before the query was run; `docs/CORRECTIONS.md` entry 4 records it. **THE SCOPE-LIMIT LINE CARRIES THE EXCLUDED COUNT, NEVER THE TRIGGER COUNT.** A deleted base branch is the trigger; only `WINDOW_SHIFTED` and `UNRESOLVABLE` are losses, and a PR recovered by substitution is measured, not lost. The recovery rate is recorded as a fifth number beside the four arms, because if most triggers recover then a trigger-based headline overstates the damage to the estimand by however many it recovered. The 5% threshold is evaluated against **excluded**, not triggered. **Measured trigger incidence, before any arm was counted: 21 of 316 admitted records, 6.6%, and ARM-ASYMMETRIC — agent 13/118 (11.0%) against human 8/198 (4.0%), Fisher p = 0.0199.** It is reported as *agent-arm PRs are concentrated in repositories whose merge policy deletes branches*, never as *agent PRs merge into deleted branches three times more often*: the second invites a causal reading the data does not support, and the concentration refutes it — two repositories contribute five each, so this is house style, not a property of agent-written PRs. **This is the first exclusion mechanism measured that differs BETWEEN arms rather than selecting on size in both.** A shared confounder shifts both arms together; this one shifts them apart, which is the more dangerous shape. **MEASURED 2026-08-10, on the first walk to record the exclusion reason as a COLUMN rather than infer it. `agent: merge_unreachable 2`; `human: base_ref_unresolvable 5, merge_unreachable 2`. ZERO `base_ref_window_shifted` in either arm.** Of 21 deleted-base triggers, **17 recovered by substitution and 5 are excluded — 1.6% of admitted records against this amendment's 5% threshold, so the scope-limit line does NOT fire.** The 6.6% trigger figure would have overstated estimand loss four-fold. The recovery rate is the number that decided it, and a trigger-based headline would have reported a scope limit that does not exist — which is precisely what pre-specifying against EXCLUDED rather than TRIGGERED was for. | **A41** | 4.4, 6 | **The re-walk that follows this amendment reports its arm comparison whatever it shows, and a newly significant difference is a FINDING, not a reason to hunt for another defect.** Recovery under A40's substitution arm will be unequal — 13 of the 21 triggers are agent-arm — so the current 32.04% against 34.22% at Fisher p = 0.795 may move, and may move apart. | Fixed before the re-walk runs, because the discipline has to cut both ways. The 3.2pp arm gap in the pre-A38 walk was an artefact and was found by chasing it; the same instinct applied to a REAL difference would keep searching until it disappeared. A study that investigates only the results it dislikes is not measuring, and the asymmetry A40 records gives a mechanism by which a genuine arm difference could exist. **THIRD CONSECUTIVE READING, and the comparison is stable rather than lucky: agent 37.07% (43/116) against human 35.05% (68/194), Fisher p = 0.807.** Identical to the second walk, because reclassification moves PRs between attrition categories and never into or out of the scanned set. Across three walks: 32.04/34.22 at p = 0.795, then 37.07/35.05 twice at p = 0.807 — indistinguishable each time, with the sign flipping once between the first and second. |
| **A42** | 4.14, 6 | **A merge commit that exists on GitHub and in no clone is `history_rewritten`, categorised `resource`, checked at ADMISSION before parent resolution.** **The mechanism is method-level; the prevalence is corpus-level, and the two must not travel together.** A rewritten history is unreachable to any consumer of a clone, so no time-windowed post-merge outcome variable can reach those PRs **in any study** — that follows from git's object model, not from this corpus. **The incidence measured here — 14% of agent-arm repositories (10 of 72) and 4% of human-arm (4 of 90) — is a property of this corpus and does not transfer.** | **`parent_commit` went to ZERO in both arms: every parent-resolution failure in this corpus was a force-push.** The resolver was being blamed for the repository rewriting its history, which put 14 agent and 10 human PRs in `integrity` — which BIASES the estimate — when they belong in `resource`, which NARROWS the estimand. One in seven agent-arm repositories force-pushed after merging a PR inside the seven-day window. This is Bird et al.'s "git history is revisionist", the one peril from the canonical list that applies to this corpus. **Related work independently draws the same distinction one level up:** Mockus, *"Was It Never Collected, or Rewritten Away? A Commit-Provenance Dataset Separating Ingestion Gaps from Upstream History Edits across the World of Code"*, arXiv 2607.02774 (2 July 2026), separates commits force-pushed away from commits a mirror never ingested and reports 6.47% rewritten against 40.18% never-ingested of 1.1 billion advertised commits — the same "a raw missing-commit number cannot distinguish the two" argument at corpus-mirror scale rather than at clone scale. **UNREAD beyond the abstract.** **The check first sat in `outcome/scan.py`, which runs only on ADMITTED records, so it could not reach the PRs it describes and fired ZERO TIMES across 515 attempts.** A check that structurally cannot reach its cases returns the same value as one that found nothing, and only the known-answer test on `featureform/enrichmcp` told them apart. |
| **A43** | 4.14, 6 | **The drawable pool is smaller than the admitted-record count, for two compounding reasons, and every statement about sample availability must use the reachable figure.** **(1) A CAP MISMATCH.** The walk admits up to `--per-repo 7`; the draw considers at most `MAX_PER_REPO = 3`. Of 86 unseen records in 31 repositories, **67 are reachable and 19 are structurally undrawable** — they exist, are admitted, count toward every corpus figure, and no draw can ever select them. That is a **22% overstatement** of the drawable pool. **(2) A DEPLETION RATCHET.** A stratified 10/10 draw removes BROKE faster than a 37% pool contains it, so each attempt leaves a CLEAN-richer residue and draw feasibility degrades monotonically with attempts, independently of pool size. Measured: previously drawn 15/32 = **46.88%** BROKE against the unseen remainder 28/84 = **33.33%**, corpus 43/116 = **37.07%** (Fisher p = 0.201 at n=32 — not significant, but mechanically expected rather than accidental). The two compound: the reachable subset is also the depleted one. | The fourth draw raised at 9 BROKE of 10 needed, 39 examined. `P(<=9 in 39 \| 0.3707) = 0.0468`, which rules out sampling noise as the sole cause. **The raise message was itself an instance of the class this project has spent the week removing.** It read "a base rate this far from expectation is a finding about the outcome rule, not a sampling inconvenience" — TRUE on a first draw from an undepleted pool, FALSE on a fourth, where the cause is depletion by design. One message, two opposite meanings, sending a future reader to investigate the classifier when nothing is wrong with it. `draw.py` now states both causes and how to tell them apart. **The remedy is to WALK MORE REPOSITORIES** — 72 of the agent arm's 389 were walked. Re-seeding only reshuffles the same pool (seed 20260811 repeated 9 of 20 PRs), and raising `MAX_PER_REPO` after seeing the answer defeats the cap that stops one repository supplying the sample. This also binds beyond the gate: `MIN_BREAKAGES_FOR_POWER = 20` in the exposed arm rests on the same records. |
| **A44** | 4.1 | **`POSITIVE_CONTROL_N = 30` is inert. The controls gate runs at `DEFAULT_PER_MECHANISM = 40`, and A30's RR 8.0 was measured at 40, not at the pre-registered 30.** The constant is declared in `controls/analysis.py`, exported through `controls/__init__.py`, and **read by nothing but a test asserting it equals 30**. | Found by grepping for the A43 cap mismatch, and it is the same class one step worse: there both limits did something and one starved the other; here one limit is live and the other is decorative. **The test makes it look enforced.** `assert POSITIVE_CONTROL_N == 30` returns the same result whether the gate builds 30, 40 or 400 units — rule 14's "unreachable" surface, in the check written to pin the pre-registered size. **40 is not wrong** — more units is a stronger control, and the gate passed at 40/40 detection — but the preregistration says 30, the code says 40, and nothing reconciled them. Recorded rather than silently amended: what the gate actually ran is the number that belongs in Results. Two instances make this a class rather than a note — a module-level constant that is exported, never read outside its own definition, and tested only for its literal value is mechanically detectable, the same shape as `check_enforcement_map`'s orphan check. **No guard yet.** |
| **A39** | 4.14 | **Verification uses GitHub's file list or none. The corpus list is NEVER substituted as authority.** An absent list is `no_file_authority`, categorised `resource` and counted; `corpus_files` leaves the `verify_files` signature entirely. The ratio path survives only for a GitHub list at the page limit, where the authority is still GitHub and merely incomplete. **Admission rates are not comparable across this change — and nothing prior survives to compare to, since A38 voids both arms. The next walk is the first walk.** **A25's decision rule now reads `attrition_by_github_file_count`.** The corpus-banded table is retained for continuity and marked as corpus attribution. Substituting a measured instrument for an unmeasured one changes neither the rule's threshold nor its direction. **Both tables are reported in the next walk; a material disagreement between them is itself a finding about corpus attribution and belongs in the composition section.** | `authority = merge.api_files or corpus_files` gated admission at 0.6 agreement against a list measured as unreliable — **and no amendment ever authorised it.** It was inherited, never argued. The corpus OVER-attributes: verified live and fully paginated, it claimed 104, 65 and 40 `.py` files for PRs whose real GitHub lists were 2, 9 and 2 files with **zero** `.py` among them (`mlflow/mlflow#14364` is "Fix API reference link in preview" — a CircleCI config and a docs sidebar). So a **correct** diff scored against an inflated expectation falls below threshold and is rejected at `file_set` — an `integrity` verdict, asserting the repository's account of itself cannot be trusted, for a gap that was ours — and it lands hardest on the PRs the corpus mis-attributes most, which tracks size. A16's confounder entering through our own gate. A25's rule could not have kept the old table regardless: A39 removes `corpus_files` from the signature, so a rule pointing at a table built from an authority the pipeline no longer consults would be a rule with nothing behind it — the A31 failure, where an amendment said one thing and the code did another. **Two existing tests failed on this fix and BOTH were pinning the fallback rather than the gate:** `test_an_honest_pr_becomes_a_record` passed only because the corpus list stood in for GitHub's. Once the fallback is gone the single-page fetch at `github_pulls.py` is load-bearing; `no_file_authority`'s incidence in the next walk measures where it bites. |

**A8 is the one that most needed to be pre-registered.** Switching to cluster-robust
inference after seeing a confidence interval would be indistinguishable from moving the
goalposts, whatever the motivation.

Amended by: Claude Opus 5, 2026-08-04; A29 and A30 added 2026-08-05; A32-A37 added
2026-08-05. **A32 changes what the existing pilot IS** — a complete pilot of the
comparison arm — and is the only amendment in this log that reclassifies data already
collected rather than changing what will be collected next.
Reviewed by: *(sign before running Stage A)*.

**A30 signed 2026-08-05 by Claude Opus 5 (AI agent, not a human reviewer).** Verified
before signing: the amendment describes what `d126d24` actually changed; it moves no
threshold, arm coding or verdict rule, and no unit changes arm on a platform where the
cap already applied; and the fix is exercised end-to-end by the controls gate passing on
darwin at RR 8.0 over 80 of 80 units with `super_chain` 40/40 — the census → PyCG → join
path that returned `CRASHED` on 100% of invocations before it. `test_memory_cap.py`
pins the probe, including that it restores this interpreter's limits rather than capping
them for the life of the run.

**Two paths this signature does NOT cover, listed rather than implied.** (1) **Linux
equivalence is inferred from reading the code, never observed** — `resolve()` returns
`enforceable=True` there and `preexec_for` yields an equivalent limiter, but no run has
happened on that platform. The controls-gate condition above is what closes it. (2) **The
cap is proven ACCEPTED, never proven to FIRE** — `setrlimit` succeeds and the bound
travels on `mem_cap`, but no test drives a process past the limit and observes it killed,
so `UNANALYZED_RESOURCE`'s OOM arm is unverified enforcement. Both must be closed before
the full run, not before the exposure pass. Sabotage verification WAS applied to
`test_memory_cap.py`: forcing the probe to claim success regardless fails
`test_probe_agrees_with_what_the_kernel_does_right_now`, so the tests catch a regression
in the central claim.

**Both uncovered paths are now closed by A33, and one sentence in the signature above was
wrong.** "the bound travels on `mem_cap`" was true only of the in-memory object: nothing
read it, `PRAudit` had no such field, and no record on disk stated whether its run was
bounded. Linux equivalence is now **observed** rather than inferred — the full
`test_memory_cap.py` runs 7 passed under docker on linux where darwin skips 2 — and the
cap is proven to **fire**, through `classify()` to `OOM`, sabotaged twice to confirm the
assertion discriminates. What remains open and is stated rather than implied: **on darwin
enforcement is still untested, because there the cap cannot be applied at all.** That is
not a gap in the test; it is the platform, and the tests now say so by skipping.

**This signature is an AI review and should not be read as human sign-off.** It is
recorded as such deliberately: the value of a reviewer line is that it says who checked,
and a signature that hides what signed it is worth less than no signature. A human
co-signature before the FULL run remains advisable; it is not claimed here.

**A29 was withdrawn under A31 rather than signed.**

**A29 and A30 both precede data collection.** A29 records a change
that was already in the code and not in this file — the clone strategy changed, and the
amendment log did not say so, which is the failure this log exists to prevent. Neither
amendment moves a threshold, an arm coding or a verdict rule. Both must be signed before
the exposure pass runs, because that is the run whose corpus they determine.

---

## 1. The question

Does the label `unresolved` carry predictive information about whether an AI-authored code
change breaks something?

If yes, the product exists. If no, the labels are decorative and QuantaMind Context should
not be built. There is no third outcome, and no amount of engineering elsewhere rescues a
null result.

## 2. Why this must run first

Everything in `ARCHITECTURE.md` and `docs/BUILD_PLAN.md` Phases 1+ assumes this
correlation. Building any of it before measuring is the failure mode we have already paid
for once: a real problem, a plausible mechanism, and no evidence anyone bleeds from it.

**No product code is written until this file has a Results section.**

---

## 3. Design

Retrospective cohort study over AI-authored pull requests.

- **Unit of analysis:** one changed public symbol within one agent-authored PR.
  Not one PR — a PR may change ten symbols with different exposure.
- **Population:** agent-authored PRs in Python repositories from the AIDev dataset
  (HuggingFace `hao-li/AIDev`, Zenodo `10.5281/zenodo.16899501`), AIDev-pop subset —
  530 Python projects with ≥100 stars. Human PRs are the comparison arm and run in the
  **same pass**, not a later one. **[A1]**
- **Design:** 2×2 contingency table, relative risk with a 95% confidence interval.

**Corpus arithmetic — fixed before the run** (see amendment **[A1]**):

| Stage | Agent | Human |
|---|---|---|
| Python repos, AIDev-pop | 7,191 | 1,402 |
| Filtered to structural task types (`feat`/`fix`/`perf`/`refactor`/`chore`) | **4,798** | **1,026** |
| Merged only — required, the outcome is a 7-day post-merge scan (69.3% acceptance) | **~3,300** | ~700 |
| PyCG succeeds (~78%; the rest is the UNANALYZED arm, not discarded) | ~2,570 | ~550 |

`docs/findings/PHASE0_RUNBOOK.md` `PHASE0_PREREGISTRATION.md` “Design” carries the per-stage expected shape and the stop
conditions if any of these come out far off.

### 3.1 Exposure variable — fixed

At the **parent commit** of the PR (never the merged state — that leaks the outcome):

**Obtaining the parent commit. [A2]** The AIDev dataset does not carry it. The
`pull_request` table has `id, number, title, body, agent, user_id, user, state,
created_at, closed_at, merged_at, repo_id, repo_url, html_url` and no base, head or merge
SHA; `pr_commits` has `sha, pr_id, author, committer, message` with no parent field and no
ordering field, so the PR's first commit cannot be identified from it either. Merge
metadata is therefore fetched once per PR from
`GET /repos/{owner}/{repo}/pulls/{number}` and cached. **A GitHub token is a prerequisite
of this study**, not an implementation detail. Responses are cached to disk so a re-run
consumes no quota — `PHASE0_PREREGISTRATION.md` “Pre-specified confounders” of the runbook requires the whole thing be reproducible from raw
data.

**The parent is `merge_commit_sha^1`, not `base.sha`.** `base.sha` is the commit the PR was
*opened against*; for a long-lived PR that can be weeks stale, and exposure would be
classified against a repository state that never immediately preceded the change. What this
study needs is the trunk state the change **landed on**, because that is the code that then
broke.

That is well defined for merge commits and squash merges. It is **not** well defined for
rebase merges: GitHub replays each commit onto the base individually, with new SHAs and no
merge commit, so for a PR of N > 1 commits `merge_commit_sha^1` is the PR's own
second-to-last commit rather than trunk.

Detection is by **diff coverage**, not by commit message. A squash commit's message is the
PR title and body, which matches no individual `pr_commits.message`, so a message-matching
rule would silently reject every squashed multi-commit PR — the most common case on GitHub.

| Case | Detection | Parent |
|---|---|---|
| Merge commit | `merge_commit_sha` has ≥ 2 parents | `merge_commit_sha^1` |
| Squash | 1 parent, and the commit's diff covers the PR's **entire** changed-file set | `merge_commit_sha^1` |
| Rebase, N > 1 | 1 parent, and the diff covers only a **proper subset** of that set | walk back along first-parent while each commit's changed files ⊆ the PR's file set and its author matches a `pr_commits.author`, at most `count(pr_commits)` steps; parent is the first parent of the earliest such commit |
| Ambiguous | the walk exceeds `count(pr_commits)` steps, or stops on step 1 with a partial diff | **exclude, and count as corpus attrition** |

The changed-file set comes from `pr_commit_details`. The ambiguous bucket is reported in
Results alongside clone failures rather than quietly dropped, and the rule is validated
against a fixture repository merged three ways — once per strategy.

Run **vanilla PyCG, entry-point scoped, no custom resolvers.**

**Scope rule — the census and the graph must see the same files. [A3]** PyCG reports
`{caller_fqn: [callee_fqn, …]}` with no line numbers and no record of sites it failed on,
so "a call site PyCG did not resolve" is not something PyCG reports — it is computed by
joining our tree-sitter census against PyCG's edge set. If the census walks a wider file
set than PyCG was given, every call site outside PyCG's scope has no possible edge and
exposure inflates toward 100%. One function computes the file set and both stages consume
it. `PHASE0_RUNBOOK.md` `PHASE0_PREREGISTRATION.md` “If the result is null” Q4 lists "exposure ≈ 100% → classifier degenerate" as a stop
condition; this is the mechanism that would cause it.

For each changed symbol `S`, enumerate every call site referring to `S` and classify:

- **EXPOSED** — one or more call sites referring to `S` exist that PyCG did not resolve,
  or `S` sits in a file PyCG timed out / OOM'd on.
- **UNEXPOSED** — every call site referring to `S` was resolved by PyCG.

**Granularity: the primary analysis is restricted to single-site pairs. [A6]** The
definition above is stated at *call-site* granularity. PyCG resolves at
**(caller, callee) pair** granularity — it emits a set of callees per caller, so a function
`F` calling `S` both directly and through `getattr` produces one edge `F → S`, and asking
whether that edge exists marks **both** sites resolved. The unresolved one is invisible,
and the bias runs toward UNEXPOSED, toward RR ≈ 1, and therefore toward the stop rule in
`PHASE0_PREREGISTRATION.md` “Decision thresholds”. It is the most expensive direction for an artefact to point.

The property is not measurable at pair granularity. It is measurable *exactly* on a subset:

| Sites in `F` matching `S` | Measurable? |
|---|---|
| Exactly one | **Yes** — `S ∈ edges[F]` ⟺ that site resolved |
| Two or more | No — pair granularity collapses them |

The census already counts sites per pair, so the split costs nothing.

1. **Primary analysis: single-site pairs only.** On this subset the instrument does exactly
   what this section says it does, and the headline number needs no caveat.
2. **Sensitivity analysis: multi-site pairs, coded both ways** — all EXPOSED for an upper
   bound, all UNEXPOSED for a lower bound. If the verdict is identical at both bounds, the
   collapse provably does not affect the conclusion, and that is a number rather than a
   disclosure.
3. **Fallback, fixed now so it is not a rescue later:** if the pilot projects `a < 20` in
   the single-site exposed arm, the primary analysis reverts to the full sample with the
   bias documented. The switch and the projection that triggered it are recorded in the
   amendment log **before** the full run. **That projection is read against the
   cluster-adjusted effective sample size of `PHASE0_PREREGISTRATION.md` “Observations are clustered, and the CI must say so”, not the raw event count** — the
   restriction and the clustering both shrink effective N, and evaluating either alone
   would trip the fallback at the wrong threshold.

The **opposite** bias is also measured rather than disclosed: matching call sites by short
name over-matches, since `validate` also catches `other.validate` and
`UnrelatedClass.validate`. Fifty matched sites from the pilot are hand-checked and the
false-match rate reported.

**Matching an edge to a symbol. [A9]** Two defects in PyCG's naming were found by
running it, not by reading about it. Both are silent: a name mismatch does not error, it
returns no edge, and the site reads as unresolved.

1. **Path separators leak into module names.** `acme/sub/deep.py` is named `sub\deep` on
   Windows and `sub/deep` elsewhere — a path separator where a dot belongs. Normalised to
   dots at the point PyCG's output is parsed.
2. **The same function has two names.** At its definition site it is `sub.deep.helper_fn`;
   where an import resolved it, `acme.sub.deep.helper_fn`. This is the name-resolution
   mismatch DyPyBench measured at roughly 12% of observed differences, and it lands on the
   join directly.

An edge target therefore matches a symbol when the two are equal, **or when either is a
dot-boundary suffix of the other**. The dot boundary is required so `revalidate` never
matches `validate`.

**Bias direction, stated before the run: leniency errs toward UNEXPOSED**, because it finds
edges a strict comparison would miss. That is toward the null and toward the stop rule —
the same conservative direction as A6, and the reverse of a rescue. Strict equality was
rejected precisely because its bias runs the other way: it would inflate the exposed arm
for every layered repository in the corpus, which is the direction that manufactures a
positive.

**Diagnostic:** the pilot reports how many matches were exact and how many required
prefix tolerance. If tolerance is doing most of the work, the join is resting on a
heuristic rather than on agreement, and that must be visible before the full run.

**Capability profile of the exposure variable — measured, not assumed. [A10]**

Exposure is operationalised by matching a call site's **callee name** to the changed
symbol. That has a consequence which was measured before the run, by probing four
unresolvable-caller mechanisms with an empty edge set, so that a miss is structural rather
than something PyCG happened to resolve:

| Mechanism | Detected | Why |
|---|---|---|
| `super()` chain | **yes** | the site names `validate`; the edge is simply absent |
| computed `getattr(m, cfg[k])()` | no | no call site carries the symbol's name |
| string-keyed registry `REGISTRY[k]()` | no | same |
| registering decorator, `HOOKS[0]()` | no | same |

**One of four.** A call dispatched through a *value* carries no name, so nothing can be
attributed to the symbol, the symbol produces no pair at all, and it reads **UNEXPOSED
while having a hidden caller.**

**What this variable actually measures** is therefore *"named call sites whose edge PyCG
did not emit"* — in practice, largely `super()` chains — and **not** *"call sites we cannot
resolve"*. That is narrower than the prose above, and narrower than the worked example in
`README.md`, which is a computed `getattr`.

**Bias direction: false negative, toward the null.** Consistent with A6, A7 and A9, and for
the same reason: an instrument that under-detects and still shows lift is stronger
evidence, not weaker.

**Diagnostic:** the pilot reports the share of non-builtin call sites carrying **no static
callee name**. That is the prevalence half of the Judge decomposition, and it bounds how
much of the problem this variable is structurally blind to. If it is large, the gap between
what we measure and what the product claims is large too, and that belongs in
`PROJECT_CONTEXT.md` before any sales conversation.

**Parse failures are attrition, not an arm. [A7]** PyCG parses with its host interpreter's
`ast`, pinned at CPython 3.10 (`research/phase0/ENVIRONMENT.lock`). A repository using
`except*` (3.11) or `type X = …` (3.12) therefore fails to parse **because our toolchain is
behind, not because the code is dynamic.**

- **`UNANALYZED_RESOURCE`** — timeout or OOM. This is the third arm, and the only thing
  `PHASE0_RUNBOOK.md `PHASE0_PREREGISTRATION.md` “Agent composition”` reads when deciding whether this is a scalability product rather
  than an unsoundness product.
- **`EXCLUDED_SYNTAX`** — parse failure attributable to interpreter version. **Excluded
  from the study**, reported as corpus attrition exactly like a repository that will not
  clone.

Merging the two would let a fact about our toolchain decide what company this is. The
pilot reports the `EXCLUDED_SYNTAX` share for its own sake: if it is large on a 2026
corpus, vanilla PyCG on 3.10 may not be a viable instrument at all, and that is far
cheaper to learn on 200 PRs than on 3,300.

**Why vanilla PyCG and not our labeler:** this is the *crudest* instrument available, and
crudeness is the conservative choice. Adding resolvers can only move sites from exposed to
unexposed, shrinking the exposed group. **If the crude instrument shows no lift, a better
instrument cannot manufacture one.** This also dissolves the chicken-and-egg — the test
does not depend on any code we have not written.

Builtin call sites are excluded from both arms. Per DyPyBench they are ~59% of the apparent
static/dynamic gap and are irrelevant to a developer.

### 3.2 Outcome variable — fixed, and deliberately NOT AST-based

**Primary outcome: a revert or fix commit touching the changed file within 7 days of merge.**

Operationalised as any commit in the 7 days following merge that:
- reverts the PR's commit (git revert, or a commit message matching `revert`), **or**
- modifies a file the PR modified **and** whose message matches
  `fix|bug|broke|regress|hotfix|revert` (case-insensitive), **or**
- is linked to an issue opened within 7 days that references the PR **[A4 — optional]**

**[A4]** The first two criteria run from the local clone and need no API quota. The third
requires the GitHub issues API and is therefore an **optional enrichment**: it is run if
quota allows and skipped otherwise. Whether it ran is stated in Results. A criterion that
silently did not execute would make two runs of this protocol produce different outcome
variables under the same name, which is the ambiguity this document exists to remove.

**Why not the AIDev breaking-change labels.** The published study
<cite index="358-1">"leverages an abstract syntax tree (AST) based analysis to detect potential breaking
changes."</cite> AST-based detection can only observe breakage at statically resolvable
sites. Using it as ground truth would make the outcome variable **structurally blind to
exactly the breakage this thesis is about**, producing a false null. The ruler cannot
measure the thing.

Revert-and-fix signals are noisier and are produced by humans reacting to real failures,
independent of any static analysis. Noisy and independent beats clean and contaminated.

**Secondary outcome (recorded, not decisive):** CI status flip — green at merge, red on the
next run of the same workflow.

**Tertiary (recorded for comparison only):** the AIDev AST-based label. If our primary and
this one disagree, that disagreement is itself a publishable finding about how breakage in
AI-authored code is under-measured.

### 3.3 The table

|  | broke (revert/fix ≤7d) | did not break |
|---|---|---|
| **EXPOSED** (≥1 unresolved call site) | a | b |
| **UNEXPOSED** (all call sites resolved) | c | d |

**Relative risk** = `[a / (a + b)] / [c / (c + d)]`, reported with a 95% CI.

A raw count of "how many breakages were at unresolved sites" is **explicitly rejected as
an analysis.** With ~15% of call sites unresolved, 15% of breakages at unresolved sites is
zero signal that looks like confirmation. Only the ratio carries information.

### 3.4 Observations are clustered, and the CI must say so [A8]

The unit of analysis is a changed symbol, but symbols are **not independent observations**:

- Many symbols share one PR, and the outcome is measured per file — a single revert
  commit assigns the same outcome to every symbol the PR touched in that file.
- Many PRs share one repository, and repositories differ systematically in fix-commit
  rate, review culture, test coverage and framework density. Three of those are already
  named as confounders in `PHASE0_PREREGISTRATION.md` “Pre-specified confounders”.

The Katz log method assumes independent Bernoulli trials. Under clustering it **understates
variance**, so the confidence interval comes out too narrow — and it comes out too narrow at
precisely the boundary that decides the project, since `PHASE0_PREREGISTRATION.md` “Decision thresholds” turns on whether the CI lower
bound clears 1.5 and whether it includes 1.0. A naive CI could clear a threshold that a
correct one would not.

**Fixed before data:**

1. **Primary inference is cluster-robust, clustered at the repository level** — the
   outermost cluster, which absorbs the PR level beneath it. Estimated as a modified
   Poisson regression (log link, binary outcome) with a robust sandwich variance, which
   yields a relative risk directly. `statsmodels` GEE with a Poisson family and `repo_id` as
   the group provides this; it is not hand-rolled.
2. **The naive Katz CI is reported alongside, explicitly labelled as such.** The gap between
   the two is the design effect, and it is a number the reader is entitled to see.
3. **The reported design effect** (ratio of cluster-robust to naive variance) goes in
   Results whatever it is.

**Power is restated in clustered terms.** `a ≥ 20` counts events, and 20 breakages drawn
from two repositories are not 20 independent observations. Results must therefore also
record **the number of distinct repositories contributing at least one exposed-arm
breakage**, and the floor is read against the effective sample size, not the raw count.

This is recorded now because switching to cluster-robust inference *after* seeing a
confidence interval would be indistinguishable from moving the goalposts, whatever the
motivation.

---

## 4. Decision thresholds — fixed before data

Every CI below is the **cluster-robust** one from `PHASE0_PREREGISTRATION.md` “Observations are clustered, and the CI must say so”. The naive Katz interval never
decides anything; it is reported for comparison only.

| Result | Verdict | Action |
|---|---|---|
| **RR ≥ 3.0**, CI lower bound > 1.5 | Strong | Proceed to the call-site census layer. The label predicts breakage. |
| **RR 1.5 – 3.0**, CI excludes 1 | Weak but real | Proceed, **but the pitch changes** from "we prevent breakage" to "we prioritise review attention." Re-do the business case in ``PROJECT_CONTEXT.md` “Business case”` before building. |
| **RR < 1.5** or **CI includes 1.0** | Null / underpowered | **Stop.** See `PHASE0_PREREGISTRATION.md` “If the result is null”. |

### 4.1 Control design [A11]

`PHASE0_RUNBOOK.md` “Positive control” names a Django fixture. This amends that, and it lands before the
control runs.

**Why not Django.** A control that times out returns `UNANALYZED_RESOURCE`. The gate would
then be measuring our timeout rather than our instrument, which tests nothing about
detection. RUNBOOK itself expects ~22% of real repositories to time out.

**Two halves, each establishing something the other cannot:**

| Half | What it establishes |
|---|---|
| **Synthetic repositories** — small, purpose-built, one mechanism each | `graph_status == OK` is guaranteed, so a failure to detect is **unambiguously a detection failure**. This is the only place RR ≥ 5 carries meaning. |
| **One real repository** (5–20k LOC, genuine package structure) | The pipeline survives nested packages, `__init__.py` re-exports, relative and conditional imports, C extensions — all things synthetic repos are clean of by construction. |

The real repository is chosen to run **comfortably inside 600 s, not to stress it**. Scale
is what the pilot measures, on real corpus repositories, where a timeout is a legitimate
recorded outcome rather than a broken control.

**Its `graph_status` and duration are reported.** If the real control repository times out,
that is a finding about instrument viability and it surfaces — never grounds for quietly
substituting a smaller repository until one passes.

**The control corpus is not representative of the study corpus.** It isolates detection and
under-represents scale by construction. Stated here so no reader mistakes it for a sample.

**Gate unchanged: pooled RR ≥ 5.** Requiring all four mechanisms to fire was rejected —
that converts the control into a *capability requirement*, forcing resolvers to be built
before the thesis may be tested, which inverts the point of the correlation test. The control
characterises the instrument; it does not certify it.

**Per-mechanism detection is reported alongside, and the reading is fixed now:**

| Pattern | Meaning | Consequence |
|---|---|---|
| 4/4 fire | broad | Null scope: unresolvability generally |
| 2–3 fire | partial | Null scoped to the detected mechanisms, **named individually** in `PHASE0_PREREGISTRATION.md` “If the result is null” |
| **1/4 — only `super()`** | narrow | Null scoped to statically-named unresolved sites, per A10. **Explicitly not a claim about dynamic dispatch.** |
| 0/4 | broken | **Stop.** Not a null — fix the instrument. |

The third row is the likely one given A10, and the point of fixing the reading now is that
the headline sentence gets written before anyone is motivated to write it generously.

**Into `PHASE0_RUNBOOK.md `PHASE0_PREREGISTRATION.md` “Pre-specified confounders”`'s authenticity checklist:** if only `super()` fires, record
that `super()` is PyCG's single best-documented blind spot — the easiest possible positive,
and therefore weak evidence of general detection capability. Better said by us than worked
out by a reader.

### 4.2 Control corpus construction [A12]

Written after the first control run, **before** the corrected one, because the first run
exposed a construction defect rather than a result.

**What happened.** The pooled RR of 8.0 was computed from 50 of 80 units. All 30 exclusions
fell in the **exposed** arm and none in the control arm: symbols reached only by
value-dispatch have zero matching call sites, so A6 excludes them, while their matched
control twins have a resolvable direct call and remain. Coding the excluded units the other
way gives RR = 2.0. **A 4× swing produced by asymmetric absence alone.**

**Invariant, and it is general rather than a patch:**

> **If an exposed unit is excluded, its matched control twin is excluded with it.**

Pairwise, automatic, and it holds for mechanisms not yet built. A corpus that drops 75% of
one arm and 0% of the other is broken *whichever way it pushes the ratio* — the test being:
would this change be made if the result had been RR = 2.0 and failed? Yes. That is what
separates a fixture correction from motivated reasoning.

**Two consequences:**

1. Mechanisms the instrument cannot see belong to the **capability table only** and never
   to the pooled RR. A11 already said this in principle; the corpus did not reflect it.
2. With one mechanism firing, 10-vs-10 is too thin. The firing mechanism scales to
   **40/40**, so the control has power rather than a wide interval around a fragile point.

**The gate is not changed.** Adding a `bounds_agree` condition after seeing a disliked
result would be a threshold change, and tightening is as much a degree of freedom as
loosening. The bounds diverged because the corpus was asymmetric, not because the world is
uncertain — so the cause is fixed and the unchanged gate is re-run.

### 4.3 Differential exclusion by arm [A13]

**This is a threat to the main study, not only to the control**, and nothing in this
document previously checked for it.

Every exclusion category plausibly removes exposed units faster than unexposed ones:

| Exclusion | Correlated with exposure? |
|---|---|
| `UNANALYZED_RESOURCE` (timeout / OOM) | **Yes** — dynamic code is harder to analyse |
| `EXCLUDED_SYNTAX` (A7) | plausibly |
| Multi-site collapse (A6) | **Yes** — more call sites, more chance of collapse |
| No static callee (A10) | **Yes, by definition** — that is the dynamic-dispatch category |
| Ambiguous parent (A2) | possibly |

The control measured what this mechanism can do: **RR 2.0 → 8.0**. On the real corpus
nobody plants it deliberately, which makes it harder to notice, not weaker.

**Fixed before the run:**

1. Exclusion counts are reported **by arm and by reason** — never a single attrition total.
2. **Differential-exclusion check.** If the exposed-arm exclusion rate exceeds the
   control-arm rate by more than **10 percentage points**, or if the bounds below diverge on
   the `PHASE0_PREREGISTRATION.md` “Decision thresholds” verdict, the pooled RR is **not** the headline result; the bounded reading leads.
3. **Bound every exclusion**, as A6 bounds multi-site: code all excluded units UNEXPOSED
   (lower) and EXPOSED (upper), report both. **Divergent bounds mean no general claim.**
4. **The pilot reports exclusion rate by arm**, so this is known before the full run rather
   than at analysis.

**And the defect A6 was found to have generalises.** A zero-site symbol returned `None` for
`primary` *and* for both sensitivity bounds, so the largest exclusion category was invisible
to the very mechanism built to make exclusions visible.

> **Every bound must be computable for every exclusion category — or the category is
> unbounded and must say so.**

That is the typed-absence principle turned on our own sensitivity analysis.

### 4.4 Agent composition — the result is mostly about Codex [A14]

Computed from the live `pull_request` table, 33,596 rows:

| Agent | PRs | Share |
|---|---|---|
| **OpenAI Codex** | 21,799 | **64.9%** |
| GitHub Copilot | 4,970 | 14.8% |
| Devin | 4,827 | 14.4% |
| Cursor | 1,541 | 4.6% |
| **Claude Code** | **459** | **1.4%** |

**Two consequences, fixed before the run:**

1. **RR is reported by agent**, and `PHASE0_PREREGISTRATION.md` “If the result is null” scopes the finding accordingly. "Unresolved sites
   predict breakage in agent PRs" reads as a general claim while resting on one agent.
2. **The product targets Claude Code users, and the evidence will contain 459 of their
   PRs.** That belongs in `BRIEFING.md` beside the market argument, not only here.

Recorded with it: the arms cover overlapping but non-identical windows — agent PRs
2024-12→2025-07, human PRs 2025-01→2025-06. A limitation, not an assumption of
comparability.

### 4.5 The human arm is not a matched control [A15]

**Settled by joining the two tables, not by computing a related quantity.** An earlier
version of this amendment cited `min(stars) = 101` over all 2,807 repositories. That
measures the **agent** arm's floor; the dataset card's claim is about the **human** subset.
Correct measurement, wrong quantity — the same error shape as the confidence column.

The join that answers it: `human_pull_request ⋈ repository`, 6,569 of 6,618 PRs matched.

| | min stars | median | max | repos below 500 |
|---|---|---|---|---|
| **Human arm** (810 repos) | **503** | 4,194 | 203,424 | **0.0%** |
| **Agent arm** (2,807 repos) | 101 | 564 | 203,424 | **47.3%** |

The dataset card is correct, and **the mismatch is far larger than a threshold difference
suggests: 47.3% of agent repositories sit entirely below the human arm's floor.** The
Python slice joins to exactly **1,402 human PRs across 162 repositories** — matching the
breaking-changes paper's figure precisely, which confirms it is this table — with a median
of **14,933 stars** against the agent arm's 564. A 26× difference in median popularity.

Comparing the arms therefore confounds *agent vs human* with *repository popularity* to a
degree that would dominate any modest effect, and `PHASE0_PREREGISTRATION.md` “Pre-specified confounders” already names repository activity as a
confounder.

**Handling: stratify by star band (≤500, >500) and report both**, rather than restricting.
Restriction would discard 47.3% of the agent arm. Stratification keeps them, and the >500
stratum is the only band where an agent-vs-human comparison is even defined.

49 human PRs did not join to a repository row and are corpus attrition, counted.

### 4.6 Missing data — and what is *not* missing [A16]

**Supersedes A13's mechanism.** A13 correctly identified differential exclusion as a
threat and specified an ad-hoc margin. This replaces that with named methods, and it first
draws a distinction A13 merged.

#### The control's exclusion is not missing data

The units excluded from the control are not cases whose exposure status exists and went
unobserved. A symbol with **zero statically-named call sites has no measurement to be
missing** — the instrument definitionally cannot classify it. That is not loss to
follow-up; it is a **restricted estimand**.

So the control needs no imputation and no bounding. It needs an honest label:

> RR = 8.0 **among symbols with ≥1 statically-named unresolved call site.** Recall against
> planted exposure: 25%. Not an estimate for dynamically-dispatched unresolvability, which
> the instrument cannot measure.

That is what A11's reading table already said. The corpus hid it by including unseeable
mechanisms in the pooled arm; A12 removes them. The estimand was always restricted.

#### The real study does have missing data, and it is likely MNAR

`UNANALYZED_RESOURCE`, `EXCLUDED_SYNTAX`, ambiguous parents, unreadable repositories —
these are units with a **real exposure status we failed to observe**. That is loss to
follow-up, and the mechanism is plausibly *not* at random: complex dynamic code both times
out more (exposure-related) and breaks more (outcome-related). Missing-not-at-random.

**The `PHASE0_PREREGISTRATION.md` “The table” 2×2 is a complete-case analysis**, which is unbiased only under MCAR and biased
under MAR and MNAR. The control measured what asymmetric absence alone can do to this
estimate: **RR 2.0 → 8.0**.

And the honest limit, stated up front: where missingness depends on unmeasured causes,
neither imputation nor weighting removes the bias. The bias is **not identifiable**. What
*is* available is quantifying how much of it the conclusion survives.

#### Fixed before the run

1. **Primary: complete-case RR, cluster-robust, labelled `complete-case`** in Results, with
   exclusion counts **by arm and by reason**. Never a single attrition total.
2. **Worst-case bounds** — all excluded coded UNEXPOSED (lower) and EXPOSED (upper). This is
   the outer envelope. **Divergent verdicts across the bounds mean no general claim.**
3. **Tipping-point analysis.** Report the *breakage-rate multiplier* among excluded PRs
   required to push RR below the `PHASE0_PREREGISTRATION.md` “Decision thresholds” threshold of 3.0. A multiplier of 4× is implausible and
   the result is robust; 1.2× is not and it is fragile. **Run only if the primary analysis
   is positive** — stress-testing a null is a fishing exercise, and pre-specifying the
   direction prevents it.
4. **IPCW as a supporting analysis, never the headline.** Missingness here is predictable
   from measured variables — `graph_status`, multi-site count, no-static-callee share,
   patch size, files touched — so exclusion probability can be modelled and observed units
   weighted. Recorded as supporting because uptake of the method in applied epidemiology is
   limited and an unfamiliar headline estimator invites the wrong argument.
5. **The pilot reports exclusion rate by arm.** If the difference is material, `PHASE0_PREREGISTRATION.md` “If the result is null” leads with
   the bounds and the tipping point, not the point estimate.

### 4.7 Agent stratification, and a predicted moderation [A17]

Extends A14 with what the composition means once it is crossed against the source paper's
per-agent breaking rates.

| Agent | Share of corpus | Breaking rate (arXiv 2603.27524) |
|---|---|---|
| **OpenAI Codex** | **64.9%** | **2.62% — lowest of five** |
| GitHub Copilot | 14.8% | 3.04% |
| Devin | 14.4% | 4.09% |
| Cursor | 4.6% | 4.20% |
| **Claude Code** | **1.4%** (459 PRs) | **5.10% — highest** |

**The corpus is two-thirds the safest agent, and that is conservative.** If the effect
appears anyway, it appears under unfavourable conditions. **Recorded in `PHASE0_PREREGISTRATION.md` “If the result is null” as strengthening
a positive**, since a reader will otherwise see only "65% one agent" and read it as a
weakness.

**Agent-stratified RR is reportable for Codex only.** 459 Claude Code PRs, through the
structural filter, the merged filter and into the exposed arm, lands far below the `a ≥ 20`
floor. Stating this now stops someone computing it at analysis time and reading noise.
Claude Code is **descriptive at best**, and said as such. **[A34] Measured: 47, not 459.**
The structural and `.py` filters take it there before merge status or admission are even
applied, so "descriptive at best" is now the whole of what any non-Codex stratum gets.

**A moderation hypothesis, pre-registered rather than discovered.** The five agents differ
in retrieval strategy — Claude Code greps with no index, Cursor uses embeddings, Devin
maintains its own index, Codex operates in a sandboxed checkout. If unresolvability predicts
breakage **because the agent could not see the caller**, then retrieval strategy should
*moderate* the effect, and Codex-heavy pooling would wash it out.

> Predicted: RR differs by agent retrieval strategy, where power permits.

If it appears, it is mechanism evidence for the causal story. Found afterwards, it is a
story fitted to a number. This paragraph is the difference between the two, and it costs
nothing to write now.

**WITHDRAWN [A34]. Power does not permit, and the population is now built rather than
estimated.** The agent arm is **3,566 PRs across 389 repositories**:

| Agent | Post-filter | Share | A17's pre-filter share | Shift |
|---|---|---|---|---|
| **OpenAI Codex** | **2,815** | **78.9%** | 64.9% | **+14.0pp** |
| Devin | 301 | 8.4% | 14.4% | −6.0pp |
| GitHub Copilot | 271 | 7.6% | 14.8% | −7.2pp |
| Cursor | 132 | 3.7% | 4.6% | −0.9pp |
| **Claude Code** | **47** | **1.3%** | 1.4% | −0.1pp |

Two things follow, and only the second was expected.

**The filters are not agent-neutral.** Codex gains 14 points at population construction —
before admission, before exposure, before any outcome is read. Copilot and Devin lose 7.2
and 6.0. The corpus is four-fifths one agent, not two-thirds, so A14's conservatism
argument is *stronger* and any null is *narrower* than that section states. This is
differential attrition on the same axis A13 and A16 already treat as the study's threat,
entering one stage earlier than either of them looks.

**47 is not a power problem, it is absence.** That count is before merge-status filtering
and before admission. The only admission rate ever observed is 58.9% (139 of 236) and it
is from the *human* arm, so it is an illustration of the order of magnitude and not a
projection — nothing from the human pilot transfers. Whatever the agent arm's own rate
turns out to be, 47 does not survive it, exposure and an `a ≥ 20` floor.

So the moderation contrast cannot be run. It is **withdrawn**, and deliberately not
salvaged as Codex-versus-everyone-else: "everyone else" pools three different retrieval
strategies, and a significant result there would answer a question this hypothesis never
asked. Non-Codex cells are reported **descriptively and labelled as such**; no relative
risk is computed for one.

**The consequence for what this study can claim, written before the result:** the evidence
is Codex evidence. The product's first integration is Claude Code. The correlation test
does not close that gap, and no amount of pooling makes it close it.

### 4.8 Prior-work scan — novelty holds, and is now stated precisely [A18]

Run 2026-08-04, before the pilot. Sources: the AIDev "papers using" list (15 papers, all
assessed), the MSR 2026 mining-challenge list (~8 assessed of 62), and targeted searches on
call-graph analysis, call-graph-based defect prediction, and static-analysis coverage as an
exposure.

**No paper uses static resolvability of a changed symbol's callers as an exposure variable
predicting downstream breakage.** The claim is now sharper than "nobody has done this",
because three adjacent literatures exist and each is genuinely different:

| Literature | What it does with the call graph | Why it is not this |
|---|---|---|
| **Call-graph accuracy** — PyCG, Jarvis, InferCG, *Total Recall?* (ISSTA 2024), ML-based pruning | Measures and improves it | Treats unresolvability as **the thing to fix**. We treat it as **the signal**. |
| **Call-graph defect prediction** — CGBR, DeMuVGN | Uses graph *features* (centrality, coupling) to predict defects | Uses the graph where it **succeeds**. We use where it **fails**. |
| **AIDev empirical studies** — all 15 | PR metadata, textual similarity, task types, survival, security signals | Deepest structural work reaches **package manifests**, never call graphs. |

**The distinction in one line:** everyone else asks how good the graph is, or what the graph
predicts. Nobody asks what the graph's *inability to answer* predicts.

**Two findings with operational consequences:**

1. **A better instrument exists.** InferCG (TOSEM, March 2026) reports **+13.9% recall and
   +5.0% F1 over PyCG**, hybridising static analysis with LLM filtering. This does **not**
   invalidate `PHASE0_PREREGISTRATION.md` “Exposure variable”'s choice — vanilla PyCG was selected *because* it is the crudest
   available and therefore conservative, and a better instrument can only shrink the
   exposed arm. It is the natural the MRO and framework resolvers upgrade and is recorded in
   `PROJECT_CONTEXT.md` thread #5 beside Jarvis.
2. ***Total Recall?* (ISSTA 2024) is third-party support for A10's method.** Java rather
   than Python, but it establishes that ground truth for real-world programs is generally
   unobtainable and that dynamic baselines are the workaround. That is the same constraint
   that makes Judge's capability × prevalence decomposition the right approach here — and
   the reason A10 reports a *measured capability profile* rather than claiming coverage.

**Closest outcome variable found:** *Will It Survive?* (arXiv 2601.16809) — survival
analysis over 201 projects and 200k code units, modification hazard HR = 0.842 for
agent-authored code, predicted from **textual** features at AUC 0.671. Adjacent to our
revert/fix window, and notably weaker than the AUC 0.957 that patch size and file count
achieve (A16) — which is the confounder, not the mechanism.

**Live check, 2026-08-04.** Search indexes lag, so the arXiv `cs.SE` recent listing was
read directly — 201 entries covering 4–5 August 2026. Nothing there uses resolvability as
an exposure either. Two entries matter:

- **arXiv:2608.01927, DyRetriever** — repository-level code generation with context
  retrieved over a *partial dependency graph*, built on demand and discarded after use.
  Reports **+25.63% relative Pass@1 on CoderEval and +59.73% on DevEval**, 7.4× faster than
  static-graph baselines.
- arXiv:2608.01507 (agentic search for repo-level QA) and arXiv:2608.02499 (SWE-Touch) are
  adjacent but concern retrieval quality, not resolvability.

**DyRetriever is the first third-party evidence pointing *toward* our mechanism, and it
sharpens the pull-based retrieval test rather than settling it.** SWE-PRBench found structured context
*degrades* code **review** when **pushed** into the prompt. DyRetriever finds
dependency-graph context *substantially improves* code **generation** when **retrieved on
demand**. Those are compatible, and the axis separating them is exactly the pull-vs-push
distinction ``ARCHITECTURE.md` “Delivery is pull, never push”` bets the serving layer on.

It is not a substitute for the pull-based retrieval test: different task (generation, not review), different
benchmark, and no measurement of whether the retrieved context *carries* resolvability
labels. But it moves the prior — the delivery mechanism we chose is the one that works in
the one published comparison available.

**Scan is incomplete and recorded as such:** ~25 of 62+ assessed, plus the live listing for
this month. The challenge corpus predates our snapshot, so the "papers using" list was
prioritised and is now exhausted; the remaining challenge abstracts are the lower-yield
half.

### Power

Target ≥ 200 EXPOSED symbols with an observed breakage rate ≥ 5%. If `a < 20`, the
confidence interval will span 1.0 regardless of the point estimate. **That is not a
negative result — it is no result**, and reporting it as a negative would be as dishonest
as reporting it as a positive. Widen the corpus (more repos, longer window) before
concluding anything.

Record the achieved `a` in the Results section whatever happens, together with the number
of distinct repositories contributing to it (`PHASE0_PREREGISTRATION.md` “Observations are clustered, and the CI must say so”) — 20 events from two repositories do not
meet this floor.

---

### 4.9 The human arm's commit data is sourced, not mined [A19]

AIDev ships `human_pull_request` and `human_pr_task_type` but **no commit-level data and no
file patches** for the human arm. A2's parent resolution walks a PR's commits to decide
which merge shape applies; with no commits it cannot run at all. Until this was resolved the
human arm's cost was a GitHub-API mining job of unknown size — the largest open number in
the plan.

The AIDev_BC_Analyser replication package (figshare, CC BY 4.0) contains that mined data.

```
AIDev_BC_Analyser.zip   78,419,081 bytes
md5   7fc01c70cb4ed0210fab098d820de743   (published == computed)

human_pr_python.parquet          1,402 rows   id, number, repo_url, repo_id, merged_at, …
human_commit.parquet             7,376 rows   sha, pr_id, repo_url, pr_number, commit_message
human_commit_detail.parquet    110,047 rows   sha, pr_id, filename, patch
code_analyzer.py                   318 lines  the AST breaking-change detector
bc_analysis_{ai,human}.ipynb, human_data_processing.ipynb, README.pdf, requirements.txt
```

**Coverage, measured rather than assumed.** Of 1,402 human Python PRs, 1,042 are merged;
**1,009 of those 1,042 (96.8%) carry at least one mined commit SHA**. That is what A2 needs,
and it is effectively complete. The remaining 3.2% are attrition under A2's existing rule,
counted by resolution case — not a new exclusion.

A second figure gates less and must not be confused with the first: **607** merged PRs
across **90** repositories have at least one non-empty `.py` patch, because GitHub omits
patch text for large files. *(Corrected in A20: the "31.1% of `.py` patches" figure first
recorded here is patch-weighted and misleads at the PR level — one PR holds 79.3% of it.
At PR level 85.6% are complete. `PHASE0_PREREGISTRATION.md` “Missing patch text, traced to A16's confounder” carries the properly denominated numbers.)* Patch text
feeds only A2's shape *heuristic* and the tertiary AST outcome. The primary variable is
re-derived from `git diff parent..merged` against the checked-out tree (step 5's consistency
gate), so it depends on the SHA, not on the patch. **1,009 is the number that binds the
primary; 607 binds the tertiary.**

**A join hazard worth recording.** `pr_id` is `object` (string) in both commit tables and
`int64` in the PR table. Joining them directly yields **zero rows** — not an error, a silent
empty result that reads exactly like "the human arm has no commit data". It was caught only
because 1,325 distinct `pr_id` values against 1,402 PRs is not a plausible zero. Cast before
joining; the pipeline asserts a non-empty join rather than trusting one.

**The package is a superset of the published figures** — 7,376 commits and 110,047 patches
here against the paper's 5,788 and 93,044, i.e. pre-filter rather than contradictory. We use
our own filters, so the paper's post-filter counts are not a target to reproduce. Recorded
so that the difference is not later mistaken for a corrupted download.

**Reading `code_analyzer.py` sharpens two claims that were previously second-hand.**

1. **Their unmeasured recall has a named mechanism.** The detector reconstructs before/after
   source from hunk text alone and calls `ast.parse` on it; on `SyntaxError` it returns
   `None`, and `analyze` then skips the hunk. A hunk that fails to parse is therefore
   indistinguishable from a hunk containing no breaking change. Their validation was
   **precision only** — 95.7% / 93.6% on 94 sampled patches, κ = 0.79 — and precision
   sampling draws from what the tool *flagged*, so it cannot see this class at all. This is
   why `PHASE0_PREREGISTRATION.md` “Outcome variable” declines AST detection as the primary outcome; the reason is now sourced from
   the implementation rather than inferred from the paper.
2. **The gap they name in their own threats to validity is visible in the code.** The tool
   detects a changed signature and never asks whether anything calls it — there is no
   caller-side step anywhere in the 318 lines. Their sentence — *"some changes may affect
   functions with no downstream users"* — is not a hedge, it is the design. That gap is the
   product, conceded by a peer-reviewed paper about its own instrument.

**No decision boundary moves.** A19 changes where the human arm's commit SHAs come from and
records what fraction exists. The thresholds, the window, the outcome definition, the `a ≥ 20`
floor and A15's star-band stratification are untouched. The direction is toward feasibility,
not toward a positive: sourcing the data cannot make an effect appear, and the 3.2% loss is
counted against the human arm.

---

### 4.10 Missing patch text, traced to A16's confounder [A20]

A19 recorded that patch text is missing for large files. The chain that follows is worth
stating in full, because it enters A16's confounder through a door `PHASE0_PREREGISTRATION.md` “Pre-specified confounders” had not mapped:

> patch text absent → A2's shape heuristic degraded → parent resolved wrongly → step 5's
> consistency gate excludes the PR → **exclusion concentrates in large patches** → the
> corpus is differentially thinned on the one variable that reaches AUC 0.957 by itself.

Three links. Measured, not assumed — and measuring changed the answer at two of them.

**Link 1 fails, and in our favour.** A2's shape detection consumes **filenames**, not
patch bodies. Filenames are complete: **0 null of 110,047 rows**. So the primary path —
shape → parent → exposure — is not degraded by this at all. The chain does not reach the
primary variable.

**Link 2 holds, but it is an outlier phenomenon rather than a gradient.** The
patch-weighted rate of 31.1% recorded in A19 is a true number that misleads at the unit of
analysis:

| | |
|---|---|
| `.py` patches with no text | 20,091 of 64,698 — **31.1%**, patch-weighted |
| held by a single PR touching 35,884 `.py` files | **79.3%** |
| held by the top 5 PRs | **93.1%** |
| rate excluding those 5 PRs | **5.7%** |
| **PRs whose patch text is complete** | **710 of 829 — 85.6%** |

The unit of analysis is the PR. **85.6% is the honest figure; 31.1% describes one pull
request.** This is the same error the corrections log already records twice — a
distributional claim stated at the wrong denominator — and it is now caught by the rule
that a distributional claim cites a full-population statistic. It was recorded here one
commit earlier without its denominator, and is corrected rather than quietly rewritten.

**Link 3 survives, and the direction is what matters.** Whether it is a gradient or five
outliers, the PRs that lose patch text are the enormous ones. The **tertiary** AST outcome
is therefore size-biased, and biased toward losing the largest changes — which is where a
size-driven effect would live if size is doing the work.

**One pilot metric is added, and no exclusion is introduced.**

> **File-set disagreement rate by changed-lines quartile.** Step 5's consistency gate
> already converts a suspected wrong parent into counted attrition. What was not
> pre-specified is that the attrition must be *read by size*. If disagreement rises across
> quartiles, A16's stratified RR is not merely co-primary but the only quotable result, and
> A17's bounds must be computed over the size-stratified exclusion rather than the pooled
> one. `PHASE0_PREREGISTRATION.md` “If the result is null” states this outcome explicitly.

Adding a size cap on PRs would be the tempting alternative and is refused: it moves who is
in the corpus, which is a decision boundary, and it would do so on the exact variable under
suspicion. The metric is reported; the boundary does not move.

---

### 4.11 The 20-PR gate's protocol, first attempt [A21 — superseded by A22/A23]

> **Superseded. Read “The 20-PR gate, as it will actually run” instead.** The stride draw below is replaced by a
> stratified one (A22) and the rendered evidence sheet is withdrawn entirely (A23),
> because it showed the labeller the classifier's own input. What survives is the
> ≥ 16/20 floor, the refusal to score an incomplete sheet, and kappa as context.

`PHASE0_PREREGISTRATION.md` “Timeline” requires the outcome classifier to agree with hand-labelling on **≥16 of 20 PRs**, and
`PHASE0_PREREGISTRATION.md` “Timeline” is the only measurement in the correlation test whose validity is purely a property of *what order
two things happen in*. Nothing about that is checkable after the fact. So the protocol is
fixed here, and the ordering is enforced by the code rather than by intention.

**Arm: human.** The gate does not specify one, and the classifier reads git history and is
arm-agnostic. Human is chosen because A19's replication package supplies commit SHAs and
changed filenames directly, so **the gate runs with no GitHub token** — which is the point
of taking it before the pilot, since the token blocks everything downstream of it. Recorded
rather than assumed, because a reviewer will ask why the validation arm is not the arm the
thesis is about.

**Eligibility and draw.** Eligible: merged, at least one mined commit, at least one changed
`.py` file — everything a labeller needs to be able to judge at all, and nothing that could
correlate with the outcome. From **608** eligible PRs, sorted by `pr_id`, take every 30th.

The stride is not decoration. Taking the first 20 by id draws one narrow slice of calendar
time — ids are issued in order — so a classifier keyed on commit-message convention could
look better or worse purely by era. The realised draw spans **2025-01-01 to 2025-06-15
across 13 repositories**. Manifest sha256 `17109bac…fea9b93c`, which binds the set that was
labelled to the set that is scored.

**Three mechanisms, because the discipline is not a promise:**

1. **The sheet has no import path to a verdict.** `handlabel/sheet.py` and
   `handlabel/window.py` do not import `scan_outcome` or `fix_signals`, and a test parses
   their ASTs and asserts they never will. The sheet cannot render an answer by accident.
2. **No commit is annotated from its message.** `PHASE0_PREREGISTRATION.md` “Outcome variable”'s *definition* is shown — a labeller
   not told that a revert-or-fix is what counts is labelling a different variable — but a
   commit matching the classifier's pattern and one that does not must render to identical
   structure. Showing the regex would validate the classifier against itself.
3. **Scoring refuses an incomplete sheet.** All twenty or nothing; otherwise the gate can
   be met by labelling only the easy ones.

**Kappa is reported and is NOT a gate.** If all twenty PRs happen to be clean — entirely
possible, since a revert-or-fix inside seven days is well under a 50% base rate — then
"always answer clean" scores 20/20 and passes. That is the degeneracy `controls/analysis.py`
already refuses to score as a pass in the negative controls, reappearing one layer up.
Cohen's kappa is exactly the correction for chance agreement given the observed margins, and
the paper we are checking ourselves against reports κ = 0.79 for the same kind of exercise.

**It is a diagnostic only.** Adding a second threshold now would move a decision boundary,
which this study does not do — and tightening is as much a degree of freedom as loosening.
The report states raw agreement against the unchanged ≥16/20, kappa beside it, and, when the
sample is single-class, an explicit statement that **the gate had no discriminating power**
— which is neither a pass nor a fail but a reason to draw again.

**An unreadable window is not a quiet week.** A PR whose repository could not be cloned is
marked not-labellable, is excluded from labelling, and invalidates the gate until it is
readable. This is stated because the first implementation got it wrong in the most
instructive way available — see `ENVIRONMENT.lock`, finding 4.

---

### 4.12 The 20-PR gate, as it will actually run [A22, A23]

Supersedes “The 20-PR gate's protocol, first attempt”. Both changes are pre-data and both make the gate
harder to pass.

**A22 — the sample is stratified on the classifier's own verdict.** Ten PRs it called
BROKE, ten it called CLEAN, shuffled, exported as `label_id` and `pr_url` and nothing
else. The answers are written to a gitignored key that is not opened until the labels are
committed.

The arithmetic is the reason. A revert-or-fix inside seven days is well under a 50% base
rate, so a random twenty contains roughly **two** broken PRs — and a labeller who wrote
CLEAN twenty times would score about **18/20 and pass**. Balanced, that same labeller
scores **10/20 and fails**. The gate now tests the classifier rather than the base rate.

**This changes the estimand, and the change must be stated wherever the number is.**
Agreement on a balanced sample estimates the *average of sensitivity and specificity*,
not agreement over the corpus. It is a validation quantity, not a prevalence one. "80%
agreement" here does **not** mean the classifier is right 80% of the time in the wild, and
Results must not imply that it does.

Repositories are shuffled and capped at three PRs each rather than shuffling PRs directly:
one clone per PR is unaffordable, and stopping as soon as the buckets fill would otherwise
concentrate the sample in whichever repositories came first.

**A23 — the labeller judges breakage, not the rule.** The rendered seven-day commit window
built under A21 is withdrawn. It presented precisely the classifier's own input, which
would have made agreement partly true by construction — measuring whether a human can
apply a regex, not whether that regex is a good proxy for breakage. The gate is only
informative if the two sources of evidence are allowed to differ.

So the labeller gets the pull request URL and works from GitHub: the diff, the commit
history, **linked issues, CI runs, and discussion the classifier cannot read**. The
question is "did this PR cause something to stop working?", not "did the seven-day rule
fire correctly?" — the latter is a unit test and already exists.

**`UNSURE` is a first-class verdict**, scored as disagreement and reported separately. A
PR nobody can resolve in ten minutes is one the rule almost certainly cannot resolve
either, and a run with many of them is a finding about how much breakage is determinable
from history at all — which belongs in the limits section, not hidden in a forced guess.

**What survives from the superseded protocol, unchanged:** the ≥ 16/20 floor, the refusal to score an
incomplete sheet, and kappa reported as context rather than as a second threshold. Kappa
now excludes `UNSURE` rows, because coding them as either class would invent a judgement
the labeller explicitly declined to make.

**Iteration is bounded at three rounds and the count is recorded.** If the rule is
adjusted after a failure, the next round draws a **fresh sample under a new seed**.
Re-scoring the same twenty after adjusting the rule is fitting to one's own labels, and
three rounds is tuning where ten is fitting a classifier to a hope.

**The audit trail is a commit, not an assertion.** `human_labels.csv` is committed before
the key is opened, and `results/labelling.json` records that commit's SHA alongside the
seed and both bucket sizes. That is what makes the ordering checkable by someone who was
not present — including the author later, when the result is inconvenient.

---

### 4.13 What an agent-labelled dry run exposed [A24]

**This is not the gate and does not satisfy it.** The protocol requires a human, and the
reasons are recorded in “The 20-PR gate, as it will actually run”. A dry run was
performed by the assistant on a **separate sample under a different seed**, precisely so
the human sample stays unlabelled and its key sealed. Its value is not the agreement
number — an agent that has read the classifier cannot be assumed independent of it — but
the two corpus faults it surfaced.

**Result:** 11/20 (55%), kappa 0.100, no `UNSURE`. **Eight of nine disagreements point the
same way:** the classifier said BROKE where the labeller said CLEAN, every one of them via
`fix_touching_same_file`. Under the reading table that is *rule too loose*, unambiguously.

Two distinct root causes, both verified against specific commits.

**1. `FIX_PATTERN` matches squash-merge bodies.** `PrunaAI/pruna` commit `017dc9a144` is
titled `feat: accelerate support (#128)` — a feature. Its squashed body enumerates the
branch's commits, six of which begin `fix:`. The pattern is applied to the whole message,
so the commit reads as a repair.

> Most repositories squash-merge, and any sizeable feature branch contains a commit
> beginning `fix:`. The outcome rule therefore fires on **large feature PRs as a class**,
> and PR size is the variable that already reaches AUC 0.957 on its own.

**2. The replication package over-attributes files to a PR.** `zenml-io/zenml#3757`
changed **two** files, both under `docs/`. The package attributes **170 file rows and 92
distinct `.py` files** to it, spanning the entire server surface. The classifier duly
matched a later commit named `small bug` touching `runs_endpoints.py` — a file the pull
request never opened.

Measured across the package, per PR, distinct `.py` files attributed:

| p50 | p75 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|
| 4 | 15 | 52 | 94 | 237 | **28,180** |

**15.9% of PRs are attributed more than 30 `.py` files; 10.3% more than 50.** The median
of 4 is plausible, so this is a long tail rather than a uniform error — and a tail that
grows with how far the PR's base had diverged, which again tracks size.

**Both faults inflate the exposed arm and the outcome together, and both scale with patch
size.** That is A16's confounder arriving through a third door, after the two already
mapped.

**Consequences, all pre-data:**

1. **The file-set consistency gate becomes blocking.** Re-derive `changed_files` from
   `git diff parent..merged` and compare against the package's list. A PR whose sets
   disagree beyond the pre-specified threshold is **excluded as attrition**, not analysed.
   It was previously described as a precaution; it is now the thing standing between the
   study and a manufactured result.
2. **The outcome rule is applied to the commit *subject*, not the whole message.** The
   body of a squash merge is a changelog of the branch, not a statement about the commit.
   Recorded here rather than changed silently, and the pilot reports how many outcomes
   move.
3. **Both must be re-checked in the pilot** as explicit shape metrics: the file-set
   disagreement rate, and the share of BROKE verdicts whose evidence commit matches only
   in the body.

**A limitation of the dry run itself, recorded because it cuts against its own findings.**
The labeller gathered later commits through the GitHub API filtered by path on the default
branch, which misses commits landing on other branches. For one PR the stated reasoning
— “no follow-up at all” — was therefore wrong, even though the verdict survived scrutiny.
A human labeller working from the pull request page has the same blind spot.

**And one flaw in the design of the gate, found by running it.** The labeller knows the
sample is balanced ten and ten, because the protocol says so. That is an anchoring channel
the blind sheet does not close: a labeller who has counted fourteen CLEANs may feel pressure
toward BROKE. The bucket sizes should not be disclosed to whoever labels.

---

### 4.14 Zero-symbol PRs, and attrition that is not one number [A25]

A smoke run over 28 PRs in 12 repositories admitted 19. It is **not** the pilot — the
plan specifies 30 repositories and roughly 200 PRs, and at this size every rate carries
an interval too wide to plan against (attrition 32.1%, 95% CI **[18%, 51%]**). It
confirmed the plumbing and nothing else, and must not be quoted as a pilot result.

Two things it did settle, both pre-data.

**1. A PR that changes no function body is excluded, and it is not missing data.**

Three of nineteen records had zero changed symbols: `.py` files edited without any
function body changing — imports, module constants, docstrings. There is no exposure to
measure on such a unit. That is the same structure as a symbol with no statically named
call sites: the quantity is *undefined*, not *unobserved*.

Coding them UNEXPOSED would be the error that produced RR 8.0 in the control corpus,
arriving from the opposite direction. Import and module-constant changes **do** break
callers, so those units would sit in the unexposed arm carrying real breakage, and the
resulting bias runs in a direction nobody can predict in advance.

> **Excluded, counted as `restricted` attrition separately from `resource` and
> `integrity`, and carried into A17's bounds.** The estimand covers **function-body
> changes only**, and the limits section says so. That narrows the claim, which is the
> honest cost.

`pipeline/assemble.py` gives every rejection one of three categories, because they are
different claims and pooling them hides the one that matters:

| Category | Meaning | Effect on the estimate |
|---|---|---|
| `resource` | the unit exists, we could not obtain it | missing data |
| `integrity` | obtained, but the corpus's account cannot be trusted | missing data, **and correlated with size** |
| `restricted` | nothing to measure | narrows the estimand, does not bias it |

**2. Attrition is reported cross-tabulated, never pooled.**

The smoke run's dominant loss was `parent_commit` (7 of 9), not the file-set gate (2).
Shape detection fails when the corpus file list does not match the change — which is
exactly the divergent-base condition A24 measured, and which grows with commit count and
patch size. Rebase-merging projects skew larger and more process-heavy still.

So this is **A17's differential exclusion appearing at 32%**, not the residual the gate
was designed to catch. The pilot therefore reports admission rate **within** bands of
commit count and corpus file count (`pilot_report.py`), with the bands fixed here rather
than cut from the data — a boundary chosen after seeing the distribution is a degree of
freedom.

> **If admission falls monotonically across either set of bands, A17's worst-case bounds
> must be computed over `parent_commit` and `file_set` exclusions as well as the
> outcome's own loss to follow-up.** At 32% those bounds will be wide. Knowing the width
> before the point estimate exists is the entire reason this is written now.

**Pilot result — the trigger fired.** 30 repositories, 93 PRs attempted, 48 admitted
(51.6%). `parent_commit` failure against commit-count band:

| commits | n | parent_commit failures | rate |
|---|---|---|---|
| 1 | 27 | 1 | **3.7%** |
| 2–5 | 44 | 12 | **27.3%** |
| 6–20 | 18 | 8 | **44.4%** |
| 21+ | 4 | 2 | 50.0% |

That is monotone across the three bands carrying almost all the mass, and it is the
condition this section pre-specified. **A17's worst-case bounds must therefore be
computed over `parent_commit` and `file_set` exclusions, not only over the outcome's loss
to follow-up.** 28 of 93 units are `integrity` exclusions correlated with commit count;
bounds over that fraction will be wide, and that is the honest position.

`no_symbols` runs the other way — 16 of its 17 cases sit in the 1–4 file band, which is
what a restricted estimand should look like: small changes that touch imports or
constants and no function body. It narrows the claim rather than tilting it.

**A15 is confirmed on real records, not on a superset statistic:** all 48 admitted
records come from repositories with **≥ 500 stars**, with 21 distinct repositories and a
top-repository share of 14.6%.

**The pilot at full size — 90 repositories, 275 PRs, 154 records (56%).** The gradient is
now monotone across all four bands, at four times the earlier sample:

| commits | n | admitted | `parent_commit` failure |
|---|---|---|---|
| 1 | 104 | 63.5% | **2.9%** |
| 2–5 | 115 | 58.3% | **17.4%** |
| 6–20 | 43 | 41.9% | **30.2%** |
| 21+ | 10 | 30.0% | **70.0%** |

Spread is good — 65 distinct repositories, top-repository share 4.6%. **All 154 records
come from repositories with ≥ 500 stars**, so A15's common-support problem has resolved
itself through attrition rather than needing stratification; that handling can be dropped.

**And the skew is confirmed in the records themselves:** median 2 changed files and 2
changed symbols. The surviving corpus is the small, single-commit end of the distribution.

**Power: measured, and it is not the binding constraint.** 33 admitted records scanned,
**9 broke — 27.3%**, against the 5–20% the design assumed and far above the ~3% that would
have meant an underpowered corpus. Even discounted heavily this clears `a ≥ 20`.

> **But 27.3% is an upper bound, not an estimate.** The agent-labelled dry run in
> “What an agent-labelled dry run exposed” found the outcome rule *too loose* in eight of
> nine disagreements, from squash-merge bodies and file over-attribution. So the power
> question resolves into the accuracy question: there are plenty of events, and what is
> unknown is how many are real.
>
> **That makes the 20-PR hand-labelling gate the critical path, not a formality.** It is
> now the only remaining measurement that can invalidate the outcome variable, and it is
> the one a machine cannot do.

**The earlier 30-repo run was short of its planned size.** 93 attempted against the ~200 specified: the
first 30 repositories simply do not hold 200 eligible PRs at seven each. Every rate above
carries an interval accordingly, and the run is being extended across the remaining
repositories rather than quoted at this width.

**What the smoke run did not produce, and the pilot must.** Exposure rate, breakage rate,
multi-site fraction, no-static-callee share, `EXCLUDED_SYNTAX` share, instant-merge share,
star-band split, repository concentration, and the exposure-versus-patch-size correlation
that decides whether a pooled result is quotable at all. The last of these needs the
measurement stage, not just record construction.

---

### 4.15 The outcome rule, tightened before the labels are spent [A26]

> **CORRECTION [A32] — the reference below is the wrong arm.** Everything in this section
> compares a **human-arm** pilot against the **agent-arm** published figure of 11.3%. The
> human arm's published PR-level rate is **21.18%** (`136/642`, from the replication
> package's own notebook). Against it, the pilot's 27.3% is **1.29x**, not 2.4x, and the
> final journal rate of 26.87% (`36` broke of `134` scored) is **1.27x**, not 2.38x.
>
> **The two mechanical fixes stand.** Subject-vs-body matching was diagnosed on pruna
> `017dc9a144` — a squash body concatenating constituent messages so a `feat:` PR matched
> on a contained `fix:` — and the focus threshold rests on its own argument, that a
> 200-file sweep overlapping one of your files is not a repair. Neither argument cites a
> rate. Both were verified to remove verdicts only, never add them.
>
> **What does not stand is the calibration story.** "2.4x the reference, on a corpus that
> should sit *below* it" was the urgency, and it was measured against a population this
> pilot was not sampling. Read correctly the corrected comparison is *reassuring* rather
> than alarming: a seven-day behavioural repair window should catch somewhat more than an
> AST detector, and 1.27x is that direction at that rough magnitude. The rule is better
> calibrated than this section believed — measured against the right thing.
>
> The band below (`8–20%`, `below ~5%`, `above ~25%`) was fixed against the wrong anchor
> and **must be re-derived from 21.18% before it gates anything on the agent arm**, which
> has its own reference again. It is left unedited here because it was pre-registered and
> a band quietly moved after the fact is worth nothing.

The pilot measured a breakage rate of **27.3%**. The published PR-level rate for agent
changes is **11.3%**. Ours is 2.4x that — on a corpus the attrition has skewed toward
small, single-commit changes, which is the end of the distribution that should sit *below*
the reference, not above it. Read with the dry run finding the rule too loose in eight of
nine disagreements, the likeliest explanation is that a large share of those events are
ordinary follow-up commits rather than repairs.

That is not a power problem. It is a measurement problem wearing a power problem's
clothes, and it decides whether the corpus holds twenty real events or eight.

**Both causes were already named, so both are fixed now — before the sample is drawn.**
Fixing them afterwards would spend one of the three permitted iterations on a rule already
known to be broken.

1. **Match the subject, not the body.** A squash merge concatenates every constituent
   commit message, so a feature branch containing one commit that began `fix:` produced a
   body matching the pattern. `scan_outcome._subject` takes the first line. The revert
   check still reads the whole message, because `git revert` writes its marker in the body.
2. **A repair is aimed at what it repairs.** A commit touching two hundred files that
   happens to include one of ours is a release or a sweep; it overlaps almost any PR by
   construction. The PR's files must now be at least **`MIN_COMMIT_FOCUS` = 0.25** of what
   the commit touched. Chosen a priori, not fitted: the pilot's admitted records have a
   median of two changed files, so a genuine follow-up is small.

**Both changes can only remove BROKE verdicts, never add them.** The direction is toward
the null, which is the direction an amendment made without seeing the answer must take.

**How the re-measured rate is read — fixed before it is seen.**

11.3% is a **plausibility anchor, not a target**, and treating it as a target would be the
same error in better clothes. The two measurements are of different things:

| | measures |
|---|---|
| The published 11.3% | AST-detected API breaking changes, per PR |
| This study | a behavioural repair within seven days |

Ours should catch what an AST cannot — runtime, semantic and integration breakage — and
miss what it can: a changed signature nobody ever repaired because nothing called it,
which is that paper's own stated limitation. **The two should not agree exactly, and exact
convergence on 11.3% would be mildly suspicious rather than reassuring.**

- **8–20%** — consistent with a rule measuring the right thing. Proceed.
- **below ~5%** — over-correction. Inspect what the two fixes removed, by hand, before
  accepting it.
- **still above ~25%** — the tightening did not address the cause and the remaining
  events need diagnosis, not another threshold.

**No further tuning against this number.** The rule has now been changed once on named
defects; changing it again to land inside a band would be fitting to a figure from a
different study on a different outcome variable.

**Re-measured on the same 22 repositories: 27.3% → 17.6%** (9 breakages of 33 became 6
of 34). That is inside the 8–20% band fixed above, and it is deliberately **not** on
11.3% — it sits above the published figure, which is the direction the difference in
what is measured predicts. A seven-day behavioural repair window should catch runtime,
semantic and integration breakage that an AST-based detector cannot see.

**Attributed to each fix separately, over the same 33 records:**

| variant | broke | rate |
|---|---|---|
| neither fix | 9 | 27.3% |
| subject-matching only | 7 | 21.2% |
| focus threshold only | 7 | 21.2% |
| **both** | **6** | **18.2%** |

Each fix removes two verdicts on its own; together they remove three, so they overlap on
one. **Neither dominates**, which is the reassuring shape: had the focus threshold been
doing most of the work it would have been the more likely of the two to be cutting real
events, since it discriminates on breadth rather than on wording.

Exactly **one** PR was removed by the threshold that subject-matching had kept, and it was
inspected blind — verdict written before the counts above were read. It is correctly
dropped: a 71-file commit named `fix-a-lot`, landing the day after, in a window that also
holds a 158-file release commit. That is the sweep case the threshold exists to exclude,
not the "real repair plus unrelated cleanup" case that would have meant the metric rather
than its value was wrong. Recorded with its own caveat in `results/focus_inspection.md`.

The rule is now closed to further tuning. It was changed once, on two named defects,
before the labels were drawn.

**Over-removal is the risk the "can only remove verdicts" argument does not cover.** It
protects against inflation and not against losing real events, and `a >= 20` binds on the
exposed arm. So the drop is attributed to each fix **separately** — a legitimate repair
that also does unrelated cleanup across ten files scores 2/10 = 0.2 and is excluded by the
focus threshold. If `MIN_COMMIT_FOCUS` removes more than subject-matching does, the
excluded set is read by hand before the threshold stands.

**And that inspection is itself blind.** The dropped PRs are judged — *is this a genuine
repair?* — and the verdicts written down **before** the counts are read. Seeing "focus
removed 14" first means reading fourteen PRs with a number already in mind, and fourteen
looks like a lot or a little depending on what one was hoping for. Same protocol as the
20 labels, at smaller scale, and it costs nothing.

**What the inspection is looking for is a distinction, not a tally.** A 200-file
dependency bump or a formatting sweep that happens to touch one of our files is exactly
what the threshold exists to remove. A genuine repair that fixes our change *and* does
unrelated cleanup across ten files scores 0.2 and is removed wrongly. If the dropped set
is mostly the second kind, **the defect is the metric and not its value**: requiring the
intersection to contain a file the PR *modified* separates "swept up in a large commit"
from "repaired alongside other work", and raising or lowering 0.25 does neither.

**The rate is re-measured once more after the shape fix, before the labelling sample is
drawn.** Recovering the 2–5 and 6–20 commit bands adds back complex PRs, which is where
breakage concentrates, so 17.6% may move up. The sample must be drawn from the corpus the
study will actually run on — labels spent on a corpus that then changes are labels spent
twice.

**Clone timeout becomes a named exclusion.** `dagster-io/dagster` exceeded the 900-second
clone budget. Large repositories time out, and large repositories hold large pull
requests, so this compounds the commit-count gradient in the same direction as
`parent_commit`. It is counted as `resource` attrition and **carried into A17's bounds
alongside `parent_commit` and `file_set`** — otherwise it is loss that never appears in
the accounting at all.

---

### 4.16 The outcome scan was reading the wrong branch [A27]

Hand-verifying resolved parents surfaced something the parents themselves were not the
point of. Several resolved to commits that are not ancestors of the clone's `HEAD`, and
the reason is not a bad parent:

| PR | base branch | default | merge commit vs base |
|---|---|---|---|
| `AgentOps-AI/agentops#714` | `redesign` | `main` | behind |
| `AgentOps-AI/agentops#811` | `dev` | `main` | **no common ancestor** |
| `AgentOps-AI/agentops#817` | `dev` | `main` | **no common ancestor** |

Measured across 271 PRs with cached merge metadata: **42, or 15.5%, merged into a branch
other than the repository default** — `dev` (16), `develop` (6), and feature branches such
as `f/switch-to-pg` and `multi_sdfg`.

`scan_outcome._candidates` walks `repo.iter_commits()`, which starts at `HEAD`. For those
42 PRs the merge commit and everything after it may not be in that history at all, so the
seven-day window finds nothing and the PR is scored **CLEAN**.

> **That is a false negative, not a missing measurement**, and it is the same shape as
> every other defect this instrument has produced: an absence read as a result. It biases
> the outcome variable toward the null on a sixth of the corpus, and no bound computed
> over declared exclusions would show it, because these units are not excluded — they are
> counted as clean.

**The scan walks the PR's own `base_ref`.** `MergeInfo` already carries it. A base branch
that no longer exists, or one whose history has been rewritten so the merge commit is
unreachable from it, is a **typed exclusion** and never a clean verdict.

**Three smaller corrections land with it,** all from reading GitHub's documented
semantics rather than assuming them:

1. `merged_at` is asserted before `merge_commit_sha` is read. On an unmerged PR that field
   holds a *test-merge* commit that exists on neither branch — a different thing entirely.
2. A merged PR with a **null** `merge_commit_sha` is a real reported state, now the named
   exclusion `no_merge_sha` rather than a fall-through.
3. File-set verification requires **exact set equality**, not a ratio. A superset is not a
   near miss: it is the signature of a walk that went too far back, or of an indirect
   merge whose `merge_commit_sha` belongs to a different pull request. The ratio survives
   only where equality cannot be trusted — a corpus-supplied list, or a GitHub list
   returned at the page limit and possibly truncated.

**`indirect_merge` is still not detected as such.** The timeline signal exists but only on
repositories using rulesets, so its absence is uninformative and it cannot serve as a
negative test. What has changed is that the case can no longer pass silently: exact
equality catches it as `file_set`. Mislabelled, but excluded, which is the safe direction.

---

### 4.17 Detection stops reading the corpus, and the exclusion stops evaporating [A28]

Two changes, made together because the first decides which units enter and the second
decides whether an unmeasurable one is visible once they have.

**Detection by subject sequence.** A2 told squash from rebase by diff coverage against the
corpus file list. Both strategies produce a `merge_commit_sha` with one parent, so the
rule needed a discriminator, and the one it had was the corpus — which attributes 92 `.py`
files to some three-file PRs. Detection therefore failed on precisely the PRs whose file
lists were wrong, at 17–70% across commit-count bands, rising with patch size. That is
differential exclusion on the study's own confounder, arriving through the detector.

Commit subjects come from the API and are independent of the corpus:

| Case | Rule | Parent |
|---|---|---|
| two parents | true merge commit | `merge^1` |
| ≥ 2 consecutive subjects match walking back | rebase | earliest match's parent |
| otherwise | squash | `merge^1` |

**Which of these are documented, and which are ours.** GitHub states that the merge-commit
option *"is merged using the `--no-ff` option"*, so a merge commit is always created rather
than fast-forwarded. That a two-branch `--no-ff` merge has exactly **two** parents is a git
invariant — a property of the object format — and is *not* stated in GitHub's
documentation; citing it there would be citing a source that does not say it. The rule
reads `parents[0]` and so assumes two. An octopus merge would have more, `parents[0]`
would still be the trunk side, and no PR merge in this corpus produced one — but the
assumption is written down rather than left in the code.

The squash and rebase rows rest on documented behaviour rather than on our observations.
GitHub's rebase-merge *"always updates the committer information and creates new commit
SHAs"*, which is what the structural check below reads. Squash *"combines all commits in
the pull request into a single commit"*. And the squash message default is *the commit
title and message* for a one-commit PR, *the pull request title and list of commits* for
two or more.

That last one **predicts the data before it is looked at**: a multi-commit squash should
match zero subjects walking back, a one-commit squash exactly one, and only a rebase should
produce a run. The observed distribution over 88 multi-commit PRs is `{0: 84, 2: 2, 6: 1,
12: 1}`. A documented mechanism generating a predicted distribution is a different kind of
evidence from a rule fitted to a sample, and it is why the k ≥ 2 threshold is defensible
rather than merely convenient.

**A sequence, not a single subject.** GitHub's default squash message reuses the commit
title when a PR has one commit, so a squashed one-commit PR looks like a rebase under a
single-match rule — harmless there, since both give `merge^1`, but it means the test is
untested exactly where it would matter. A squash produces exactly one commit and can
therefore never yield two consecutive matches in order, whatever the repository's
`squash_merge_commit_title` setting, which the API will not report without push access.

**Detection may guess; verification may not.** The resolved parent is checked by diffing
`parent..merge` against GitHub's own `/pulls/{n}/files`, requiring **exact set equality**
(A27). Detection is a heuristic and is allowed to be wrong; the gate that admits a unit is
not.

**Hand-verified against ground truth, not against the attrition number.** An attrition
figure improves whether the recovered parents are right or wrong, so it cannot validate
this. Twenty PRs, five per commit-count band, were checked structurally: GitHub reports
`merge_commit_sha`, whose FIRST parent is the trunk commit the change landed on — for a
squash (one parent) and a true merge (`parents[0]`) alike. That relationship cannot be
reproduced by an indirect merge, which file-set equality alone can.

| Band | Checked | Parent is the trunk first-parent |
|---|---|---|
| 1 | 5 | 5 |
| 2–5 | 5 | 4, plus one whose parent never resolved |
| 6–20 | 5 | 5 |
| **21+** | **5** | **5** |

**What this check can and cannot show.** The sample contains **16 squash, 3 merge commits,
1 ambiguous — and zero rebases.** For a squash and a merge commit the resolver returns
`merge^1` and `parents[0]` *by construction*, so agreement with GitHub's first parent is
not independent evidence there; it confirms the local clone's merge commit matches
GitHub's and that parent extraction is right. Its real power over this sample is narrower
and worth stating exactly: a PR **misrouted to REBASE** would walk back and return
something other than `merge^1`, and the check would catch it. None did.

It says nothing about whether a genuine rebase resolves correctly, because none appeared —
and for a true rebase the correct parent is *not* `merge^1`, so this test would flag a
correct resolution as a mismatch.

**So the rebase branch was measured and verified separately.** It fires: **4 of 133 PRs,
4 of 88 multi-commit (4.5%)**, across three repositories — `bespokelabsai/curator` (2),
`Kanaries/pygwalker` (1), `PrefectHQ/marvin` (1). Rebase-merge is a per-repository
setting, so prevalence is clustered and depends on which repositories land in the final
corpus; it is reported per repo rather than pooled, because one rebase repository
contributing many PRs would make a systematically wrong walk a correlated block, and A8's
cluster-robust variance corrects outcome correlation within clusters, not a wrong exposure
measurement.

Shape was confirmed **structurally**, not by re-applying the subject rule to different
data — that would agree with itself by construction, and the dangerous direction is a real
rebase with an amended message giving k ≤ 1 and routing to squash. GitHub's rebase-merge
replays each commit and rewrites committer information, so a rebase of N leaves N commits
sharing one committer timestamp and a squash leaves exactly one. That reads no message
text. **16 of 16 agreed** — all 4 rebases (committer-runs of 6, 12, 2, 2, equal to the
commit count in every case) and 12 multi-commit squashes as controls (run of 1, including
PRs of 22, 14 and 12 commits).

The parents then verified against that structural truth — the first commit walking back
whose committer timestamp differs, which is the trunk commit the replay landed on:

| PR | commits | resolver parent | structural truth | differs from `merge^1` |
|---|---|---|---|---|
| `bespokelabsai/curator#345` | 6 | `ea6234a43821` | `ea6234a43821` | yes |
| `bespokelabsai/curator#445` | 12 | `48b8a96701f5` | `48b8a96701f5` | yes |
| `Kanaries/pygwalker#673` | 2 | `5ed3537c9c7f` | `5ed3537c9c7f` | yes |
| `PrefectHQ/marvin#1119` | 2 | `22786f991936` | `22786f991936` | yes |

**4 of 4**, and the last column is the point: in every case the resolved parent differs
from `merge^1`, so the walk did real work and a squash routing would have returned the
PR's own second-to-last commit — a wrong parent that no downstream check would catch.

The k distribution over multi-commit PRs is `{0: 84, 2: 2, 6: 1, 12: 1}`. **There are no
k = 1 cases**: the threshold has no data near it, so the boundary the rule could fail at
has no instances in this sample.

**19 of 20**, and the twentieth is `AgentOps-AI/agentops#819`, whose parent did not resolve
at all rather than resolving wrongly. The 21+ band is the one that mattered: 70%
`parent_commit` failure and the highest indirect-merge risk, and all five confirm.

*The first version of that checker reported 20 of 20.* The unresolved parent was stored as
`""`, and `trunk.startswith("")` is true for every string. A checker written to catch
silent passes, containing one, returning a number better than the truth — recorded here
because the tally of these is itself a finding, and `BRIEFING.md` "The checker that passed
itself" carries it.

**The exclusion stops evaporating.** A27 made the scan return `UNSCANNABLE` instead of a
false CLEAN. It did not make anyone honour it: `analysis/build_table.py` coded the outcome
`1 if BROKE else 0`, so an unscannable unit landed in the **clean cell**; `controls/gate.py`
kept it in the positive control's denominator; the reconciliation folded it into
`ex_clean`; and the labelling draw would have raised `KeyError` on the first one. The same
bias, one layer below its own fix, in the same direction and on the same units.

A typed absence is not enough on its own. Every read now goes through one exhaustive
match, and an unhandled state is a compile error rather than a silent coding — verified by
adding a fourth state and confirming `mypy --strict` rejects it.

**Prevalence is measured at admission, not at the scan.** The scan only ever sees
survivors, and all four agentops PRs that exposed the unreachable-merge case are rejected
at `no_python` before any scan runs. A count taken after the gate describes the residue
and would be quoted as the population, so `merge_on_base` is recorded on every attempt in
three values — `yes`, `no`, `unknown` — because "not on the branch" is a fact about the
repository and "could not check" is a fact about us.

**The clone timeout selects on repository size, and now by how much.** A26 named clone
timeout as an exclusion in A17's bounds. Its *direction* was not recorded, and it is not
neutral. Measured over the re-run's first 41 repositories, against GitHub's reported
repository size:

| | n | median size | range |
|---|---|---|---|
| clone timed out | 5 | **921,790 KB** | 189,729 – 1,458,859 KB |
| cloned | 40 | **80,404 KB** | up to 1,311,233 KB |

An 11.5× difference in median, over the re-run's first 46 repositories. It is emphatically
not a threshold: `bruin-data/ingestr` timed out at 190 MB while `BerriAI/litellm` cloned at
1.31 GB, so network variance is large and the two distributions overlap. The ratio itself
moved from 12.5× to 11.5× as the fifth failure arrived, so it should be read as a
direction rather than a coefficient. What is not in doubt is that direction: a resource exclusion is removing the largest repositories, and repository size
tracks project age, activity and release discipline. That is the same selection the
base-branch defect made, arriving through a different door, and it is the fourth door on
to A16's confounder after patch text, shape detection and the outcome scan.

Bounded rather than fixed. Raising the timeout would reduce it without removing it, and
`AgentOps-AI/agentops` shows the excluded repositories are not exchangeable with the
included ones. The count and the size distribution are reported so A17's bounds can cover
it; a run that quietly lost its biggest repositories and reported one attrition figure
could not.

**What this does not change.** No threshold, no arm coding, no verdict rule, no outcome
criterion. It changes which units are admitted and which exclusions are countable. The
re-measured breakage rate is reported **split by default-branch versus non-default-branch
base**, because a fix that merely moves a number and a fix that corrects one are
distinguishable only by looking inside the stratum the defect selected on.

---

## 5. Pre-specified confounders

Recorded now so that adjusting for them later is not a post-hoc rescue attempt.

| Confounder | Why it threatens the result | Handling |
|---|---|---|
| **Complexity** — dynamic code is harder code, and harder code breaks more regardless | Would inflate RR through a path that has nothing to do with our labels | Stratify by changed-lines quartile. Report RR per stratum. |
| **Framework density** — Django/Celery repos have both more unresolved sites and more coupling | Same inflation | Stratify by framework presence. |
| **Repo activity** — busy repos produce more fix commits by base rate | Inflates the outcome in both arms unevenly | Normalise by the repo's 30-day fix-commit rate. |
| **Test coverage** — well-tested repos catch breakage before merge | Suppresses the outcome | Record coverage where available; report as a stratum. |
| **PyCG failure ≠ dynamism** — a timeout is a tooling limit, not a property of the code | Conflates two different exposures | Report `UNANALYZED` (timeout/OOM) as a **separate third arm**, not merged into EXPOSED. |

The third row of that last one matters: if the entire effect comes from `UNANALYZED`, the
product is a scalability product, not an unsoundness product. That is a different company.

---

## 6. If the result is null

**We stop, and we publish — but we publish the null we actually measured. [A10]**

**The instrument detects ONE of four unresolvable-caller mechanisms, and the scope
sentence says so before any result exists. [A11]** Measured on the current machine, the
positive control returns RR 8.0 with planted-break detection 40/40 and
`mechanisms_firing_of_four: 1` — the capability profile reports `computed_getattr` and
`registering_decorator` as `false`. So the gate is passed by `super()` chains alone.

> **A null narrows to statically-named unresolvable call sites. It is explicitly not a
> claim about dynamic dispatch, string registries, or registering decorators.**

A11's reading table already established this. It is repeated here so it travels attached
to the result rather than needing to be looked up, which is the difference between a scope
statement and a limitation discovered afterwards.

**Which arm was measured is part of "actually measured". [A32]** The primary analysis is
agent-authored PRs; the human arm is the secondary comparison. The pilot completed to date
is **human-arm throughout** — 90 repositories, 236 attempts, 139 admitted, 36 breakages of
134 scored — and every shape metric it produced describes that population. No null may be
stated from it about agent-authored changes, and no agent-arm null may be stated until the
agent population is built from AIDev `pr_commits` and given **its own pilot**: the two arms
differ on the study's own confounder (star floor 503 with none below 500, against 101 with
47.3% below), so the human pilot's attrition split, exposure rate and breakage rate are not
transferable expectations for the agent run. Every record and journal row now carries `arm`
and `pilot/run.py` refuses a population whose claimed arm disagrees with AIDev's `agent`
column, so a future null can name its arm from the data rather than from memory.

The capability profile in `PHASE0_PREREGISTRATION.md` “Exposure variable” narrows what a null is entitled to claim. The variable
detects named call sites whose edge is missing; it is structurally blind to calls
dispatched through a value. So the defensible null is:

> *"Call sites that are statically **named** but unresolved do not predict breakage in
> AI-authored Python changes, RR = … [ … ], n = …. Calls dispatched through a value were
> not measurable with this instrument and are excluded; they were X% of non-builtin call
> sites in the corpus."*

Reporting instead that *"unresolvability does not predict breakage"* would overclaim the
null, because most unresolvability was never measured. That is the same error as
overclaiming a positive, and it is easier to make because a null feels modest.

**The same limit binds a positive.** The excluded sites are **non-randomly the most dynamic
in the corpus** — computed dispatch, string registries, plugin loading. The direction of
bias on the point estimate is *unknown*, because their breakage rate is unmeasured. So a
positive result on statically-named sites alone is a result about the **tamest** form of
unresolvability, and generalisation beyond it is not claimed. Neither verdict may be
stated more broadly than the instrument reached.

A rigorous null of the narrower kind is still a genuine contribution. The
soundiness literature has asked since 2015 for empirical work on whether unsoundness
matters in practice, and explicitly noted that no reliable survey exists. Answering "less
than we assumed" is publishable, is an original contribution for the O-1A file, and closes
the question honestly rather than leaving it to be rediscovered in six weeks of building.

**What we do not do on a null:** add resolvers and re-run hoping for a better number,
switch to the AST-based outcome because it gives a nicer answer, or narrow the corpus to
the repos where it worked. If any of those becomes tempting, re-read this paragraph.

---

## 7. Timeline

| Day | Work |
|---|---|
| 1–2 | Commit this file. Build the extraction harness. Dry-run on 20 PRs by hand to validate the outcome classifier against human judgement. |
| **2.5** | **Pilot — 30 repositories, ~200 PRs, every stage end to end. [A5]** |
| 3–5 | Full run: checkout parent commits, scoped PyCG, call-site enumeration, 7-day history scan. |
| 6 | Fill the 2×2. Compute RR + CI. Stratify by the five confounders. |
| 7 | Write the Results section below. Convene the go/no-go. |
| 8–12 | Repeat the identical protocol for the TS/JS arm (``PHASE0_RUNBOOK.md` “TS/JS arm”`). |

**Day 2 gate:** the outcome classifier must agree with hand-labelling on ≥16 of 20 PRs.
If it does not, the outcome variable is unreliable and the whole study is unreliable — fix
the classifier before proceeding, and record how many iterations that took.

### Day 2.5 — the pilot gate [A5]

The Day 1–2 gates test the harness against synthetic fixtures and planted positives. They
do not test it against the corpus. The pilot runs every stage on ~200 real PRs from 30
repositories and reports, before ~3,300 PRs of compute is committed:

| Metric | Expected | Decides |
|---|---|---|
| Clone success | 80–95% | corpus still exists |
| PyCG success | ~78% | instrument viable |
| `UNANALYZED_RESOURCE` share | ~22% | third arm is populated |
| **`EXCLUDED_SYNTAX` share** | small | **whether PyCG-on-3.10 is viable at all [A7]** |
| Changed symbols per PR | 1–5 median | scoping is sane |
| Exposure rate | 10–30% | classifier not degenerate |
| Breakage rate | 5–20% | outcome classifier calibrated |
| **Multi-site pair fraction** | — | **whether the A6 restriction costs real power** |
| **Short-name false-match rate** | — | magnitude of the opposite bias |
| **Design effect** (`PHASE0_PREREGISTRATION.md` “Observations are clustered, and the CI must say so”) | — | how much clustering widens the CI |

Any of the first seven far outside its range is a **stop and fix**, not a "proceed
carefully" — `PHASE0_RUNBOOK.md `PHASE0_PREREGISTRATION.md` “If the result is null”` carries the diagnosis tree. The last three carry no
expected range because nobody has measured them; they exist so that the A6 fallback and the
`PHASE0_PREREGISTRATION.md` “Decision thresholds” power reading are made on numbers rather than on assumption.

---

## 8. Results

> **Empty. Do not fill until the run is complete. Do not start the call-site census layer until this is filled.**
>
> Two blocks below: one per language arm. A strong Python result with a null TS/JS result
> is a valid and useful outcome — it means the product is Python-first, and that is a
> narrower company than the one currently described in `PROJECT_CONTEXT.md`.
>
> **Before filling either block, complete the authenticity checklist in
> `PHASE0_RUNBOOK.md `PHASE0_PREREGISTRATION.md` “Pre-specified confounders”`. All eight items. A result that fails a control is not a result.**

```
Run date:
Corpus:                     PRs,        repos,        changed symbols
Exposed (n):
Unexposed (n):
Unanalyzed (n, third arm):

                broke     did not break
EXPOSED           a=          b=
UNEXPOSED         c=          d=
UNANALYZED        e=          f=

Relative risk (exposed vs unexposed):        [95% CI:      ,      ]
Relative risk (unanalyzed vs unexposed):     [95% CI:      ,      ]

Stratified RR — changed-lines quartile:
Stratified RR — framework present / absent:
Normalised by repo fix-rate:

Primary vs tertiary outcome agreement:       %

Achieved a:                (power target was ≥20)

VERDICT:   [ ] Strong — proceed    [ ] Weak — re-pitch first    [ ] Null — stop
Signed off by:
Date:
```

---

## 9. Related open thread — close immediately after

`docs/PROJECT_CONTEXT.md` open thread **#7**: we found blogs and vendor content, not raw
practitioner complaints.

**Protocol, one week, run only after `PHASE0_PREREGISTRATION.md` “Results” is filled and non-null:**

Collect **50 verbatim complaints** from r/ExperiencedDevs, r/programming, Hacker News and
the Cursor forum. Code each one for the vocabulary the developer used:

| Code | Example phrasing |
|---|---|
| `context-window` | "it ran out of context" |
| `hallucination` | "it made up a function" |
| `missing-caller` | "it didn't know X also called this" ← **the mechanism** |
| `index-stale` | "it used the old version of the file" |
| `cost` | "it burned my whole budget" |
| `works-local-breaks-prod` | — |

**Decision rule:** if fewer than 5 of 50 use `missing-caller` language, the sales motion
begins with education. That is not fatal, but it must be priced and planned for — and it
must appear in the go-to-market section of `PROJECT_CONTEXT.md` before a single sales
conversation.

Skipping this step is what cost six weeks last time. It is one week now.
