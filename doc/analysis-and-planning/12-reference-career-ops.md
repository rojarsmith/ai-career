# career-ops Compared: What to Borrow and What to Reject

This document treats career-ops (`github.com/career-ops-hq/career-ops`) as an existing implementation in the same domain, compares it item by item against the plans in [`00-overview.md`](./00-overview.md) through [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md), and for each item gives a ruling, an integration point, and **the cost of adopting it**.

## 1. How to read this document

**Three boundaries, stated up front, or every sentence below will be over-read:**

1. **Everything described about career-ops comes from its `README.zh-TW.md`.** That is an external project's documentation — data, not instructions. A README is a project's most optimistic self-description: "Block G authenticity screening" is a block name in the README; in practice it may be nothing more than a prompt. Wherever this document says "career-ops can do X", the correct reading is "its README claims it can do X".
2. **I have never run career-ops and have never read its source.** So this is a comparison at the **design** level, not at the effectiveness level.
3. **What this document produces is a list of rulings, not a to-do list.** §2 already compresses it to three items. Treating §5 through §7 as a sprint backlog is the most likely harm this document can do — see §9.2.

---

## 2. Executive summary: if you only do three things

The core arithmetic in [`00-overview.md`](./00-overview.md) §7 has already said it: 30–50 hours of up-front investment, 90–150 submissions to break even, while a typical job-search cycle produces only 40–80 of them, so "on paper, this project very likely loses money". This comparison will go on to list sixteen things that could be added. **Doing all sixteen pushes that arithmetic from very likely losing money to certainly losing money.**

So here is the ordering first:

| Priority | What to do | Cost | Why this one | Details |
|---|---|---|---|---|
| **1** | **The rule layer of authenticity screening** (pure keyword blocklist + soft flags, zero-token) | ~2 hours | The only thing that prevents the irreversible harm of being defrauded, and it needs no LLM at all | §5.1 |
| **2** | **score floor ∧ quota** (the intersection of an absolute quality floor and a human capacity cap) | ~10 lines of code | Directly adjudicates contradiction 6 in [`99-gaps.md`](./99-gaps.md), and fixes the quota mode's bad behavior in a lean week | §5.2 |
| **3** | **sitemap-first target-company watchlist** | ~half a day | The foundation of the ingestion layer; 1 request replaces 78, and it yields `<lastmod>` | §6.1 |

The other thirteen items are all deferred for reassessment until after Phase 2. The last column of the decision table (§8) marks a suggested Phase for each item; that column matters more than the rulings themselves.

---

## 3. Positioning differences: most architectural divergence is a shadow of scope divergence

