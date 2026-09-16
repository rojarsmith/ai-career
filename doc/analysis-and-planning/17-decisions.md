# Ruling Record

This document is the **formal ruling record** for the hard contradictions listed in [98-revision-gaps.md](98-revision-gaps.md), decided item by item by the user on 2026-09-16.

**The authority of this document**: when this document conflicts with any of `00`–`16`, **this document wins**. Overturned passages have been marked in place with a pointer back here, but the original text is not deleted, so the line of argument is preserved.

**Contradictions not yet ruled on**: A5–A14, B1–B4 and C1–C4 in `98-revision-gaps.md` are still open and **must not** be treated as resolved by this document.

### Batch 1 (2026-09-16)

| ID | Issue | Ruling | Status |
|---|---|---|---|
| A1 | How sitemap is classified under `access_mode` | Keep `feed`, redefine what it covers | Settled |
| A2 | Which modules may `import playwright` | A `browser/` package plus three submodules that cannot import each other | Settled |
| A3 | The main line for résumé rendering | **Ruling deferred**; measure `.docx` vs PDF parse success rates first | Deliberately held open |
| A4 | The data model for the assessment stage | Add `assessment` as a first-class state | Settled |

### Batch 3 (2026-09-16, P1 / P2)

| ID | Issue | Ruling | Status |
|---|---|---|---|
| A8 | The request-interval constant | 5 seconds globally; per-source may only tighten, and the clamp lives in the throttler | Settled |
| A9 | Score floor | **No new constant**; upgrade the existing guardrail in `05` §6.2 to hard elimination | Settled |
| A10 | The criterion for creating a new table | Set the criterion and **retroactively re-review** eight entities | Settled |
| A11 | Where interview stories live | `content_block(kind='story')` + `reflection` | Settled |
| A12 | `evergreen` encoded twice | `posting_kind` describes what it is, `disposition` describes what we do with it | Settled |
| A13 | The shape of `fields.json` | Single file plus an `ats_profile` field | Settled |
| A14 | Where "deliberately not done" is defined | Three places with a division of labor; `04` §2.6 demoted to a summary | Settled |
| B3 | Whether design documents go into git | **Keep all of them out of git** (measured: the repo is PUBLIC) | Settled |
| B4 | Machine overwrites of files that carry human annotations | Human annotations do not go into files the machine overwrites | Settled |
| C3 | Where `data/` lives | `%LOCALAPPDATA%`, not version-controlled | Settled |
| C4 | Scope of the backup drill | Must cover all three zones and define a restore order | Settled |

### Batch 2 (2026-09-16, P0)

| ID | Issue | Ruling | Status |
|---|---|---|---|
| A5 | Naming the background-check stage | `reference_check`, plus a "single definition site for states" rule | Settled |
| A6 | The model for questionnaire questions and answers | Split out `application_question`; the block kind stays `qa_answer` | Settled |
| A7 | Where per-employer throttling constants live | A three-layer division of labor: the `00` registry / `target_employer` / `states.yml` | Settled |
| B1 | Whether read-only automation under logged-in session state gets an exception | **No exception**; rules 1 and 2 both stay exception-free | Settled |
| B2 | What qualifies as a "red line" | Split into two tables, mechanism red lines and commitment red lines | Settled |
| C1 | Which zone `pipeline.md` / `evaluations/` belong to | The private zone; `12`'s goal is met instead by `ai-career status` | Settled |
| C2 | Rebuild inputs landing in a deletable zone | The criterion for the derived layer tightens to "can be fetched again from outside" | Settled |

---

## A1 — sitemap keeps `access_mode = feed`

### Ruling

`access_mode` gets **no new enum value**. The definition of `feed` is widened to:

> **`feed`** — a **public read-only endpoint** that can be polled on a schedule (RSS / Atom / sitemap / a single-page HTTP GET). Scheduled polling is allowed, and conditional requests (`If-Modified-Since` / `If-None-Match`) are **mandatory**.

Differences in data format are carried by `source.kind` instead; its CHECK gains a `'sitemap'` value.

### Rationale

The `access_mode` column exists to **dispatch on "what actions are permitted"**, not to describe data format. `public_http` and `feed` permit exactly the same actions (schedulable, read-only GET, conditional requests required, must not be loaded in a browser), so an extra enum value **blocks nothing that was not already blocked**, while growing the dispatch table in [02-architecture.md](02-architecture.md) §5.6 from 5 rows to 6 and giving every new guard one more branch.

