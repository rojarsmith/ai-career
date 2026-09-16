# Gaps and Contradictions in This Revision Batch

This document reports only the **contradictions** among the revision proposals derived from the five new documents `12`–`16`, their **conflicts with the product principles**, the places **handled too shallowly**, and the **flaws** that adding the TSMC vertical pries open in the existing general design but that none of the five new documents points out. It does not restate what the five documents already say.

Severity markers: **P0** = starting work without ruling on it first leads straight to rework or a principle violation; **P1** = it will leave the documents contradicting each other long-term; **P2** = better to fill in.

---

## Contradictions

### A. Hard contradictions: the same spot changed into different results by two or more of the new documents

Every item below is a case of "these two proposals cannot both be adopted," not a difference in wording.

#### A1 (P0) Does `access_mode` get a new enum value or not

| Proposal source | Claim |
|---|---|
| `14-browser-automation.md` | Add `public_http` to [02-architecture.md](./02-architecture.md) §5.6, on the grounds that cramming sitemap + JobDetail GET into `feed` distorts the semantics |
| `15-target-tsmc.md` | Adds "authoritative sitemap" as a first-class source **kind**, but takes no position on access_mode |
| `16-plan-revisions.md` R-02-3 / R-04-1 | **Explicitly confirms that sitemap falls under the existing `feed` value; no new enum value** |

The two are mutually exclusive. This is not a naming-taste question, because the original text of 02 §5.6 carries a code-level constraint: "sources other than `manual_assisted` must not load Playwright." The set of enum values determines the shape of the import-linter rules, and once the schema lands, changing it takes a migration.

**Recommended ruling**: adopt `feed`, and rewrite the definition of `feed` as "a public read-only endpoint that can be polled on a schedule (RSS / Atom / sitemap / single-page HTTP GET), and must carry conditional requests." The reason is that the purpose of the `access_mode` column is to **dispatch the permitted actions**, not to describe the data format; `public_http` and `feed` permit exactly the same actions, so an extra value blocks nothing extra while turning the §5.6 table from 5 rows into 6 and forcing every new guard to carry one more branch. The "semantic distortion" 14 raises is real, but it should be carried by `source.kind` (12 has already proposed adding `'sitemap'` to the CHECK on `source.kind`), not by `access_mode`.

#### A2 (P0) Which modules may `import playwright`

