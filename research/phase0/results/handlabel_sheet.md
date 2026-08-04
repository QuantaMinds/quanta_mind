# Hand-labelling sheet — the correlation test day-2 gate

Manifest sha256: `17109bacf936fc4ab0b8a275d507fe75646a1896ad14194d0e8861f0fea9b93c`
Drawn from 608 eligible PRs at stride 30.

For each PR below, read the commits that landed in the seven days after it
merged and decide: **did this PR break something?** Judge as a reviewer would —
a later commit that repairs behaviour this PR introduced, or reverts it, counts
as broke. Unrelated work in the same files does not.

Record `broke` or `clean` for all twenty in `handlabel_answers.txt`, one per
line as `<index>: <label>`. Scoring refuses to run until all twenty are filled.

**Do not run the classifier before finishing.** The gate measures whether the
machine agrees with an independent human judgement; reading its output first
replaces that with a memory test and the result is worth nothing.

---
## 1. keephq/keep#2958

- **Merged:** 2025-01-01T08:13:06Z
- **Title:** fix: slow lastalert query
- **Python files this PR changed** (4):
  - `keep/api/core/db.py`
  - `keep/api/middlewares.py`
  - `keep/api/models/db/alert.py`
  - `keep/api/models/db/migrations/versions/2025-01-01-09-59_dcb7f88a04da.py`

### Commits in the 7 days after this merge