The "semantic distortion" that `14-browser-automation.md` points to is real, but it is a **format** problem: `kind` should solve it, not a column that controls **permissions**.

### The criterion in one sentence

> If two sources permit exactly the same actions, they should share one `access_mode`, no matter how far apart their data formats are.

### Scope of impact

| Document | Change |
|---|---|
| [02-architecture.md](02-architecture.md) §5.6 | Definition of the `feed` row widened (applied) |
| [04-ingestion.md](04-ingestion.md) §2.1 | `kind` in `source_registry` gains `sitemap` (applied) |
| [03-data-model.md](03-data-model.md) | Add `'sitemap'` to the CHECK on `source.kind` (applied when the schema lands) |

---

## A2 — A `browser/` package with three submodules that cannot import each other

### Ruling

Abolish the single-module rule "only `deliver/gate.py` may import playwright" and replace it with a `browser/` package holding three submodules that **must not import each other**:

| Submodule | Permitted scheme / actions | Purpose | Layer |
|---|---|---|---|
| `browser/render.py` | **`file://` and `127.0.0.1` only**; importing any network client is forbidden | résumé HTML → PDF | L4 assembly |
| `browser/capture.py` | **GET only, read-only**; no form filling, no clicking, no submitting | JD snapshot evidence | L0/L1 |
| `browser/assisted.py` | Full interaction, but **a human must be present and it runs in the foreground** | semi-automatic form fill, then hand off to the human | L5 delivery |

Only three narrow functions are exposed outside the package; everything else is private.

### Rationale

The intersection of the three original proposals is the **empty set**, and the version in `16` R-02-2 would leave **JD snapshot evidence with no legal place to live**: a snapshot has to load remote http(s), but `gate.py` is the delivery layer and `render/pdf.py` is restricted to `file://`. Meanwhile `14`'s argument that "Playwright is going to be installed anyway, so HTML→PDF has zero marginal cost" presupposes that capture exists — the two proposals are each other's premise and point in opposite directions, so a third proposal has to break the deadlock.

The three-submodule design gives each of the three legitimate uses a legal home while keeping "capability isolated by purpose" statically checkable.

### The price that must be written down honestly

1. **Static strength really does drop.** import-linter goes from 1 contract to 3; "which modules may touch the browser" goes from a binary question to a table. The point `16` R-02-2 concedes about itself **still holds** under this design, and must not be erased by the act of ruling.
2. **The no-mutual-import rule between the submodules must be enforced by tooling**, or `capture.py` bypasses every restriction the moment it imports `assisted.py`.

### Knock-on fix: a bug that would fail silently

Both `14` and `16` write the directory as `delivery/`, but the actual directory name in [11-tech-stack-roadmap.md](11-tech-stack-roadmap.md) §16 is **`src/aicareer/deliver/`**.

**An import-linter contract is a string comparison — a rule with the wrong path does not error, it passes quietly**, leaving you believing the defense is there. This fix has nothing to do with the present ruling, but it must be handled alongside it.

### The import-linter contracts required (four)

```toml
# 1. smtplib still has exactly one egress
[[tool.importlinter.contracts]]
name = "only deliver.gate may import smtplib"
type = "forbidden"
source_modules = ["aicareer"]
forbidden_modules = ["smtplib"]
ignore_imports = ["aicareer.deliver.gate -> smtplib"]

# 2. playwright only inside the browser/ package
[[tool.importlinter.contracts]]
name = "only aicareer.browser.* may import playwright"
type = "forbidden"
source_modules = ["aicareer"]
forbidden_modules = ["playwright"]
ignore_imports = [
  "aicareer.browser.render -> playwright",
  "aicareer.browser.capture -> playwright",
  "aicareer.browser.assisted -> playwright",
]

# 3. the three submodules are independent (miss this one and the first two are wasted)
[[tool.importlinter.contracts]]
name = "the three browser submodules do not import each other"
type = "independence"
modules = [
  "aicareer.browser.render",
  "aicareer.browser.capture",
  "aicareer.browser.assisted",
]

# 4. render must not touch the network
[[tool.importlinter.contracts]]
name = "browser.render must not import a network client"
type = "forbidden"
source_modules = ["aicareer.browser.render"]
forbidden_modules = ["httpx", "requests", "urllib.request", "aiohttp"]
```