| Proposal source | Permitted set |
|---|---|
| `02-architecture.md` (current) | Only `delivery/gate.py`; and sources other than `manual_assisted` must not load Playwright |
| `14-browser-automation.md` | Modules under `src/aicareer/browser/` (`delivery/` and `ingest/` may only use `browser/`'s narrow interface) |
| `16-plan-revisions.md` R-02-2 | Two modules, `delivery/gate.py` and `render/pdf.py`; and `render/pdf.py` **must not import any network client**, with the render context allowed to load only `file://` and `127.0.0.1` |

This contradiction is worse than it looks, because the intersection of the two proposals is empty, and 16's scheme **leaves 14's core use case nowhere to live**:

- 14 §9.2's JD snapshot evidence (P1) requires Playwright to load a remote http(s) page.
- Of the two modules 16 R-02-2 permits, `gate.py` is the delivery layer (a JD snapshot is not a send), and `render/pdf.py` is explicitly restricted at the behavior layer to `file://` and `127.0.0.1`.
- So under 16's rules, JD snapshot evidence **has no legal place to be implemented**. And 14 in turn uses the JD snapshot as the premise of its argument that "Playwright is installed anyway, so the marginal dependency of HTML→PDF is zero" (see A3).

There is a knock-on error as well: both documents write `delivery/`, but the actual directory name in [11-tech-stack-roadmap.md](./11-tech-stack-roadmap.md) §16 is `src/aicareer/deliver/`. An import-linter contract is string matching, and a rule with the wrong path passes silently.

**Recommended ruling**: adopt "one `browser/` package plus three submodules inside it that may not import each other" — `browser/render.py` (`file://` only), `browser/capture.py` (GET only, read-only, no form filling or clicking), `browser/assisted.py` (human present, foreground, L5). Only three narrow functions are exposed outward. This satisfies both 14's "PDF and snapshots should not be blocked by the delivery layer's rules" and 16's "static constraints must be checkable by import-linter," at the cost of writing 3 import-linter contracts instead of 1. **The "loss of static strength" that 16 R-02-2 honestly acknowledges still holds under this scheme, and must be written into 02's cost column as 16 requires — do not quietly erase it while ruling.**

#### A3 (P0) The résumé rendering mainline: there are now four candidates, and instead of converging, the new documents added one

| Source | Mainline | .docx output |
|---|---|---|
| [06-content-assembly.md](./06-content-assembly.md) §6 (current) | **Typst** (PDF) + Pandoc `reference.docx` (DOCX) | Yes |
| [11-tech-stack-roadmap.md](./11-tech-stack-roadmap.md) §8 (current) | **docxtpl + LibreOffice headless** | Yes |
| `14-browser-automation.md` | **HTML + Playwright**, listed as an official fallback; the argument is zero marginal install cost | No |
| `16-plan-revisions.md` R-11-4 | **HTML template + Chromium print vs docxtpl + LibreOffice, evaluated side by side**; LibreOffice must not be dropped before V4 | Only one route has it |
| `12-reference-career-ops.md` | "Playwright PDF rendering can replace LibreOffice" **holds only on the premise that .docx output is abandoned** | Treated as mandatory |

Three problems at once:

1. **Typst is silently eliminated**. Typst is absent from 16 R-11-4's side-by-side evaluation list, yet Typst is the official recommendation of 06 §6. No new document explains why it is overturned. `99-gaps.md`'s contradiction list never recorded the original conflict between 06 §6 and 11 §8 either — 14 correctly points this out, but the fix it offers (promoting HTML + Playwright to an official fallback) takes the candidates from 2 to 3.
2. **Whether `.docx` is a required output — nobody has ruled on this prior question**. 12 treats it as a constraint; one of 16 R-11-4's routes simply does not produce `.docx`. Before ruling on the rendering tool, the item 11 §8 has already flagged as needing verification must be answered first: the difference in ATS parsing success rate between `.docx` and PDF.
3. **14's "zero marginal cost" argument depends on how A2 is ruled**. If A2 goes with 16's scheme (render context limited to `file://`, network clients forbidden), the JD snapshot will not install Playwright, and 14's zero-marginal-cost premise disappears. The two proposals are each other's premise, and they point in opposite directions.

**Recommended ruling**: write this into `99-gaps.md`'s contradiction section (it is not there today), and require that until V4 (`.docx` vs PDF parsing success rate) is done, `06` and `11` write only "candidates + criteria," never "recommendation." Whoever writes a recommendation first manufactures the next contradiction.

#### A4 (P0) Is `assessment` a state or not

- `12-reference-career-ops.md`: the semantics of `info_requested` cover "application questionnaires and online tests"; add a `due_at` column, and **explicitly do not add an `assessment` state**.
- `16-plan-revisions.md` R-08-4: the state machine is extended to `screening / assessment / interviewing / reference_check / offer / closed`, **explicitly adding `assessment`**, bound to R-10-1's test red line.

This one has knock-on effects: R-10-1's `assessment_windows` mechanism (disable LLM assistance during a test) needs to know "am I in a test window right now." Under 12's scheme that signal has to be derived from `info_requested` + `due_at` + some kind; under 16's it is a first-class state.

**Recommended ruling**: adopt 16's `assessment`. The reason is not state-machine aesthetics but that R-10-1's red line is the only rule in this batch that requires "the system to know when to shut up," and hanging it on a state knowable only by derivation weakens the weakest red line by one more layer. 12's "no new states" principle is right elsewhere (`job_flag`, `block_note`); here it happens to hit the one exception.

#### A5 (P0) What the background-check stage is called

- `15-target-tsmc.md`: add **`background_check`** to [03-data-model.md](./03-data-model.md) §4.2 (`interviewing → background_check → offer / rejected_by_employer`); entering it forces a checklist for referee consent and current-employer disclosure.
- `16-plan-revisions.md` R-08-4: add **`reference_check`** to [08-delivery-tracking.md](./08-delivery-tracking.md) §1.1.
- `15-target-tsmc.md` also proposes: the inconsistent state naming between 03 and 08 is a real contradiction `99-gaps.md` never recorded, and 03's vocabulary should be the schema truth.

In other words, 15 proposes "unify the naming between 03 and 08" while it and 16 each pick a different name for the same new state, so this batch **has itself created a contradiction of exactly the type 15 complains about**. Which is a neat demonstration of why naming needs a single point of definition.

**Recommended ruling**: `reference_check` (what gets checked is referees and work history, not a criminal record; in Taiwanese practice the term "background check" reads as a PI credit check). And turn 15's demand that "03 is the schema truth" into a rule: **every new state lands in 03 §4.2 first, and 08 §5.1 is its projection**; 08 must not invent state names of its own.

#### A6 (P0) There are two data models for questionnaire answers

- `15-target-tsmc.md`: `content_block`'s `faq_answer` is upgraded to **`questionnaire_answer`**, adding `question_key` / `question_variants` / `used_in` on the block, with assembly automatically comparing against historical answers under the same `question_key`.
- `16-plan-revisions.md` R-03-1 / R-03-3: add an **`application_question(+answer_block)`** entity; answers get the same `artifact_block_usage` provenance as résumé bullets.
- `12-reference-career-ops.md`: the block kind enum follows 03's CHECK, i.e. **`qa_answer`**, and asks that the table in 06 §2.1 be changed to match.

Three documents give three names to the same field (`faq_answer` → `questionnaire_answer` / `qa_answer` / split into its own entity), and 15's scheme stuffs the question into the block while 16's makes the question its own entity. In the TSMC context the difference is substantive: TSMC's application questionnaire is per-role, and the same question shows up on different postings with different wording — exactly the problem 15's `question_variants` is trying to solve, and in 16's model it naturally lands on `application_question`.

**Recommended ruling**: adopt 16's split (the question is the employer's asset, the answer is mine; their lifecycles differ), keep the block kind as 03's existing `qa_answer` without renaming (renaming means touching the CHECK and existing data, and buys only readability), and hang 15's `question_key` / `question_variants` on `application_question`. This must be ruled before `content_block` holds any data.