**`823563e10a`** · 2025-01-02T16:30:42+02:00 · Shahar Glazner

  > fix: CEL with quote (#2965)

  Touches: _none of this PR's files_

**`e47ecafed6`** · 2025-01-03T11:09:49+02:00 · Tal

  > fix(smtp): no encryption (#2969)

  Touches: _none of this PR's files_

**`3db4fed1d5`** · 2025-01-03T15:49:35+02:00 · Tal

  > chore(version): bump (#2972)

  Touches: _none of this PR's files_

**`0b5e146e2d`** · 2025-01-03T20:08:02+00:00 · Adilbek Kangerey

  > fix: event as list[AlertDTO]  not included in the condition (#2966)
  > 
  > Co-authored-by: Tal <tal@keephq.dev>

  Touches: _none of this PR's files_

**`1a6ea83486`** · 2025-01-04T18:28:45+02:00 · Shahar Glazner

  > feat(ui): minor changes in the uI (#2977)

  Touches: _none of this PR's files_

**`81d69fe122`** · 2025-01-05T12:27:28+02:00 · dependabot[bot]

  > chore(deps): bump next from 14.2.18 to 14.2.22 in /keep-ui (#2976)
  > 
  > Signed-off-by: dependabot[bot] <support@github.com>
  > Co-authored-by: dependabot[bot] <49699333+dependabot[bot]@users.noreply.github.com>
  > Co-authored-by: Tal <tal@keephq.dev>

  Touches: _none of this PR's files_

**`8ecb6b810c`** · 2025-01-05T10:40:08+00:00 · Adilbek Kangerey

  > feat(api): change calculation variable for pull data from providers (#2962)
  > 
  > Co-authored-by: Tal <tal@keephq.dev>

  Touches: _none of this PR's files_

**`dd60931927`** · 2025-01-05T15:35:52+02:00 · Shahar Glazner

  > feat(api): grafana extra values (#2979)

  Touches: _none of this PR's files_

**`067df4a724`** · 2025-01-05T23:10:46+04:00 · Matvey Kukuy

  > fix: allow clickhouse protocol variaty (#2981)

  Touches: _none of this PR's files_

**`ee49e7c1bc`** · 2025-01-06T15:56:56+02:00 · Shahar Glazner

  > fix(api): workflowdb handler (#2988)

  Touches: _none of this PR's files_

**`84aa5269e0`** · 2025-01-06T15:22:23+01:00 · Matvey Kukuy

  > fix: posthog to None if disabled (#2989)

  Touches: _none of this PR's files_

**`d09d9ebbfc`** · 2025-01-07T12:49:29+04:00 · Kirill Chernakov

  > fix: handle unhealthy backend on frontend (#2971)

  Touches: _none of this PR's files_

**`b7ebda01a1`** · 2025-01-07T17:14:39+04:00 · Kirill Chernakov

  > fix: test run bug and feat: general UI/UX improvements (#2993)

  Touches: _none of this PR's files_

**`0da8d31ce8`** · 2025-01-08T04:54:49+00:00 · Adilbek Kangerey

  > docs: Update howdoeskeepgetmyalerts.mdx (#2994)
  > 
  > Signed-off-by: Adilbek Kangerey <adilbekq@halykbank.kz>

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    1. broke / clean  ->  

---
## 2. huggingface/smolagents#146

- **Merged:** 2025-01-10T11:31:00Z
- **Title:** Vastly simplify Model class ✨
- **Python files this PR changed** (5):
  - `src/smolagents/agents.py`
  - `src/smolagents/models.py`
  - `tests/test_agents.py`
  - `tests/test_all_docs.py`
  - `tests/test_monitoring.py`

### Commits in the 7 days after this merge

**`d8a4b831bb`** · 2025-01-10T13:00:24+01:00 · GamifyAI.ai

  > Fix several typos in docs. (#140)

  Touches: `src/smolagents/agents.py`

**`eca83800e3`** · 2025-01-10T15:00:28+01:00 · Aymeric Roucher

  > Halve import time by removing torch dependency (#147)
  > 
  > * Halve import time by removing torch dependency

  Touches: `src/smolagents/models.py`

**`4e80e1b79a`** · 2025-01-10T16:24:40+01:00 · Aymeric

  > Bump version following release of 1.2.0

  Touches: _none of this PR's files_

**`9c1a0fa2e5`** · 2025-01-10T21:45:19+01:00 · Aymeric

  > Fix output types with torch not installed

  Touches: _none of this PR's files_

**`6743d01ed5`** · 2025-01-10T21:45:52+01:00 · Aymeric

  > Formatting

  Touches: _none of this PR's files_

**`82a2fe5bb4`** · 2025-01-10T22:30:29+01:00 · Aymeric

  > Fix output type sanitization

  Touches: _none of this PR's files_

**`fec65e154a`** · 2025-01-10T23:46:22+01:00 · Aymeric Roucher

  > More flexible verbosity level (#150)

  Touches: `src/smolagents/agents.py`

**`d4b5e811f5`** · 2025-01-11T19:28:21+01:00 · Rob Taylor

  > Add top level docs link to README (#121)

  Touches: _none of this PR's files_

**`14134c23e9`** · 2025-01-12T15:02:32+01:00 · Aggelos Kyriakoulis

  > Also added the right link for website button (#159)

  Touches: _none of this PR's files_

**`320dd77f37`** · 2025-01-12T15:12:53+01:00 · Jack Kingston

  > Tools from Spaces: Fix bug preventing use of long prompts. (#134)

  Touches: _none of this PR's files_

**`5a62304c91`** · 2025-01-12T15:33:28+01:00 · chloefeal

  > Fixed typo in `parse_code_blobs` docstring (#155)
  > 
  > Fixed typo in `parse_code_blobs` docstring

  Touches: _none of this PR's files_

**`289c06df0f`** · 2025-01-13T12:08:27+01:00 · Aymeric Roucher

  > Log list of tool calls in ActionStep (#172)

  Touches: `src/smolagents/agents.py`

**`695d303401`** · 2025-01-13T16:20:45+01:00 · Aggelos Kyriakoulis

  > Bug fixes on TransformersModel (#165)
  > 
  > * TransformersModel bug fixes

  Touches: `src/smolagents/models.py`

**`60b1abdae6`** · 2025-01-13T16:21:51+01:00 · sid tuladhar

  > Fixed agents.md (#164)
  > 
  > Fix docs: custom_model should return an object that has a .content attribute

  Touches: _none of this PR's files_

**`c0496dc6bc`** · 2025-01-13T16:24:23+01:00 · Ayuilos

  > [i18n] Add Chinese translation(`zh`) for smolagents (#156)
  > 
  > * Add Chinese version (`zh`) of the documentation for smolagents

  Touches: _none of this PR's files_

**`a0b4350409`** · 2025-01-13T16:27:42+01:00 · joaopauloschuler

  > Agents deserve freedom. Freedom is the path to success! additional_authorized_imports=['*'] (#129)
  > 
  > * Add an option to authorize all imports

  Touches: `src/smolagents/agents.py`

**`67ee777370`** · 2025-01-13T16:31:36+01:00 · duydl

  > Fix minor docs (#173)

  Touches: _none of this PR's files_

**`2a51efe11f`** · 2025-01-13T16:33:45+01:00 · stackviolator

  > Add option to upload files to GradioUI (#138)
  > 
  > * Add option to upload files to GradioUI

  Touches: _none of this PR's files_

**`a5a3448551`** · 2025-01-13T16:34:55+01:00 · Albert Villanova del Moral

  > Fix formatting tests (#171)

  Touches: _none of this PR's files_

**`c611dfc7e5`** · 2025-01-13T17:23:03+01:00 · Aymeric Roucher

  > Clean local python interpreter: propagate imports (#175)

  Touches: `src/smolagents/agents.py`, `src/smolagents/models.py`, `tests/test_agents.py`

**`ad18041078`** · 2025-01-13T17:24:18+01:00 · tanhuajie

  > Fix tool_calls parsing error in ToolCallingAgent (#160)

  Touches: `src/smolagents/agents.py`

**`1f96560c92`** · 2025-01-13T17:26:32+01:00 · Albert Villanova del Moral

  > Fix minor issues in building_good_agents docs (#170)
  > 
  > * Fix doc inter-link to intro_agents in building_good_agents, make text italic, minor typos

  Touches: _none of this PR's files_

**`1d846072eb`** · 2025-01-13T19:46:36+01:00 · Aymeric

  > Improve GradioUI file upload system

  Touches: `src/smolagents/agents.py`, `src/smolagents/models.py`, `tests/test_agents.py`

**`c04e8de825`** · 2025-01-14T09:58:45+01:00 · Ilya Gusev

  > Bugfix: Fix plan_update message display (#179)

  Touches: `src/smolagents/agents.py`

**`12a2e6f4b4`** · 2025-01-14T10:00:08+01:00 · Deng Tongwei

  > feat: Add multi-GPU support for TransformersModel (#139)
  > 
  > Add multi-GPU support for TransformersModel

  Touches: `src/smolagents/models.py`

**`5f32373551`** · 2025-01-14T14:57:11+01:00 · Aymeric Roucher

  > Make default tools more robust (#186)

  Touches: `src/smolagents/agents.py`, `src/smolagents/models.py`, `tests/test_agents.py`, `tests/test_monitoring.py`

**`77f656c80d`** · 2025-01-14T17:21:38+01:00 · Aggelos Kyriakoulis

  > Implemented support for ast.Pass in the interpeter. (#189)

  Touches: _none of this PR's files_

**`ce1cd6d906`** · 2025-01-14T19:27:07+01:00 · Aymeric Roucher

  > Support pandas' iloc indexer (#191)

  Touches: _none of this PR's files_

**`450934ce79`** · 2025-01-15T12:10:52+01:00 · Aymeric Roucher

  > Add support for OpenTelemetry instrumentation 📊 (#200)

  Touches: `src/smolagents/models.py`

**`a22c221fa7`** · 2025-01-15T13:58:52+01:00 · NeverLucky

  > call.func parameter (#194)

  Touches: _none of this PR's files_

**`7ce27f1590`** · 2025-01-15T14:00:15+01:00 · kingdomad

  > fix: fix string concatenation bug in GradioUI.log_user_message (#199)

  Touches: _none of this PR's files_

**`06aca55be6`** · 2025-01-15T14:03:41+01:00 · Aymeric Roucher

  > Fix import from ChatMessage in test_monitoring (#202)

  Touches: `tests/test_monitoring.py`

**`25e00c6e74`** · 2025-01-15T16:07:34+01:00 · Aymeric Roucher

  > Document OpenTelemetry (#204)

  Touches: _none of this PR's files_

**`df76ed517f`** · 2025-01-15T16:12:31+01:00 · Albert Villanova del Moral

  > Fix quality in gradio_ui (#206)

  Touches: _none of this PR's files_

**`e5c054cc5b`** · 2025-01-15T16:56:12+01:00 · Aymeric Roucher

  > Pre-release fixes (#207)

  Touches: `tests/test_all_docs.py`

**`369d066c9d`** · 2025-01-15T17:32:23+01:00 · Aymeric

  > Bump version following release of 1.3.0

  Touches: _none of this PR's files_

**`4c5f1fe4b4`** · 2025-01-15T18:04:54+01:00 · Ruggero Rossi

  > fix typo in building_good_agents.md (#193)
  > 
  > Change function get_coordinates_from_location to convert_location_to_coordinates

  Touches: _none of this PR's files_

**`6ef0837f94`** · 2025-01-15T18:08:17+01:00 · Aymeric Roucher

  > Update README.md (#208)

  Touches: _none of this PR's files_

**`98c6688c3d`** · 2025-01-16T09:39:28+01:00 · Aymeric

  > Add pip install for instrumentation

  Touches: _none of this PR's files_

**`4449c51cad`** · 2025-01-16T09:54:47+01:00 · Albert Villanova del Moral

  > Align data types in example benchmark (#205)

  Touches: _none of this PR's files_

**`2ae590edf4`** · 2025-01-16T09:57:00+01:00 · Albert Villanova del Moral

  > Rename the benchmark dataset split from train to test (#216)

  Touches: _none of this PR's files_

**`40087aad0b`** · 2025-01-16T11:38:09+01:00 · Aymeric

  > Update mascot

  Touches: `src/smolagents/agents.py`

**`34a718cf02`** · 2025-01-16T11:40:23+01:00 · Aymeric

  > Fix mascot positioning

  Touches: _none of this PR's files_

**`96ebe01dc7`** · 2025-01-16T11:48:16+01:00 · Aymeric

  > Add license_to_call graphic to documentation index

  Touches: _none of this PR's files_

**`72b01a9909`** · 2025-01-16T11:54:23+01:00 · Aymeric

  > Restore previous agents.py

  Touches: `src/smolagents/agents.py`

**`2a69f1574e`** · 2025-01-16T12:04:41+01:00 · Albert Villanova del Moral

  > Fix vanilla model answer in example benchmark (#219)

  Touches: _none of this PR's files_

**`fdf4fe49ba`** · 2025-01-16T15:47:23+01:00 · Aymeric Roucher

  > Fix additional args in stream_to_gradio (#221)

  Touches: `src/smolagents/agents.py`

**`a4ec1e5be3`** · 2025-01-16T16:33:01+01:00 · stackviolator

  > Return textboxes on file upload errors (#214)

  Touches: _none of this PR's files_

**`a1d8f3c398`** · 2025-01-16T23:00:11+01:00 · RolandJAAI

  > fix tool example with additional args (#228)

  Touches: _none of this PR's files_

**`b4091cb5ce`** · 2025-01-16T23:03:38+01:00 · Aymeric Roucher

  > Allow passing kwargs to all models (#222)
  > 
  > * Allow passing kwargs to all models

  Touches: `src/smolagents/models.py`

**`c56d73731d`** · 2025-01-16T23:04:40+01:00 · matterattetatte

  > Dead Link to Duck Duck Go search tool (#233)
  > 
  > * Update multiagents.md URL to DuckDuckGo

  Touches: _none of this PR's files_

**`d5c2ef48e7`** · 2025-01-16T23:05:23+01:00 · Jan

  > Add resizeable option to Gradio UI component for better usabilty (#234)

  Touches: _none of this PR's files_

**`c255c1ff84`** · 2025-01-17T11:40:49+01:00 · Aymeric Roucher

  > Fix subpackage import vulnerability (#238)
  > 
  > * Fix subpackage import vulnerability

  Touches: _none of this PR's files_

**`11a738e53a`** · 2025-01-17T11:55:36+01:00 · Aymeric Roucher

  > Add trust_remote_code arg to TransformersModel (#240)

  Touches: `src/smolagents/models.py`

**`fabc59aa08`** · 2025-01-17T11:59:30+01:00 · Edward Beeching

  > Fix missing python modules in CodeAgent system prompt (#226)
  > 
  > * fix modules in system prompt + test

  Touches: `src/smolagents/agents.py`, `tests/test_agents.py`

**Your label** — did this PR break something, judged from the commits above?

    2. broke / clean  ->  

---
## 3. crewAIInc/crewAI#1931

- **Merged:** 2025-01-20T16:30:09Z
- **Title:** Stateful flows
- **Python files this PR changed** (11):
  - `src/crewai/cli/templates/flow/main.py`
  - `src/crewai/flow/__init__.py`
  - `src/crewai/flow/flow.py`
  - `src/crewai/flow/persistence/decorators.py`
  - `src/crewai/flow/persistence/sqlite.py`
  - `src/crewai/memory/storage/kickoff_task_outputs_storage.py`
  - `src/crewai/memory/storage/ltm_sqlite_storage.py`
  - `src/crewai/utilities/paths.py`
  - `src/crewai/utilities/printer.py`
  - `tests/test_flow_default_override.py`
  - `tests/test_flow_persistence.py`

### Commits in the 7 days after this merge

**`e254f11933`** · 2025-01-21T02:55:27-03:00 · Sanjeed

  > Fix wrong llm value in example (#1929)
  > 
  > Original example had `mixtal-llm` which would result in an error.
  > Replaced with gpt-4o according to https://docs.crewai.com/concepts/llms

  Touches: _none of this PR's files_

**`aba68da542`** · 2025-01-21T11:03:37-05:00 · Abhishek Patil

  > feat: add Composio docs (#1904)
  > 
  > * feat: update Composio tool docs
  > 
  > * Update composiotool.mdx
  > 
  > * fix: minor changes
  > 
  > ---------
  > 
  > Co-authored-by: Brandon Hancock (bhancock_ai) <109994880+bhancockio@users.noreply.github.com>

  Touches: _none of this PR's files_

**`a21e310d78`** · 2025-01-21T11:10:25-05:00 · Brandon Hancock (bhancock_ai)

  > add docs for crewai chat (#1936)
  > 
  > * add docs for crewai chat
  > 
  > * add version number

  Touches: _none of this PR's files_

**`c642ebf97e`** · 2025-01-22T10:30:16-05:00 · Tony Kipkemboi

  > docs: improve formatting and clarity in CLI and Composio Tool docs (#1946)
  > 
  > * docs: improve formatting and clarity in CLI and Composio Tool docs
  > 
  > - Add Terminal label to shell code blocks in CLI docs
  > - Update Composio Tool title and fix tip formatting
  > 
  > * docs: improve installation guide with virtual environment details
  > 
  > - Update Python version requirements and commands
  > - Add detailed virtual environment setup instructions
  > - Clarify project-specific environment activation steps

  Touches: _none of this PR's files_

**`67f0de1f90`** · 2025-01-22T14:24:00-05:00 · Brandon Hancock (bhancock_ai)

  > Bugfix/kickoff hangs when llm call fails (#1943)
  > 
  > * Wip to address https://github.com/crewAIInc/crewAI/issues/1934
  > 
  > * implement proper try / except
  > 
  > * clean up PR
  > 
  > * add tests
  > 
  > * Fix tests and code that was broken
  > 

  Touches: _none of this PR's files_

**`a836f466f4`** · 2025-01-22T14:36:15-05:00 · Brandon Hancock (bhancock_ai)

  > Updated calls and added tests to verify (#1953)
  > 
  > * Updated calls and added tests to verify
  > 
  > * Drop unused import

  Touches: _none of this PR's files_

**`e27a15023c`** · 2025-01-22T14:55:24-05:00 · Bobby Lindsey

  > Add SageMaker as a LLM provider (#1947)
  > 
  > * Add SageMaker as a LLM provider
  > 
  > * Removed unnecessary constants; updated docs to align with bootstrap naming convention
  > 
  > ---------
  > 
  > Co-authored-by: Brandon Hancock (bhancock_ai) <109994880+bhancockio@users.noreply.github.com>

  Touches: _none of this PR's files_

**`8c76bad50f`** · 2025-01-23T23:32:10-05:00 · Brandon Hancock (bhancock_ai)

  > Fix litellm issues to be more broad (#1960)
  > 
  > * Fix litellm issues to be more broad
  > 
  > * Fix tests

  Touches: _none of this PR's files_

**`67bf4aea56`** · 2025-01-24T17:04:41-05:00 · devin-ai-integration[bot]

  > Add version check to crew_chat.py (#1966)
  > 
  > * Add version check to crew_chat.py with min version 0.98.0
  > 
  > Co-Authored-By: brandon@crewai.com <brandon@crewai.com>
  > 
  > * Fix import sorting in crew_chat.py
  > 
  > Co-Authored-By: brandon@crewai.com <brandon@crewai.com>
  > 
  > * Fix import sorting in crew_chat.py (attempt 3)
  > 

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    3. broke / clean  ->  

---
## 4. crewAIInc/crewAI#2010

- **Merged:** 2025-02-04T21:07:22Z
- **Title:** Small update in tasks to current year
- **Python files this PR changed** (3):
  - `src/crewai/llm.py`
  - `tests/llm_test.py`
  - `tests/task_test.py`

### Commits in the 7 days after this merge

**`9cf3fadd0f`** · 2025-02-04T16:18:50-05:00 · TomuHirata

  > Add documentation for mlflow tracing integration (#1988)
  > 
  > Signed-off-by: Tomu Hirata <tomu.hirata@gmail.com>
  > Co-authored-by: Brandon Hancock (bhancock_ai) <109994880+bhancockio@users.noreply.github.com>

  Touches: _none of this PR's files_

**`515478473a`** · 2025-02-04T16:44:07-05:00 · rishi154

  > Fix :  short_term_memory with bedrock - using user defined model(when passed as attribute) rather than default (#1959)
  > 
  > * Update embedding_configurator.py
  > 
  > Modified  _configure_bedrock method to use user submitted model_name rather than default  amazon.titan-embed-text-v1.
  > 
  > Sending model_name in short_term_memory (embedder_config/config) was not working.
  > 
  > 
  >  # Passing model_name to use model_name provide by user than using default. Added if/else for backward compatibility
  > 
  > * Update embedding_configurator.py

  Touches: _none of this PR's files_

**`f4bb040ad8`** · 2025-02-04T16:46:48-05:00 · Brandon Hancock (bhancock_ai)

  > Brandon/improve llm structured output (#2029)
  > 
  > * code and tests work
  > 
  > * update docs
  > 
  > ---------
  > 
  > Co-authored-by: Lorenze Jay <63378463+lorenzejay@users.noreply.github.com>

  Touches: `src/crewai/llm.py`, `tests/llm_test.py`

**`ea64c29fee`** · 2025-02-04T16:49:29-05:00 · Juan Figuera

  > Added expected_output field to tasks to prevent ValidationError from Pydantic (#1971)
  > 
  > Co-authored-by: Brandon Hancock (bhancock_ai) <109994880+bhancockio@users.noreply.github.com>

  Touches: _none of this PR's files_

**`77c7b7dfa1`** · 2025-02-05T10:55:09-05:00 · Nicolas Lorin

  > FIX: correctly initialize embedder for crew knowledge (#2035)

  Touches: _none of this PR's files_

**`92731544ae`** · 2025-02-05T15:53:15-05:00 · Thiago Moretto

  > Fix ignored Crew task callback when one is set on the Task (#2040)
  > 
  > * Fix ignored Crew task callback when one is set on the Task
  > 
  > * type checking

  Touches: _none of this PR's files_

**`abee94d056`** · 2025-02-05T21:19:28-08:00 · João Moura

  > fix version

  Touches: _none of this PR's files_

**`e6100debac`** · 2025-02-06T15:19:22-05:00 · Nicolas Lorin

  > agent: improve knowledge naming (#2041)

  Touches: _none of this PR's files_

**`5a8649a97f`** · 2025-02-07T10:38:15-05:00 · hyjbrave

  > fix unstructured example flow (#2052)

  Touches: _none of this PR's files_

**`f6c2982619`** · 2025-02-07T10:58:38-05:00 · Brandon Hancock (bhancock_ai)

  > fix manager (#2056)

  Touches: _none of this PR's files_

**`fa26f6ebae`** · 2025-02-07T09:49:25-08:00 · Vidit Ostwal

  > Added reset memories function inside crew class (#2047)
  > 
  > * Added reset memories function inside crew class
  > 
  > * Fixed typos
  > 
  > * Refractored the code
  > 
  > * Refactor memory reset functionality in Crew class
  > 
  > - Improved error handling and logging for memory reset operations
  > - Added private methods to modularize memory reset logic

  Touches: _none of this PR's files_

**`0cc02d9492`** · 2025-02-07T13:16:44-05:00 · Vidit Ostwal

  > Added support for logging in JSON format as well. (#1985)
  > 
  > * Added functionality to have json format as well for the logs
  > 
  > * Added additional comments, refractored logging functionality
  > 
  > * Fixed documentation to include the new paramter
  > 
  > * Fixed typo
  > 
  > * Added a Pydantic Error Check between output_log_file and save_as_json parameter
  > 

  Touches: _none of this PR's files_

**`a7f5d574dc`** · 2025-02-07T14:45:36-05:00 · Brandon Hancock (bhancock_ai)

  > General Clean UP (#2042)
  > 
  > * clean up. fix type safety. address memory config docs
  > 
  > * improve manager
  > 
  > * Include fix for o1 models not supporting system messages
  > 
  > * more broad with o1
  > 
  > * address fix: Typo in expected_output string #2045
  > 

  Touches: `src/crewai/llm.py`

**`e529766391`** · 2025-02-07T16:49:46-05:00 · Lorenze Jay

  > Enhance embedding configuration with custom embedder support (#2060)
  > 
  > * Enhance embedding configuration with custom embedder support
  > 
  > - Add support for custom embedding functions in EmbeddingConfigurator
  > - Update type hints for embedder configuration
  > - Extend configuration options for various embedding providers
  > - Add optional embedder configuration to Memory class
  > 
  > * added docs
  > 
  > * Refine custom embedder configuration support

  Touches: _none of this PR's files_

**`74a1de8550`** · 2025-02-07T16:58:13-05:00 · Brandon Hancock (bhancock_ai)

  > clean up google docs (#2061)

  Touches: _none of this PR's files_

**`6f4ad532e6`** · 2025-02-07T17:00:41-05:00 · Brandon Hancock (bhancock_ai)

  > Brandon/general cleanup (#2059)
  > 
  > * clean up. fix type safety. address memory config docs
  > 
  > * improve manager
  > 
  > * Include fix for o1 models not supporting system messages
  > 
  > * more broad with o1
  > 
  > * address fix: Typo in expected_output string #2045
  > 

  Touches: _none of this PR's files_

**`8eef02739a`** · 2025-02-09T12:55:33-05:00 · João Moura

  > adding shoutout to enterprise

  Touches: _none of this PR's files_

**`56ec9bc224`** · 2025-02-09T16:20:16-03:00 · devin-ai-integration[bot]

  > fix: handle multiple task outputs correctly in conditional tasks (#1937)
  > 
  > * fix: handle multiple task outputs correctly in conditional tasks
  > 
  > - Fix IndexError in _handle_conditional_task by using first output
  > - Modify _execute_tasks to accumulate task outputs instead of resetting
  > - Update _create_crew_output to handle multiple outputs correctly
  > - Add tests for multiple tasks with conditional and multiple conditional tasks
  > 
  > Co-Authored-By: brandon@crewai.com <brandon@crewai.com>
  > 
  > * feat: validate at least one non-conditional task and refine task outputs

  Touches: _none of this PR's files_

**`a79d77dfd7`** · 2025-02-09T16:21:56-03:00 · devin-ai-integration[bot]

  > docs: document FileWriterTool as solution for file writing issues (#2039)
  > 
  > * docs: add FileWriterTool recommendation for file writing issues
  > 
  > - Add FileWriterTool recommendation in _save_file docstring
  > - Update error message to suggest using FileWriterTool for cross-platform compatibility
  > - Resolves #2015
  > 
  > Co-Authored-By: Joe Moura <joao@crewai.com>
  > 
  > * docs: enhance FileWriterTool documentation
  > 

  Touches: _none of this PR's files_

**`e0600e3bb9`** · 2025-02-09T16:35:52-03:00 · devin-ai-integration[bot]

  > fix: ensure proper message formatting for Anthropic models (#2063)
  > 
  > * fix: ensure proper message formatting for Anthropic models
  > 
  > - Add Anthropic-specific message formatting
  > - Add placeholder user message when required
  > - Add test case for Anthropic message formatting
  > 
  > Fixes #1869
  > 
  > Co-Authored-By: Joe Moura <joao@crewai.com>
  > 

  Touches: `src/crewai/llm.py`, `tests/llm_test.py`

**`d6d98ee969`** · 2025-02-09T16:47:31-03:00 · devin-ai-integration[bot]

  > docs: fix long term memory class name in examples (#2049)
  > 
  > * docs: fix long term memory class name in examples
  > 
  > - Replace EnhanceLongTermMemory with LongTermMemory to match actual implementation
  > - Update code examples to show correct usage
  > - Fixes #2026
  > 
  > Co-Authored-By: Joe Moura <joao@crewai.com>
  > 
  > * docs: improve memory examples with imports, types and security
  > 

  Touches: _none of this PR's files_

**`17e25fb842`** · 2025-02-09T20:23:52-03:00 · Bradley Goodyear

  > Fix a typo in the Task Guardrails section (#2043)
  > 
  > Co-authored-by: João Moura <joaomdmoura@gmail.com>

  Touches: _none of this PR's files_

**`fbd0e015d5`** · 2025-02-09T20:25:33-03:00 · Nicolas Lorin

  > doc: use the corresponding source depending on filetype (#2038)
  > 
  > Co-authored-by: Brandon Hancock (bhancock_ai) <109994880+bhancockio@users.noreply.github.com>

  Touches: _none of this PR's files_

**`90b3145e92`** · 2025-02-10T08:56:32-08:00 · Kevin King

  > Updated excel_knowledge_source.py to account for excel files with multiple tabs. (#1921)
  > 
  > * Updated excel_knowledge_source.py to account for excel sheets that have multiple tabs. The old implementation contained a single df=pd.read_excel(excel_file_path), which only reads the first or most recently used excel sheet. The updated functionality reads all sheets in the excel workbook.
  > 
  > * updated load_content() function in excel_knowledge_source.py to reduce memory usage and provide better documentation
  > 
  > * accidentally didn't delete the old load_content() function in last commit - corrected this
  > 
  > * Added an override for the content field from the inheritted BaseFileKnowledgeSource to account for the change in the load_content method to support excel files with multiple tabs/sheets. This change should ensure it passes the type check test, as it failed before since content was assigned a different type in BaseFileKnowledgeSource
  > 
  > * Now removed the commented out imports in _import_dependencies, as requested
  > 

  Touches: _none of this PR's files_

**`c408368267`** · 2025-02-10T12:10:53-05:00 · Brandon Hancock (bhancock_ai)

  > fix linting issues in new tests (#2089)
  > 
  > Co-authored-by: Lorenze Jay <63378463+lorenzejay@users.noreply.github.com>

  Touches: _none of this PR's files_

**`9b10fd47b0`** · 2025-02-10T12:17:41-05:00 · Brandon Hancock (bhancock_ai)

  > incorporate Small update in memory.mdx, fixing Google AI parameters #2008 (#2087)

  Touches: _none of this PR's files_

**`47818f4f41`** · 2025-02-10T12:48:12-05:00 · Brandon Hancock (bhancock_ai)

  > updating bedrock docs (#2088)
  > 
  > Co-authored-by: Lorenze Jay <63378463+lorenzejay@users.noreply.github.com>

  Touches: _none of this PR's files_

**`e51355200a`** · 2025-02-11T12:52:49+01:00 · Jannik Maierhöfer

  > docs: add Langfuse guide

  Touches: _none of this PR's files_

**`1adbcf697d`** · 2025-02-11T13:11:08+01:00 · Jannik Maierhöfer

  > fix openlit typo

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    4. broke / clean  ->  

---
## 5. julep-ai/julep#1144

- **Merged:** 2025-02-09T02:12:11Z
- **Title:** chore(cli): misc cli fixes for auth and agents
- **Python files this PR changed** (5):
  - `cli/src/julep_cli/agents.py`
  - `cli/src/julep_cli/auth.py`
  - `cli/src/julep_cli/importt.py`
  - `cli/src/julep_cli/tasks.py`
  - `cli/src/julep_cli/utils.py`

### Commits in the 7 days after this merge

_No commits landed in the window._

**Your label** — did this PR break something, judged from the commits above?

    5. broke / clean  ->  

---
## 6. julep-ai/julep#1166

- **Merged:** 2025-02-17T07:58:58Z
- **Title:** feat(agents-api): add state to workflows, modified by SetStep
- **Python files this PR changed** (3):
  - `agents-api/agents_api/common/protocol/tasks.py`
  - `agents-api/agents_api/workflows/task_execution/__init__.py`
  - `agents-api/tests/test_prepare_for_step.py`

### Commits in the 7 days after this merge

_No commits landed in the window._

**Your label** — did this PR break something, judged from the commits above?

    6. broke / clean  ->  

---
## 7. vlm-run/vlmrun-hub#105

- **Merged:** 2025-02-25T18:09:27Z
- **Title:** feat(schemas): Add lease agreement extraction schema
- **Python files this PR changed** (8):
  - `tests/test_instructor.py`
  - `vlmrun/hub/schemas/contrib/document/india/aadhaar_card.py`
  - `vlmrun/hub/schemas/contrib/document/india/pan_card.py`
  - `vlmrun/hub/schemas/contrib/document/request_for_proposal.py`
  - `vlmrun/hub/schemas/contrib/healthcare/pathology_report.py`
  - `vlmrun/hub/schemas/contrib/real_estate/lease_agreement.py`
  - `vlmrun/hub/schemas/contrib/social/twitter_card.py`
  - `vlmrun/hub/version.py`

### Commits in the 7 days after this merge

**`c2375a3ddd`** · 2025-02-25T23:42:08+05:30 · Kaushik B

  > bump version to 0.1.33 (#113)

  Touches: `vlmrun/hub/version.py`

**`37d4e8fe9c`** · 2025-02-26T11:18:09+05:30 · Scott

  > HIPAA Release form (#106)

  Touches: _none of this PR's files_

**`57ba8fce01`** · 2025-02-26T21:28:34+06:00 · shahrear33

  > fix: rename document.w2-form to accounting.form-w2

  Touches: _none of this PR's files_

**`f5d10544ef`** · 2025-03-01T13:26:53+05:30 · Shahrear

  > feat(schema): add accounting.form-payslip schema (#118)
  > 
  > ## Input
  > 
  > https://storage.googleapis.com/vlm-data-public-prod/hub/examples/accounting.form-playslip/ps-6.webp
  > 
  > ## Output JSON
  > ```
  > {
  >   "employer": {
  >     "name": "Zoonodle Inc",
  >     "address": {

  Touches: _none of this PR's files_

**`02f069eda4`** · 2025-03-01T13:27:32+05:30 · Mirajul Mohin

  > feat(schema): add insurance claim schema (#117)
  > 
  > # Schema: add schema for `document.insurance-claim`
  > 
  > ## Schema Motivation
  > Enhanced schema for structured extraction of insurance claim information
  > from claim documents, supporting various insurance types and claim
  > processes.
  > 
  > Benefits:
  > - Standardizes insurance claim data extraction from diverse document
  > formats

  Touches: _none of this PR's files_

**`d3c8848883`** · 2025-03-01T19:08:02-08:00 · devin-ai-integration[bot]

  > feat(schema): add `logistics.bill-of-lading` schema (#121)
  > 
  > # Add logistics.bill-of-lading schema
  > 
  > This PR adds a new schema for the Bill of Lading document type to the
  > vlmrun-hub repository.
  > 
  > ## Schema Details
  > - **Domain**: logistics.bill-of-lading
  > - **Schema**:
  > vlmrun.hub.schemas.contrib.logistics.bill_of_lading.BillOfLading
  > - **Supported Inputs**: ["image", "document"]

  Touches: _none of this PR's files_

**`d11de8648a`** · 2025-03-01T19:12:01-08:00 · devin-ai-integration[bot]

  > feat(schema): add `food.nutrition-facts-label` schema (#122)
  > 
  > # Schema Request: food.nutrition-facts-label
  > 
  > ## Schema Details
  > - **Domain**: food.nutrition-facts-label
  > - **Schema**:
  > vlmrun.hub.schemas.contrib.food.nutrition_facts_label.NutritionFactsLabel
  > - **Sample Data**:
  > https://www.wymans.com/cdn/shop/products/dried-nutritionals_1000x1000.jpg
  > - **Metadata**:
  >   - **Supported Inputs**: ["image", "document"]

  Touches: _none of this PR's files_

**`66f77da404`** · 2025-03-01T20:49:39-08:00 · devin-ai-integration[bot]

  > feat(schema): add `document.bank-check` schema (#123)
  > 
  > # Add `document.bank-check` schema
  > 
  > This PR adds a new schema for the `document.bank-check` type to extract
  > structured information from bank check images.
  > 
  > ## Schema Details
  > - **Domain**: document.bank-check
  > - **Schema**: BankCheck
  > - **Supported Inputs**: image, document
  > - **Tags**: accounting, banking, finance

  Touches: _none of this PR's files_

**`aca333ed32`** · 2025-03-01T23:15:51-08:00 · devin-ai-integration[bot]

  > feat(schema): New schema for `document.business-card` (#124)

  Touches: _none of this PR's files_

**`5d3ca77645`** · 2025-03-03T11:37:25+05:30 · Mirajul Mohin

  > feat(schema): add balance sheet schema (#114)
  > 
  > # Schema: New schema for finance.balance-sheet
  > 
  > ## Schema Motivation
  > Enhanced schema for structured extraction of balance sheet data from
  > financial reports, supporting various reporting standards and company
  > types.
  > 
  > Benefits:
  > - Standardizes financial data extraction from balance sheets
  > - Comprehensive capture of assets, liabilities, and equity components

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    7. broke / clean  ->  

---
## 8. AgentOps-AI/agentops#714

- **Merged:** 2025-03-03T15:24:34Z
- **Title:** Client HTTP Module Refactoring and Test Fixes
- **Python files this PR changed** (21):
  - `agentops/client/__init__.py`
  - `agentops/client/api.py`
  - `agentops/client/api/__init__.py`
  - `agentops/client/api/base.py`
  - `agentops/client/api/versions/__init__.py`
  - `agentops/client/api/versions/v3.py`
  - `agentops/client/api_client.py`
  - `agentops/client/auth_manager.py`
  - `agentops/client/exporters.py`
  - `agentops/client/http/__init__.py`
  - `agentops/client/http/auth_manager.py`
  - `agentops/client/http/http_adapter.py`
  - `agentops/client/http/http_client.py`
  - `agentops/client/v3_client.py`
  - `tests/smoke/test_authentication.py`
  - `tests/unit/client/__init__.py`
  - `tests/unit/client/test_auth_manager.py`
  - `tests/unit/client/test_exporters.py`
  - `tests/unit/client/test_http_adapter.py`
  - `tests/unit/client/test_http_client.py`
  - `tests/unit/test_otlp_exporter_auth.py`

### Commits in the 7 days after this merge

**`71c43fdcd2`** · 2025-03-08T11:25:35-06:00 · teocns

  > bye entelligence-ai-pr-reviews (#752)
  > 
  > Signed-off-by: Teo <teocns@gmail.com>

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    8. broke / clean  ->  

---
## 9. AgentOps-AI/agentops#817

- **Merged:** 2025-03-13T05:37:06Z
- **Title:** Added Anthropic examples
- **Python files this PR changed** (25):
  - `agentops/__init__.py`
  - `agentops/client/client.py`
  - `agentops/instrumentation/__init__.py`
  - `agentops/legacy/__init__.py`
  - `agentops/sdk/__init__.py`
  - `agentops/sdk/_compat.py`
  - `agentops/sdk/commands.py`
  - `agentops/sdk/converters.py`
  - `agentops/sdk/core.py`
  - `agentops/sdk/decorators/context.py`
  - `agentops/sdk/decorators/utility.py`
  - `agentops/sdk/processors.py`
  - `agentops/semconv/span_attributes.py`
  - `examples/session_commands_example.py`
  - `third_party/opentelemetry/instrumentation/haystack/__init__.py`
  - `third_party/opentelemetry/instrumentation/haystack/config.py`
  - `third_party/opentelemetry/instrumentation/haystack/utils.py`
  - `third_party/opentelemetry/instrumentation/haystack/version.py`
  - `third_party/opentelemetry/instrumentation/haystack/wrap_node.py`
  - `third_party/opentelemetry/instrumentation/haystack/wrap_openai.py`
  - `third_party/opentelemetry/instrumentation/haystack/wrap_pipeline.py`
  - `third_party/opentelemetry/instrumentation/ollama/__init__.py`
  - `third_party/opentelemetry/instrumentation/ollama/config.py`
  - `third_party/opentelemetry/instrumentation/ollama/utils.py`
  - `third_party/opentelemetry/instrumentation/ollama/version.py`

### Commits in the 7 days after this merge

**`ef381d2a01`** · 2025-03-13T04:22:55-07:00 · Pratyush Shukla

  > [RELEASE] `v0.4.0`  (#820)
  > 
  > * agentops.start_session: accept **kwargs
  > 
  > Signed-off-by: Teo <teocns@gmail.com>
  > 
  > * tests: isolate session fixtures
  > 
  > Signed-off-by: Teo <teocns@gmail.com>
  > 
  > * tests: session fixture - introduce kwargs marker
  > 

  Touches: `agentops/__init__.py`, `agentops/client/client.py`, `agentops/instrumentation/__init__.py`, `agentops/legacy/__init__.py`, `agentops/sdk/__init__.py`, `agentops/sdk/commands.py`, `agentops/sdk/converters.py`, `agentops/sdk/core.py`, `agentops/sdk/decorators/context.py`, `agentops/sdk/decorators/utility.py`, `agentops/sdk/processors.py`, `agentops/semconv/span_attributes.py`, `examples/session_commands_example.py`

**`49665e4392`** · 2025-03-13T21:57:54+05:30 · Travis Dent

  > Remove dotenv, version bump. (#822)

  Touches: `agentops/__init__.py`

**`6a0d3e19a6`** · 2025-03-13T22:15:57+05:30 · Travis Dent

  > Make legacy ErrorEvent / ToolEvent part of public API. (#823)

  Touches: `agentops/__init__.py`

**`d0b8f8af3c`** · 2025-03-13T22:24:19+05:30 · Pratyush Shukla

  > version: 0.4.2 (#824)
  > 
  > bump version (again)

  Touches: _none of this PR's files_

**`e47b8949f3`** · 2025-03-13T22:05:41-06:00 · teocns

  > fix-a-lot (#830)
  > 
  > Fixes #827 
  > Fixes #787
  > Fixes #783 
  > 
  > ---
  > 
  > 
  > Restores `start_session` from legacy SDK
  > 
  > ```

  Touches: `agentops/__init__.py`, `agentops/legacy/__init__.py`, `agentops/sdk/__init__.py`, `agentops/sdk/commands.py`, `agentops/sdk/converters.py`, `agentops/sdk/core.py`, `agentops/sdk/decorators/context.py`, `agentops/sdk/decorators/utility.py`, `examples/session_commands_example.py`

**`2d93c0fad9`** · 2025-03-13T23:56:00-07:00 · Alex Reibman

  > replace icons (#831)

  Touches: _none of this PR's files_

**`66e2841edf`** · 2025-03-14T00:00:06-07:00 · Alex Reibman

  > Better icons (#832)
  > 
  > * replace icons
  > 
  > * agents-sdk
  > 
  > * better langchain

  Touches: _none of this PR's files_

**`1ce1ac2d62`** · 2025-03-14T10:34:22-07:00 · Alex Reibman

  > Update pyproject.toml (#836)

  Touches: _none of this PR's files_

**`ad3c9fab6d`** · 2025-03-15T02:25:03+05:30 · Pratyush Shukla

  > fix: Remove `X-API-Key` from headers to fix auth (#840)
  > 
  > fix auth

  Touches: _none of this PR's files_

**`cebfa05db1`** · 2025-03-15T02:39:10+05:30 · Dwij

  > Updated decorators and session tags documentations (#841)
  > 
  > * Refactor tags documentation for clarity and accuracy.
  > 
  > * Update documentation to reflect changes in event tracking terminology and introduce new decorators for operations.
  > 
  > ---------
  > 
  > Co-authored-by: Pratyush Shukla <ps4534@nyu.edu>

  Touches: _none of this PR's files_

**`d29ced6b16`** · 2025-03-14T17:47:37-06:00 · teocns

  > backwards compat: track_agent, end_all_sessions (#847)
  > 
  > Signed-off-by: Teo <teocns@gmail.com>

  Touches: `agentops/legacy/__init__.py`

**`d5dcddeae7`** · 2025-03-15T14:46:13-06:00 · Ikko Eltociear Ashimine

  > docs: update agentops-anthropic-understanding-tools.ipynb (#853)
  > 
  > intial -> initial

  Touches: _none of this PR's files_

**`c9faca8e71`** · 2025-03-17T15:05:32-06:00 · teocns

  > 0.4.4 (#848)
  > 
  > * 0.4.4
  > 
  > Signed-off-by: Teo <teocns@gmail.com>
  > 
  > * Client.init() | auto_start_session | forward tags
  > 
  > Signed-off-by: Teo <teocns@gmail.com>
  > 
  > * client: recreate Config on init()
  > 

  Touches: `agentops/__init__.py`, `agentops/client/client.py`, `agentops/instrumentation/__init__.py`, `agentops/legacy/__init__.py`, `agentops/sdk/core.py`

**`8e832de8ce`** · 2025-03-18T05:08:22+05:30 · Dwij

  > Updated README with updated usage examples for new decorators and session management. Introduce `session`, `agent`, `operation`, `task`, and `workflow` decorators for improved observability. (#862)

  Touches: _none of this PR's files_

**`26df23b8a3`** · 2025-03-19T21:12:00+05:30 · Dwij

  > Updated unit tests for decorators by adding workflow and task nesting validation. (#863)
  > 
  > * Updated unit tests for decorators by adding workflow and task nesting validation.
  > 
  > * Refactor span attribute keys in decorators to use constants from SpanAttributes class. Update unit tests to reflect changes in attribute access for operation names and versions.
  > 
  > ---------
  > 
  > Co-authored-by: Pratyush Shukla <ps4534@nyu.edu>

  Touches: `agentops/sdk/decorators/utility.py`, `agentops/semconv/span_attributes.py`

**`de67c4ad36`** · 2025-03-19T15:55:36-07:00 · Sri Laasya Nutheti

  > Update README.md (#872)
  > 
  > Update agents SDK installation

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    9. broke / clean  ->  

---
## 10. julep-ai/julep#1277

- **Merged:** 2025-03-20T10:53:47Z
- **Title:** chore(agents-api): Reasoning support & misc fixes in Responses
- **Python files this PR changed** (53):
  - `agents-api/agents_api/activities/execute_api_call.py`
  - `agents-api/agents_api/activities/execute_integration.py`
  - `agents-api/agents_api/activities/utils.py`
  - `agents-api/agents_api/autogen/Docs.py`
  - `agents-api/agents_api/autogen/Executions.py`
  - `agents-api/agents_api/autogen/Responses.py`
  - `agents-api/agents_api/autogen/Tools.py`
  - `agents-api/agents_api/common/interceptors.py`
  - `agents-api/agents_api/common/protocol/models.py`
  - `agents-api/agents_api/common/utils/__init__.py`
  - `agents-api/agents_api/common/utils/db_exceptions.py`
  - `agents-api/agents_api/common/utils/memory.py`
  - `agents-api/agents_api/queries/docs/__init__.py`
  - `agents-api/agents_api/queries/docs/bulk_delete_docs.py`
  - `agents-api/agents_api/queries/docs/search_docs_by_text.py`
  - `agents-api/agents_api/queries/docs/search_docs_hybrid.py`
  - `agents-api/agents_api/queries/executions/create_execution_transition.py`
  - `agents-api/agents_api/queries/executions/get_execution.py`
  - `agents-api/agents_api/queries/executions/get_paused_execution_token.py`
  - `agents-api/agents_api/queries/executions/list_executions.py`
  - `agents-api/agents_api/queries/utils.py`
  - `agents-api/agents_api/routers/docs/__init__.py`
  - `agents-api/agents_api/routers/docs/bulk_delete_docs.py`
  - `agents-api/agents_api/routers/responses/create_response.py`
  - `agents-api/agents_api/routers/responses/get_response.py`
  - `agents-api/agents_api/routers/utils/model_converters.py`
  - `agents-api/agents_api/web.py`
  - `agents-api/agents_api/worker/codec.py`
  - `agents-api/agents_api/workflows/task_execution/helpers.py`
  - `agents-api/gunicorn_conf.py`
  - `agents-api/tests/fixtures.py`
  - `agents-api/tests/test_activities_utils.py`
  - `agents-api/tests/test_docs_routes.py`
  - `agents-api/tests/test_execution_queries.py`
  - `agents-api/tests/test_memory_utils.py`
  - `agents-api/tests/test_pg_query_step.py`
  - `agents-api/tests/test_query_utils.py`
  - `agents-api/tests/test_task_execution_workflow.py`
  - `agents-api/tests/test_tool_call_step.py`
  - `agents-api/tests/test_validation_errors.py`
  - …and 13 more

### Commits in the 7 days after this merge

_No commits landed in the window._

**Your label** — did this PR break something, judged from the commits above?

    10. broke / clean  ->  

---
## 11. crewAIInc/crewAI#2498

- **Merged:** 2025-04-02T04:54:35Z
- **Title:** fix expected output
- **Python files this PR changed** (3):
  - `src/crewai/crew.py`
  - `src/crewai/tools/base_tool.py`
  - `src/crewai/utilities/converter.py`

### Commits in the 7 days after this merge

**`403ea385d7`** · 2025-04-02T10:00:53-03:00 · Lucas Gomide

  > Merge branch 'main' into bug_fix

  Touches: `src/crewai/crew.py`, `src/crewai/tools/base_tool.py`, `src/crewai/utilities/converter.py`

**`efe27bd570`** · 2025-04-02T08:54:46-07:00 · Brandon Hancock (bhancock_ai)

  > Feat/individual react agent (#2483)
  > 
  > * WIP
  > 
  > * WIP
  > 
  > * wip
  > 
  > * wip
  > 
  > * WIP
  > 

  Touches: _none of this PR's files_

**`12e98e1f3c`** · 2025-04-03T11:32:56-04:00 · exiao

  > Update and rename phoenix-observability.mdx to arize-phoenix-observability.mdx

  Touches: _none of this PR's files_

**`26ccaf78ec`** · 2025-04-03T11:33:18-04:00 · exiao

  > Update arize-phoenix-observability.mdx

  Touches: _none of this PR's files_

**`c14f990098`** · 2025-04-03T11:33:51-04:00 · exiao

  > Update docs.json

  Touches: _none of this PR's files_

**`a661050464`** · 2025-04-03T11:34:29-04:00 · exiao

  > Merge branch 'crewAIInc:main' into main

  Touches: _none of this PR's files_

**`afa8783750`** · 2025-04-03T13:03:39-04:00 · exiao

  > Update arize-phoenix-observability.mdx

  Touches: _none of this PR's files_

**`d216edb022`** · 2025-04-05T18:01:20-04:00 · Tony Kipkemboi

  > Merge pull request #2520 from exiao/main
  > 
  > Fix title and position in docs for Arize Phoenix

  Touches: _none of this PR's files_

**`c9d3eb7ccf`** · 2025-04-07T10:08:40+08:00 · sakunkun

  > fix ruff check error of  project_test.py

  Touches: _none of this PR's files_

**`918c0589eb`** · 2025-04-07T02:46:40-04:00 · João Moura

  > adding new docs

  Touches: _none of this PR's files_

**`d7fa8464c7`** · 2025-04-07T10:40:35-07:00 · Lucas Gomide

  > Add support for External Memory (the future replacement for UserMemory) (#2510)
  > 
  > * fix: surfacing properly supported types by Mem0Storage
  > 
  > * feat: prepare Mem0Storage to accept config paramenter
  > 
  > We're planning to remove `memory_config` soon. This commit kindly prepare this storage to accept the config provided directly
  > 
  > * feat: add external memory
  > 
  > * fix: cleanup Mem0 warning while adding messages to the memory
  > 

  Touches: `src/crewai/crew.py`

**`b992ee9d6b`** · 2025-04-08T10:27:02-07:00 · João Moura

  > small comments

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    11. broke / clean  ->  

---
## 12. TobikoData/sqlmesh#4101

- **Merged:** 2025-04-14T17:16:58Z
- **Title:** Feat!: Add support for multiple virtual layers controlled by gateway
- **Python files this PR changed** (32):
  - `examples/multi_virtual_layer/macros/__init__.py`
  - `sqlmesh/core/config/root.py`
  - `sqlmesh/core/context.py`
  - `sqlmesh/core/context_diff.py`
  - `sqlmesh/core/environment.py`
  - `sqlmesh/core/loader.py`
  - `sqlmesh/core/model/decorator.py`
  - `sqlmesh/core/model/definition.py`
  - `sqlmesh/core/plan/builder.py`
  - `sqlmesh/core/plan/evaluator.py`
  - `sqlmesh/core/snapshot/definition.py`
  - `sqlmesh/core/snapshot/evaluator.py`
  - `sqlmesh/core/state_sync/base.py`
  - `sqlmesh/core/state_sync/cache.py`
  - `sqlmesh/core/state_sync/common.py`
  - `sqlmesh/core/state_sync/db/environment.py`
  - `sqlmesh/core/state_sync/db/facade.py`
  - `sqlmesh/core/state_sync/db/snapshot.py`
  - `sqlmesh/engines/commands.py`
  - `sqlmesh/migrations/v0056_restore_table_indexes.py`
  - `sqlmesh/migrations/v0078_add_gateway_managed_property.py`
  - `sqlmesh/migrations/v0078_add_gateway_managed_virtual_layer.py`
  - `sqlmesh/migrations/v0079_add_gateway_managed_property.py`
  - `sqlmesh/schedulers/airflow/state_sync.py`
  - `tests/core/state_sync/test_state_sync.py`
  - `tests/core/test_config.py`
  - `tests/core/test_context.py`
  - `tests/core/test_integration.py`
  - `tests/core/test_plan.py`
  - `tests/core/test_snapshot_evaluator.py`
  - `tests/fixtures/multi_virtual_layer/macros/__init__.py`
  - `tests/schedulers/airflow/test_client.py`

### Commits in the 7 days after this merge

**`a81cfda8b7`** · 2025-04-14T20:39:46+03:00 · Themis Valtinos

  > Feat: Improve the cli before all after all diff and include python env (#4116)

  Touches: `sqlmesh/core/context_diff.py`, `sqlmesh/core/model/definition.py`, `tests/core/test_plan.py`

**`0fa05348f5`** · 2025-04-14T18:51:36+01:00 · Ben

  > feat: introduce lsp (#4127)
  > 
  > Co-authored-by: Jo <46752250+georgesittas@users.noreply.github.com>

  Touches: _none of this PR's files_

**`e3e32bf88f`** · 2025-04-14T11:12:57-07:00 · Ryan Eakman

  > feat: add helm chart and docker compose for hybrid executors (#4084)
  > 
  > Co-authored-by: Trey Spiller <1831878+treysp@users.noreply.github.com>

  Touches: _none of this PR's files_

**`7271e8f296`** · 2025-04-14T16:55:17-05:00 · Trey Spiller

  > Feat: print CLI messages when no physical layer or model evals occurred (#4113)

  Touches: `sqlmesh/core/plan/evaluator.py`, `sqlmesh/core/snapshot/evaluator.py`

**`a2a9793078`** · 2025-04-14T15:26:28-07:00 · Ryan Eakman

  > feat: add custom exception for signal eval errors (#4141)

  Touches: `sqlmesh/core/snapshot/definition.py`

**`a0f75666fc`** · 2025-04-14T17:29:03-05:00 · Trey Spiller

  > Docs: add custom loader example (#4136)

  Touches: _none of this PR's files_

**`d1c34ce9fb`** · 2025-04-15T10:40:44+12:00 · Erin Drummond

  > Chore: Refactor the state stream interface (#4125)

  Touches: `sqlmesh/core/state_sync/common.py`, `sqlmesh/core/state_sync/db/facade.py`

**`a8e54b3e89`** · 2025-04-14T17:16:23-07:00 · Ryan Eakman

  > fix: include stacktrace in signal eval error message (#4143)

  Touches: `sqlmesh/core/snapshot/definition.py`

**`3ced033ac4`** · 2025-04-15T10:11:29+01:00 · Jo

  > Chore!: bump sqlglot to v26.13.2 (#4142)

  Touches: _none of this PR's files_

**`b3044281c0`** · 2025-04-15T14:00:05+03:00 · Vaggelis Danias

  > Fix!: Propagate gateway variables to model tests (#4102)

  Touches: `sqlmesh/core/context.py`, `sqlmesh/core/loader.py`

**`6386a93656`** · 2025-04-15T14:49:38+03:00 · Themis Valtinos

  > Fix: Handle macros in model properties when formatting (#4144)

  Touches: _none of this PR's files_

**`91446a512f`** · 2025-04-15T16:20:36+01:00 · Ben

  > feat: introduce minimal extension (#4139)

  Touches: _none of this PR's files_

**`a8a8477a89`** · 2025-04-15T13:33:00-07:00 · Sung Won Chung

  > update getting started and docker docs (#4140)

  Touches: _none of this PR's files_

**`2d87813d25`** · 2025-04-15T21:50:01+01:00 · Ben

  > chore: make ts stricter in extension (#4146)

  Touches: _none of this PR's files_

**`1891ef7381`** · 2025-04-15T23:08:29+01:00 · Ben

  > improve lsp error messaging (#4148)

  Touches: _none of this PR's files_

**`1865bd9e6e`** · 2025-04-15T23:19:03+01:00 · Ben

  > refactor: breaking up the console interface (#4147)

  Touches: _none of this PR's files_

**`bd305b7b21`** · 2025-04-16T14:17:16+01:00 · Ben

  > feat: vscode extension for enterprise work (#4145)

  Touches: _none of this PR's files_

**`1bc4661173`** · 2025-04-16T15:10:11+01:00 · Ben

  > refactor: breaking up the console interface (#4151)

  Touches: _none of this PR's files_

**`73c6ad7a0a`** · 2025-04-16T10:28:22-05:00 · Trey Spiller

  > Feat: fit eval progress bar column widths to content (#4149)

  Touches: `sqlmesh/core/plan/evaluator.py`, `sqlmesh/core/snapshot/evaluator.py`

**`ccd72c695a`** · 2025-04-16T08:35:37-07:00 · Iaroslav Zeigerman

  > Feat: Add a janitor configuration that allows to warn instead of failing if it fails to delete an expired environment schema / view  (#4150)

  Touches: `sqlmesh/core/config/root.py`, `sqlmesh/core/context.py`, `sqlmesh/core/state_sync/common.py`, `tests/core/state_sync/test_state_sync.py`

**`3f102a0370`** · 2025-04-16T17:49:29+01:00 · Ben

  > chore: add ci for vscode (#4154)

  Touches: _none of this PR's files_

**`151da8c3b5`** · 2025-04-16T14:09:35-05:00 · Trey Spiller

  > Feat: improve CLI virtual layer progress bar (#4064)

  Touches: _none of this PR's files_

**`bdff2291ec`** · 2025-04-16T23:34:01+03:00 · Themis Valtinos

  > Fix(snowflake): Support cloning transient tables for dev previews (#4155)

  Touches: `sqlmesh/core/snapshot/evaluator.py`, `tests/core/test_snapshot_evaluator.py`

**`7791e8d518`** · 2025-04-16T21:42:03+01:00 · Ben

  > chore: fix developer flow for vscode (#4156)

  Touches: _none of this PR's files_

**`e6ab1246c8`** · 2025-04-16T15:56:38-05:00 · Trey Spiller

  > Fix: column spacing for progress bar updates (#4159)

  Touches: _none of this PR's files_

**`6c7cf7aa10`** · 2025-04-16T16:07:53-05:00 · Ben

  > fix: fix circle ci job (#4160)

  Touches: _none of this PR's files_

**`bbdd50121a`** · 2025-04-16T15:19:12-07:00 · Toby Mao

  > fix: allow macro defs to references dates and other builtins (#4157)

  Touches: _none of this PR's files_

**`d1beef6dee`** · 2025-04-16T23:30:29+01:00 · Ben

  > chore: remove unused imports (#4161)

  Touches: _none of this PR's files_

**`1c1e9ad647`** · 2025-04-16T16:27:41-07:00 · Ryan Eakman

  > fix: properly share engine adapter config to spark engine adapter (#4162)

  Touches: _none of this PR's files_

**`eb9f77f1dd`** · 2025-04-16T16:51:01-07:00 · Iaroslav Zeigerman

  > Fix: Apply empty backfill only to snapshots that have been selected for backfill within a plan (#4163)

  Touches: `sqlmesh/core/plan/evaluator.py`, `tests/core/test_integration.py`

**`f3a037ce53`** · 2025-04-16T19:31:43-07:00 · Sung Won Chung

  > BigQuery must delete old datasets (#4164)

  Touches: _none of this PR's files_

**`dafb0c7e81`** · 2025-04-17T09:35:38+03:00 · Themis Valtinos

  > Fix: Escape backslash in string to prevent syntax error (#4165)

  Touches: _none of this PR's files_

**`a02d8b3e06`** · 2025-04-17T11:36:25+01:00 · Ben

  > refactor: move ruleset into linter definition (#4166)

  Touches: `sqlmesh/core/loader.py`

**`83ba55144e`** · 2025-04-17T14:01:40+03:00 · Themis Valtinos

  > Chore: Refine environment statements cli output (#4153)

  Touches: `sqlmesh/core/context.py`, `sqlmesh/core/context_diff.py`, `tests/core/test_context.py`, `tests/core/test_plan.py`

**`bb73daf40d`** · 2025-04-17T13:45:02+01:00 · Ben

  > feat: publish linter errors through lsp (#4152)

  Touches: `sqlmesh/core/context.py`

**`fb0a444576`** · 2025-04-17T14:38:03+01:00 · Ben

  > ci: fix vscode extension job (#4169)

  Touches: _none of this PR's files_

**`4858861070`** · 2025-04-17T17:07:44+01:00 · Ben

  > chore: small reusage of console (#4168)

  Touches: `sqlmesh/core/plan/builder.py`

**`466f2498e1`** · 2025-04-17T17:08:22+01:00 · Ben

  > refactor: further break apart console interface (#4167)

  Touches: _none of this PR's files_

**`4c89eb0712`** · 2025-04-17T19:38:51+01:00 · Ben

  > refactor: move out the plan builder console (#4170)

  Touches: `sqlmesh/core/plan/builder.py`

**`46eaf497ae`** · 2025-04-17T15:27:21-07:00 · Ryan Eakman

  > fix: pass multithreaded with log level (#4173)

  Touches: _none of this PR's files_

**`1cc9da4500`** · 2025-04-18T19:55:35+03:00 · Jo

  > Feat: support dynamic blueprinting for Python models, add docs (#4177)

  Touches: `sqlmesh/core/model/decorator.py`, `sqlmesh/core/model/definition.py`

**`c13c40fc32`** · 2025-04-18T20:13:03+03:00 · Vaggelis Danias

  > Fix: Make date range inclusive for audits ran in `sqlmesh plan` (#4179)

  Touches: `sqlmesh/core/model/definition.py`, `sqlmesh/core/snapshot/evaluator.py`, `tests/core/test_context.py`

**`cf3b0fa5a5`** · 2025-04-18T10:45:49-07:00 · Iaroslav Zeigerman

  > Chore: Deprecate Airflow integration (#4180)

  Touches: `sqlmesh/core/model/definition.py`, `sqlmesh/core/plan/evaluator.py`, `sqlmesh/schedulers/airflow/state_sync.py`, `tests/core/test_config.py`, `tests/schedulers/airflow/test_client.py`

**`044854f567`** · 2025-04-18T22:56:49+03:00 · Themis Valtinos

  > Fix(motherduck): Attach multiple catalogs in MotherDuck (#4178)

  Touches: _none of this PR's files_

**`67e5e722fe`** · 2025-04-18T13:58:20-07:00 · Iaroslav Zeigerman

  > Fix: Forward-only models can't be categorized manually (#4184)

  Touches: `sqlmesh/core/plan/builder.py`, `tests/core/test_plan.py`

**`f28341a79a`** · 2025-04-18T18:38:50-07:00 · Andrew Madson

  > Update CLI documentation descriptions to match current output format (#4183)
  > 
  > Co-authored-by: Trey Spiller <1831878+treysp@users.noreply.github.com>

  Touches: _none of this PR's files_

**`8a7dbda57e`** · 2025-04-19T18:57:17+01:00 · Ben

  > feat: adds auth to vscode extension (#4188)

  Touches: _none of this PR's files_

**`b6d5bcf3b2`** · 2025-04-20T09:44:57+01:00 · Ben

  > docs: adding better readme to vscode extension (#4190)

  Touches: _none of this PR's files_

**`beb24f0156`** · 2025-04-20T09:45:12+01:00 · Ben

  > feat: add device flow to vscode extension (#4189)

  Touches: _none of this PR's files_

**`7a2275766c`** · 2025-04-20T17:56:44+01:00 · Ben

  > ci(vscode): fix vscode job (#4192)

  Touches: _none of this PR's files_

**`dbf69c0c50`** · 2025-04-20T18:58:56+01:00 · Ben

  > fix(vscode): improve naming of lsp channel (#4193)

  Touches: _none of this PR's files_

**`29714e0c05`** · 2025-04-20T18:59:04+01:00 · Ben

  > fix(vscode): force extension to run on host (#4194)

  Touches: _none of this PR's files_

**`f01a5a46ce`** · 2025-04-20T19:26:06+01:00 · Ben

  > feat(vscode): add icon to extension (#4195)

  Touches: _none of this PR's files_

**`7f00f3d193`** · 2025-04-20T20:07:22+01:00 · Ben

  > chore(vscode): not pacakge esbuild.js file (#4196)

  Touches: _none of this PR's files_

**`ddd7f83e4b`** · 2025-04-20T20:57:48+01:00 · Ben

  > fix(vscode): specify python requirement (#4197)

  Touches: _none of this PR's files_

**`5a8e2302d2`** · 2025-04-21T13:34:25+03:00 · Themis Valtinos

  > Chore(vscode): Fix typo in readme of extension (#4199)

  Touches: _none of this PR's files_

**`3321a2af08`** · 2025-04-21T15:23:06+01:00 · Ben

  > refactor(vscode): share is python model present code (#4200)

  Touches: _none of this PR's files_

**`d49e1f3b78`** · 2025-04-21T15:34:03+01:00 · Ben

  > feat(vscode): improve tcloud project detection (#4201)

  Touches: _none of this PR's files_

**`6559a00296`** · 2025-04-21T16:45:52+01:00 · Ben

  > refactor(vscode): moving format code into function (#4204)

  Touches: _none of this PR's files_

**`effeba3d49`** · 2025-04-21T08:48:20-07:00 · Iaroslav Zeigerman

  > Fix: Columns should be sourced from the target table and not the temporary merge table (#4191)

  Touches: _none of this PR's files_

**`1473bc6182`** · 2025-04-21T08:52:49-07:00 · Toby Mao

  > feat: add the ability to check intervals (#4187)

  Touches: `sqlmesh/core/context.py`, `tests/core/test_context.py`

**`8000bfbc83`** · 2025-04-21T08:53:32-07:00 · Trey Spiller

  > Fix: column width for execution progress bar with standalone audit (#4186)

  Touches: _none of this PR's files_

**`b166ff29ce`** · 2025-04-21T08:53:41-07:00 · Ryan Eakman

  > chore: document multi-repo migrations (#4185)

  Touches: _none of this PR's files_

**`786033f00b`** · 2025-04-21T08:53:49-07:00 · Afzal Jasani

  > Docs: Fix/clean up okta saml attributes image (#4182)

  Touches: _none of this PR's files_

**`27d09c4edc`** · 2025-04-21T08:54:28-07:00 · Themis Valtinos

  > Fix: When initialising multiple connections pass concurrent tasks (#4176)

  Touches: `sqlmesh/core/context.py`, `tests/core/test_config.py`

**`d513f24084`** · 2025-04-21T08:55:05-07:00 · Ryan Eakman

  > fix: prevent past ttl values for environment and snapshot (#4158)

  Touches: `sqlmesh/core/config/root.py`

**`f2f7cdeeb3`** · 2025-04-21T18:58:07+03:00 · Vaggelis Danias

  > Feat: Introduce `format` flag for models and audits (#4203)

  Touches: `sqlmesh/core/context.py`

**`34039b3d27`** · 2025-04-21T09:00:02-07:00 · Themis Valtinos

  > Docs: Update multi engine guide with gateway managed virtual layer info (#4171)
  > 
  > Co-authored-by: Trey Spiller <1831878+treysp@users.noreply.github.com>

  Touches: _none of this PR's files_

**`9952bbba55`** · 2025-04-21T09:07:05-07:00 · Iaroslav Zeigerman

  > Fix: formatting

  Touches: `sqlmesh/core/config/root.py`

**Your label** — did this PR break something, judged from the commits above?

    12. broke / clean  ->  

---
## 13. featureform/enrichmcp#16

- **Merged:** 2025-04-21T22:15:37Z
- **Title:** Streamable HTTP
- **Python files this PR changed** (17):
  - `src/mcpengine/client/__main__.py`
  - `src/mcpengine/client/transports/http.py`
  - `src/mcpengine/errors.py`
  - `src/mcpengine/server/auth/backend.py`
  - `src/mcpengine/server/auth/errors.py`
  - `src/mcpengine/server/http.py`
  - `src/mcpengine/server/lowlevel/server.py`
  - `src/mcpengine/server/mcpengine/prompts/base.py`
  - `src/mcpengine/server/mcpengine/resources/types.py`
  - `src/mcpengine/server/mcpengine/server.py`
  - `src/mcpengine/server/mcpengine/tools/base.py`
  - `src/mcpengine/server/session.py`
  - `src/mcpengine/server/settings.py`
  - `src/mcpengine/shared/memory.py`
  - `src/mcpengine/types.py`
  - `tests/server/auth/test_errors.py`
  - `tests/shared/test_http.py`

### Commits in the 7 days after this merge

_No commits landed in the window._

**Your label** — did this PR break something, judged from the commits above?

    13. broke / clean  ->  

---
## 14. Significant-Gravitas/AutoGPT#9885

- **Merged:** 2025-04-28T15:41:15Z
- **Title:** fix(frontend): Add support to optional multiselect
- **Python files this PR changed** (1):
  - `autogpt_platform/backend/backend/data/credit.py`

### Commits in the 7 days after this merge

**`8fdfd75cc4`** · 2025-04-28T17:58:23+00:00 · Nicholas Tindle

  > feat: allow admins to download agents for review (#9881)
  > 
  > <!-- Clearly explain the need for these changes: -->
  > for admins to approve agents for the marketplace, we need to be able to
  > run them. this is a quick workaround for downloading them so you can put
  > them in your marketplace to check
  > 
  > ### Changes 🏗️
  > - clones various endpoints related to downloading into an admin side
  > with logging, and admin checks
  > - adds download button and removes open in builder action
  > <!-- Concisely describe all of the changes made in this pull request:

  Touches: _none of this PR's files_

**`a1f17ca797`** · 2025-04-28T18:38:43+00:00 · Nicholas Tindle

  > fix: use subheading for agent info not description (#9891)
  > 
  > <!-- Clearly explain the need for these changes: -->
  > we oopsed and used the wrong attribute for short desc
  > ### Changes 🏗️
  > Uses sub heading instead now
  > <!-- Concisely describe all of the changes made in this pull request:
  > -->
  > 
  > ### Checklist 📋
  > 
  > #### For code changes:

  Touches: _none of this PR's files_

**`fb5ce0a16d`** · 2025-04-28T19:07:44+00:00 · Japh

  > Add Note to "Getting Started" page for Raspberry Pi 5 page size issue (#9888)
  > 
  > Add Note to "Getting Started" page for Raspberry Pi 5 page size issue
  > with `supabase-vector` that prevents `docker compose up` from running
  > successfully.
  > 
  > <!-- Clearly explain the need for these changes: -->
  > 
  > ### Changes 🏗️
  > 
  > - Added a Note to the "Getting Started" page that explains a change in
  > Raspberry Pi OS for Raspberry Pi 5s, and how to revert the change to

  Touches: _none of this PR's files_

**`d5dc687484`** · 2025-04-28T19:16:04+00:00 · Mareddy Lohith Reddy

  > fix: handle empty 204 responses in SendWebRequestBlock (#9887)
  > 
  > <!-- Clearly explain the need for these changes: -->
  > This PR fixes [Issue
  > #9883](https://github.com/Significant-Gravitas/AutoGPT/issues/9883),
  > where the SendWebRequestBlock crashes when receiving a 204 No Content
  > response, such as when posting to a Discord webhook. The fix ensures
  > that empty responses are handled gracefully, and the block does not
  > crash.
  > 
  > ### Changes 🏗️
  > - Added a check to handle empty HTTP responses (like 204 status) in

  Touches: _none of this PR's files_

**`9fa62c03f6`** · 2025-04-29T17:06:03+00:00 · Zamil Majdy

  > feat(backend): Improve cancel execution reliability (#9889)
  > 
  > When an executor dies, an ongoing execution will not be retried and will
  > just stuck in the running status.
  > This change avoids such a scenario by allowing an execution of an entry
  > that is not in QUEUED status with the low-probability risk of double
  > execution.
  > 
  > ### Changes 🏗️
  > 
  > * Allow non-QUEUED status to be re-executed.
  > * Improve cleanup of node & graph executor.

  Touches: _none of this PR's files_

**`04c4340ee3`** · 2025-04-29T17:39:25+00:00 · Nicholas Tindle

  > feat(frontend,backend): user spending admin dashboard (#9751)
  > 
  > <!-- Clearly explain the need for these changes: -->
  > We need a way to refund people who spend money on agents wihout making
  > manual db actions
  > 
  > ### Changes 🏗️
  > - Adds a bunch for refunding users
  > - Adds reasons and admin id for actions
  > - Add admin to db manager
  > - Add UI for this for the admin panel
  > - Clean up pagination controls

  Touches: `autogpt_platform/backend/backend/data/credit.py`

**`3526986f98`** · 2025-04-30T13:59:17+00:00 · Zamil Majdy

  > fix(backend): Failing test on a new Pydantic version (#9897)
  > 
  > ```
  > FAILED test/model_test.py::test_agent_preset_from_db - pydantic_core._pydantic_core.ValidationError: 1 validation error for AgentNodeExecutionInputOutput
  > 
  > E       pydantic_core._pydantic_core.ValidationError: 1 validation error for AgentNodeExecutionInputOutput
  > E       data
  > E         JSON input should be string, bytes or bytearray [type=json_type, input_value=Json, input_type=Json]
  > E           For further information visit https://errors.pydantic.dev/2.11/v/json_type
  > ```
  > 
  > ### Changes 🏗️

  Touches: _none of this PR's files_

**`1edde778c5`** · 2025-04-30T16:46:50+01:00 · Bentlybro

  > Merge branch 'master' into dev

  Touches: _none of this PR's files_

**`602f887623`** · 2025-04-30T17:24:26+00:00 · Bently

  > feat(frontend): fix admin add dollars (#9898)
  > 
  > Fixes the admin add dollars, in the ``add-money-button.tsx`` file, in
  > the handleApproveSubmit action it was trying to use formatCredits for
  > the value which is wrong, this fix changes it
  > 
  > ```diff
  >  <form action={handleApproveSubmit}>
  >    <input type="hidden" name="id" value={userId} />
  >    <input
  >      type="hidden"
  >      name="amount"

  Touches: _none of this PR's files_

**`86d5cfe60b`** · 2025-05-01T04:38:06+00:00 · Zamil Majdy

  > feat(backend): Support flexible RPC client (#9842)
  > 
  > Using sync code in the async route often introduces a blocking
  > event-loop code that impacts stability.
  > 
  > The current RPC system only provides a synchronous client to call the
  > service endpoints.
  > The scope of this PR is to provide an entirely decoupled signature
  > between client and server, allowing the client can mix & match async &
  > sync options on the client code while not changing the async/sync nature
  > of the server.
  > 

  Touches: `autogpt_platform/backend/backend/data/credit.py`

**`f5a07f1a35`** · 2025-05-01T10:11:09-05:00 · Zamil Majdy

  > hotfix(backend): Avoid executing any agent with zero balance (#9902)
  > 
  > ### Changes 🏗️
  > 
  > * Avoid executing any agent with a zero balance.
  > * Make node execution count global across agents for a single user.
  > 
  > ### Checklist 📋
  > 
  > #### For code changes:
  > - [x] I have clearly listed my changes in the PR description
  > - [x] I have made a test plan

  Touches: `autogpt_platform/backend/backend/data/credit.py`

**`475c5a5cc3`** · 2025-05-01T15:11:38+00:00 · Zamil Majdy

  > fix(backend): Avoid executing any agent with zero balance (#9901)
  > 
  > ### Changes 🏗️
  > 
  > * Avoid executing any agent with a zero balance.
  > * Make node execution count global across agents for a single user.
  > 
  > ### Checklist 📋
  > 
  > #### For code changes:
  > - [x] I have clearly listed my changes in the PR description
  > - [x] I have made a test plan

  Touches: `autogpt_platform/backend/backend/data/credit.py`

**`d7077b5161`** · 2025-05-01T16:02:03+00:00 · Zamil Majdy

  > feat(backend): Continue instead of retrying aborted/broken agent execution (#9903)
  > 
  > Currently, the agent/graph execution engine is consuming the execution
  > queue and acknowledges the message after fully completing its execution
  > or failing it.
  > 
  > However, in the case of the agent executor failing due to a
  > hardware/resource issue, or the executor did not manage to acknowledge
  > the execution message. Another agent executor will pick it up and start
  > the execution again from the beginning.
  > 
  > The scope of this PR is to make the next executor pick up the next work

  Touches: _none of this PR's files_

**`59ec61ef98`** · 2025-05-02T14:42:01+00:00 · Krzysztof Czerwinski

  > feat(platform): Onboarding design&UX update (#9905)
  > 
  > A collection of updates regarding onboarding and wallet.
  > 
  > ### Changes 🏗️
  > 
  > - `try-except` instead of `if` when rewarding (skip unnecessary db call)
  > - Make external services question onboarding step optional
  > - Add `SmartImage` component to lazy load images with pulse animation
  > and use it throughout onboarding
  > - Use store agent name instead of graph graph name (run page)
  > - Fix some images breaking layout on the agent card (run page)

  Touches: `autogpt_platform/backend/backend/data/credit.py`

**`afb66f75ec`** · 2025-05-02T19:40:51+00:00 · Nicholas Tindle

  > fix: disable google sheets in prod based on oauth review (#9906)
  > 
  > <!-- Clearly explain the need for these changes: -->
  > 
  > Our oauth review wants us to drop this in favor of a diff scope that
  > will require additional work
  > 
  > ### Changes 🏗️
  > Disables the oauth sheets scopes in prod
  > 
  > <!-- Concisely describe all of the changes made in this pull request:
  > -->

  Touches: _none of this PR's files_

**`79319ad1a7`** · 2025-05-05T13:27:04+00:00 · Zamil Majdy

  > fix(backend): Avoid broken process pool by not failing process initializer (#9907)
  > 
  > Process initializer on the process pool should never fail, but we do
  > network-related stuff there.
  > This cause the pool to be in a broken state.
  > 
  > ### Changes 🏗️
  > 
  > Remove the health check step on process initializer.
  > 
  > ### Checklist 📋
  > 

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    14. broke / clean  ->  

---
## 15. Significant-Gravitas/AutoGPT#9902

- **Merged:** 2025-05-01T15:11:09Z
- **Title:** hotfix(backend): Avoid executing any agent with zero balance
- **Python files this PR changed** (5):
  - `autogpt_platform/backend/backend/data/credit.py`
  - `autogpt_platform/backend/backend/executor/database.py`
  - `autogpt_platform/backend/backend/executor/manager.py`
  - `autogpt_platform/backend/backend/executor/utils.py`
  - `autogpt_platform/backend/backend/util/settings.py`

### Commits in the 7 days after this merge

**`475c5a5cc3`** · 2025-05-01T15:11:38+00:00 · Zamil Majdy

  > fix(backend): Avoid executing any agent with zero balance (#9901)
  > 
  > ### Changes 🏗️
  > 
  > * Avoid executing any agent with a zero balance.
  > * Make node execution count global across agents for a single user.
  > 
  > ### Checklist 📋
  > 
  > #### For code changes:
  > - [x] I have clearly listed my changes in the PR description
  > - [x] I have made a test plan

  Touches: `autogpt_platform/backend/backend/data/credit.py`, `autogpt_platform/backend/backend/executor/database.py`, `autogpt_platform/backend/backend/executor/manager.py`, `autogpt_platform/backend/backend/executor/utils.py`, `autogpt_platform/backend/backend/util/settings.py`

**`d7077b5161`** · 2025-05-01T16:02:03+00:00 · Zamil Majdy

  > feat(backend): Continue instead of retrying aborted/broken agent execution (#9903)
  > 
  > Currently, the agent/graph execution engine is consuming the execution
  > queue and acknowledges the message after fully completing its execution
  > or failing it.
  > 
  > However, in the case of the agent executor failing due to a
  > hardware/resource issue, or the executor did not manage to acknowledge
  > the execution message. Another agent executor will pick it up and start
  > the execution again from the beginning.
  > 
  > The scope of this PR is to make the next executor pick up the next work

  Touches: `autogpt_platform/backend/backend/executor/database.py`, `autogpt_platform/backend/backend/executor/manager.py`

**`59ec61ef98`** · 2025-05-02T14:42:01+00:00 · Krzysztof Czerwinski

  > feat(platform): Onboarding design&UX update (#9905)
  > 
  > A collection of updates regarding onboarding and wallet.
  > 
  > ### Changes 🏗️
  > 
  > - `try-except` instead of `if` when rewarding (skip unnecessary db call)
  > - Make external services question onboarding step optional
  > - Add `SmartImage` component to lazy load images with pulse animation
  > and use it throughout onboarding
  > - Use store agent name instead of graph graph name (run page)
  > - Fix some images breaking layout on the agent card (run page)

  Touches: `autogpt_platform/backend/backend/data/credit.py`

**`afb66f75ec`** · 2025-05-02T19:40:51+00:00 · Nicholas Tindle

  > fix: disable google sheets in prod based on oauth review (#9906)
  > 
  > <!-- Clearly explain the need for these changes: -->
  > 
  > Our oauth review wants us to drop this in favor of a diff scope that
  > will require additional work
  > 
  > ### Changes 🏗️
  > Disables the oauth sheets scopes in prod
  > 
  > <!-- Concisely describe all of the changes made in this pull request:
  > -->

  Touches: _none of this PR's files_

**`79319ad1a7`** · 2025-05-05T13:27:04+00:00 · Zamil Majdy

  > fix(backend): Avoid broken process pool by not failing process initializer (#9907)
  > 
  > Process initializer on the process pool should never fail, but we do
  > network-related stuff there.
  > This cause the pool to be in a broken state.
  > 
  > ### Changes 🏗️
  > 
  > Remove the health check step on process initializer.
  > 
  > ### Checklist 📋
  > 

  Touches: `autogpt_platform/backend/backend/executor/manager.py`

**`6f1578239a`** · 2025-05-05T16:47:58+00:00 · Krzysztof Czerwinski

  > feat(platform): Update Marketplace Agent listing buttons (#9843)
  > 
  > Currently agent listing on Marketplace have bad UX.
  > 
  > ### Changes 🏗️
  > 
  > - Add function and endpoint to check if user has `LibraryAgent` by given
  > `storeListingVersionId`
  > - Redesign listing buttons
  > - `Add to library` shown when user is logged in and doesn't have an
  > agent in library
  >   - `See runs` shown when user logged in as has the agent in the library

  Touches: _none of this PR's files_

**`505320fcd3`** · 2025-05-05T18:59:28+00:00 · Nicholas Tindle

  > feat(backend): Move Scheduler (#9904)
  > 
  > <!-- Clearly explain the need for these changes: -->
  > We want the scheduler shouldn't scale with the rest API lol
  > 
  > ### Changes 🏗️
  > pulls out the scheduler into its own service
  > <!-- Concisely describe all of the changes made in this pull request:
  > -->
  > 
  > ### Checklist 📋
  > 

  Touches: _none of this PR's files_

**`519ad94ec9`** · 2025-05-06T20:30:36+07:00 · Zamil Majdy

  > Merge branch 'master' of github.com:Significant-Gravitas/AutoGPT into dev

  Touches: _none of this PR's files_

**`ac8ef9bdb2`** · 2025-05-07T05:00:37+00:00 · Zamil Majdy

  > feat(backend): Introduce late execution check scheduled job (#9914)
  > 
  > Introduce a late execution check scheduled job. The late threshold
  > duration is configurable.
  > This initial version only reports the error to Sentry.
  > 
  > ### Changes 🏗️
  > 
  > * Added late execution check scheduled job
  > * Move the registration weekly notification processing job out of API
  > call and calling it directly from the scheduler service.
  > 

  Touches: `autogpt_platform/backend/backend/executor/database.py`, `autogpt_platform/backend/backend/util/settings.py`

**`0726a00fb7`** · 2025-05-07T17:28:39+00:00 · Reinier van der Leer

  > fix(backend): Include sub-graphs in graph-level credentials support (#9862)
  > 
  > The Library Agent credentials UX (#9789) currently doesn't work for
  > sub-graphs.
  > 
  > ### Changes 🏗️
  > 
  > - Include sub-graphs in generating `Graph.credentials_input_schema`
  > - Propagate `node_credentials_input_map` into `AgentExecutionBlock`
  > executions
  > - Fix: also apply `node_credentials_input_map` in `_enqueue_next_nodes`
  > 

  Touches: `autogpt_platform/backend/backend/executor/manager.py`, `autogpt_platform/backend/backend/executor/utils.py`

**`104928c614`** · 2025-05-07T21:08:12+00:00 · Bently

  > feat(platform): Add captcha to login, signup and password reset pages (#9847)
  > 
  > This PR adds Cloudflare's Turnstile CAPTCHA to the login, signup, and
  > password reset pages. it is setup to only show and work when behave as
  > is set to CLOUD so it will not show for local hosted users.
  > 
  > ### Changes 🏗️
  > 
  > #### Backend Changes
  > -
  > **[backend/server/v2/turnstile/routes.py](https://github.com/Significant-Gravitas/AutoGPT/compare/dev...bently/secrt-1169-implement-captcha-on-sign-up?expand=1#diff-2c5c2cb13346370fc48bdde8691a0d3bbfc030f7718288101b67b641c7948c10)**:
  > Created API endpoint at `/api/turnstile/verify` to proxy verification

  Touches: `autogpt_platform/backend/backend/util/settings.py`

**`1ad6c76f9c`** · 2025-05-08T09:45:22+00:00 · Reinier van der Leer

  > feat(backend): Require discriminator value on graph save (#9858)
  > 
  > If a node has a multi-credentials input (e.g. AI Text Generator block)
  > but the discriminator value (e.g. model choice) is missing, the input
  > can't be discriminated into a single-provider input. Discrimination into
  > a single-provider input is necessary to make a graph-level credentials
  > input for use in the Library.
  > 
  > ### Changes 🏗️
  > 
  > - feat(backend): Require discriminator fields to always have a value
  > 

  Touches: _none of this PR's files_

**`433b76b539`** · 2025-05-08T11:26:51+00:00 · Reinier van der Leer

  > fix(backend/scheduler): Unbreak `Scheduler.get_execution_schedules` (#9919)
  > 
  > - Resolves #9918
  > - Follow-up fix for #9914
  > 
  > ### Changes 🏗️
  > 
  > - In `get_graph_execution_schedules`, skip jobs when their kwargs can't
  > be parsed as `GraphExecutionJobArgs`
  > - Rename methods of `Scheduler` to clarify their scope (scheduled
  > *graph* executions)
  > 

  Touches: _none of this PR's files_

**`74e6a6a43a`** · 2025-05-08T11:41:27+00:00 · Toran Bruce Richards

  > fix(frontend/library): Quick Patch for Rendering Agent Outputs (#9922)
  > 
  > <!-- Clearly explain the need for these changes: -->
  > The goal of this change is a quick and temporary tweak to improve the
  > displaying of output text in the Agent Runs screen.
  > 
  > This change is made anticipating that these outputs will be properly
  > improved in the near future, and is thus just a temporary change in
  > order to display text in a human readable format.
  > 
  > ### Changes 🏗️
  > There is one change in this PR:

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    15. broke / clean  ->  

---
## 16. a16z/halmos#509

- **Merged:** 2025-05-13T23:05:07Z
- **Title:** support exclude{Sender,Target,Selector} cheatcode
- **Python files this PR changed** (9):
  - `src/halmos/__main__.py`
  - `src/halmos/build.py`
  - `src/halmos/cheatcodes.py`
  - `src/halmos/hashes.py`
  - `src/halmos/mapper.py`
  - `src/halmos/sevm.py`
  - `src/halmos/solve.py`
  - `src/halmos/utils.py`
  - `tests/test_utils.py`

### Commits in the 7 days after this merge

**`477eeb4db5`** · 2025-05-14T14:23:07-07:00 · karmacoma

  > feat/invariant targets (#516)

  Touches: `src/halmos/__main__.py`, `src/halmos/sevm.py`, `src/halmos/solve.py`

**`9829484aa5`** · 2025-05-14T15:04:31-07:00 · karmacoma

  > chore: set up Trusted Publishing for publish-pypi.yml (#518)

  Touches: _none of this PR's files_

**`5671f5cc64`** · 2025-05-16T20:47:32+00:00 · Daejun Park

  > feat: add createCalldata with address (#517)

  Touches: `src/halmos/cheatcodes.py`

**`8042a5b4c2`** · 2025-05-19T11:17:54-07:00 · Daejun Park

  > refactor: move Contract and Instruction to separate module (#520)

  Touches: `src/halmos/sevm.py`

**`c05179f582`** · 2025-05-19T12:15:38-07:00 · Daejun Park

  > fix: Exec.dump error (#522)

  Touches: `src/halmos/sevm.py`

**`dfca7161d7`** · 2025-05-19T22:45:02+00:00 · Daejun Park

  > refactor: extract_bytes(x, y, 32) => x.get_word(y) (#519)
  > 
  > Co-authored-by: karmacoma <karma@coma.lol>

  Touches: `src/halmos/cheatcodes.py`, `src/halmos/sevm.py`, `src/halmos/utils.py`

**Your label** — did this PR break something, judged from the commits above?

    16. broke / clean  ->  

---
## 17. mangiucugna/json_repair#112

- **Merged:** 2025-05-16T10:27:00Z
- **Title:** ⚡️ Speed up method `ObjectComparer.__init__` by 51%
- **Python files this PR changed** (1):
  - `src/json_repair/object_comparer.py`

### Commits in the 7 days after this merge

**`cbfa7a1c6f`** · 2025-05-16T12:28:22+02:00 · Stefano Baccianella

  > Merge pull request #113 from mangiucugna/codeflash/optimize-ObjectComparer.is_same_object-maqnixde
  > 
  > ⚡️ Speed up method `ObjectComparer.is_same_object` by 109%

  Touches: `src/json_repair/object_comparer.py`

**`850cec4865`** · 2025-05-16T13:49:57+02:00 · Stefano Baccianella

  > add github actions

  Touches: _none of this PR's files_

**`a6f34d089b`** · 2025-05-18T11:48:59+02:00 · Stefano Baccianella

  > Fix typo in json_parser comment

  Touches: _none of this PR's files_

**`99881a444a`** · 2025-05-18T11:50:06+02:00 · Stefano Baccianella

  > Fix typo in docstring

  Touches: _none of this PR's files_

**`d762fa93fd`** · 2025-05-18T11:50:36+02:00 · Stefano Baccianella

  > Add CLI error handling tests

  Touches: _none of this PR's files_

**`3a715ab893`** · 2025-05-18T11:51:47+02:00 · Stefano Baccianella

  > initialize boolean value

  Touches: _none of this PR's files_

**`5cd71128ce`** · 2025-05-18T11:54:32+02:00 · Stefano Baccianella

  > Fix env

  Touches: _none of this PR's files_

**`08f201de47`** · 2025-05-18T11:54:53+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/impostare-value-none-in-json-parser-py

  Touches: _none of this PR's files_

**`e479f7512d`** · 2025-05-18T11:55:57+02:00 · Stefano Baccianella

  > test again

  Touches: _none of this PR's files_

**`e4a9bf7c8a`** · 2025-05-18T11:56:14+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/impostare-value-none-in-json-parser-py

  Touches: _none of this PR's files_

**`164b68d5bb`** · 2025-05-18T11:57:54+02:00 · Stefano Baccianella

  > try again

  Touches: _none of this PR's files_

**`04251a53c6`** · 2025-05-18T11:59:26+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/impostare-value-none-in-json-parser-py

  Touches: _none of this PR's files_

**`4294f544f9`** · 2025-05-18T12:00:44+02:00 · Stefano Baccianella

  > try again

  Touches: _none of this PR's files_

**`fa669229b2`** · 2025-05-18T12:01:51+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/correggere-commento-in-json-parser-py

  Touches: _none of this PR's files_

**`eb8488cdeb`** · 2025-05-18T12:01:56+02:00 · Stefano Baccianella

  > Merge pull request #116 from mangiucugna/codex/correggere-commento-in-json-parser-py
  > 
  > Fix typo in json_parser comment

  Touches: _none of this PR's files_

**`18803d9409`** · 2025-05-18T12:02:15+02:00 · Stefano Baccianella

  > Merge pull request #117 from mangiucugna/codex/sostituire-parantheses-con-parentheses-nella-docstring
  > 
  > Fix typo in json_repair docstring

  Touches: _none of this PR's files_

**`9f49bfacca`** · 2025-05-18T12:02:25+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/impostare-value-none-in-json-parser-py

  Touches: _none of this PR's files_

**`cf78aca094`** · 2025-05-18T12:02:30+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/add-test-cases-for-cli-with-inline-and-output

  Touches: _none of this PR's files_

**`078bd9ca49`** · 2025-05-18T12:03:34+02:00 · Stefano Baccianella

  > try again

  Touches: _none of this PR's files_

**`85791fa259`** · 2025-05-18T12:06:59+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/add-test-cases-for-cli-with-inline-and-output

  Touches: _none of this PR's files_

**`de06b8bca4`** · 2025-05-18T12:08:08+02:00 · Stefano Baccianella

  > missing dependency

  Touches: _none of this PR's files_

**`453929e24a`** · 2025-05-18T12:08:27+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/add-test-cases-for-cli-with-inline-and-output

  Touches: _none of this PR's files_

**`233ca5a6bd`** · 2025-05-18T12:10:33+02:00 · Stefano Baccianella

  > again

  Touches: _none of this PR's files_

**`2d6824b171`** · 2025-05-18T12:11:38+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/add-test-cases-for-cli-with-inline-and-output

  Touches: _none of this PR's files_

**`043bdb4048`** · 2025-05-18T12:13:09+02:00 · Stefano Baccianella

  > Merge pull request #118 from mangiucugna/codex/add-test-cases-for-cli-with-inline-and-output
  > 
  > Add CLI argument validation tests

  Touches: _none of this PR's files_

**`607563a248`** · 2025-05-18T12:13:19+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/impostare-value-none-in-json-parser-py

  Touches: _none of this PR's files_

**`77fc03d5eb`** · 2025-05-18T12:14:51+02:00 · Stefano Baccianella

  > Merge pull request #119 from mangiucugna/codex/impostare-value-none-in-json-parser-py
  > 
  > Fix variable initialization in parser

  Touches: _none of this PR's files_

**`9e59fbbbfd`** · 2025-05-18T12:38:22+02:00 · Stefano Baccianella

  > move constant at the beginning of the class

  Touches: _none of this PR's files_

**`acbbc32f5e`** · 2025-05-19T10:03:17+02:00 · Stefano Baccianella

  > update pre-commit

  Touches: _none of this PR's files_

**`07ba400265`** · 2025-05-19T12:58:32+02:00 · Stefano Baccianella

  > Potential fix for code scanning alert no. 8: Workflow does not contain permissions
  > 
  > Co-authored-by: Copilot Autofix powered by AI <62310815+github-advanced-security[bot]@users.noreply.github.com>

  Touches: _none of this PR's files_

**`f0ff088003`** · 2025-05-19T13:00:50+02:00 · Stefano Baccianella

  > Merge pull request #122 from mangiucugna/alert-autofix-8
  > 
  > Potential fix for code scanning alert no. 8: Workflow does not contain permissions

  Touches: _none of this PR's files_

**`bc0ac8a554`** · 2025-05-19T13:01:33+02:00 · Stefano Baccianella

  > add permissions

  Touches: _none of this PR's files_

**`71c5cbdc49`** · 2025-05-20T10:34:01+02:00 · Stefano Baccianella

  > Fix #121, if repair_json() is returning an empty string, skip json.dumps() to avoid returning just ""

  Touches: _none of this PR's files_

**`e02e0767ef`** · 2025-05-21T04:20:34+02:00 · Stefano Baccianella

  > Update pyproject.toml to indicate dropping 3.9

  Touches: _none of this PR's files_

**`3e2fe2ae91`** · 2025-05-21T04:21:28+02:00 · Stefano Baccianella

  > Document handling of stray slash

  Touches: _none of this PR's files_

**`6640847e7a`** · 2025-05-21T04:25:24+02:00 · Stefano Baccianella

  > bump version

  Touches: _none of this PR's files_

**`b79873c134`** · 2025-05-21T04:25:54+02:00 · Stefano Baccianella

  > Merge branch 'main' into codex/fix-infinite-loop-with-in-repair-json

  Touches: _none of this PR's files_

**`e27c9ac713`** · 2025-05-21T04:27:35+02:00 · Stefano Baccianella

  > Fix #123, Merge pull request #125 from mangiucugna/codex/fix-infinite-loop-with-in-repair-json
  > 
  > Fix comment parser infinite loop

  Touches: _none of this PR's files_

**`754fe7716e`** · 2025-05-21T06:15:07+02:00 · Stefano Baccianella

  > Update python-package.yml

  Touches: _none of this PR's files_

**`691894b62a`** · 2025-05-22T07:16:18+01:00 · Stefano Baccianella

  > Fix #126, fix an edge case in which an unclosed array inside an object leads to a weird parsing mistake

  Touches: _none of this PR's files_

**`2f01cc9608`** · 2025-05-23T06:25:15+01:00 · Stefano Baccianella

  > Update README.md

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    17. broke / clean  ->  

---
## 18. langchain-ai/langgraph#4819

- **Merged:** 2025-05-28T21:04:08Z
- **Title:** Pregel: Add NodeBuilder class to replace Channel.subscribe_to
- **Python files this PR changed** (10):
  - `libs/langgraph/langgraph/graph/graph.py`
  - `libs/langgraph/langgraph/pregel/__init__.py`
  - `libs/langgraph/langgraph/pregel/read.py`
  - `libs/langgraph/langgraph/pregel/validate.py`
  - `libs/langgraph/langgraph/pregel/write.py`
  - `libs/langgraph/langgraph/types.py`
  - `libs/langgraph/tests/test_large_cases.py`
  - `libs/langgraph/tests/test_large_cases_async.py`
  - `libs/langgraph/tests/test_pregel.py`
  - `libs/langgraph/tests/test_pregel_async.py`

### Commits in the 7 days after this merge

**`9320bedd2a`** · 2025-05-28T14:04:26-07:00 · Nuno Campos

  > Remove Checkpoint.pending_sends (#4820)

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`76661f4c9c`** · 2025-05-28T14:04:45-07:00 · Nuno Campos

  > Remove Checkpoint.writes (#4822)

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`26d5fccfa0`** · 2025-05-28T14:05:03-07:00 · Nuno Campos

  > Modify stream mode messages and custom to respect subgraphs=False (#4843)

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel_async.py`

**`045d6dfb82`** · 2025-05-28T14:05:14-07:00 · Nuno Campos

  > Update managed value usage in local_read (#4854)

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`

**`1b961f68b9`** · 2025-05-28T14:14:47-07:00 · Nuno Campos

  > Remove Channel node builder
  > 
  > - Replaced by NodeBuilder introduced in earlier PR

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/tests/test_pregel.py`

**`d55cafad29`** · 2025-05-28T14:30:12-07:00 · Nuno Campos

  > Remove Channel node builder (#4858)

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/tests/test_pregel.py`

**`0afc4ebda3`** · 2025-05-29T11:45:54-07:00 · Nuno Campos

  > Flip default for checkpoint_during
  > 
  > - Now defaulting to False, ie. saving only the final checkpoint
  > - All features other than time travel into an intermediate step are supported by checkpoint_during=False so this is a better default for almost all use cases

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`583fe9fd84`** · 2025-05-29T11:52:10-07:00 · Nuno Campos

  > Remove UntrackedValue channel (#4859)

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`05f3904d09`** · 2025-05-29T12:07:51-07:00 · Nuno Campos

  > Remove UntrackedValue channel
  > 
  > - This is incompatible with distributed execution modes, so needs to go

  Touches: `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`

**`2615c7046c`** · 2025-05-29T12:14:36-07:00 · Nuno Campos

  > Remove UntrackedValue channel (#4868)

  Touches: `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`

**`f8fae30aa9`** · 2025-05-29T19:37:43+00:00 · Sydney Runkle

  > docs: fix pprint import (#4869)

  Touches: _none of this PR's files_

**`2066e4c018`** · 2025-05-29T13:10:16-07:00 · infra

  > docs: fix self hosted control plane concepts/docs

  Touches: _none of this PR's files_

**`8e82c7d1a0`** · 2025-05-29T16:16:02-04:00 · langchain-infra

  > docs: fix self hosted control plane concepts/docs (#4870)

  Touches: _none of this PR's files_

**`c46f7a4c3d`** · 2025-05-29T21:54:54+01:00 · David Asamu

  > add support for image_distro in config file

  Touches: _none of this PR's files_

**`574a9246a6`** · 2025-05-29T23:30:27+01:00 · David Asamu

  > add unit tests for image_distro config

  Touches: _none of this PR's files_

**`1e8f5dd2b6`** · 2025-05-30T00:25:27+01:00 · David Asamu

  > add warning when image distro is not configured as wolfi

  Touches: _none of this PR's files_

**`afb83d2201`** · 2025-05-29T21:38:58-04:00 · Nuno Campos

  > Remove non-state Graph
  > 
  > - Not used in any examples/docs

  Touches: `libs/langgraph/langgraph/graph/graph.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`a5e6223569`** · 2025-05-29T21:50:23-04:00 · Sydney Runkle

  > Remove `MessageGraph` (#4875)
  > 
  > Remove MessageGraph
  > 
  > Co-authored-by: Nuno Campos <nuno@langchain.dev>

  Touches: `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel.py`

**`5cbf31e8a4`** · 2025-05-29T21:56:53-04:00 · Sydney Runkle

  > Remove non-state Graph (#4872)

  Touches: `libs/langgraph/langgraph/graph/graph.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`d661d528b2`** · 2025-05-30T16:30:53-07:00 · Nuno Campos

  > Avoid repeated runtime calls to get_type_hints
  > 
  > - Replace get_type_hints logic with much simpler implementation which only collects annotated keys (not the annotations themselves)
  > - Cache annotations in a WeakKeyDictionary

  Touches: `libs/langgraph/langgraph/types.py`

**`08f88ce8da`** · 2025-05-30T21:49:22-04:00 · Eugene Yurtsev

  > docs: add gtm (#4887)
  > 
  > Add google tag manager

  Touches: _none of this PR's files_

**`3b85c83d51`** · 2025-05-31T08:37:23-07:00 · Nuno Campos

  > Avoid repeated runtime calls to get_type_hints (#4888)

  Touches: `libs/langgraph/langgraph/types.py`

**`78d3d8c802`** · 2025-06-01T06:46:51-04:00 · Nuno Campos

  > Remove add_conditional_edge(..., then=) (#4893)
  > 
  > - This is redundant with deferred nodes, and not documented

  Touches: `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`765bc3b9e0`** · 2025-06-01T10:47:35+00:00 · Ikpreet S Babra

  > docs: Update 2-add-tools.md (#4896)
  > 
  > Typo in first sentence.

  Touches: _none of this PR's files_

**`d05b323b88`** · 2025-06-02T01:52:40+02:00 · Tat Dat Duong

  > feat(sdk-js): add docs for `reconnectOnMount`, expose run metadata

  Touches: _none of this PR's files_

**`624c688013`** · 2025-06-02T01:53:46+02:00 · David Duong

  > feat(sdk-js): add docs for `reconnectOnMount`, expose run metadata (#4898)

  Touches: _none of this PR's files_

**`5973fcb0ae`** · 2025-06-02T02:09:43+02:00 · Tat Dat Duong

  > docs(sdk-js): improve resumability docs

  Touches: _none of this PR's files_

**`21f762140a`** · 2025-06-02T02:10:16+02:00 · David Duong

  > docs(sdk-js): improve resumability docs (#4899)

  Touches: _none of this PR's files_

**`eaa1b37645`** · 2025-06-02T01:52:35+00:00 · Sydney Runkle

  > Require `state_schema` in `StateGraph.__init__` (#4897)

  Touches: _none of this PR's files_

**`8fd50a50d4`** · 2025-06-02T13:46:29+00:00 · Michael Li

  > docs: fix grammar errors in mcp.md and multi-agent.md (#4903)
  > 
  > * docs: fix a grammar error in mcp.md
  > 
  > * docs: fix a grammar error in multi-agent.md

  Touches: _none of this PR's files_

**`7d6243e6b4`** · 2025-06-02T13:48:06+00:00 · Michael Li

  > docs: fix incorrect word in custom_docker.md (#4901)

  Touches: _none of this PR's files_

**`f00b994692`** · 2025-06-02T13:48:18+00:00 · Michael Li

  > docs: fix incorrect word in memory.md (#4902)

  Touches: _none of this PR's files_

**`469576f966`** · 2025-06-02T17:47:16+00:00 · Michael Li

  > docs: fix grammar issues in langgraph_self_hosted_control_plane.md and langgraph_server.md (#4907)

  Touches: _none of this PR's files_

**`0d6af09187`** · 2025-06-02T13:48:50-04:00 · Michael Li

  > docs: fix grammar issues in application_structure.md and assistants.md (#4904)
  > 
  > * docs: fix a grammar error in mcp.md
  > 
  > * docs: fix a grammar error in multi-agent.md
  > 
  > * docs: fix grammar issues in application_structure.md and assistants.md

  Touches: _none of this PR's files_

**`dc787b5aa6`** · 2025-06-02T17:48:55+00:00 · Michael Li

  > docs: fix grammar issues in langgraph_data_plane.md and langgraph_platform.md (#4906)
  > 
  > * docs: fix grammar issues in langgraph_data_plane.md and langgraph_platform.md
  > 
  > * docs: further update the wording in langgraph_data_plane.md

  Touches: _none of this PR's files_

**`d44581d754`** · 2025-06-02T17:49:04+00:00 · Michael Li

  > docs: fix typos in langgraph_studio.md and low_level.md (#4909)

  Touches: _none of this PR's files_

**`6cde3ee7a3`** · 2025-06-02T15:03:03-04:00 · Eugene Yurtsev

  > ci: add depandabot config for upgrading actions (#4911)
  > 
  > Depandabot config for suggesting to update old actions

  Touches: _none of this PR's files_

**`f8b5e05c47`** · 2025-06-02T15:03:23-04:00 · Daiki Inoue

  > docs: fix a typo (#4908)

  Touches: _none of this PR's files_

**`871b1dccd8`** · 2025-06-02T15:04:03-04:00 · Michael Li

  > docs: fix grammar issues in deployment_options.md and faq.md (#4905)

  Touches: _none of this PR's files_

**`dd059fea3c`** · 2025-06-02T15:17:04-04:00 · dependabot[bot]

  > build(deps): bump actions/checkout from 3 to 4 (#4912)
  > 
  > Bumps [actions/checkout](https://github.com/actions/checkout) from 3 to 4.
  > - [Release notes](https://github.com/actions/checkout/releases)
  > - [Changelog](https://github.com/actions/checkout/blob/main/CHANGELOG.md)
  > - [Commits](https://github.com/actions/checkout/compare/v3...v4)
  > 
  > ---
  > updated-dependencies:
  > - dependency-name: actions/checkout
  >   dependency-version: '4'
  >   dependency-type: direct:production

  Touches: _none of this PR's files_

**`7e45a0530b`** · 2025-06-02T15:17:21-04:00 · dependabot[bot]

  > build(deps): bump actions/cache from 3 to 4 (#4913)
  > 
  > Bumps [actions/cache](https://github.com/actions/cache) from 3 to 4.
  > - [Release notes](https://github.com/actions/cache/releases)
  > - [Changelog](https://github.com/actions/cache/blob/main/RELEASES.md)
  > - [Commits](https://github.com/actions/cache/compare/v3...v4)
  > 
  > ---
  > updated-dependencies:
  > - dependency-name: actions/cache
  >   dependency-version: '4'
  >   dependency-type: direct:production

  Touches: _none of this PR's files_

**`b4cb4e72ab`** · 2025-06-02T15:36:18-04:00 · dependabot[bot]

  > build(deps): bump actions/configure-pages from 4 to 5 (#4916)
  > 
  > Bumps [actions/configure-pages](https://github.com/actions/configure-pages) from 4 to 5.
  > - [Release notes](https://github.com/actions/configure-pages/releases)
  > - [Commits](https://github.com/actions/configure-pages/compare/v4...v5)
  > 
  > ---
  > updated-dependencies:
  > - dependency-name: actions/configure-pages
  >   dependency-version: '5'
  >   dependency-type: direct:production
  >   update-type: version-update:semver-major

  Touches: _none of this PR's files_

**`bbbadc3db9`** · 2025-06-02T20:50:48+01:00 · David Asamu

  > regenerate schema + lint & format

  Touches: _none of this PR's files_

**`2563301f39`** · 2025-06-02T15:53:26-04:00 · Nuno Campos

  > Remove unused deprecation decorator/warning (#4917)

  Touches: _none of this PR's files_

**`e2b14a9499`** · 2025-06-02T13:43:16-07:00 · William FH

  > feat: Add onRequest callback to JS SDK (#4919)
  > 
  > Add onRequest callback

  Touches: _none of this PR's files_

**`e5e78e4192`** · 2025-06-02T16:05:32-07:00 · Nuno Campos

  > Fix Command(graph=PARENT) when used together w checkpointer=True

  Touches: `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`7828003958`** · 2025-06-02T16:18:52-07:00 · Nuno Campos

  > Fix Command(graph=PARENT) when used together w checkpointer=True (#4921)

  Touches: `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`5e5840805e`** · 2025-06-02T16:35:48-07:00 · Nuno Campos

  > Fix makefile command file for dev server
  > - pidfile was always empty

  Touches: _none of this PR's files_

**`36bd88287f`** · 2025-06-02T16:41:59-07:00 · Nuno Campos

  > Fix makefile command file for dev server (#4922)

  Touches: _none of this PR's files_

**`952017fbe2`** · 2025-06-02T17:17:07-07:00 · Arjun Natarajan

  > feat: support custom tracer when creating run in ts sdk

  Touches: _none of this PR's files_

**`a75e40192f`** · 2025-06-02T17:18:59-07:00 · Arjun Natarajan

  > perhaps better typing

  Touches: _none of this PR's files_

**`70dc0323c1`** · 2025-06-02T17:26:20-07:00 · Arjun Natarajan

  > i want this exported

  Touches: _none of this PR's files_

**`b908e96541`** · 2025-06-02T17:27:33-07:00 · Arjun Natarajan

  > need to export it here too

  Touches: _none of this PR's files_

**`b438210a0d`** · 2025-06-02T17:33:29-07:00 · Arjun Natarajan

  > maybe fixes lint

  Touches: _none of this PR's files_

**`6002aebec5`** · 2025-06-02T17:35:12-07:00 · Arjun Natarajan

  > maybe nees the full lint rewrite

  Touches: _none of this PR's files_

**`1e324b681a`** · 2025-06-03T01:43:59+01:00 · David Asamu

  > update dockerfile generation logic, fix pip removal in wolfi

  Touches: _none of this PR's files_

**`8c560ef62a`** · 2025-06-02T18:10:01-07:00 · lc-arjun

  > feat: support custom tracer when creating run in ts sdk (#4924)

  Touches: _none of this PR's files_

**`f4b480c4b8`** · 2025-06-02T18:13:36-07:00 · Arjun Natarajan

  > bump sdk

  Touches: _none of this PR's files_

**`7d27d108fc`** · 2025-06-02T18:16:08-07:00 · lc-arjun

  > bump sdk (#4925)

  Touches: _none of this PR's files_

**`723cff9001`** · 2025-06-03T08:37:31-04:00 · dependabot[bot]

  > build(deps): bump actions/setup-node from 3 to 4 (#4915)
  > 
  > Bumps [actions/setup-node](https://github.com/actions/setup-node) from 3 to 4.
  > - [Release notes](https://github.com/actions/setup-node/releases)
  > - [Commits](https://github.com/actions/setup-node/compare/v3...v4)
  > 
  > ---
  > updated-dependencies:
  > - dependency-name: actions/setup-node
  >   dependency-version: '4'
  >   dependency-type: direct:production
  >   update-type: version-update:semver-major

  Touches: _none of this PR's files_

**`2b759a2a33`** · 2025-06-03T15:20:13+02:00 · Tat Dat Duong

  > fix(sdk-js): `uiMessageReducer` should handle `undefined` metadata

  Touches: _none of this PR's files_

**`3a74514bc3`** · 2025-06-03T15:21:25+02:00 · David Duong

  > fix(sdk-js): `uiMessageReducer` should handle `undefined` metadata (#4931)

  Touches: _none of this PR's files_

**`cd28bef155`** · 2025-06-04T01:20:29+10:00 · Michael Li

  > docs: fix a grammar issue in multiple files

  Touches: _none of this PR's files_

**`f528f5ebd6`** · 2025-06-03T18:18:22+01:00 · Asamu David

  > Merge branch 'main' into david/05-28/support-image-distro-config

  Touches: `libs/langgraph/langgraph/graph/graph.py`, `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/langgraph/types.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_large_cases_async.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`37c215b5a2`** · 2025-06-03T15:21:51-04:00 · Sydney Runkle

  > Improve type checking on graph `init` and `invoke`/`stream` (#4932)

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`

**`7ba5636200`** · 2025-06-03T20:59:06+01:00 · Asamu David

  > add support for image_distro in config file (#4871)

  Touches: _none of this PR's files_

**`5c18123bb7`** · 2025-06-03T21:37:25+01:00 · Asamu David

  > cli v0.2.11 release
  > 
  > ## Description 
  > 
  > bump cli version to 0.2.11

  Touches: _none of this PR's files_

**`c31c940bbb`** · 2025-06-03T14:59:56-07:00 · Nuno Campos

  > checkpoint-postgres: Use lock also for pipeline mode

  Touches: _none of this PR's files_

**`4473db6361`** · 2025-06-03T18:12:41-04:00 · infra

  > fix: use right link

  Touches: _none of this PR's files_

**`8837b8534f`** · 2025-06-03T18:15:51-04:00 · langchain-infra

  > fix: use right link (#4943)

  Touches: _none of this PR's files_

**`fce7652b7c`** · 2025-06-03T23:26:42+01:00 · Asamu David

  > Merge branch 'main' into david/06-03/update-cli-version

  Touches: _none of this PR's files_

**`bb990715f1`** · 2025-06-03T15:29:49-07:00 · Nuno Campos

  > Allow same-name channels and nodes in StateGraph
  > 
  > - We no longer auto create a same-name channel for each node, so this limitation can now be lifted

  Touches: _none of this PR's files_

**`b00ea605e2`** · 2025-06-03T15:30:04-07:00 · Nuno Campos

  > checkpoint-postgres: Use lock also for pipeline mode (#4942)

  Touches: _none of this PR's files_

**`394ea1c12b`** · 2025-06-03T23:40:10+01:00 · Asamu David

  > Merge branch 'main' into david/06-03/update-cli-version

  Touches: _none of this PR's files_

**`7335b80586`** · 2025-06-03T18:42:11-04:00 · infra

  > fix: use right deployment link

  Touches: _none of this PR's files_

**`cd2847ee07`** · 2025-06-03T15:53:19-07:00 · Nuno Campos

  > docs: fix double article typos

  Touches: _none of this PR's files_

**`ae3c2e0b89`** · 2025-06-03T18:55:05-04:00 · langchain-infra

  > fix: use right deployment link (#4945)

  Touches: _none of this PR's files_

**`9c6e8d5237`** · 2025-06-03T15:56:04-07:00 · Nuno Campos

  > Fix duplicate article typos in docs (#4946)

  Touches: _none of this PR's files_

**`7080eaa79e`** · 2025-06-03T15:56:41-07:00 · Nuno Campos

  > docs: fix ensure_config docstring

  Touches: _none of this PR's files_

**`d4018497a9`** · 2025-06-03T16:02:44-07:00 · Nuno Campos

  > Fix ensure_config docstring (#4947)

  Touches: _none of this PR's files_

**`89e827bd15`** · 2025-06-03T16:14:46-07:00 · Nuno Campos

  > Make it possible to run test command without docker installed

  Touches: _none of this PR's files_

**`a534807ec9`** · 2025-06-03T16:15:07-07:00 · Nuno Campos

  > Allow same-name channels and nodes in StateGraph (#4944)

  Touches: _none of this PR's files_

**`5ab5da767b`** · 2025-06-03T16:17:17-07:00 · Nuno Campos

  > Pass tags when configuring async callback manager

  Touches: _none of this PR's files_

**`0b609646d5`** · 2025-06-03T16:23:22-07:00 · Nuno Campos

  > Fix async callback manager tag handling (#4949)

  Touches: _none of this PR's files_

**`b211d4e767`** · 2025-06-03T16:29:14-07:00 · Nuno Campos

  > Make it possible to run test command without docker installed (#4948)

  Touches: _none of this PR's files_

**`ae2b766d0f`** · 2025-06-04T00:53:56+01:00 · David Asamu

  > bump version

  Touches: _none of this PR's files_

**`13ebe1ad8c`** · 2025-06-04T01:00:06+01:00 · Asamu David

  > cli v0.2.11 release (#4941)

  Touches: _none of this PR's files_

**`5f1d76ba3b`** · 2025-06-03T17:04:20-07:00 · Nuno Campos

  > docs: fix a grammar issue in multiple files (#4935)

  Touches: _none of this PR's files_

**`f8995f234c`** · 2025-06-03T17:25:17-07:00 · Nuno Campos

  > Remove scheduler-kafka library
  > 
  > Superseded by upcoming distributed runner

  Touches: _none of this PR's files_

**`161a1e3af6`** · 2025-06-03T17:26:13-07:00 · Nuno Campos

  > Remove from ci matrix

  Touches: _none of this PR's files_

**`314115513c`** · 2025-06-03T17:26:29-07:00 · Nuno Campos

  > Fix step_timeout causing ParentCommand/GraphInterrupt exception to bubble up
  > 
  > - We should not re-raise exceptions in commit() as that is now called in a future done callback
  > - panic_or_proceed takes care of re-raising exceptions as needed anyway

  Touches: `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`1ea5812ed0`** · 2025-06-03T17:32:46-07:00 · Nuno Campos

  > Fix step_timeout causing ParentCommand/GraphInterrupt exception to bubble up (#4950)

  Touches: `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`02f3944e88`** · 2025-06-04T14:55:06+00:00 · Sydney Runkle

  > rename `retry` -> `retry_policy` (#4957)

  Touches: `libs/langgraph/langgraph/pregel/__init__.py`, `libs/langgraph/tests/test_large_cases.py`, `libs/langgraph/tests/test_pregel.py`, `libs/langgraph/tests/test_pregel_async.py`

**`9fde14079a`** · 2025-06-04T17:12:13+00:00 · Sydney Runkle

  > docs: use `retry_policy` instead of `retry` in docs (#4958)

  Touches: _none of this PR's files_

**`c0b6a85488`** · 2025-06-04T17:20:19+00:00 · Sydney Runkle

  > docs: format to allow for deploy (#4959)
  > 
  > formatting

  Touches: _none of this PR's files_

**`aedf974dfd`** · 2025-06-04T13:27:48-04:00 · Sydney Runkle

  > docs: deploy from v0 branch for now (#4960)
  > 
  > only deploy docs on v0

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    18. broke / clean  ->  

---
## 19. crewAIInc/crewAI#2961

- **Merged:** 2025-06-05T00:49:07Z
- **Title:** Update version to 0.126.0 and dependencies in pyproject.toml and lock…
- **Python files this PR changed** (1):
  - `src/crewai/__init__.py`

### Commits in the 7 days after this merge

**`e03ec4d60f`** · 2025-06-05T09:42:10-04:00 · Lucas Gomide

  > fix: remove duplicated message about Tool result (#2964)
  > 
  > We are currently inserting tool results into LLM messages twice, which may unnecessarily increase processing costs, especially for longer outputs.

  Touches: _none of this PR's files_

**`3e075cd48d`** · 2025-06-05T11:37:19-04:00 · Lucas Gomide

  > docs: add minimum UV version required to use the Tool repository (#2965)
  > 
  > * docs: add minimum UV version required to use the Tool repository
  > 
  > * docs: remove memory from Agent docs
  > 
  > The Agent does not support `memory` attribute

  Touches: _none of this PR's files_

**`f1cfba7527`** · 2025-06-05T12:34:52-04:00 · Greyson LaLonde

  > docs: update hallucination guardrail examples
  > 
  > - Add basic usage example showing guardrail uses task's expected_output as default context
  > - Add explicit context example for custom reference content

  Touches: _none of this PR's files_

**`02912a653e`** · 2025-06-06T09:43:38-07:00 · Mike Plachta

  > Increasing the default X-axis spacing for flow plotting (#2967)
  > 
  > * Increasing the default X-axis spacing for flow plotting
  > 
  > * removing unused imports

  Touches: _none of this PR's files_

**`21d063a46c`** · 2025-06-06T15:28:09-04:00 · Lucas Gomide

  > Support multi org in CLI (#2969)
  > 
  > * feat: support to list, switch and see your current organization
  > 
  > * feat: store the current org after logged in
  > 
  > * feat: filtering agents, tools and their actions by organization_uuid if present
  > 
  > * fix linter offenses
  > 
  > * refactor: propagate the current org thought Header instead of params
  > 

  Touches: _none of this PR's files_

**`b0d89698fd`** · 2025-06-08T13:39:01-04:00 · Akshit Madan

  > docs: added Maxim support for Agent Observability (#2861)
  > 
  > * docs: added Maxim support for Agent Observability
  > 
  > * enhanced the maxim integration doc page as per the github PR reviewer bot suggestions
  > 
  > * Update maxim-observability.mdx
  > 
  > * Update maxim-observability.mdx
  > 
  > - Fixed Python version, >=3.10
  > - added expected_output field in Task

  Touches: _none of this PR's files_

**`e6ac1311e7`** · 2025-06-09T08:55:12-04:00 · Lucas Gomide

  > build: upgrade LiteLLM to support latest Openai version (#2963)
  > 
  > Co-authored-by: Tony Kipkemboi <iamtonykipkemboi@gmail.com>

  Touches: _none of this PR's files_

**`8a37b535ed`** · 2025-06-09T10:17:04-04:00 · Lucas Gomide

  > docs: improve docs about planning LLM usage (#2977)

  Touches: _none of this PR's files_

**`db3c8a49bd`** · 2025-06-09T12:21:12-04:00 · Lucas Gomide

  > feat: improve docs and logging for Multi-Org actions in CLI (#2980)
  > 
  > * docs: add organization management in our CLI docs
  > 
  > * feat: improve user feedback when user is not authenticated
  > 
  > * feat: improve logging about current organization while publishing/install a Tool
  > 
  > * feat: improve logging when Agent repository is not found during fetch
  > 
  > * fix linter offences
  > 

  Touches: _none of this PR's files_

**`3e74cb4832`** · 2025-06-09T12:46:09-04:00 · Lorenze Jay

  > docs: add integrations documentation and images for enterprise features (#2981)
  > 
  > - Introduced a new documentation file for Integrations, detailing supported services and setup instructions.
  > - Updated the main docs.json to include the new "integrations" feature in the contextual options.
  > - Added several images related to integrations to enhance the documentation.
  > 
  > Co-authored-by: Tony Kipkemboi <iamtonykipkemboi@gmail.com>

  Touches: _none of this PR's files_

**`e9d9dd2a79`** · 2025-06-09T13:16:05-04:00 · hegasz

  > Fix missing manager_agent tokens in usage_metrics from kickoff (#2848)
  > 
  > * fix(metrics): prevent usage_metrics from dropping manager_agent tokens
  > 
  > * Add test to verify hierarchical kickoff aggregates manager and agent usage metrics
  > 
  > ---------
  > 
  > Co-authored-by: Lucas Gomide <lucaslg200@gmail.com>

  Touches: _none of this PR's files_

**`5b740467cb`** · 2025-06-09T14:09:56-04:00 · Richard Luo

  > docs: fix the guide on persistence (#2849)
  > 
  > Co-authored-by: Lucas Gomide <lucaslg200@gmail.com>

  Touches: _none of this PR's files_

**`5c51349a85`** · 2025-06-10T12:17:06-04:00 · Lucas Gomide

  > Support async tool executions (#2983)
  > 
  > * test: fix structured tool tests
  > 
  > No tests were being executed from this file
  > 
  > * feat: support to run async tool
  > 
  > Some Tool requires async execution. This commit allow us to collect tool result from coroutines
  > 
  > * docs: add docs about asynchronous tool support

  Touches: _none of this PR's files_

**`b0d2e9fe31`** · 2025-06-10T12:44:28-04:00 · Lucas Gomide

  > docs: update Python version requirement from <=3.13 to <3.14 (#2987)
  > 
  > This correctly reflects support for all 3.13.x patch version

  Touches: _none of this PR's files_

**`739eb72fd0`** · 2025-06-10T13:32:32-04:00 · Lucas Gomide

  > LiteAgent w/ Guardrail (#2982)
  > 
  > * feat: add guardrail support for Agents when using direct kickoff calls
  > 
  > * refactor: expose guardrail func in a proper utils file
  > 
  > * fix: resolve Self import on python 3.10

  Touches: _none of this PR's files_

**`06c991d8c3`** · 2025-06-10T17:38:40-07:00 · devin-ai-integration[bot]

  > Fix telemetry singleton pattern to respect dynamic environment variables (#2946)
  > 
  > * Fix telemetry singleton pattern to respect dynamic environment variables
  > 
  > - Modified Telemetry.__init__ to prevent re-initialization with _initialized flag
  > - Updated _safe_telemetry_operation to check _is_telemetry_disabled() dynamically
  > - Added comprehensive tests for environment variables set after singleton creation
  > - Fixed singleton contamination in existing tests by adding proper reset
  > - Resolves issue #2945 where CREWAI_DISABLE_TELEMETRY=true was ignored when set after import
  > 
  > Co-Authored-By: João <joao@crewai.com>
  > 

  Touches: _none of this PR's files_

**`970a63c13c`** · 2025-06-11T12:08:00-04:00 · devin-ai-integration[bot]

  > Fix issue 2993: Prevent Flow status logs from hiding human input (#2994)
  > 
  > * Fix issue 2993: Prevent Flow status logs from hiding human input
  > 
  > - Add pause_live_updates() and resume_live_updates() methods to ConsoleFormatter
  > - Modify _ask_human_input() to pause Flow status updates during human input
  > - Add comprehensive tests for pause/resume functionality and integration
  > - Ensure Live session is properly managed during human input prompts
  > - Fix prevents Flow status logs from overwriting user input prompts
  > 
  > Fixes #2993
  > 

  Touches: _none of this PR's files_

**`99133104dd`** · 2025-06-11T17:01:11-07:00 · Lorenze Jay

  > Update version to 0.130.0 and dependencies in pyproject.toml and uv.lock (#3002)
  > 
  > - Bump CrewAI version from 0.126.0 to 0.130.0 in pyproject.toml and uv.lock.
  > - Update optional dependency 'crewai-tools' version from 0.46.0 to 0.47.1.
  > - Adjust dependency specifications in CLI templates to reflect the new version.

  Touches: `src/crewai/__init__.py`

**Your label** — did this PR break something, judged from the commits above?

    19. broke / clean  ->  

---
## 20. strawberry-graphql/strawberry#3907

- **Merged:** 2025-06-15T00:17:35Z
- **Title:** Fix inconsistent naming of aiohttp adapters
- **Python files this PR changed** (1):
  - `strawberry/aiohttp/views.py`

### Commits in the 7 days after this merge

**`2422b68c1b`** · 2025-06-15T02:24:46+02:00 · Jonathan Ehwald

  > Fix chalice did not send content type headers (#3904)
  > 
  > * Fix Chalice did not send content-type headers
  > 
  > * Add release file

  Touches: _none of this PR's files_

**`94cb9cd081`** · 2025-06-15T00:26:13+00:00 · Botberry

  > Release 🍓 0.273.1

  Touches: _none of this PR's files_

**`585fccd7ee`** · 2025-06-15T02:44:38+02:00 · Jonathan Ehwald

  > Fix test case unnecessarily skipped aiohttp (#3908)

  Touches: _none of this PR's files_

**`4dc1f00448`** · 2025-06-15T02:45:20+02:00 · Jonathan Ehwald

  > Replace undocumented async generator (#3906)
  > 
  > * Replace undocumented async generator
  > 
  > * Add release file

  Touches: `strawberry/aiohttp/views.py`

**`feb6f3e6af`** · 2025-06-15T00:46:21+00:00 · Botberry

  > Release 🍓 0.273.2

  Touches: _none of this PR's files_

**`071b32ae08`** · 2025-06-15T16:15:41+02:00 · Jonathan Ehwald

  > Remove redundant test app/view creation code (#3905)
  > 
  > * Remove redundant create_app code from test clients
  > 
  > * Omit unused args from signatures
  > 
  > * Fix type

  Touches: _none of this PR's files_

**`8649ebe620`** · 2025-06-16T22:17:21+02:00 · Jonathan Ehwald

  > Include pyright in our lockfile (#3915)

  Touches: _none of this PR's files_

**`45ae1fd632`** · 2025-06-16T22:18:02+02:00 · Jonathan Ehwald

  > Fix incorrectly typed params (#3914)
  > 
  > * Fix incorrectly typed param
  > 
  > * Fix root_value types were also incorrect
  > 
  > * Fix pylance doesn't like our UnsetType
  > 
  > * Remove more unneeded type ignores

  Touches: _none of this PR's files_

**`df8767f9c0`** · 2025-06-16T22:19:10+02:00 · Jonathan Ehwald

  > Fix some test clients set unwanted body data (#3913)

  Touches: _none of this PR's files_

**`261527c972`** · 2025-06-16T22:19:36+02:00 · Jonathan Ehwald

  > Fix type ignore was hiding support for HEAD (#3912)

  Touches: _none of this PR's files_

**`9f788cedbe`** · 2025-06-16T22:20:19+02:00 · Jonathan Ehwald

  > Fix django test client set unwanted content type (#3911)

  Touches: _none of this PR's files_

**`55a5d2ebdf`** · 2025-06-16T22:21:44+02:00 · Jonathan Ehwald

  > Sync subscription protocols arg types (#3910)
  > 
  > * Sync subscription protocols arg types
  > 
  > * Add release file

  Touches: `strawberry/aiohttp/views.py`

**`3f7b6118e2`** · 2025-06-16T20:24:38+00:00 · Botberry

  > Release 🍓 0.273.3

  Touches: _none of this PR's files_

**`2783c8f799`** · 2025-06-16T23:43:27+02:00 · Jonathan Ehwald

  > Fix operation selection (#3916)
  > 
  > * Fix operation selection
  > 
  > * Add release file
  > 
  > * Remove unneeded paranthesis
  > 
  > * Fix typo

  Touches: _none of this PR's files_

**`8a019ce102`** · 2025-06-16T21:44:47+00:00 · Botberry

  > Release 🍓 0.274.0

  Touches: _none of this PR's files_

**`9bd3665ea7`** · 2025-06-18T23:20:42+01:00 · Erik Wrede

  > fix: support lists in maybe annotation (#3920)
  > 
  > * fix: support lists in maybe annotation
  > 
  > * chore: lint
  > 
  > * chore: simplify test
  > 
  > * chore: add RELEASE.md

  Touches: _none of this PR's files_

**`cb54604341`** · 2025-06-18T22:21:56+00:00 · Botberry

  > Release 🍓 0.274.1

  Touches: _none of this PR's files_

**`a4c18769a6`** · 2025-06-18T23:26:48+01:00 · Matt Gilene

  > Add operation extensions to `ExecutionContext` (#3878)
  > 
  > * add operation extensions to extension execution context
  > 
  > * Add RELEASE.md
  > 
  > * Add docs and test

  Touches: _none of this PR's files_

**`3ea1cfcd88`** · 2025-06-18T22:28:12+00:00 · Botberry

  > Release 🍓 0.274.2

  Touches: _none of this PR's files_

**`c6c402bb67`** · 2025-06-19T17:54:48+01:00 · Patrick Arminio

  > Fix LibCST DummyPool import (#3921)
  > 
  > * fix codemod DummyPool import
  > 
  > * Add release notes and bump libcst dev dep
  > 
  > * fix libcst compatibility
  > 
  > * Update release note
  > 
  > * Fix lock file
  > 

  Touches: _none of this PR's files_

**`377e6f3cbd`** · 2025-06-19T16:56:06+00:00 · Botberry

  > Release 🍓 0.274.3

  Touches: _none of this PR's files_

**`78b34af9e3`** · 2025-06-20T21:38:55+01:00 · Sam Millar

  > add `locate-definition` command to cli (#3902)
  > 
  > * add locate definition code
  > 
  > * [pre-commit.ci] auto fixes from pre-commit.com hooks
  > 
  > for more information, see https://pre-commit.ci
  > 
  > * add failure cases
  > 
  > * [pre-commit.ci] auto fixes from pre-commit.com hooks
  > 

  Touches: _none of this PR's files_

**`6b3bd5a6ee`** · 2025-06-20T20:39:45+00:00 · Botberry

  > Release 🍓 0.275.0

  Touches: _none of this PR's files_

**`2e61c2d505`** · 2025-06-20T20:41:43+00:00 · Strawberry GraphQL Bot

  > Remove TWEET.md

  Touches: _none of this PR's files_

**Your label** — did this PR break something, judged from the commits above?

    20. broke / clean  ->  

---