> `file://`-only and "read-only GET" are **runtime** properties that import-linter cannot check. Contract 4 only blocks static dependencies; the real scheme restriction must be enforced inside `render.py` with runtime assertions and covered by tests.

### Scope of impact

| Document | Change |
|---|---|
| [02-architecture.md](02-architecture.md) §5.6, §6 | Playwright constraints rewritten, `delivery/` → `deliver/` (applied) |
| [11-tech-stack-roadmap.md](11-tech-stack-roadmap.md) §16 | Project structure gains a `browser/` package |
| [14-browser-automation.md](14-browser-automation.md) | Module boundaries aligned with this ruling |

---

## A3 — Résumé rendering: the ruling is deliberately deferred

### Ruling

**No main rendering line is chosen now.** Until the prerequisite question has been answered by measurement:

- [06-content-assembly.md](06-content-assembly.md) §6 and [11-tech-stack-roadmap.md](11-tech-stack-roadmap.md) §8 both **list "candidates + criteria" only, and no "recommendation"**.
- The recommendations currently in those two documents (Typst in 06, docxtpl in 11) are **suspended with immediate effect**, but the text stays so the argument is preserved.

> **Whoever writes a recommendation first manufactures the next contradiction.**

### The prerequisite question that must be answered first

**V4: the difference in parse success rate between `.docx` and PDF on the target ATS.**

The only reason [11-tech-stack-roadmap.md](11-tech-stack-roadmap.md) §8 gives for recommending docxtpl is "ATS parse success rates for `.docx` are generally higher than for PDF" — a sentence it tags **needs verification** itself. **Picking a tool before the prerequisite question is answered is rolling dice.**

How to verify: produce one representative résumé in both formats, put them through the actual target platform (or its parser preview), and compare the extracted fields; supplement with a `pdftotext` round-trip to check the ordering of the text layer.

### Why deferring costs less than it looks

What [15-target-tsmc.md](15-target-tsmc.md) established: **TSMC has you fill in a structured résumé online, not upload a document**. So the first vertical (TSMC) **never passes through the rendering layer at all**. The main rendering line matters for direct email submission, 104 and headhunter channels — and none of those sit on the Phase 1 critical path.

Deferring does not block progress, and that is exactly why it can be deferred.

### The four candidates and where they stand (kept side by side, not ranked)

| Candidate | PDF | `.docx` | Main risk | Source |
|---|---|---|---|---|
| Typst + Pandoc `reference.docx` | Good | Yes (quality needs verification) | Young ecosystem, templates written by hand | 06 §6 |
| docxtpl + Word template + LibreOffice | Medium | Yes | Template is binary and diff-hostile; one more LibreOffice dependency | 11 §8 |
| HTML + Playwright print-to-PDF | Good | **None** | Gives up `.docx`; the marginal-cost argument depends on A2 | 14 |
| HTML + WeasyPrint | Good | **None** | Native dependencies on Windows have historically been painful (needs verification) | 06 §6 |

### Three facts that have to be held at once

1. **Typst was silently eliminated.** It is 06's formal recommendation, yet it is absent from the side-by-side list in `16` R-11-4, and nobody explained why it was overturned. This ruling **puts it back among the candidates**.
2. **Whether `.docx` is a required output at all is a question further upstream than "which tool".** If the answer is no, the candidate list drops from four to two immediately.
3. **Candidate 3's cost argument depends on A2.** A2 has ruled for the three-submodule `browser/` package, `browser/render.py` exists, and so Playwright really will be installed — candidate 3's "low marginal cost" holds. But that **is not a reason to pick it**; it only removes one reason against it.

### Conditions for lifting the deferral

Once V4 is done, **exactly one document** (06 §6 is suggested) writes the final recommendation and 11 §8 becomes a pointer back to it. Until then, no document may declare a main line.

---

## A4 — Add `assessment` as a first-class state

### Ruling

The `application` state machine in [03-data-model.md](03-data-model.md) §4.2 gains **`assessment`**:

```
acknowledged ──→ assessment ──→ interviewing
     │               │
     │               └──→ rejected_by_employer / ghosted / withdrawn
     └──→ interviewing (employers with no assessment skip straight ahead)
```

`assessment` covers "questionnaires, online tests and skills certifications the employer requires you to complete". Entering and leaving it are **human-triggered only** (the same tier as the existing `interviewing`).

### Rationale

R-10-1's red line is "**LLM assistance is disabled during an assessment**" — concretely, for TSMC, that the English test must not be sat by an AI on your behalf. To enforce it, the system has to be able to answer "are we in an assessment right now?".