#### A7 (P0) The per-employer SLA and throttling constants have four homes

| Proposal | Where the constants live |
|---|---|
| `12-reference-career-ops.md` | Moved out of the SQL CHECK into **`states.yml`** (display name, `D_suspect` / `D_ghost`, suggested-next-step copy, whether it counts in the denominator) |
| `15-target-tsmc.md` | A new **`employer_policy` table** (`cooldown_days` / `max_active_applications` / `max_per_90d` / `d_suspect_days` / `d_ghost_days`) as the single truth |
| `16-plan-revisions.md` R-08-2 | **`target_employer.suspect_after_days` / `ghosted_after_days`** override columns |
| `16-plan-revisions.md` R-00-5 | A new **shared constant registry** in [00-overview.md](./00-overview.md), holding `employer_cooldown_days` and the §5.5 ghosted dual thresholds |

Four homes, and `employer_policy` and `target_employer` are two entity names for the same concept (12 adds a third phrasing, "target-company watchlist"). `99-gaps.md` contradiction 5 (inconsistent ghosted SLA values) used to be merely "inconsistent values"; this batch upgrades it to "inconsistent values **and** inconsistent homes."

**Recommended ruling**: three tiers, each holding exactly one kind of thing —
1. **The constant registry in 00** holds only global defaults plus a "measured / placeholder" marker, and no per-employer data whatsoever;
2. **The `target_employer` table** (one entity name; abolish the two aliases `employer_policy` and `watchlist`) holds per-employer overrides;
3. **`states.yml`** holds only **employer-independent** presentation-layer data (display name, next-step copy, whether it counts in the denominator), and no day counts.

12 putting day counts into `states.yml` is wrong: under 15's model day counts are per-employer while `states.yml` is per-state; the dimensions do not line up.

#### A8 (P1) The request-interval constant: unified, but the place it is unified into does not exist yet

`14` says "the two documents must be merged into the same number" but does not pick one; `15` says "unify on the stricter 5 seconds and set the single point of definition in the **shared constant registry** in 00-overview.md." The problem is that **00 §8 is currently titled "points not yet converged across documents," and it contains no constant registry at all** — that registry is something `16` R-00-5 only proposes creating. 15's revision is written as "add to the existing table" when it is really "add to a table that does not exist yet," and there is an unmarked ordering dependency between the two proposals.

There is also a technical consequence nobody discusses: the 2 seconds in [04-ingestion.md](./04-ingestion.md) §7 is not a number scattered through prose — it is the per-source default in the source registry YAML (`rate: { min_interval_s: 2, concurrency: 1 }`). Once the global value becomes 5 seconds, **whether per-source can still override it, and whether it may go below 5 seconds**, must be answered in writing, or "take the stricter value" gets quietly cancelled by one YAML field.

**Recommended ruling**: 5 seconds globally; per-source may override only **toward stricter** (`max(5, min_interval_s)`), and that clamping logic lives in the throttler, not in config validation. And per 14's proposal, state explicitly: this limit binds automated requests only; manual human browsing is unconstrained.

#### A9 (P1) The score floor: effective immediately, effective after 40 decisions, or already there all along

- `12-reference-career-ops.md`: the intersection of floor ∧ quota, but **in Phase 0–1 only record `floor_pass` without eliminating on it; it takes effect only after ≥ 40 accumulated human decisions**.
- `16-plan-revisions.md` R-05-3: a three-tier order (veto → floor → quota), `score_floor` **placeholder value 35**, with no delayed-activation condition.
- `16-plan-revisions.md` R-00-2: writes "anything below `score_floor` does not enter the queue even when slots are free" straight into 00's core argument, in a tone of immediate effect.

Beyond the direct conflict over "when it takes effect," there is a fact neither document noticed: [05-scoring-triage.md](./05-scoring-triage.md) §6.2 **already has a lower guardrail, and its value happens to be 35 too** (`T_l` clamped to `[35, 60]`). Under the existing design, a posting scoring below 35 **already cannot reach the gray-band queue**. So R-05-3's "floor tier = 35" is very nearly a no-op in quota mode; the only behavior it changes is leaving slots empty when qualifying postings fall short of the quota — and `12` has already handled that separately with another proposal (spend the empty slots on capture planning).

Add a third number: `05` §6.3 makes the condition for switching to fixed mode "≥ 80 accumulated human decisions," and `12` uses 80 again as "the activation condition for a second profile." So the same "accumulated human decision count" carries three thresholds and three meanings: 40 / 80 / 80.

**Recommended ruling**: do not add a `score_floor` constant. Rewrite the behavior R-05-3 wants as "**§6.2's lower guardrail is upgraded from 'clamp `T_l`' to 'hard elimination'**" — same number, same observable anchor, one fewer constant. Keep 12's "Phase 0–1 records without eliminating" as the activation condition for that upgrade, but change the threshold to reuse §6.3's existing 80; do not introduce a fourth number.