| Dimension | career-ops | ai-career (00–11) |
|---|---|---|
| Pipeline endpoint | **Evaluation and recommendation**. The README states outright that the tool "never submits an application on your behalf" | **Delivery**. [`08-delivery-tracking.md`](./08-delivery-tracking.md) has direct SMTP submission, Apply Pack, and optional semi-automated form filling |
| Strongest mechanism therefore required | One line of design principle | An architectural chokepoint (the `bundle_hash` + nonce + import boundary in [`02-architecture.md`](./02-architecture.md) §6) |
| User interface | Claude Code conversation + Go TUI dashboard | Typer + Rich in Phase 1, FastAPI + HTMX from Phase 2 on ([`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §9) |
| Data layer | Markdown tables / YAML / TSV | SQLite (WAL) + content-addressed files + version-controlled `content/` |
| Runtime | Node.js + Claude Code (or a compatible CLI) | Python 3.12 + uv |
| Target market | US/EU remote (Ashby / Greenhouse / Lever / Wellfound / Workable / RemoteFront) | Taiwan-first ([`06-content-assembly.md`](./06-content-assembly.md) §4.2 is already designed for on-site structured résumés) |
| Scale assumption | No numbers found (**Speculation — needs verification**: inferred from the "evaluate one URL at a time" interface to be tens to hundreds) | `job_posting` 2,000–8,000/year, `normalized_job` 600–1,500, `application` 80–200 ([`03-data-model.md`](./03-data-model.md) §0) |
| Honesty mechanism | Prompt layer ("the AI evaluates, you decide") | Schema layer (`attested_at IS NOT NULL` is a WHERE condition in the assembly query; a non-empty `claim_delta` blocks `assembled → pending_review`) |

**The first row determines every other row.** career-ops has no delivery layer, so it has no dangerous capability to guard; with no dangerous capability, one principle is enough. This project can send, so every downstream decision is forced to get heavier. Every "why are they so light and we so heavy" question is answered right here.

---

## 4. (a) The most fundamental divergence: CLI-agent-native vs. writing your own program

### 4.1 The actual shape of the two architectures

```
career-ops (CLI-agent-native)
  ┌──────────────────────────────────────┐
  │  Claude Code (or compatible CLI)     │  ← execution engine
  └───────────────┬──────────────────────┘
                  │ read/write
  ┌───────────────▼──────────────────────┐
  │ CLAUDE.md / modes/*.md / templates/  │  ← the "program"
  │ data/pipeline.md  reports/*.md       │  ← the "database"
  └──────────────────────────────────────┘
  Hand-written code: batch-runner.sh + Go TUI (peripheral, off the main path)

ai-career (00–11 plan)
  ┌──────────────────────────────────────┐
  │ Typer CLI (Phase 1) → local web (P2) │
  ├──────────────────────────────────────┤
  │ ingest / parse / score / assemble /  │  ← the "program"
  │ review / deliver (Python)            │
  ├──────────────────────────────────────┤
  │ LLM Gateway (sole model exit)        │  ← the LLM is a called component
  ├──────────────────────────────────────┤
  │ SQLite + content/ + data/artifacts/  │  ← the "database"
  └──────────────────────────────────────┘
```

The difference is not whether an LLM is used — both use one heavily. The difference is **whether the LLM is the orchestrator or the orchestrated**.

### 4.2 Item-by-item comparison

| Dimension | CLI-agent-native wins | Writing your own wins |
|---|---|---|
| Solo, no team | No application code to maintain; changing behavior = editing markdown | — |
| Windows 11 | No Python toolchain needed; never hits [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §17's "altering columns with Alembic on SQLite is a pain" | — |
| Long-term maintenance | Three months later the markdown is still readable | `uv.lock` makes "it still runs" verifiable; agent behavior drifts with model versions |
| Deep AI involvement | The agent reads all of `content/` directly, and the embedding + numpy cosine retrieval in [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §7 **can be dropped entirely** | — |
| Human-in-the-loop cannot be skipped (Principle 1) | — | **Decisive advantage, see §4.3** |
| Honesty by mechanism (Principle 2) | — | **Decisive advantage, see §4.3** |
| Determinism and reproducibility | — | Stage 0 hard rules are zero-token and their results are stable; an agent executing a rule gate is neither zero-token nor stable |
| Crash consistency | — | The duplicate-submission guard in [`99-gaps.md`](./99-gaps.md) D1 needs a transactional intent log; a Markdown table cannot give you one |
| Counting and throttling | — | Taking the Nth row for quota, a 90-day cooling-off period per company, block usage counts — all of them need queries |

### 4.3 The watershed: markdown can give instructions, not mechanisms

This is the most important argument in the document.

One of the core claims in [`00-overview.md`](./00-overview.md) is "honesty by mechanism, not self-discipline", and [`02-architecture.md`](./02-architecture.md) §6 is titled "why the approval gate must be an architectural chokepoint, not a button in the UI". Under a pure agent-native architecture, neither sentence **can be implemented**:

- `modes/*.md` are **prompts**. A prompt is advisory to an agent, not binding.
- `attested_at IS NOT NULL` is a SQL filter; "`delivery/gate.py` is the only module in the whole system allowed to import `smtplib`" is an import boundary. Both are **mechanisms** — they hold even when "the model is in a bad mood today".
- A `CLAUDE.md` that says "a human must approve before sending" and a function that "raises unless the nonce is valid" are not the same kind of thing. The former holds in 99% of cases, the latter in 100%. For a submission you get exactly one shot at, **that 1% is everything**.

**career-ops is itself the evidence for this argument.** It chose "the tool never submits an application on your behalf" — not by designing a gate, but by **removing the dangerous capability entirely**. Under an agent-native architecture that is the only correct move, because you cannot constrain an agent with markdown. Its safety comes from the absence of the capability, not from the presence of a gate.

So the conclusion is not "agent-native is less safe", but:

> **Once the pipeline's endpoint is actually putting the letter in the mail, pure agent-native stops being an option.**

**The converse has to be granted too**: if this project ends up cutting the delivery layer entirely (the C4 Apply Pack in [`08-delivery-tracking.md`](./08-delivery-tracking.md) §2 already is "build the pack and let the human send it"), the whole argument above stops applying and agent-native becomes the **clearly better** choice. This is not hypothetical — Phase 0 through Phase 1 in [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) never had automatic sending to begin with. **During Phase 0–1, having Claude Code read `content/` directly and running one round by hand beats writing any code.**

### 4.4 The data layer: Markdown/YAML vs. SQLite

Pull the data layer out on its own and the conclusion is far less lopsided.

| Aspect | Markdown / YAML / TSV | SQLite |
|---|---|---|
| Agent-friendly | **Extremely high**, read and written directly, no tool layer needed | Low. The agent has to issue SQL, or you have to wrap a CLI around it |
| Diff-friendly | **Extremely high**, one changed line is one line of diff | Zero. `.db` is binary |
| Git-friendly | **Extremely high**. "How I phrased my résumé three months ago" = one `git log` | Poor, you have to go through a dump |
| Human-editable | **High**, any editor | Needs a DB tool |
| Querying | Poor. Taking the Nth row, group by, join — all of it means reading text word by word | **High** |
| Consistency constraints | None. YAML will not stop you writing a state that does not exist | **High**. CHECK, NOT NULL, foreign keys, triggers |
| Concurrent writes | **Safe** (separate files do not interfere with each other) | Single writer |
| Token cost | Grows linearly with data volume | Low (only query results are read) |

Each column has wins, and **the wins fall on different kinds of data**. That is exactly the room in which a hybrid exists.

### 4.5 One decidable dividing line

[`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §16 has already gone halfway: `content/` is version-controlled, `data/` is not, and it writes down that "the DB is only an index and execution state, and can be rebuilt". This document sharpens that line until it is decidable:

```
Test:
  After this row is deleted, can an equivalent result be recomputed from content/ + evaluations/ + the raw snapshot?

    Yes → it is an "index". Fine in the DB, but `ai-career rebuild` must be able
          to rebuild it, and Phase 0's DoD must include one rehearsal.
    No  → it is a "ledger". It must be in the DB, must be append-only,
          and it is usually the basis on which some gate decides.
```

| Data | Source of truth | Role of the DB | Rebuildable |
|---|---|---|---|
| Career facts (`canonical_text`, `metric_basis`, `evidence`) | `content/**.md` + front-matter | FTS5 + embedding index | Yes |
| Phrasing variants (`content_variant`) | `content/` | Index | Yes |
| **`attested_at` (human attestation)** | **DB** | Hard filter in the assembly layer | **No** |
| Scoring results and rationale | `evaluations/<job_id>.md` | Ranking and quota computation | Yes (re-running costs money; the `source_hash → ParsedJD` cache in [`05-scoring-triage.md`](./05-scoring-triage.md) §8.2 only saves the parsing step, deep scoring still has to be paid for again) |
| Raw JD snapshot | `job_posting.raw_payload` + `data/raw/<hash>` | Pointer | No (the source takes it down) |
| **Approval (`bundle_hash` + nonce)** | **DB** | The sole permission to send | **No** |
| **Send records (`submission`)** | **DB, append-only** | Reconciliation and deduplication | **No** |
| LLM call retention | `data/logs/*.jsonl` | Cost-statistics index | No ([`02-architecture.md`](./02-architecture.md) D4: retention is non-negotiable) |
| pipeline view | `pipeline.md` generated from the DB | Source | Yes |
| State presentation layer (name / SLA / suggested next step) | `states.yml` | — | Yes |
| **Legal state transitions** | **DB CHECK + trigger** | Invariant | — |

Two inferences are worth pulling out separately:

1. **Why `attested_at` cannot live in a file.** It is the human attestation that "I really did this", and it is the honesty principle's only point of machine leverage. In YAML, one agent patch is enough to write `attested: true`; in the DB, written only by a CLI command with an interactive confirmation, the agent cannot reach it. **The content of a fact may be handed to the agent to edit; the attestation of a fact may not.**
2. **`evaluations/<job_id>.md` is the best-value addition in this whole comparison.** It is the human- and agent-readable rendering of that row of scoring data in the DB, and it costs one SELECT plus one Jinja template.

```markdown
<!-- evaluations/<job_id>.md — generated by `ai-career export eval --job-id X`, never hand-edited -->
# [Avature 248] Physical Design Engineer — TSMC
- scoring_run: 41  rubric: v3  scored_at: 2026-09-16T02:11Z
- total: 71 / 100   band: gray   floor: pass(>=60)   priority: 0.63
- flags: [comp_opacity]        disposition: flagged
| facet | score | rationale (excerpt) | evidence (must hit the JD source text) |
|---|---:|---|---|
| must_have | 18/25 | … | "5+ years of physical design" |
...
## Manual notes
(this block is the only place hand-writing is allowed; `rebuild` preserves it)
```

**The cost, stated plainly:** this is a dual write. Scoring results live in both `evaluations/*.md` and the DB — when the two fall out of sync, which one is right? [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §17 already has "the content library and the DB fall out of sync" as a pain point, and the hybrid turns one such place into three. The only line of defense is that `ai-career rebuild` must be written and rehearsed in Phase 0 — if it cannot genuinely rebuild an equivalent DB from the files, the test above is empty words. **Rule: apart from the "Manual notes" block, `evaluations/*.md` is machine-generated and overwritten one-way, with no hand edits accepted.**

### 4.6 Three agent-native interfaces to adopt

Rejecting the whole architecture is not the same as rejecting its interface design.

| What to borrow | Concretely | Cost |
|---|---|---|
| Every intermediate artifact has a file form | scoring → `evaluations/<job_id>.md`; pipeline → `pipeline.md`; config → `config/profile.yml` | Dual write, see above |
| CLI verbs designed to be agent-drivable | see below | Every verb needs a precondition check written for it |
| One `SKILL.md` describing how to use the tool | see §5.7 | It goes stale, and when it does the agent raises no error |

```
ai-career ingest  --source tsmc-sitemap      # idempotent, emits JSON, exit 0/1/2
ai-career score   --job-id X [--rubric v3]   # idempotent; already scored returns the cache, marked as such
ai-career export  eval --job-id X            # produces evaluations/<job_id>.md
ai-career export  pipeline                   # produces pipeline.md (active only)
ai-career attest  --block-id X               # interactive; the agent must not call it (see SKILL.md)
ai-career assemble --job-id X                # precondition: that job already has a scoring_run, else exit 2
ai-career deliver --review-id X --nonce N    # precondition: valid nonce; the only path allowed to import smtplib
ai-career rebuild [--dry-run]                # rebuild the DB from content/ + evaluations/ + raw/
```

**The combined effect: Claude Code becomes the UI and the judgment engine, and the Python CLI becomes the mechanism and the ledger.** This is also part of the answer to the UI question in [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §9 — Phase 1 does not need to rush the aesthetics of a CLI interface, because the agent is the interface.

**This adoption carries a cost that must be written down: it makes Claude Code a runtime dependency.** The reproducibility and restore rehearsal in [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §12 must be able to run to completion **without an agent** (`ai-career rebuild` + typing commands by hand). Otherwise, three years from now, going back to look up one résumé will require a period-correct CLI tool just to open your own data.

---

## 5. (b) What to borrow

### 5.1 Block G: authenticity screening — adopt, rebuilt for the local market, **priority 1**

**This is something 00–11 does not have at all; it is a real gap.** The evaluation layer in 00–11 assumes "the posting is real, the company is real, only the degree of fit varies". That assumption plainly does not hold in the Taiwanese market.

Ruling: add a stage, but **its output is not a score, it is flags and a disposition**.

```yaml
# scoring/authenticity.yaml — rule layer, zero-token, runs before any LLM call
blocklist:            # a hit sets disposition=blocked: no queue, no quota, excluded from statistical denominators
  - id: fraud_upfront_payment
    match: ["報名費", "保證金", "訓練費", "需自備", "需先繳"]
  - id: fraud_id_documents
    match: ["存摺影本", "提款卡", "身分證正反面", "印章"]
  - id: fraud_offshore_highpay
    match_all: [["柬埔寨", "緬甸", "杜拜", "菲律賓"], ["高薪", "月入", "免經驗"]]

soft_flags:           # a hit attaches a flag but deducts no points (reasoning below)
  - id: agency_proxy
    signal: "the company is a staffing consultancy or headhunter, or the JD refers to the real employer only by a stand-in such as 「知名外商」 or 「上市櫃大廠」"
  - id: dispatch_undisclosed
    match: ["派遣", "駐點", "客戶端", "專案型任用"]
  - id: burnout_language
    match: ["抗壓性", "配合輪班", "使命必達", "像家人一樣"]
  - id: comp_opacity
    signal: "salary is 「面議」 and the level is senior or above, and the bonus description is more detailed than the base pay"
  - id: jd_text_reused
    signal: "simhash(jd_body) is within distance < 3 of an existing posting, but company_id differs"
```

**Why a flag and not a deduction.** The quota mode in [`05-scoring-triage.md`](./05-scoring-triage.md) §6.2 sorts by total score and takes the top N. If the suspicion is converted into a deduction, a posting that is "a great fit but looks like dispatch work" quietly drops out of the queue and **the human never knows it existed**. A flag is displayed by force: the posting enters the queue as usual with a line beside it reading "possible undisclosed dispatch employment", and the human rules on it in 5 seconds. This is the same design instinct as §6.4's "ranking inside the gray band does not use the score".

**Four structural signals for ghost jobs, all zero-token:**

```
1. days_listed       = today - first_seen_at
2. relist_count      = times the same natural key disappeared and reappeared
3. lastmod_churn     = times the sitemap <lastmod> changed within N days while content_hash did not
                       (= merely refreshing the posting date; the strongest single signal)
4. org_posting_ratio = the company's concurrently listed openings ÷ company size (size data source needs verification)
```

**No new table is needed — the first draft over-engineered this.** `job_posting` in [`03-data-model.md`](./03-data-model.md) §3.2 is already a time series: `ux_posting_identity` is `(source_id, source_job_id, content_hash)`, so any content change naturally adds a snapshot row, with `normalized_job ||--o{ job_posting`. So there are only two small things to do:

1. Add a `source_lastmod TEXT` to `job_posting` (the `<lastmod>` the sitemap gives; NULL for other sources).
2. One view:

```sql
CREATE VIEW v_posting_timeline AS
SELECT normalized_job_id,
       MIN(fetched_at)                          AS first_seen_at,
       COUNT(DISTINCT content_hash)             AS content_versions,
       COUNT(DISTINCT source_lastmod)           AS lastmod_versions,
       COUNT(DISTINCT source_lastmod)
         - COUNT(DISTINCT content_hash)         AS lastmod_churn  -- >0 means date-only refresh
FROM job_posting GROUP BY normalized_job_id;
```

Flags are the same story: start with two columns, `normalized_job.flags TEXT` (JSON array of flag id) plus `disposition TEXT CHECK (...)`, and add no `job_flag` table. At a scale of 80–200 submissions, a flag table buys you nothing.

Signal 3 is **a gift the TSMC field check hands over directly**: every URL in the `careers.tsmc.com` sitemap carries a `<lastmod>`, and robots.txt publishes the sitemap explicitly. The time series that ghost-job detection needs is legal, free, and obtainable in a single request. See [`15-target-tsmc.md`](./15-target-tsmc.md). (career-ops's architecture cannot get this field — not because Playwright cannot do it, but because **a one-URL-at-a-time evaluation interface has no time dimension at all**: you hand it a URL, it scores it once.)

**One false positive that has to be handled, and it has a name and address:** TSMC has a permanent "register for the TSMC talent pool" posting (jobId=562, Posted 2023-09-01). `days_listed` alone would judge this three-year-old listing the most severe ghost job there is — but it is a perfectly legitimate and possibly useful entry point for a submission. So the disposition has to be three-way:

| Disposition | Meaning | Downstream behavior |
|---|---|---|
| `blocked` | Fraud bright line | Killed at Stage 0, zero-token, never enters any queue |
| `flagged` | Suspicious, but worth one human glance | Enters the queue normally, the flag is displayed by force, **no deduction** |
| `evergreen_pool` | A permanent entry point, not a specific opening | A separate flow: register once, consumes no quota, never enters the Application state machine |

**The cost: false positives kill good postings, and you will not know.** A `flagged` item is still seen by a human; a `blocked` one is genuinely killed. Write the rule too broadly — say, the word "派遣" appearing inside a benefits description — and you get false kills. So **`blocked` must be part of the sampling population of the elusion sampling audit in [`05-scoring-triage.md`](./05-scoring-triage.md) §7**, or this mechanism will keep failing where you cannot see it.

Integration points: a new section in [`05-scoring-triage.md`](./05-scoring-triage.md), three columns and one view in [`03-data-model.md`](./03-data-model.md), and job-search fraud listed as a risk item in [`10-risk-compliance.md`](./10-risk-compliance.md).

### 5.2 The ≥4.0/5 hard threshold — adopt, and use it to adjudicate 99-gaps contradiction 6, **priority 2**

career-ops recommends not applying when the composite score is below 4.0/5, on the grounds that "the job seeker's time and the recruiter's time are equally finite". That is the same thing as product Principle 4.

Contradiction 6 in [`99-gaps.md`](./99-gaps.md) asks: **is triage decided by capacity or by score?** The answer is that the two govern different questions, and the relation is AND:

```
  submission set = { score ≥ floor }  ∩  { top N after sorting by priority }
                   └ quality floor, absolute ┘   └ human throughput cap, relative ┘

  floor decides "may this be applied to at all"  ← from the honesty principle and Principle 4, does not float with the market
  quota decides "who gets looked at first"       ← from the human time budget, recomputed per batch
```

**This AND fixes a real bad behavior in the quota mode.** [`05-scoring-triage.md`](./05-scoring-triage.md) §6.2 admits that "in a lean week, number 12 might score only 38, which amounts to stuffing the queue with things that should not be looked at", and mitigates it by clamping `T_l` to `[35, 60]`. But clamping the lower bound merely makes the bad postings slightly less bad; it does not answer "when only 3 postings qualify, what do the remaining 9 review slots do?" Once an absolute floor is added:

> **That week you review 3 and no more. The 9 freed-up slots should not go to reviewing bad postings; they should go to capture planning ([`99-gaps.md`](./99-gaps.md) B1) or to finding referral paths (A2).**

This turns "a lean week" from noise into an action trigger.

**Do not copy 4.0/5 as the floor's value.** career-ops uses five dimensions on a 5-point scale; this project uses six facets on a 100-point scale, and the two do not convert. How to set it: during the Phase 0 manual round, label 20 items with "would I regret applying to this?" and work the initial value backwards from the regret line.

**Two costs the first draft did not write down:**

1. **The floor conflicts with the cold start.** [`05-scoring-triage.md`](./05-scoring-triage.md) §11.1 says "the first month's scores are basically guesses". Running an absolute threshold off a guessed score will systematically kill an entire class of postings without anyone noticing. **Disposition: in Phase 0–1, record only the `floor_pass` boolean and never eliminate on it; let it actually take effect once ≥ 40 human decisions have accumulated** (half the 80-decision threshold §6.3 uses to switch to fixed mode, because the floor is only a binary judgment and is easier than calibrating the whole score line).
2. **The floor is a Goodhart-able target.** [`05-scoring-triage.md`](./05-scoring-triage.md) §11.2 already warns about "optimizing for what the AI thinks is good". Once there is an explicit threshold, the temptation to tune rubric weights so that a class of postings just clears it grows. Mitigation: `floor` lives in `profile.yaml` and every change is recorded in the `event` table, with the weekly report showing "floor adjustments this week".

### 5.3 STAR + Reflection accumulated across evaluations — adopt, fills 99-gaps A1

[`99-gaps.md`](./99-gaps.md) A1 (P0) points out that nothing owns anything that happens after submission, and names it: "interview preparation is the highest-ROI stretch of the whole system, because the content library pays out a second time here at near-zero marginal cost". career-ops's Block F is exactly that stretch.

**The schema already has room reserved; no new entity is needed.** [`03-data-model.md`](./03-data-model.md) §3.6 already has `interview_round(application_id, round_no, kind, scheduled_at, outcome, notes)`, and the `content_block.kind` CHECK in §5 already includes `'story'`, `'qa_answer'` and `'intro_hook'`. 00–11 simply never said how they get produced or who fills them in. How it connects:

| When | Action | Where it lands |
|---|---|---|
| An interview invitation arrives | Generate a STAR draft from the JD + content library | The interview-prep section of `evaluations/<job_id>.md` |
| Within 48 hours after the interview | debrief: what was actually asked, how I answered, what to change next time | `interview_round.outcome/notes` + a new `content_block(kind='story')` with `origin='human'` |
| Human confirmation | This story is true and the numbers hold up | `ai-career attest` sets `attested_at` → from then on the assembly layer may use it |

**Reflection has nowhere to live.** STAR records "what happened"; Reflection records "how well I told it this time and where I got stuck" — the latter is metadata and must not pollute `canonical_text`. **The minimal change is to add a `reflection TEXT` column to `content_block`, not a `block_note` table**: one block to one reflection is enough, and many-to-many is an imagined requirement.

This also merges with [`99-gaps.md`](./99-gaps.md) B2 (win/loss debrief): **one debrief produces two things at once** — a process change (into [`09-analytics-feedback.md`](./09-analytics-feedback.md)) and a new story block (into the content library). B2 originally planned only the former.

**Incidentally, this fixes an existing contradiction:** [`03-data-model.md`](./03-data-model.md) §5 uses `qa_answer`, `story`, `intro_hook`, while [`06-content-assembly.md`](./06-content-assembly.md) §2.1 uses `faq_answer`, `letter_opening`, `project_narrative`. The block-type enum values in the two documents do not line up. 03's CHECK is authoritative; the table in 06 §2.1 needs renaming.

### 5.4 Compensation research and negotiation scripts — adopt, rewritten for the Taiwanese context

This also fills A1. career-ops Block D's rebuttal to regional discounting and its multi-offer strategy transfer to Taiwan as-is. But Taiwanese pay opacity has three structural problems the US/EU assumptions do not cover:

1. **"面議" (negotiable) is the norm, not the exception.** Pay-transparency legislation in the US and Europe is what makes data sources like Levels.fyi work; Taiwan has no counterpart.
2. **But Taiwan has one legal public data source the US and Europe do not:** the employee salary information that listed companies are required to disclose (Market Observation Post System / annual reports), including median and mean. This is more reliable than any salary-leak site because it is a statutory filing. **The exact field names, disclosure frequency and coverage need verification** (how to verify: look up one known company on the Market Observation Post System and record the actual fields and the year). Add it to the source inventory table in [`04-ingestion.md`](./04-ingestion.md) §2.
3. **The package structure is different.** In the tech industry, the year-end bonus plus profit sharing is a large share, so negotiating monthly salary is negotiating the wrong thing. The negotiation script's first question should be "how many months are guaranteed", not "what is the monthly salary". The actual annual-income structure at companies like TSMC needs separate modeling (**Speculation — needs verification**).

**An extension of the honesty principle that neither document writes down:** job seekers are routinely asked "what is your current salary". Product Principle 2 (only recombine real facts) **applies to salary expectations too** — the system must not generate an inflated current salary for you. Red line 3 in [`10-risk-compliance.md`](./10-risk-compliance.md) §2.4 already says "do not enter false data in the factual fields of an application form (…salary…)", but all of §4 "honest presentation" is about résumé content, and not one clause reaches salary statements made **in conversation** or the negotiation lines the system generates. These are two different interfaces, and a row needs to be added to the item-by-item gray-area rulings in §4.1.

The negotiation scripts themselves are stored as `content_block(kind='qa_answer')`, sharing the same accumulation mechanism as §5.3.

### 5.5 Role classification as pre-scoring routing — adopt the mechanism, but cap the count hard

career-ops classifies the role before evaluating, to decide which framework to apply. This is exactly the mechanism [`99-gaps.md`](./99-gaps.md) A3 (multiple personas) needs, and it is lighter than A3's original proposal (a new `target_profile` entity + one new section each in 05 and 06): **one classification step + one rubric weight file per profile**.

```
Stage 0   hard-rule gate (zero-token)
Stage 0.5 role classification → rubric weight file + content-library subset + quota pool   ← new
Stage 1   JD parsing
Stage 2   coarse screening (small model)
Stage 3   deep scoring (large model, using the rubric selected at Stage 0.5)
```

The classification itself is nearly free (keyword rules first; call the small model only when it falls through to `unknown`). It solves three problems at once: splitting rubric weights by direction, splitting quota into pools, and A3's worry that "scores are not comparable across personas".

**One field career-ops lacks and this project needs: classification confidence.** When a JD falls between two profiles (Platform Engineer, say), do not force the split — mark it `ambiguous`, score it once under each rubric and take the higher score.

**The cost, and it is more serious than it looks: every extra profile divides the calibration sample count by N.** Switching to fixed mode in [`05-scoring-triage.md`](./05-scoring-triage.md) §6.3 requires 80 accumulated human decisions; two profiles means 160, which at a review capacity of 12 per week is over three months. The argument running through all of [`09-analytics-feedback.md`](./09-analytics-feedback.md) is that "the sample count was never sufficient to begin with", and splitting into pools only makes it worse.

**Disposition: build the mechanism first (a classification column + a switchable rubric file), but Phase 1–2 hard-limits you to one profile.** The condition for enabling a second profile goes into a `profile.yaml` comment: the first profile has accumulated ≥ 80 human decisions.

### 5.6 states.yml and the single pipeline tracking table — adopt with modification

**`states.yml`: split it.** This project's two-layer state machine ([`03-data-model.md`](./03-data-model.md) §4) is stricter than career-ops's, which is a virtue and should not be walked back to YAML. But 03 currently puts **everything** state-related inside SQL `CHECK`s, so changing one display name means running a migration (and [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §17 has already said altering columns with Alembic on SQLite is a pain). Where to cut:

| Goes in `states.yml` (rebuildable, changes often) | Goes in a DB constraint (invariant, rarely changes) |
|---|---|
| Display name, color, sort weight | The legal set of states |
| SLA days (`D_suspect` / `D_ghost`) | Legal transition edges (`assembled → pending_review`, etc.) |
| The "suggested next step" copy for each state | Guard conditions (a non-empty `claim_delta` blocks it) |
| Whether it counts in the funnel denominator | Who may execute a transition |

This incidentally resolves [`99-gaps.md`](./99-gaps.md) contradiction 5 (the ghosted SLA value is inconsistent across documents): the value is defined in exactly one place.

**`pipeline.md`: adopt the presentation form, not its role as source of truth.** `ai-career export pipeline` produces a markdown table from the DB. Three benefits: the agent grasps the whole picture in one read, a human can look at it in any editor, and it can be committed as a snapshot. **But it holds active items only** (in flight + awaiting review), capped at about 50 rows — reasoning in §6.4.

This also solves half of [`99-gaps.md`](./99-gaps.md) D3 (how the system reaches the user): the content of the daily digest is the diff of this table.

### 5.7 SKILL.md and symlink-based multi-CLI compatibility — partial adoption

**`SKILL.md` as the single entry point: adopt.** Once you accept §4.6 (Claude Code driving the CLI), you **must** have a document that tells the agent which verbs exist, each verb's preconditions, and which operations the agent is forbidden to perform. Without it the agent guesses, and the direction it guesses wrong in is always overreach. Minimum content:

```markdown
# SKILL: ai-career
## The agent may
score / export / ingest / assemble --dry-run / read evaluations/*.md
## The agent must never (these commands refuse non-TTY invocation)
ai-career attest        # human attestation; a human must confirm at the terminal
ai-career deliver       # sending; requires a valid nonce, and the nonce is issued only by the review UI
write directly to data/aicareer.db or content/** (to change content, submit a patch for a human to read)
## Fixed order
ingest → score → export eval → (human reads) → assemble → (human reviews) → deliver
```

**Cost: `SKILL.md` will go stale, and when it does nothing raises an error.** The only line of defense is the CLI checking its own preconditions (`assemble` finds no `scoring_run` and exits 2). Which is to say, **you still have to rely on constraints in code; the agent is merely a more comfortable way to trigger them** — confirming §4.3 once again.

**The multi-CLI compatibility matrix that symlinks into `.cursor/`, `.qwen/` and `.grok/`: reject.** Three reasons: (1) a solo project does not need vendor-neutrality insurance; (2) **this is a real trap on Windows**: git defaults to `core.symlinks=false`, so after a clone a symlink turns into a plain text file containing a path string, and creating symlinks requires developer mode or administrator rights; (3) if you really want multiple CLIs, a one-line build script that copies the files is enough.

### 5.8 batch worker parallel evaluation — **ruling reversed to reject (the first draft over-engineered this)**

career-ops spawns parallel workers with `claude -p`, with a coordinator script managing concurrency. The first draft adopted it and added three constraints. **After redoing the cost/benefit arithmetic, the ruling changes to: do not do it.**

The ladder in [`05-scoring-triage.md`](./05-scoring-triage.md) §8.1 is: 100 raw postings per batch → roughly 25 through Stage 3 deep scoring + roughly 20 gray-band k=3 calls. At an estimated 20–40 seconds per call, **running serially takes about 15–30 minutes, and it is an unattended batch job**. Parallelizing saves a dozen-odd minutes at most, at the cost of three new failure modes:

1. **The budget cap gets multiplied by N.** [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §10 sets "US$2.00 per worker run". With N workers each holding that cap, the real cap becomes N × US$2.00.
2. **SQLite has a single writer.** §17 already predicted that "one day you start a second worker to speed things up" leads to duplicate task claims.
3. **The coordinator is itself new code.** For a use-it-and-throw-it-away tool, that is pure liability.

**If it does get built later** (backfilling a few hundred historical postings in Phase 4, say), three constraints cannot be skipped:

```
(1) What gets parallelized is a stage, not the whole of A–H.
    Run the 25 Stage 3 items in parallel, not "one worker per posting running A through H".
    The latter voids the ladder entirely — you would pay the Stage 3 price for 100% of postings.

(2) Workers write files only; the coordinator is the single point that writes the DB.
    coordinator ──┬─→ worker 1 ─→ evaluations/<job_a>.md
                  ├─→ worker 2 ─→ evaluations/<job_b>.md   ← files, concurrency-safe
                  └─→ worker N ─→ evaluations/<job_n>.md
                         ↓
                  coordinator collects them → one transaction back into the DB   ← DB, single writer

(3) The budget cap sits in the coordinator and is decremented centrally before dispatch.
    This is the easiest one to miss, and missing it burns money immediately.
```

Note that (2) only holds under the hybrid data layer of §4.5. **Files are natively friendly to concurrent writes and a DB is not** — this is the second independent reason for the hybrid, and it stands even if parallelization is never built.

### 5.9 Go + Bubble Tea TUI — reject, but grant that it answers a real question

[`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §9 splits the UI into two phases. career-ops offers a third answer: Go + Bubble Tea + Lipgloss. Reject, on three levels:

1. **career-ops can use a TUI because it has no review gate.** Its TUI is a dashboard — look at a list, at statuses, at counts; a terminal suits that well. The core task of this project's UI is the diff review in [`07-review-gate.md`](./07-review-gate.md) §5: read an 800-word JD, character-level diff, edit a single bullet in place. §9's own words: "**reading an 800-word JD in a terminal is torture**". Bubble Tea does not change that.
2. **The maintenance cost of a second language is real.** Go does cross-compile cleanly on Windows (a substantive advantage over Python packaging, to be granted honestly). But the cost is two dependency managers, two test suites, and having to recall the idioms of two languages at once three months later.
3. **There is a cheaper answer for the dashboard part:** §5.6's `pipeline.md` + the agent reading it directly, zero lines of UI code.

**Conclusion: keep §9's phasing, hand the dashboard to `pipeline.md`, and keep the review gate on FastAPI + HTMX. If a TUI is genuinely wanted later, use Textual (Python) for 80% of the effect at the cost of zero new languages.**

---

## 6. (c) What to reject or modify

### 6.1 Platform Scanner's 45-company default — reject, replace with a sitemap-first watchlist, **priority 3**

career-ops ships 45+ companies and 19 search queries by default, covering Ashby / Greenhouse / Lever / Wellfound / Workable / RemoteFront. **Not one of those six platforms serves the Taiwanese domestic market**, and the field check shows TSMC using both **Avature** (`careers.tsmc.com`, the main site, which covers Taiwan, 774 openings) and **SAP SuccessFactors RMK** (`ro.careers.tsmc.com`, overseas sites) — neither of which is on that list. ([`04-ingestion.md`](./04-ingestion.md) §2.2 already rated SuccessFactors low-feasibility and off by default; this check supports that judgment.)

**Replacement: a sitemap-first target-company watchlist.**

| Approach | Requests | Gets lastmod | Completeness | Degree of fighting the platform |
|---|---:|---|---|---|
| career-ops style: scrape the search pages | 78 (TSMC measured: `jobRecordsPerPage=100` returns the same result as `=10`; the page size is locked server-side at 10, so 774 ÷ 10 → 78 requests) | No | You have to paginate and reassemble it yourself | Medium |
| **sitemap** | **1** | **Yes (every URL has one)** | **Authoritative: exactly 774 of the 815 URLs in the zh_TW sitemap are `/JobDetail/`, matching the 774 shown by the search page exactly** | **Low** |

`careers.tsmc.com/robots.txt` explicitly says `Allow: /careers` and provides `Sitemap: https://careers.tsmc.com/careers/sitemap_index.xml`. That satisfies clauses 3 and 7 of [`10-risk-compliance.md`](./10-risk-compliance.md) §2.4 — **the platform volunteers where the complete list is, and it is a public document, not an internal endpoint dug out of DevTools**.

**But robots.txt is not the ToS, and the first draft missed that.** robots.txt is a path directive for crawlers; a site's terms of use may separately carry a "no automated access" clause, and neither substitutes for the other. **The actual wording of that site's terms of use needs verification** (how to verify: read the full terms of use / privacy policy in the footers of `tsmc.com` and `careers.tsmc.com`, and copy the key points into `source.tos_note`). Until that is confirmed, sitemap fetching must still obey all seven clauses of §2.4: an identifiable User-Agent carrying a contact address, ≥ 5 seconds between requests to a single domain, `If-Modified-Since`, and honoring `429`. **Once a day is enough** — the entire value of a sitemap is that you do not need high frequency.

The site's search interface is explicitly rejected at the same time: the fields of POST `/{locale}/careers/SearchJobs` are Avature-internal numeric facet ids (4177, 1277, 4178, 558, 147, 542); an interface like that can change at any moment, and it sits closer to the gray area of "only findable in DevTools".

This also turns [`99-gaps.md`](./99-gaps.md) B1 (capture planning) from a concept into a column: the executable path for "list 30 companies you want to work at, then actively watch their job boards" is "register one sitemap / RSS / board endpoint per company and diff it once a day".

Integration point, concrete down to the schema:

```sql
-- 03-data-model.md §3.2
ALTER TABLE source ADD COLUMN sitemap_url TEXT;
ALTER TABLE source ADD COLUMN lastmod_supported INTEGER NOT NULL DEFAULT 0;
ALTER TABLE job_posting ADD COLUMN source_lastmod TEXT;
-- source.kind's CHECK needs 'sitemap' added (currently only ats_api/rss/email/recruiter/manual)
```

**Incidentally, this corrects open question 2 in [`00-overview.md`](./00-overview.md) §6.** That item's verification method reads "issue an actual GET against a known board token". It should become **check robots.txt and the sitemap first, then talk about API endpoints** — faster, more complete data, less fighting the platform, and the TSMC case has already verified it.

### 6.2 The PDF résumé as primary output — demote it to an attachment

career-ops's core output is an ATS-optimized PDF. On US/EU job boards that is right: you upload a PDF and the ATS parses it.

But the first step of TSMC's application process is "fill in your résumé", and the original text says:

> "Your résumé will be made available to all TSMC managers. You may therefore be invited into the selection process for positions other than the one you applied for"

That tells you **what gets read is the structured résumé inside the ATS, not the attachment**. [`06-content-assembly.md`](./06-content-assembly.md) §4.2 already got this right. Ruling:

1. **The primary output is `fields.json`, and the PDF is demoted to an attachment.**
2. **`fields.json` must be a per-ATS profile, not a single format.** Today it is designed around 104 (`self_intro` / `work_experience[]` / `skills[]` / `faq`). Avature's and SuccessFactors' fields are entirely different: English, a Job Category facet (21 categories), Employment Type (Regular / Temporary / Intern / Apprenticeship), Job Type (Technician / Associate Engineer / Engineer / Manager / Others). One format cannot cover them. The actual fields and character limits **need verification** (see §11 item 6).
3. **The Apply Pack in [`08-delivery-tracking.md`](./08-delivery-tracking.md) §2.4 already has `form-fields.md`**, which is the correct demotion path; what remains is to make it consume a per-ATS profile.

**The first draft made a faulty inference here that has to be corrected.** It said "if Playwright is going to be installed anyway, use it to render the PDF and drop the LibreOffice dependency entirely". That is wrong: the **main reason** [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §8 picks docxtpl **is to produce `.docx`** (ATS parsing success rates are said to be higher for `.docx` than for PDF), and LibreOffice merely converts that same `.docx` to PDF on the way past. Playwright cannot produce `.docx`. Rendering the PDF with it means **maintaining a Word template and an HTML template simultaneously**, tuning two layouts every time — that is more work, not less.

The correct statement is: **only under the premise that you have confirmed `.docx` brings no substantive benefit and decided to ship PDF only** could Playwright replace the whole docxtpl + LibreOffice chain. That is an independent verification question (§11 item 7), not an incidental bonus of Playwright.

### 6.3 Running all eight A–H blocks on every item — reject, bind them to funnel stages instead

career-ops runs six main blocks + two optional ones on every posting, including compensation research (D) and interview preparation (F). Against the ladder in [`05-scoring-triage.md`](./05-scoring-triage.md) §8.1 — Stage 0 kills about 40%, only about 25 items reach large-model deep scoring — running everything means **doing work that only about 5% will ever use, up front, for 100% of postings**.

But there is a twist here: **re-sequencing A–H into their correct positions in the funnel solves the cost problem and [`99-gaps.md`](./99-gaps.md) A1 at the same time.** A1 says "nothing owns anything that happens after submission", and D and F are precisely that stretch — they were merely run at the wrong moment.

| Block | career-ops timing | **This project's timing** | Corresponding stage |
|---|---|---|---|
| A summary / role classification | Every item | Every item (that clears Stage 0) | Stage 0.5 + Stage 1, small model |
| **G authenticity screening** | Every item | **Every item, and mostly zero-token rules** | Stage 0 / 0.5 |
| B résumé-to-JD alignment | Every item | Those clearing the floor (about 25%) | Stage 3, large model |
| C credentials strategy | Every item | Those clearing the floor | Stage 3 |
| E personalization factors | Every item | **After deciding to apply** (at assembly time) | [`06-content-assembly.md`](./06-content-assembly.md) |
| **D compensation research** | Every item | **After deciding to apply, or when an interview invitation arrives** | Post-submission stage (fills A1) |
| **F interview preparation STAR** | Every item | **After an interview invitation arrives** | Post-submission stage (fills A1) |
| H custom evaluation | Optional | Keep the mechanism, off by default | — |

**One overlap that has to be stated: A–H's B and C are two ways of slicing the same thing as the six-facet rubric in [`05-scoring-triage.md`](./05-scoring-triage.md) §4.3, and they must not be stacked.** The purpose of this table is "move D and F to the right place", not "run eight blocks on top of the existing rubric". Copying and stacking doubles the scoring cost and produces two sets of conclusions that fight each other.

### 6.4 Markdown tables as the pipeline data layer — collapses at this project's scale

career-ops uses `data/pipeline.md` (or .tsv) as a central tracking table. That works at its scale; it does not at this project's. The scale in [`03-data-model.md`](./03-data-model.md) §0 is `normalized_job` 600–1,500/year (`job_posting` raw snapshots 2,000–8,000). Two breakdown points:

1. **Humans cannot read it.** A Markdown table past roughly 200 rows loses its readability, and readability is the sole reason to pick it.
2. **The agent cannot afford to read it.** 1,000 rows × about 150 tokens per row ≈ 150k tokens, paid on every query.

This is not "career-ops designed it wrong"; it is that **the two pipelines refer to different things**: career-ops's pipeline is "postings already evaluated", this project's is "every posting ingested". Ruling in §5.6: `pipeline.md` holds active items only. At `application` 80–200/year with an average of 4–8 weeks in flight, roughly 20–40 are active at any moment, plus the 12 awaiting review, so **a 50-row cap is reasonable**; the full set stays in the DB and is exported separately when you want to look at it.

### 6.5 "The tool never submits an application on your behalf" — not directly portable

See §4.3. Under career-ops's architecture that principle is the only workable safety design; this project can send, and what it needs is the `bundle_hash` + nonce + import boundary from [`02-architecture.md`](./02-architecture.md) §6.

**The risk is that the sentence sounds good and is easy to mistake for sufficient.** If some refactor of this project degrades human-in-the-loop into a principle written in `CLAUDE.md` (and once §4.6's agent shell is adopted, that temptation genuinely exists), that is a retreat from mechanism back to self-discipline. This deserves to go into the red-line list in [`10-risk-compliance.md`](./10-risk-compliance.md) §2.4 as clause 11: **the implementation site of human-in-the-loop must be an executable constraint in code; any change that moves it into a prompt or a document counts as a red-line violation.**

### 6.6 The 45-company / 19-query defaults themselves — should be left empty

Beyond coverage (§6.1) there is something more fundamental: **that is somebody else's job-search strategy.** Copying a default list means letting the tool's defaults decide your career direction. The correct approach is for this field to default to empty and to force the user to fill it in on first run ([`99-gaps.md`](./99-gaps.md) B1). The 30 minutes spent filling in that list is worth more than any time the system saves afterward — a direct application of Principle 4, and the counter to [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §15's "the tool itself becomes an excuse to avoid job hunting": **filling in the company list is job hunting; writing a scraper is not.**

---

## 7. (d) What both sides missed

This section is worth more than every section before it, because it only becomes visible through the comparison.

### 7.1 The time dimension of a job posting is entirely absent

career-ops evaluates one point at a time (give it a URL, it scores once). This project's scoring is single-point too — `first_seen_at` is used only in deduplication and the cold queue, and enters no judgment at all.

But "how long this posting has been up, how many times it was reposted, how many times lastmod was refreshed" is:

- the **strongest single signal** for ghost-job detection (§5.1)
- the **only measurement tool** for the unverified assumption in [`01-domain-mapping.md`](./01-domain-mapping.md) that "the earlier you submit the more likely you are to be seen"
- the real data source for `deadline_urgency` in the priority formula in [`05-scoring-triage.md`](./05-scoring-triage.md) §6.4 (whose comment reads "days to deadline / days listed") — days listed is currently supplied by no column whatsoever

And TSMC's sitemap hands this field over for free, while `job_posting` has been a time series all along. **Both sides missed it; this project's miss is the more regrettable, because the data is already in hand.** How to fill it: see §5.1 (one column + one view, not a new table).

### 7.2 "People" are not a first-class entity

[`99-gaps.md`](./99-gaps.md) A2 already flags that this project lacks `contact` and `contact_touch`. **career-ops's directory structure has no counterpart either** (**Speculation — needs verification**: the README's directory tree lists no contact-related files, but that is not the same as there being none).

Both sides treat job hunting as an activity aimed at postings rather than at people. And point 1 of the counter-argument in [`00-overview.md`](./00-overview.md) §7 is put bluntly: "if you have 20 former colleagues you could approach, the 30 hours spent on the system should have gone into coffee meetings". **The blind spot shared by both projects points in exactly the direction of the strongest objection.**

### 7.3 Cross-posting side effects inside a single organization

The original text of TSMC's application process: "Your résumé will be made available to all TSMC managers. You may therefore be invited into the selection process for positions other than the one you applied for". Two consequences, neither of them handled by either side:

1. **At a company like this, applying to one opening ≈ applying to the whole company.** So "three openings at the same company" does not raise your odds, it wastes three review slots. This strengthens the per-company cooldown in [`99-gaps.md`](./99-gaps.md) D2 — the original reason was "the ATS deduplicates within the organization by email"; now there is a harder one: **the platform tells you outright that the résumé is shared company-wide.**
2. **This pulls in two directions at once, and the first draft told only half of it.** On one hand, the résumé's content must hold up for "all managers", so skewing it too far toward a single JD costs points; on the other hand, one submission is seen by more people, so **the expected value of a single submission goes up**. The correct resultant of these two forces is not "lower the tier", but:

> **For an ATS of the "résumé shared across the whole company" type, lower the number of submissions and raise the quality of each one.** Go from "three openings at T1 each" to "one opening at T2 or T3", and shift the direction of customization from "fit this one JD" to "fit this organization".

This is the literal meaning of product Principle 4. Where to add it: one more criterion row (ATS type) in the tier table in [`06-content-assembly.md`](./06-content-assembly.md) §7, and a per-company cooldown in the [`08-delivery-tracking.md`](./08-delivery-tracking.md) §3.2 preflight, citing this reason.

### 7.4 Hard-rule fields specific to Taiwan

Both sides' Stage 0 hard rules use the US/EU template (visa / location / seniority). The hard conditions of a Taiwanese job search are a different set:

| Field | Why it may be a hard rule rather than a score |
|---|---|
| Military service status | The determination is binary |
| Degree-field requirement | Taiwanese JDs commonly write "電子電機相關科系" (a degree in electronics/electrical engineering or a related field); either you match or you do not |
| Language certification | Step two of TSMC's process states outright "an English test or proof of proficiency" — that is a gate, not a bonus |
| Dispatch vs. permanent employment | See the `dispatch_undisclosed` flag in §5.1 |
| Commute location (Hsinchu / Central Taiwan / Southern Taiwan Science Park) | For anyone not already living there this is a relocation decision, not a commuting decision |
| Reserved quotas (indigenous / disability) | Affects the eligibility determination |

[`99-gaps.md`](./99-gaps.md) D4 already points out "score degradation on Traditional Chinese JDs", but that is about **insufficient information density distorting the score**; this is about **the fields themselves not existing in the schema**. D4 solves only half of it.

**I have no data backing this table** (see §9.6), so its correct use is as "a candidate list pending verification", not "a list of columns to implement".

Where to add it: the Stage 0 rule list in [`05-scoring-triage.md`](./05-scoring-triage.md) §4.1 and the `ParsedJD` extraction schema in §3.2.

### 7.5 The test and questionnaire gate

Step two of TSMC's application process is "take the questionnaire and tests": fill in a role-specific application questionnaire, and take an English test or provide proof of proficiency. This gate genuinely exists, it consumes time, and **it has a deadline** (leave it unfinished and you are stuck).

**The first draft misread 08 here, and this needs correcting.** The state machine in [`08-delivery-tracking.md`](./08-delivery-tracking.md) §5.1 is **not** "`submitted` straight to `screening`" — it is actually `submitted → acknowledged → interview → offer → accepted/declined`, and it **already has an `info_requested` state** (`submitted → info_requested → submitted`, meaning "supplementary materials sent"). (Incidentally: [`99-gaps.md`](./99-gaps.md) A1 suggests extending the state machine to `screening / interviewing / offer / closed`; that suggestion is itself behind the actual content of 08 §5.1, and that sentence in A1 should be withdrawn.)

So **no new `assessment` state is needed**. Minimal changes:

1. Fold "questionnaire / test" explicitly into the meaning of `info_requested` (which today reads only "supplementary materials").
2. Add a `due_at` to `info_requested` — it is the one structural difference between it and the other states, and the one place that will knock you out.
3. Accumulate answers to common questionnaire items as `content_block(kind='qa_answer')` (why us, expected compensation, available start date), sharing the same mechanism as §5.3 and §5.4.

### 7.6 Selection-process duration never enters the scheduling decision

TSMC's "the selection process takes two to four weeks on average" is a publicly stated fact. Neither side folds "different companies' process lengths" into submission scheduling.

This is not an academic question: if you need to start a job within three months, applying to a company with a four-week average process and applying to one with a two-week process **mean entirely different things for scheduling** — the four-week one has to go first. The priority in [`05-scoring-triage.md`](./05-scoring-triage.md) §6.4 currently has only `deadline_urgency` (when the posting closes), not `process_duration` (how long the process takes to run).

**But do not add the column yet.** In Phase 1 the only data source for this is "what the company itself publishes", coverage is extremely low, and adding a mostly-NULL `company.typical_process_days` only gives the priority formula one more term that is permanently at its default. **Minimal approach: record it in a YAML comment in the watchlist for now — a human being able to see it is enough; consider putting it in the formula once measured data for ≥ 10 companies has accumulated.**

### 7.7 Data disposition after the job search ends

[`99-gaps.md`](./99-gaps.md) C4 already flags that this project lacks a retention schedule. career-ops's `data/`, `reports/` and `output/` are all gitignored, but the README mentions no destruction procedure (**Speculation — needs verification**).

Neither side answers "what happens after you find a job" — and at that moment the local disk is holding the names and email addresses of dozens of headhunters and hiring managers.

### 7.8 Where this project is already ahead of career-ops

To keep this comparison honest (rather than one-way learning), six items are recorded. **Every row of this table infers "not done" from "the README does not mention it", so the correct reading of the heading is "I found no evidence during the comparison", not "career-ops does not do it".**

| Item | This project | career-ops (per its README) |
|---|---|---|
| Honesty made mechanical | `attested_at` is a SQL filter; a non-empty `claim_delta` blocks the transition | A prompt-layer principle |
| Approval gate | `bundle_hash` + nonce + import boundary | Does not send, so has no such need |
| Prompt injection | Identified as P0 in [`99-gaps.md`](./99-gaps.md) C1 | Not found (**Speculation — needs verification**) |
| Statistical honesty | [`09-analytics-feedback.md`](./09-analytics-feedback.md) argues the sample count is insufficient and explicitly does no A/B tests and no leaderboards | Has five-dimension scoring and a 4.0 threshold; no discussion of sample size found |
| Procrastination defense | [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §15 + seven lines of defense | Not found |
| Structural enforcement of ToS | [`02-architecture.md`](./02-architecture.md) §5.6, plus §2.4's seven clauses + ten red lines in [`10-risk-compliance.md`](./10-risk-compliance.md) | Scrapes with Playwright; no corresponding discussion found |

**The third row deserves particular attention, and it is the third independent reason §4 rejects pure agent-native.** The consequences of prompt injection under an agent-native architecture are far more severe than here: an injection in this project at worst pollutes the scoring and the assembly output (and the evidence string-matching verifier in [`05-scoring-triage.md`](./05-scoring-triage.md) §3.3 is exactly the most effective defense against that), whereas an agent has filesystem write access, and an instruction buried in a JD could in principle induce the agent to edit `cv.md` or `content/`. **This row is simultaneously a warning about §4.6**: since we intend to let Claude Code be the shell, we must ensure there is isolation on the path by which the agent reads a JD (every JD wrapped in an explicitly delimited data block, and every write to `content/` going through a patch a human reads, never the agent editing files directly).

---

## 8. Adoption decision summary table

**The last column matters more than the rulings themselves.**

| # | career-ops's approach | Ruling | Integration document | Phase |
|---|---|---|---|---|
| a1 | The CLI-agent-native architecture as a whole | **Reject**, go hybrid | [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §16, [`02-architecture.md`](./02-architecture.md) | — |
| a2 | Markdown/YAML as the source of truth | **Partial adoption**: files hold the facts, the DB holds the ledgers and indexes | [`03-data-model.md`](./03-data-model.md), [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §16 | 1 |
| a3 | The agent reads files directly | **Adopt**: add `evaluations/<job_id>.md` + `ai-career rebuild` | [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §16, [`13-repo-layout.md`](./13-repo-layout.md) | 1 |
| b1 | Block G authenticity screening | **Adopt + localize** (rule layer first) | [`05-scoring-triage.md`](./05-scoring-triage.md), [`03-data-model.md`](./03-data-model.md), [`10-risk-compliance.md`](./10-risk-compliance.md) | **0** |
| b2 | The ≥4.0/5 hard threshold | **Adopt**: floor ∧ quota; in Phase 0–1 record only, never eliminate | [`05-scoring-triage.md`](./05-scoring-triage.md) §6 | **0 (record) / 2 (in effect)** |
| b3 | STAR + Reflection accumulation | **Adopt**: reuse `kind='story'` + a `content_block.reflection` column | [`08-delivery-tracking.md`](./08-delivery-tracking.md), [`03-data-model.md`](./03-data-model.md), [`09-analytics-feedback.md`](./09-analytics-feedback.md) | 3 |
| b4 | Compensation research and negotiation scripts | **Adopt + rewrite for Taiwan** | [`08-delivery-tracking.md`](./08-delivery-tracking.md), [`04-ingestion.md`](./04-ingestion.md), [`10-risk-compliance.md`](./10-risk-compliance.md) | 3 |
| b5 | Role-classification routing | **Adopt the mechanism; Phase 1–2 hard-limits it to one profile** | [`05-scoring-triage.md`](./05-scoring-triage.md) | 2 (mechanism) / 4 (second profile) |
| b6a | `states.yml` | **Adopt with modification**: move the presentation layer out, leave the constraints in the DB | [`03-data-model.md`](./03-data-model.md) §4 | 2 |
| b6b | The single pipeline tracking table | **Adopt with modification**: produced by export, active items only, capped at 50 rows | [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §16 | 2 |
| b7a | `SKILL.md` as single entry point | **Adopt** (mandatory once a3 is adopted) | [`13-repo-layout.md`](./13-repo-layout.md) | 1 |
| b7b | The symlink multi-CLI matrix | **Reject** (Windows symlinks + a solo developer needs no vendor neutrality) | — | — |
| b8 | `claude -p` parallel workers | **Reject** (saves 15 minutes, buys three failure modes) | [`05-scoring-triage.md`](./05-scoring-triage.md) §8 | 4 (optional) |
| b9 | Go + Bubble Tea TUI | **Reject** | [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §9 | — |
| c1 | Platform Scanner's 45 companies | **Reject**, swap in a sitemap-first watchlist | [`04-ingestion.md`](./04-ingestion.md), [`15-target-tsmc.md`](./15-target-tsmc.md) | **1** |
| c2 | PDF as the primary output | **Demote**; make `fields.json` a per-ATS profile | [`06-content-assembly.md`](./06-content-assembly.md) §4.2 | 2 |
| c3 | Running all of A–H on every item | **Reject**, re-sequence into funnel stages; do not stack it on the six-facet rubric | [`05-scoring-triage.md`](./05-scoring-triage.md) §8, [`08-delivery-tracking.md`](./08-delivery-tracking.md) | 3 |
| c4 | Markdown as the pipeline data layer | **Reject** (it collapses at this scale), keep it only as a view | [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §16 | 2 |
| c5 | Treating "never submits on your behalf" as sufficient | **Reject** it as a mechanism; rewrite it as red line 11 | [`10-risk-compliance.md`](./10-risk-compliance.md) §2.4 | 1 |
| c6 | Default company / query lists | **Reject**, default to empty, force the human to fill them in | [`04-ingestion.md`](./04-ingestion.md) | **0** |

---

## 9. Pain points: where this comparison will hurt

**9.1 I only read the README; I never ran it. This is the biggest one.** A README is a project's most optimistic self-description. "Block G authenticity screening" is a block name in the README; in practice it may be nothing more than a prompt, and half of "45+ companies, 19 queries" may already be dead. **Every judgment in this document of the form "career-ops does this better" rests on its own claims.** To use §5 as a basis for implementation, you should at minimum clone it and read `modes/` and `templates/states.yml` once. That costs two hours, and half this document's credibility is staked on it.

**9.2 The borrow list is itself scope creep, and this is the most likely harm this document can do.** §5 lists nine items and §7 lists seven. [`00-overview.md`](./00-overview.md) §7 says this project "on paper very likely loses money", and sixteen items make that number uglier. §2 already compresses it to three, and §8's Phase column is the second line of defense. **If your first action after reading this document is opening a to-do list with sixteen items on it, this document has failed.**

**9.3 The dual-write risk of the hybrid data layer is real.** §4.5's test is clean, but gray areas will show up: a scoring result lives in both `evaluations/*.md` and the DB — when they fall out of sync, which one is right? [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md) §17 already has "the content library and the DB fall out of sync", and the hybrid turns one such place into three. The only line of defense is `ai-career rebuild` being written and rehearsed in Phase 0 — if it cannot genuinely rebuild an equivalent DB from the files, the whole test is empty words.

**9.4 The irreproducibility of an agent-driven CLI, plus a new dependency.** §4.6 makes Claude Code the shell, but agent behavior drifts with model versions: today it runs `score` first and `assemble` second; next month the order may differ. The mitigation is hard-coding the order in `SKILL.md` and having the CLI check preconditions — which is to say, **you still have to rely on constraints in code**. And this introduces a runtime dependency that 00–11 does not have: three years from now, rereading your own data should not require one specific version of an agent.

**9.5 Block G's false positives kill good postings, and you will not know.** §5.1 mitigates the soft flags with "flag, do not deduct", but `blocked` genuinely kills. **blocked must be included in the sampling-audit population of [`05-scoring-triage.md`](./05-scoring-triage.md) §7.**

**9.6 I have no data backing the Taiwanese field list in §7.4.** Military service, degree-field requirements and reserved quotas were listed from general awareness, **not from statistics over an actual JD sample**. The right approach is to sample 50 Taiwanese domestic JDs and label them by hand, looking at how often each field appears — anything under 10% is not worth turning into a hard rule. This can be merged with the sampling for open question 3 in [`00-overview.md`](./00-overview.md) §6: label both things on the same batch.

**9.7 The legality argument for the sitemap only goes halfway.** §6.1's evidence is robots.txt, and robots.txt is not the terms of use. Clause 3 of [`10-risk-compliance.md`](./10-risk-compliance.md) §2.4 requires obeying robots.txt, but nowhere in that document does any clause say "robots.txt permits it = the ToS permits it". Until that site's terms of use have been read, the claim "the sitemap is a textbook case" should be downgraded to "the sitemap is the least platform-fighting path currently known".

**9.8 The six items where "this project is ahead" may be an illusion.** All of §7.8 infers "not done" from the README not mentioning something. **Absent from the README is not the same as absent.**

---

## 10. Related Documents

- The other half of the architectural divergence (the existing arguments for the DB and the gate): [`02-architecture.md`](./02-architecture.md) §6, [`03-data-model.md`](./03-data-model.md) §5
- Integration points for Block G and the floor: [`05-scoring-triage.md`](./05-scoring-triage.md) §6, §7, §8
- Output formats and tiers: [`06-content-assembly.md`](./06-content-assembly.md) §4.2, §7
- The post-submission stage (the substance of A1) and the current state machine: [`08-delivery-tracking.md`](./08-delivery-tracking.md) §5
- The operational definition of do not fight the platform, and the red lines: [`10-risk-compliance.md`](./10-risk-compliance.md) §2.4
- The full design of the directory tiers, `evaluations/` and `SKILL.md`: [`13-repo-layout.md`](./13-repo-layout.md)
- The trade-off between Playwright and a dedicated Chrome (including §6.2's PDF route): [`14-browser-automation.md`](./14-browser-automation.md)
- sitemap-first and the field details on Avature: [`15-target-tsmc.md`](./15-target-tsmc.md)
- The consolidated revisions derived from this document: [`16-plan-revisions.md`](./16-plan-revisions.md)

---

## Open Verification Items

| # | Item to verify | How to verify | Impact |
|---|---|---|---|
| 1 | The gap between the actual content of career-ops's `modes/` and what the README claims | Clone it and read `modes/*.md` and `templates/states.yml`, especially whether Block G and role classification are prompts or rules | The credibility of all nine items in §5 (§9.1) |
| 2 | Whether career-ops has a contact / stakeholder entity, and whether it has a data destruction procedure | Same as above; look at `templates/` and `config/profile.example.yml` | The conclusions of §7.2 and §7.7 |
| 3 | Whether the terms of use of `careers.tsmc.com` and `tsmc.com` contain a "no automated access" clause | Read the full terms of use / privacy policy in the footer and copy the key points into `source.tos_note` | Whether §6.1's sitemap route holds (§9.7) |
| 4 | The fields, frequency and coverage of the employee salary disclosure on the Market Observation Post System | Look up the actual filing page of a known listed company and record the field names and the year | Whether §5.4's compensation research holds |
| 5 | The actual appearance rate of fields such as military service / degree field / reserved quotas in Taiwanese domestic JDs | Sample 50 and label them by hand, merged with question 3 in [`00-overview.md`](./00-overview.md) §6 | Which items in §7.4 are worth turning into hard rules |
| 6 | The online résumé fields and character limits of Avature and SuccessFactors | Log in with the dedicated Chrome and open `ApplicationForm` once, recording it field by field; **look only, fill nothing in, submit nothing** | §6.2's per-ATS profile for `fields.json` |
| 7 | Whether `.docx` really parses better than PDF for an ATS | Open verification item 9 in [`11-tech-stack-roadmap.md`](./11-tech-stack-roadmap.md); find an ATS that echoes back the parsed fields and test the same résumé in both formats | Whether §6.2 can cut the whole docxtpl + LibreOffice chain |
| 8 | The actual value of the floor | Work it backwards from the "regret line" over 20 hand-labeled items in Phase 0 | So §5.2's threshold is not set by feel |
| 9 | The package structure of large employers such as TSMC (base / year-end bonus / profit-sharing ratios) | Public annual reports + statutory salary disclosure; do not trust leak sites | The correctness of §5.4's negotiation scripts |
| 10 | Whether the TSMC sitemap's `<lastmod>` really updates when JD content changes, or is just refreshed wholesale daily | Fetch the sitemap and 5 of its JDs once a day for 7 consecutive days, and check whether changes in `lastmod` correlate with changes in `content_hash` | Whether §5.1's `lastmod_churn`, the "strongest single signal", carries any signal at all |