This is **the only rule in this revision batch that requires the system to know when to shut up**, and it is itself already classified by [98-revision-gaps.md](98-revision-gaps.md) B2 as a "commitment red line" — the weakest tier of mechanical strength. **Hanging the weakest red line on a state you can only learn by inferring it from `info_requested` + `due_at` + kind weakens it one layer further.**

### The opposing argument, recorded fairly

[03-data-model.md](03-data-model.md) §0 item 8 sets an explicit precedent for restraint:

> Giving first round / second round / onsite their own states would let the state machine run away; `interviewing` is a single state and the rounds go in an `interview_round` child table

By that precedent, `assessment` should be a child table too, not a state. **This ruling knowingly violates the precedent**, on the grounds that enforceability of a red line outranks minimality of the state machine. It is an exception with a price, not a repudiation of the precedent — the restraint principle in `12-reference-career-ops.md` **still holds** at `job_flag`, `block_note` and the rest.

### Knock-on change

The `times_in_replied` computation in `v_block_stats` has to take `assessment` in — an employer asking you to sit an assessment is itself a reply signal. Leaving it out understates the reply rate.

### What this ruling does **not** cover

- **A5 (the naming of `reference_check` vs `background_check`) is still open.** `16` R-08-4 bundles `assessment` and `reference_check` into a single proposal, but the user ruled on `assessment` only. `reference_check` **must not** be slipped in on the back of it.
- The remaining extension states such as `screening` / `closed` are likewise unruled.

### Scope of impact

| Document | Change |
|---|---|
| [03-data-model.md](03-data-model.md) §4.2 | State machine gains `assessment` (applied) |
| [03-data-model.md](03-data-model.md) `v_block_stats` | `times_in_replied` takes in `assessment` (applied) |
| [10-risk-compliance.md](10-risk-compliance.md) | The R-10-1 red line reads the state directly instead of inferring it |
| [15-target-tsmc.md](15-target-tsmc.md) | The English test flow maps onto this state |

---

## A5 — `reference_check`, plus a "single definition site for states" rule

### Ruling

The background-check stage is named **`reference_check`** (`background_check`, proposed by `15`, is not adopted).

**And a rule is established alongside it, which matters more than the name itself:**

> **Every new state lands in [03-data-model.md](03-data-model.md) §4.2 first; [08-delivery-tracking.md](08-delivery-tracking.md) §5.1 is a projection of it. 08 must not add state names of its own.**

### Rationale

The name: what is checked is your references and work history, not a criminal record. In Taiwanese practice "background investigation" is read as a private-investigator credit check, which is too large a semantic drift.

The rule: `15` points out that "the state-naming mismatch between `03` and `08` is a real contradiction `99-gaps` failed to record" and, in the same breath, picks a different name than `16` for the same new state — **this revision batch manufactured a contradiction of exactly the shape it was complaining about**. Which demonstrates exactly why naming must have a single definition site.

### Note

The **transition conditions for `reference_check`, and whether it is in scope for this cycle, have not been ruled on**; this item fixes only the name and the rule. The remaining extension states such as `screening` / `closed` are likewise unruled.

---

## A6 — Split out `application_question`

### Ruling

| Entity | Whose asset | Lifecycle | Carries |
|---|---|---|---|
| **`application_question`** (new) | The employer | Dies with the job posting | `question_key`, `question_variants`, the verbatim question text, the job posting it belongs to |
| **`content_block(kind='qa_answer')`** (kept, **not renamed**) | Me | Reused across years | Answer material; provenance runs through the existing `artifact_block_usage` |

`question_key` / `question_variants`, proposed by `15`, **hang off `application_question`**, not off the block.

### Rationale

**The question is the employer's asset, the answer is mine, and their lifecycles differ.** Once a job posting comes down the question is dead, but the answer gets reused for years — bind them to one entity and the delete semantics fight each other.

TSMC makes this concrete: TSMC's application questionnaire is **per role**, and the same question turns up in different job postings with different wording. That is exactly the problem `question_variants` is for, and it belongs naturally to the question, not to the answer.

The reason for **not renaming `qa_answer`** is very practical: a rename touches the CHECK in `03` and the existing data, and buys nothing but readability.

### Scope of impact