#### A10 (P1) Schema minimalism vs eight new entities

`12`'s stance throughout is explicit restraint: "explicitly no `job_flag` table," "explicitly no `block_note` table," "ghost job detection needs no new table," on the grounds that "at a scale of 80–200 submissions it buys nothing." `16` R-03-1 adds eight entities at once, and `15` adds three more (`employer_policy`, `application_question`, the `canonical_profile` family).

This is not a question of who is right; it is that this batch has **no shared criterion** for when a table should be created. The result is that the same 03 receives revision proposals in two opposite styles, and anyone who wants to add a table later can cite whichever document suits as precedent.

**Recommended ruling**: write down one criterion and put it at the top of 03 — **a new table is justified when "the thing has a lifecycle of its own and is queried by primary key from more than one place."** Re-review with it: `employer_policy`/`target_employer` passes (an employer's lifecycle far outlasts any single application), `application_question` passes, `interview_story` fails (it is just `content_block(kind='story')`, see A11), `comp_research` fails (it is a column group on `target_employer`), `role_class` fails (an enum does not need a table).

#### A11 (P1) Where interview stories live

`12` says the 48-hour post-interview debrief produces a `content_block(kind='story')` and adds a `reflection` column on `content_block` to carry the STAR self-critique. `16` R-03-1 adds a standalone `interview_story` entity. These are two homes for the same data. Adopting both forks the honesty principle's provenance chain: a résumé bullet goes through `artifact_block_usage` back to `content_block`, an interview story takes another path, and `07` §5.3's factual-assertion check only recognizes the former.

**Recommended ruling**: adopt `content_block(kind='story')` + `reflection`. This also gives `16` R-03-4's `usable_in: [resume, profile, questionnaire, interview]` something to tag.

#### A12 (P2) `evergreen` is encoded twice

`12` adds `'evergreen_pool'` to `normalized_job.disposition`; `16` R-05-5 adds `'evergreen'` to `normalized_job.posting_kind`. Same table, same row, two columns describing the same thing, and the two can contradict each other (`disposition='ok'` + `posting_kind='evergreen'`).

**Recommended ruling**: `posting_kind` describes **what this posting is** (`job` / `talent_pool` / `evergreen`); `disposition` describes **what we decided to do with it** (`ok` / `blocked` / `flagged`). Remove the `'evergreen_pool'` value from `disposition`.

#### A13 (P2) The shape of `fields.json`

`12`: change to per-ATS profiles, with **one schema file each** for 104 / Avature / SuccessFactors.
`16` R-06-3: **a single `fields.json` plus an `ats_profile` field** (`avature` / `successfactors` / `tw_104` / `generic`).

A small contradiction, but both forms will show up inside 06 §4.2's code example. Recommend 16 (single file + field), because `fields.json` is a per-application artifact, one artifact maps to exactly one ATS, and splitting the file only adds a lookup on the assembly side.

#### A14 (P2) "Deliberately not doing" will now have four points of definition

`16` R-00-4 asks for a new "deliberately not doing" list and for `11` §14 to be merged into it so that it has "only one point of definition." But it never names the other two existing lists: the 10 red lines in [10-risk-compliance.md](./10-risk-compliance.md) §2.4, and the "explicitly listed as not done" in [04-ingestion.md](./04-ingestion.md) §2.6. And `15`'s proposed red line 12 (do not register accounts on the user's behalf) **is already there verbatim in 04 §2.6** ("automatically registering accounts, automatically accepting terms of service").

**Recommended ruling**: divide the labor three ways — red lines (10 §2.4) = things that cause real harm and should be enforced in code; deliberately not doing (new section in 00) = evaluated, declined, overturnable by future data; 04 §2.6 is demoted to "a summary pointing at 10 §2.4" and stops defining entries of its own.

---

### B. Revision proposals that conflict with the product principles

#### B1 (P0) The exception for logged-in-session automation strikes at the foundation of Principle 3

`14` §9.3 (read-only status queries after login) asks for an explicitly listed exception on rule 2 of [10-risk-compliance.md](./10-risk-compliance.md) §2.4, and honestly says "you cannot keep both sides." But it only handles rule 2 and **misses rule 1**: "access only endpoints obtainable without logging in; sources with `requires_login = 1` are always manual." Two rules in the same section block this; pardoning one leaves a literal violation of the other.

The structural risk matters more: rule 2 is currently a rule with no exceptions, so it can be checked with the binary question "was logged-in session state used." Add the five conditions "own account, human present, read-only, at most once a week, single employer," and it turns from **a checkable rule** into **a rule requiring judgement** — and the core argument of [07-review-gate.md](./07-review-gate.md) §10.3 is precisely that "friction that can be bypassed will eventually be bypassed." At least two of the five conditions ("human present," "read-only") cannot be verified in code.

**Recommendation**: do not pardon it. The actual gain from 14 §9.3 is "saving one manual browser open per week to check status," and the dedicated Chrome already makes manual checking cheap; the price is demoting Principle 3 from a binary rule to a judgement call. If it is kept anyway, it must: (a) revise rule 1 and rule 2 together; (b) carry an expiry date (re-evaluate at the end of Phase 2, say); (c) be written into the inverse of 00's "deliberately not doing" list — a "deliberate exceptions" list — so it stays visible.

#### B2 (P0) The term "red line" got diluted in this batch

Red line 11 as proposed by `12`: **the implementation site of human-in-the-loop must be an executable code constraint; any change that moves it into a prompt, CLAUDE.md or documentation counts as a red-line violation.**
The red line proposed by `16` R-10-1 (do not sit ability tests on the user's behalf) admits of itself: **its mechanism strength is the weakest grade, the kind of friction 07 §10.3 calls bypassable without noticing.**

If 12's red line 11 holds, 16's new red line does not qualify as a red line. This is the batch's only **meta-level** contradiction: two documents give incompatible definitions of "what qualifies as a red line." And `15`'s red lines 11 and 12 likewise admit "this cannot be blocked at the code layer; the only mechanism is not building that entry point."

Three documents all grab the number "11," which is also a real merge conflict (12 = the implementation site of human-in-the-loop; 15 = do not sit tests on the user's behalf; 15's number 12 = do not register accounts on the user's behalf; 16 R-10-1 = do not sit tests, duplicating 15).

**Recommended ruling**: split §2.4's red-line list into **two tables** — mechanism red lines (enforceable by code, a violation = a bug, e.g. existing lines 1, 6, 9, 10 plus 12's new proposal) and commitment red lines (not enforceable by code, a violation = lying to yourself, e.g. do not sit tests, do not fill in legal identification numbers). Merge 15's and 16's duplicate test proposals into one. State the cost explicitly: commitment red lines really are weaker, and putting them in the same table makes the mechanism red lines look soft too.

#### B3 (P1) Design docs going into the remote repo — the tension with Principle 5 has not been fully costed

`13` proposes: once the main repo's visibility is confirmed private, remove `doc/analysis-and-planning/` from `.gitignore` and let the design docs into git. Confirmed locally that the remote is `git@github.com:rojarsmith/ai-career.git`, and that the current `.gitignore` really does contain only that one line.

The problem is that 13's own threat model is internally inconsistent: it argues `content/` must move out of the repo on the grounds that "`.gitignore` is a procedural defense, and this project assumes an AI agent will run `git add -A` by itself." But the contents of `15-target-tsmc.md` — "my target is TSMC, this is my submission battle plan, this is how I intend to work around the résumé being visible company-wide" — are no less sensitive than parts of `content/profile.yaml`, and they are headed into **the same repo that has a remote**. Private solves "strangers can see it"; it does not solve "the platform can see it" or "a stolen account sees all of it," and those last two are exactly what Principle 5 (local-first) exists to prevent.

**Recommendation**: two steps. `00`–`14` and `16` go into git (they are system design, cheap to leak, and the AI agent genuinely needs to read them); battle plans that **name an employer**, like `15-target-tsmc.md`, stay in `vault/`, with only an unnamed `15-target-playbook-template.md` kept in the repo. This preserves 13's core argument ("the AI agent is the primary reader; not version-controlling the definition of its behavior is self-contradictory") without betting on how strong private is.

#### B4 (P2) A machine one-way overwriting a file that contains human annotations

`12` proposes that `evaluations/` be "a machine-generated rendering of the scores, **overwritten one-way except for the human annotation block**." That design puts human judgement and machine output in the same file, separated by a single block marker, and then has the machine periodically overwrite the file. Any parse error, any accidentally deleted marker, any re-run silently eats the human's annotations — and those annotations are `09`'s only learning material at small sample sizes (`99-gaps.md` B2).

**Recommendation**: human annotations do not go into a file the machine overwrites. Annotations go into the DB or `journal/`, and `evaluations/` is purely regenerable rendering output (and therefore safe to delete wholesale, see C3).

---

### C. Internal inconsistencies in the three-zone layout and data governance

#### C1 (P0) Which zone `evaluations/` and `pipeline.md` belong to — 12 and 13 give incompatible answers

`12` asks that `evaluations/` and `pipeline.md` (active postings, capped at 50 rows) be added to the project structure in [11-tech-stack-roadmap.md](./11-tech-stack-roadmap.md) §16 (= under the repo tree). `13`'s three-zone governance moves private data out of the repo and rules that the derived zone `run/` must satisfy "**deleting the whole thing must be safe**."

The content of `pipeline.md` is "which postings at which companies I am applying to, and their current status" — one of the most sensitive pieces of data in this project, fresher than `content/profile.yaml` and more usable for inferring intent. Putting it under the repo tree directly violates 13's own zoning principle and B3's reasoning. Same for `evaluations/` (company names plus my scores and snark about each posting).

**Recommended ruling**: both go to the private zone, under `vault/` or the data root. 12's goal (giving the AI agent a human-readable pipeline overview) is met by the read-only output of `ai-career status` (which is precisely `16` R-02-4's notifier / status CLI).