| Document | Change |
|---|---|
| [03-data-model.md](03-data-model.md) | New `application_question` entity (applied) |
| [06-content-assembly.md](06-content-assembly.md) §2.1 | Block-kind table aligned to `qa_answer` |
| [15-target-tsmc.md](15-target-tsmc.md) | The questionnaire material store now hangs off `application_question` |

⚠ **Must land before `content_block` holds any data**, otherwise it becomes a migration.

---

## A7 — Constants: a three-layer division of labor

### Ruling

| Layer | What goes here | What does **not** |
|---|---|---|
| The shared-constants registry in [00-overview.md](00-overview.md) | Global defaults plus a "measured / placeholder" marker | Any per-employer data |
| **The `target_employer` table** | per-employer overrides (`cooldown_days`, `max_active_applications`, `suspect_after_days`, `ghosted_after_days`…) | Global defaults |
| `states.yml` | The **employer-independent** presentation layer: display name, next-step copy, whether it counts in the denominator | **Day counts** |

**Abolish the two aliases `employer_policy` and `watchlist`**, unifying on `target_employer`.

### Rationale

`12` putting day counts into `states.yml` is **wrong on dimensionality**: day counts are per-employer, `states.yml` is per-state, and the two do not line up.

`99-gaps` contradiction 5 was originally just "the **values** disagree"; this revision batch upgraded it to "the values disagree **and so do the homes**" (four homes, three entity names). The three-layer split gives every kind of data exactly one home.

### Note

The constants registry from `16` R-00-5 **does not exist yet** — `00` §8 is currently called "points not yet converged across documents". This ruling depends on it being created, which is an **ordering dependency** (A8 depends on it too).

---

## B1 — Logged-in session state automation: no exception

### Ruling

**Rules 1 and 2 in [10-risk-compliance.md](10-risk-compliance.md) §2.4 both stay exception-free.** Sources with `requires_login = 1` are handled manually, always. The "read-only status query while logged in" from `14` §9.3 is **not adopted**.

### Rationale

**A structural reason outranks a benefit calculation.** Rule 2 currently has no exceptions, so it can be checked with a binary question: **was logged-in session state used or not**. Add five conditions (your own account, a human present, read-only, at most once a week, a single employer) and it turns from a **checkable rule** into a **rule that requires judgement** — and at least two of the five ("a human present", "read-only") **cannot be verified in code**.

The core argument of [07-review-gate.md](07-review-gate.md) §10.3 is that **friction that can be bypassed is eventually bypassed**. Demoting Principle 3 from a structural constraint to a judgement call makes that argument apply to itself.

**The benefit side was small to begin with**: what you save is "opening a browser by hand once a week to look at status", and the dedicated Chrome already makes that cheap.

**Incidental fix**: `14` §9.3 asks for a pardon from rule 2 only and **misses rule 1**. Both rules block this, so pardoning one leaves a literal violation of the other — and the oversight itself shows that the boundary of an exception is harder to hold than the proposer assumed.

### Effect on `browser/assisted.py`

`browser/assisted.py` as ruled in A2 (human present, foreground, semi-automatic form fill) is **unaffected by this ruling**: it serves L5 delivery and is open only to `manual_assisted` sources. What this ruling blocks is **scheduled automatic queries under logged-in session state**, which is a different thing.

---

## B2 — Red lines split into two tables

### Ruling

[10-risk-compliance.md](10-risk-compliance.md) §2.4 splits into two tables:

| | **Mechanism red line** | **Commitment red line** |
|---|---|---|
| Definition | Enforceable in code | Not enforceable in code |
| A violation means | **this is a bug** | **you are lying to yourself** |
| Examples | the approval gate, the sole delivery egress, never filling in a statutory ID number on your behalf (the field is simply never built), `12`'s new proposal that "the implementation site of human-in-the-loop must not be moved into the prompt" | never sitting a skills assessment on your behalf, never fabricating experience |
| How it is checked | CI / tests | none |

And **merge the duplicate "never sit an assessment on your behalf" proposals from `15` and `16` into one**, renumbering as you go (all three documents currently claim "item 11", which is a real merge conflict).

### Rationale

This is the batch's only **meta-level** contradiction: if `12`'s red line 11 (human-in-the-loop must be a code-level constraint) holds, then the new red line in `16` R-10-1, which concedes it is "the weakest tier of mechanical strength", **does not qualify as a red line at all**. The two documents give incompatible definitions of what earns the name.

Splitting the table saves both sides: the most important ethical commitment (never sitting an assessment for you) stays on the top-priority list, and the term "red line" is not devalued by taking in entries that cannot be enforced.

### The price that must be written out

> **Commitment red lines really are weaker in practice.** Putting both in one document makes the mechanism red lines look soft too — so the two tables must be visually separated beyond doubt, and the commitment table's header must say outright: "this table has no code-level defense; it rests on self-discipline alone".

---

## C1 — `pipeline.md` and `evaluations/` go to the private zone

### Ruling

Both go to the **private zone** (under the data root) and **not into the repo tree**.

`12`'s goal — giving an AI agent a human-readable overview of the pipeline — is met instead by **the read-only output of `ai-career status`**, the status CLI already proposed in `16` R-02-4.

### Rationale

What `pipeline.md` contains is "**which job postings at which companies I am applying to, and what state each is in right now**" — more current than `content/profile.yaml`, and more usable for inferring intent. `evaluations/` is the same (company name plus my score for the posting and my snark about it).

Putting them under the repo tree **directly violates [13-repo-layout.md](13-repo-layout.md)'s own zoning principle**, a principle this project has already adopted. There is no need to break it for a convenience a read-only CLI can deliver.

---

## C2 — Tightening the criterion for the derived layer

### Ruling

The criterion for the derived layer tightens from "**it is derived**" to "**it can be fetched again from outside**".

| | Examples | Belongs to |
|---|---|---|
| Regenerable | HTTP cache, render scratch, aggregate reports | the derived layer `run/`, deletable wholesale |
| **Not** regenerable | **the raw JD snapshot** (job postings come down), human decisions, the bytes that were sent | **the private zone `vault/`, must be backed up** |

The JD snapshots under `raw/` **move to the private zone**.

### Rationale

`12` requires the Phase 0 DoD to include "rebuild an equivalent DB from `content/` + `evaluations/` + `raw/`", but under `13`'s zoning the derived layer carries the promise that deleting the whole thing must be safe.

**A directory cannot be both "a required input to the rebuild" and "deletable at any time".** That is a logical contradiction, not a trade-off.

A JD snapshot's non-regenerability is exogenous: **job postings come down**, and once one is down you can never get back the JD text as it stood — which is the only evidence for "why I wrote it that way at the time". That is also exactly where `14` §9.2's evidentiary requirement lands; the two concerns converge here.

---

## A8 — Request interval: 5 seconds globally, per-source may only tighten

**Ruling**: the global minimum interval is **5 seconds**. A per-source override may only **tighten**, implemented as `max(5, min_interval_s)`, and **the clamping logic lives in the throttler, not in config validation**. This limit **constrains automated requests only; a human browsing by hand is unconstrained**.

**Rationale**: the 2 seconds in `04` §7 is not a number scattered through prose, it is the per-source default in the source registry YAML (`rate: { min_interval_s: 2 }`). Without the clamp, "tighten the global to 5 seconds" gets quietly cancelled by one YAML field. Clamping in config validation is not enough either — config can be bypassed, the throttler cannot.

**Dependency**: `14` says "the two documents must converge on one number" but does not pick one; `15` says "set a single definition point in the shared-constants registry in `00`", but **that registry does not exist yet** (`00` §8 is currently called "points not yet converged across documents"). See open item 2.

---

## A9 — No new `score_floor`; upgrade the existing guardrail

**Ruling**: **no new `score_floor` constant.** Instead, upgrade the lower-edge guardrail in [05-scoring-triage.md](05-scoring-triage.md) §6.2 from "clamp `T_l`" **to "hard elimination"** — same number (35), same observable anchor, no extra constant.

The activation condition reuses the existing threshold of **80** human decisions from §6.3, **introducing no fourth number**.

**Rationale**: neither proposal noticed that §6.2 **already has a lower-edge guardrail, and its value happens to be 35 as well** (`T_l` clamped to `[35, 60]`). Under the existing design a posting below 35 could never enter the gray-band queue anyway, so R-05-3's "floor = 35" is **very nearly a no-op** in quota mode. The one behavior it changes is "leave slots empty when qualifying postings fall short of the quota", and `12` already handles that separately with another recommendation (spend the empty slots on capture planning).