#### C2 (P0) Half the inputs to `ai-career rebuild` land in the "safe to delete wholesale" zone

`12` requires the Phase 0 DoD to include "rebuild an equivalent DB from `content/` + `evaluations/` + `raw/`," and it must run to completion without an agent. `16` R-11-2 likewise declares "the DB can be deleted and rebuilt wholesale." But under `13`'s zoning, if `evaluations/` and `raw/` fall in the derived zone they carry the promise "deleting the whole thing must be safe" — a directory that is both "a required input to the rebuild" and "deletable at any time" cannot hold both properties.

**Recommended ruling**: distinguish explicitly between **regenerable** (re-fetchable from outside, e.g. raw JD HTML) and **non-regenerable** (human decisions, the JD snapshot as it was at the time, the bytes that were sent). Only the former may live in the derived zone. The JD snapshots in `raw/` are the latter (postings get taken down) and must go to the backed-up private zone — which is also exactly where `14` §9.2's evidence requirement lands.

#### C3 (P1) Where `data/` lives: `%LOCALAPPDATA%` or "another repo on the same machine with no remote"

`13`: `data/` → `%LOCALAPPDATA%\ai-career\` (pointed at by `AI_CAREER_DATA_DIR`); `content/` → `vault/content/`, in a separate local git repo with no remote.
`16` R-11-3 recommends option A: **move `content/` and `data/` out of this repo into another repo on the same machine with no remote**.

Putting `data/` into a git repo is an implementation mistake: it holds a SQLite file (every commit stores the whole binary), WAL/SHM, and artifact blobs. 13's scheme is right.

**Recommended ruling**: adopt 13. And rewrite R-11-3's option A as "`content/` goes into a local repo with no remote; `data/` goes into `%LOCALAPPDATA%`, unversioned, backed up to the encrypted external drive per §12."

#### C4 (P1) The backup and restore drill does not cover the three zones

`11` §12 has a backup and restore drill, and `13` adds the row "the dedicated Chrome profile is not backed up" (correct), but no new document states **the backup strategy and restore order for each of the three zones**. If the drill restores only `data/` while `vault/content/` is another repo and `%LOCALAPPDATA%` is a third location, then passing the drill does not mean you can actually recover.

---

## Places handled too shallowly

The user raised four things explicitly this time. Below is how deeply each was actually handled, and what is missing.

### 1. Borrowing from career-ops — the form is borrowed in detail, the most fundamental difference gets one sentence

`12` dissects career-ops in real detail (the A–H framework, Block G authenticity screening, states.yml, and the Agent Skill Standard each get their trade-offs spelled out); that part is not shallow. What is shallow is this:

`16` R-11-2 records that "career-ops outsources human-in-the-loop to 'the system has no ability to send,' while this system keeps that ability and therefore has to carry the `approved_review_id` constraint itself" — the most valuable sentence in this batch, but it is written as a footnote and nobody chases its implication.

**The implication is**: [08-delivery-tracking.md](./08-delivery-tracking.md) §8.1 has already rejected Playwright form filling; and this batch's first target employer (TSMC) **cannot be applied to by direct email**, only through the C4 Apply Pack (the human pastes it in the browser). So in Phase 1 **the system's ability to send is zero** — the entire `bundle_hash` + nonce + HMAC apparatus of [02-architecture.md](./02-architecture.md) §6 has no path that executes in Phase 1.

`12` has even written down the trigger condition ("if the delivery layer is cut, agent-native flips into the better choice"), yet never checks **whether that condition already holds on the first vertical**. This needs a section of honest discussion: is it "build a delivery layer in Phase 1 that nothing uses, because Phase 2's direct email submission will use it," or "do not build a delivery layer in Phase 1; the approval gate exists in the form of the C4 Apply Pack for now." The difference in Phase 1 effort is on the order of weeks.

Two other spots are shallow:

- **A1 (the post-submission stage) is nominally handled and actually still empty**. `12` says a new section in 08 will cover Block D + Block F; `16` R-03-1 lists `interview_story` / `comp_research` as "define the schema, do not create the tables." So this gap, marked P0 by `99-gaps.md`, still has nothing executable in it once the batch ends.
- **career-ops's reasoning for "do not submit below 4.0/5"** (the job seeker's time and the recruiter's time are equally finite) never reaches `05`'s floor discussion. That is exactly what A9 needs, and currently the only non-arbitrary argument available.

### 2. Playwright + dedicated Chrome — the browser governance is written, how the two connect is not

Handled well: the profile path, no backup, retention period, monthly logged-in session state check, quarterly manual update, retention of traces/screenshots and `.gitignore`, an unpacked extension replacing the bookmarklet.

What is not handled is all of the "how do these two become one thing" kind:

- **Playwright uses its own bundled Chromium by default and will not use `C:\my\build\toolchain\GoogleChromePortable64-Job\App\Chrome-bin\chrome.exe` (version 153.0.8010.37 confirmed).** Using the dedicated Chrome requires specifying `executablePath` + `userDataDir`, and the PortableApps launcher `GoogleChromePortable.exe` performs a profile redirect — pointing straight at `chrome.exe` bypasses that redirect and the profile lands somewhere unexpected. No document writes down how to wire this, and none marks it **needs verification**.
- **The version-drift risk goes unnamed**: Playwright's CDP support is tied to its bundled Chromium version; a manually updated Chrome that may be several versions behind will drift against an auto-updating Playwright dependency. `14` proposes quarterly manual updates, but that is a security-update rationale, not a compatibility one.
- **`Data\profile` does not exist yet (brand new, never run)**, which means there is **no logged-in session state at all** right now. The premise of the entire "dedicated Chrome holds job-site logged-in session state" argument has not been established, and the SOP for establishing it (which sites to log into, how MFA is handled, where the passwords come from, who is responsible for never writing a password into any file) is absent from the six items of the Phase 0 DoD.
- **Chrome's cookie encryption on Windows is bound to DPAPI / the user account.** That turns 13's "do not back up the profile" from a choice into a factual constraint (backing it up would not restore anyway), and is worth rewriting as a statement of fact rather than policy.
- **An unpacked extension is a new code asset**, with its own permission declarations, update path and review responsibility; `14` treats it as a simple upgrade from a bookmarklet, but it needs a short section on what it may and may not touch — especially since it lives permanently inside a browser holding every job-site logged-in session.

### 3. TSMC — the facts are solid, but "what the first vertical actually costs in money and time, and where it gets stuck" is skipped

The fact-checking itself is solid (774 items, sitemap, robots.txt, pagination locked at 10, the application flow, the résumé being visible company-wide, the jobId=562 talent pool). What is shallow is the stretch between facts and execution:

- **There is no number at all for the cold-start cost**. Day one there are 774 `JobDetail` URLs. At the 5-second interval ruled in A8, one full pass takes about **65 minutes**; multiply that by the token cost of having an LLM parse 774 JDs. And `15` itself lays down a rule that "weak signals at the index layer (URL slug) may only be used to exclude from fetching, never to positively select" — which is precisely why you **cannot** fetch just 30 of them. `11` has a budget-cap mechanism, but nobody has put these two things together and done the arithmetic. This is what you hit on day one of Phase 1.
- **One employer has three indexes**: `careers.tsmc.com` (Avature), `ro.careers.tsmc.com` (SuccessFactors), and the separate R&D postings page on `research.tsmc.com`. `15`'s `index_authority` (a single authoritative index) and its "index completeness reconciliation" (774 matching up) hold only for the `zh_TW` sub-sitemap. `16` R-04-4 lists "the same employer duplicated across ATS instances" as **P2** — but for the first and only vertical it is P0.
- **The ToS has not been read.** `15` and `16` both lay down the rule that a source must not be enabled while `tos_checked_at` is null. What has been verified so far is robots.txt, not the terms of service. By this batch's own rules, **the TSMC source must not be enabled right now**, and Phase 1 is blocked by its own gate at step one. This should be written as a named prerequisite action with an owner, not scattered across rules in two documents.
- **The English test will trip the new red line in week one.** Step 2 of the application flow explicitly includes "an English test or proof of proficiency." `16` R-10-1 proposes the `assessment_windows` mechanism but never defines who triggers it, how wide the scope is (disable the whole CLI? only the LLM?), for how long, or how it is lifted. A mechanism the very first target employer will exercise should have more than a name.
- **The practical account-registration flow is unwritten.** Avature has `Login` / `ApplicationForm`; `15` proposes the red line "do not register accounts or fill in legal identification numbers on the user's behalf" (and 04 §2.6 already lists it as not done). So the human has to register personally — and that step must have an explicit place in the battle plan, marked "the machine does not participate in this step," or the red line is just a sentence in a document.
- **Under Mode P there is almost nothing for `05` to do, yet the Phase 1 DoD still demands end-to-end scoring.** `16` R-11-1 requires "sitemap polling → parsing → role_class routing → scoring → CLI review → one manual Mode P registration completed." But under Mode P the scoring output does not affect the artifact (the only artifact is one profile). Scoring's real use on the TSMC vertical is "deciding which job codes to apply to," which is a far smaller problem. The DoD reads like it validates the whole pipeline; what it actually validates is less than it looks.
- **"Actually submit 10" has no clear meaning under Mode P**: is it 1 profile plus 10 job applications? Or 10 profile updates (which would be meaningless)? `16` R-11-1 keeps this original DoD line without redefining it.

### 4. The three-zone layout — the zoning is established, but not every existing path has been placed into it

`13`'s core decisions (`data/` out of the repo, `content/` into a local repo with no remote, completing `.gitignore`, adding the Chrome profile to the retention schedule, the three-stage C4 closeout) are all solid. What is missing is the follow-through:

- **There is no complete "existing path → owning zone" mapping table**. The tree in `11` §16 contains at least `data/artifacts/{application_id}/{version}/` (the bytes that were sent, containing personal data), `data/logs/*.jsonl`, `tests/cassettes/` (recorded LLM replay — **very likely containing real JDs and résumé fragments**), and `tests/golden/` (the JD parsing regression set, same risk). `tests/` sits in the repo and gets committed, and 13 mentions only an allowlist `.gitignore` for `tests/fixtures/`. Cassettes and the golden set are this project's most textbook "the test data is real personal data" trap, and nobody names them.
- **Whether BitLocker is enabled is unconfirmed**. `13` honestly writes that "the only real destruction guarantee is destroying the BitLocker key or overwriting the whole disk," but device encryption on Windows 11 Pro N is not necessarily on. The premise of that entire destruction argument needs one actual check, and it belongs in the Phase 0 security prerequisites.
- **`journal/` is designated by 13 as the source of per-item detail, but it is never defined** (format, location, who writes it, retention period, whether it is backed up). `09`'s reporting rules depend on it directly.
- **The interaction between the three zones and the backup/restore drill is unwritten** (see C4).

---

## Recommended next steps

Execute in order. The first four are the "must have an answer before touching any code" kind.

1. **Hold one ruling session and settle all seven P0 hard contradictions A1–A7 in one pass**, with exactly one conclusion per item, written into the single point of definition in the corresponding document. The output is an addendum to `99-gaps.md`'s contradiction section (A3's PDF mainline, A5's state naming and A8's request interval are all still unrecorded in `99-gaps.md`).

2. **Establish the "single point of definition" rules first, then fill in content**, or A7 (four homes) will repeat itself in another form:
   - Constants → the shared constant registry newly added to `00-overview.md` (create the table first, so 15's revision has somewhere to go)
   - States → `03-data-model.md` §4.2, with `08` as the projection
   - Red lines → `10-risk-compliance.md` §2.4, split into mechanism and commitment tables
   - Deliberately not doing → a new section in `00-overview.md`, with `11` §14 and `04` §2.6 changed to point at it
   - Employers → a single entity `target_employer`, abolishing the two aliases `employer_policy` and watchlist

3. **Complete TSMC's two prerequisites, or Phase 1 stalls at its own gate**: (a) actually read and record the terms of service for `careers.tsmc.com` and fill in `tos_checked_at`; (b) compute the cold-start cost of 774 JDs (request time + LLM tokens) against `11`'s budget cap. If the cost is unacceptable, `15`'s rule that "weak index-layer signals may not be used to positively select" has to be redesigned, not quietly violated at run time.

4. **Rule on "does Phase 1 build a delivery layer at all."** The first vertical has no direct email channel, so `02` §6's entire approval apparatus never executes in Phase 1. That conclusion may be the right one (build it now for Phase 2), but it has to be chosen, not overlooked. `12` has already written down the condition for judging this; all that is missing is someone applying it.

5. **Fill in the join between the dedicated Chrome and Playwright**: the actual form of `executablePath` / `userDataDir` (including the effect of the PortableApps launcher's redirect), how version drift is checked, and the SOP for creating the profile the first time (which sites to log into, how to keep passwords off disk). Mark all of it **needs verification**, and actually run it once in Phase 0.

6. **Add a complete "existing path → owning zone" mapping table** to `13-repo-layout.md`, covering `tests/cassettes/`, `tests/golden/`, `data/artifacts/`, `journal/`, `evaluations/` and `pipeline.md`. Confirm the BitLocker status at the same time.

7. **Turn A1 (the post-submission stage) from "add a section" into something executable**, or honestly move it into the "deliberately not doing" list with the reason written down. Right now it is in the worst possible state: marked P0, assigned an owning document, and with no revision proposal that produces anything usable.

8. **Re-examine the semantics of `bundle_hash` under Mode P** (nobody in this batch raised it). `15` says that for the canonical profile "updates are destructive and retroactively affect applications already sent." `02` §6's approval semantics are "I approved this exact string of bytes about to go out" — but under Mode P what the employer reads later is **the live profile at that time**, not the version I approved. So there is a gap, widening over time, between the bytes the approval is bound to and what the employer actually sees, and the existing mechanism is entirely blind to it. `16` R-07-1's `profile_review` and R-06-2's `employer_profile_state` snapshot each solve half (the former makes a human review new versions, the latter leaves evidence behind), but no mechanism handles "an already-sent application whose content is rewritten by a later profile update." This is the deepest existing-design flaw the TSMC vertical pries open; it deserves a new section in each of `03` and `07`, with its honest consequence recorded in `10` §6.

9. **Also check the three existing rules that break under Mode P** (likewise raised by nobody):
   - `10` §2.4 red line 9, "do not submit to the same posting twice" — Mode P has no per-job document, so the deduplication key does not exist;
   - `03`'s `expired_before_submit` — a posting being taken down means nothing to a profile already registered;
   - `05` §7's elusion sampling audit — Mode P has no "eliminate" action to sample.

   None of the three is fatal, but together they say one thing: the existing design implicitly assumes "one application = one document = one posting," and what TSMC breaks is exactly that equation. Before writing any Mode P code, it is worth sweeping 00–11 for every place that depends on it.