**And it clears up a numeric mess along the way**: the same "cumulative human decision count" had been given three thresholds with three meanings — **40 / 80 / 80** (`12`'s floor taking effect, `05` §6.3's switch to fixed mode, `12`'s second profile unlocking). This ruling unifies them at 80.

---

## A10 — The criterion for creating a new table, applied retroactively

**Ruling**: write this at the top of [03-data-model.md](03-data-model.md):

> **You create a new table when "this thing has a lifecycle of its own, and more than one place queries it by primary key".** Both conditions must hold.

On that basis, the entities already proposed get a **retroactive re-review**:

| Entity | Verdict | Destination |
|---|---|---|
| `target_employer` | **passes** | New table (an employer's lifecycle far outlasts any one application) |
| `application_question` | **passes** | New table (ruled in A6) |
| `interview_story` | fails | → `content_block(kind='story')`, see A11 |
| `comp_research` | fails | → a field group on `target_employer` |
| `role_class` | fails | An enum value does not need a table |
| `job_flag` | fails | Keep `12`'s argument for restraint |
| `block_note` | fails | Same as above |

**Rationale**: `12` argues for restraint throughout ("at a volume of 80–200 submissions it buys you nothing"), `16` R-03-1 adds eight entities in one go, and `15` adds three more. **This is not a question of who is right, it is that there is no shared criterion** — the result is one `03` receiving revisions in two opposite styles, so anyone who wants to add a table later can cite whichever document suits them as precedent.

---

## A11 — Interview stories use `content_block(kind='story')`

**Ruling**: the 48-hour post-interview debrief produces a `content_block(kind='story')`, and `content_block` gains a `reflection` field to carry the STAR self-critique. **No `interview_story` entity is created.**

**Rationale**: a separate entity would **fork the provenance chain** the honesty principle rests on — a résumé bullet goes through `artifact_block_usage` back to `content_block` while an interview story takes another path, and the factual-assertion check in [07-review-gate.md](07-review-gate.md) §5.3 **only recognizes the former**.

**Side benefit**: it gives `16` R-03-4's `usable_in: [resume, profile, questionnaire, interview]` something to tag.

---

## A12 — `posting_kind` and `disposition` each do their own job

**Ruling**:

| Column | Describes | Values |
|---|---|---|
| `posting_kind` | **what this job posting is** | `job` / `talent_pool` / `evergreen` |
| `disposition` | **what we decided to do with it** | `ok` / `blocked` / `flagged` |

**Remove the `'evergreen_pool'` value from `disposition`.**

**Rationale**: `12` adds `'evergreen_pool'` to `disposition` and `16` R-05-5 adds `'evergreen'` to `posting_kind` — one table, one row, two columns describing the same thing, and they **can contradict each other** (`disposition='ok'` + `posting_kind='evergreen'`).

---

## A13 — A single `fields.json` plus an `ats_profile` field

**Ruling**: adopt the single-file design from `16` R-06-3, with `ats_profile` taking `avature` / `successfactors` / `tw_104` / `generic`. `12`'s per-ATS file split is not adopted.

**Rationale**: `fields.json` is a **per-application output**; one generation corresponds to exactly one ATS, so splitting the file only adds one more lookup on the assembly side.

---

## A14 — "Deliberately not done": a three-way division of labor

**Ruling**:

| List | Location | What it takes in |
|---|---|---|
| **Mechanism red lines** | [10-risk-compliance.md](10-risk-compliance.md) §2.4, table one | things that will cause harm and **should be enforced in code** |
| **Commitment red lines** | Same section, table two | things that will cause harm but **cannot be enforced in code** (see B2) |
| **Deliberately not done** | a new section in [00-overview.md](00-overview.md) | things evaluated, declined, and **open to being overturned by future data** |

[04-ingestion.md](04-ingestion.md) §2.6 is **demoted to a summary pointing at `10` §2.4** and no longer defines entries of its own.

**Rationale**: `16` R-00-4 demands "only one definition site" without naming the other two lists that already exist. And the red line `15` proposes, "never register an account on your behalf", **is already written verbatim into `04` §2.6** ("automatically registering accounts, automatically accepting terms of service") — four definition sites would only manufacture the next contradiction.

---

## B3 — Design documents all stay out of git

### Ruling

`doc/analysis-and-planning/` **keeps its current gitignore status**; every document lives on the local machine only.

### The decisive fact

> **`gh repo view rojarsmith/ai-career --json visibility` → `{"isPrivate": false, "visibility": "PUBLIC"}`** (measured 2026-09-16)

`13`'s B3 proposal reads: "**after confirming the main repo's visibility is private**, remove `doc/analysis-and-planning/` from `.gitignore`". **That premise does not hold**, so the proposal lapses automatically.

### Rationale

`13`'s threat model is internally inconsistent: it argues `content/` must move out of the repo (on the grounds that "this project assumes an AI agent will run `git add -A` on its own"), yet wants [15-target-tsmc.md](15-target-tsmc.md) to sit in **the same repo, the one with a remote**. And what `15` contains is "my target is TSMC, and here is my submission battle plan" — no less sensitive than parts of `content/profile.yaml`.

The repo is public, so this is not even a question of whether private is strong enough.

### The argument that was sacrificed (recorded honestly)

`13`'s central claim — **"an AI agent is the primary reader of these documents, and not version-controlling the definition of its behavior is self-contradictory" — holds on its own terms**. This ruling does not refute it; it only judges the price too high under a public repo.

**Compensating measure**: `content/` and `journal/` under `vault/` are already planned as a **local git repo with no remote** (see C3). The design documents can go into that same local repo and gain version history without leaking. That cuts the price of "not version-controlled" down to nothing more than "switching machines means moving them by hand".

### Conditions for re-evaluating

If the repo later turns private, this issue can be reopened — but even then, a battle plan like `15` that **names an employer** should stay in `vault/`, with only unnamed templates in the repo.

---

## B4 — Human annotations do not go into files the machine overwrites

**Ruling**: human annotations are written to the DB or to `journal/`. `evaluations/` is **purely regenerable render output** and can therefore be deleted wholesale (consistent with C2's criterion).

**Rationale**: `12` proposes that `evaluations/` be "machine-generated, one-way overwritten **except for the human annotation block**". That design puts human judgement and machine output in the same file, separates them with a block marker, and then lets the machine overwrite it on a schedule. **Any parse error, any marker accidentally deleted, any re-run will silently eat the human's annotations** — and those annotations are the only learning material `09` has at small sample sizes (`99-gaps` B2).

This is a data-loss bug, not a matter of style.

---

## C3 — `data/` lives in `%LOCALAPPDATA%`, not version-controlled

**Ruling**: adopt `13`'s design.

- `content/` → `vault/content/`, a **local git repo with no remote**
- `data/` → `%LOCALAPPDATA%\ai-career\` (pointed at by `AI_CAREER_DATA_DIR`), **not version-controlled**, backed up to an encrypted external drive

`16` R-11-3's option A (put both `content/` and `data/` in a second repo) is **rewritten** into the form above.

**Rationale**: putting `data/` into git is an implementation error — what is in there is a SQLite file (every commit stores the whole binary), WAL/SHM, and artifact blobs. This is not a trade-off, it is misuse of git.

---

## C4 — The backup and restore drill must cover all three zones

**Ruling**: the backup and restore drill in `11` §12 **must cover all three physical locations at once** and define a **restore order**:

| Order | Location | Back up? |
|---|---|---|
| 1 | the git repo (system layer) | git is the backup |
| 2 | `vault/content/` (local repo, no remote) | **required**, encrypted and off-machine |
| 3 | `%LOCALAPPDATA%\ai-career\vault\` | **required**, encrypted and off-machine |
| — | `run/` (the derived layer) | **no** (backing it up is waste and widens the exposure surface) |
| — | the dedicated Chrome profile | **not backed up**, but the destruction procedure must cover it |

**Rationale**: `13` correctly added the row "the dedicated Chrome profile is not backed up", but no document states the strategy for each of the three zones or the **restore order**. **A drill that passes by restoring `data/` alone does not mean you can actually recover** — `vault/content/` is a second repo and `%LOCALAPPDATA%` is a third location.

The pass condition for the drill must be "restore everything on a clean machine and get one working run of `ai-career status`".

---

## Open items

1. **A3's V4 measurement** (`.docx` vs PDF parse success rate) — the only thing holding up a decision on the rendering layer.
2. **Create the shared-constants registry in `00`** — A7 and A8 both depend on it, and it does not exist yet.
3. **Fix the `deliver/` path** across every document (knock-on from A2).
4. **The transition conditions for `reference_check`, and whether it is in scope for this cycle**, have not been ruled on (A5 fixed only the name).
5. **The four items under §"handled too shallowly" in `98-revision-gaps.md` are still untouched** — especially item 3, "what the first TSMC vertical actually costs in money and time, and where it gets stuck", which is a precondition for scheduling Phase 1.

**A1–A14, B1–B4 and C1–C4 are all ruled.**
