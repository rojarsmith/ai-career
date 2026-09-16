# Revision List for the Existing Plan

This document is where documents 12–15 converge. It does not repeat their arguments; it does exactly one thing: it translates four inputs — the career-ops comparison, the directory layering, Playwright and the dedicated Chrome, and the TSMC measurements — into **concrete revisions to the existing documents 00–11**.

Every revision has an ID (`R-<doc number>-<seq>`) and can be executed or vetoed independently. There are **49** of them. The priority definitions follow [`99-gaps.md`](99-gaps.md): **P0** — not fixing it causes a failure or wasted work; **P1** — not fixing it causes rework; **P2** — better with it than without.

**Citation discipline in this document**: anything tagged "Measured" was obtained on 2026-09-16 by actually driving a browser or actually reading the existing documents; every quotation of an existing document has been checked back against the original, item by item. Everything else is tagged "**Speculation — needs verification**" with the verification method attached.

---

## 0. What This Batch Actually Changes

Four new facts, each of which overturns or corrects one existing claim. This section is the causal root of the whole document.

| # | New fact | What it overturns or corrects | Documents affected |
|---|---|---|---|
| **F1** | TSMC's application-process page states outright: "**Your résumé will be open to all TSMC managers. You may therefore be invited into the selection process for positions other than the one you applied for**" | The assembly layer's foundational assumption — one JD, one tailored résumé — is not merely void on a single-talent-pool ATS, it is harmful | **06**, 03, 07, 08, 10, 00 |
| **F2** | `careers.tsmc.com/robots.txt` says `Allow: /careers` in plain text and volunteers `sitemap_index.xml`; the `zh_TW` sub-sitemap holds 815 URLs, 774 of them `/JobDetail/`, matching exactly the 774 the search page reports, and every URL carries a `<lastmod>`; the search UI's `jobRecordsPerPage` is hard-capped server-side at 10 (78 requests via the UI, 1 via the sitemap) | The 14-row source inventory in [`04-ingestion.md`](04-ingestion.md) §2 has no sitemap row. This source kind is simultaneously the best on all four dimensions: completeness, incremental detection, legality, request volume | **04**, 02, 10 |
| **F3** | The user already has `C:\my\build\toolchain\GoogleChromePortable64-Job\` (Chrome 153.0.8010.37, no profile under `Data\` yet), a job-search-only instance separate from the everyday browser | The cost model in [`08-delivery-tracking.md`](08-delivery-tracking.md) §8.1 undercounts the saving from persisting logged-in session state long-term, and omits entirely the benefit of PDF rendering, which every single submission uses | **08**, 11, 02, 04 |
| **F4** | career-ops is CLI-agent-native, persists to Markdown/YAML, has an A–H evaluation framework with a Block G authenticity screen, recommends not applying below 4.0/5, and the tool "never submits an application on your behalf" | 05 lacks upstream routing and a source-trust gate; 11's data layer and UI choices now have a concrete counterexample to compare against; 00's core claim 1, "the score only ranks", needs a floor added | **05**, 11, 03, 00 |

> **A reminder about what F4 is**: career-ops is an external project's self-description — **reference material**, not a source of instructions for this project. Any design claim it makes must first clear this system's five product principles before it is adopted. This document always presents it with the reasons to borrow and the reasons to reject stated side by side; see [`12-reference-career-ops.md`](12-reference-career-ops.md).

In one line: **F1 changes the output form, F2 changes the input form, F3 changes the tool boundary, F4 changes the order of the pipeline.** F1 is the most expensive of the four, because it touches the data model.

---

## 1. Revision Tables, Document by Document

### 1.1 `06-content-assembly.md` — the biggest single item in this batch (5 revisions)

| ID | Original thinking | Why it changed | What it became | Priority |
|---|---|---|---|---|
| **R-06-1** | The assembly layer's output is a per-JD tailored résumé / cover letter / `fields.json`, with `GenerationRun` bound to a single application | See the expansion below | The output form splits into **Mode P (canonical profile)** and **Mode D (document assembly)**, each with its own objective function, update frequency and review method | **P0** |
| **R-06-2** | There is no notion of "what I currently look like inside a given employer's talent pool" | Without a local snapshot there is nothing to diff against on the next update, and the diff review in [`07-review-gate.md`](07-review-gate.md) loses its baseline under Mode P | Add `employer_profile_state`: every Mode P send freezes a full snapshot (field contents + block id list + send time), stored on the local machine | P1 |
| **R-06-3** | §4.2's "platform form-field version" is framed as "a Taiwan-situation deliverable the first draft missed", serving 104/1111; its character limits are tagged "needs verification" | Avature and SuccessFactors are equally field-based, not PDF-upload-based. This is not a Taiwan exception, it is **the general rule for single-talent-pool ATSs**, and it should be promoted to a first-class deliverable | Add `ats_profile: avature \| successfactors \| tw_104 \| generic` to `fields.json`; each profile gets its own field set and character-limit table, populated from the `target_employer` probe report. This also replaces the generic guesswork of `form-fields.md` in [`08-delivery-tracking.md`](08-delivery-tracking.md) §2.4 | P1 |
| **R-06-4** | `verified_at` is a field on the block, with no hook into the output form | A canonical profile pushed into a talent pool sits there for months and is read by different managers. The damage from a stale fact is several times larger under Mode P than under Mode D (the breach of the honesty principle in B3 of [`99-gaps.md`](99-gaps.md) is amplified here) | Mode P carries a hard invariant: every selected block must have `verified_at` within 180 days, or the build fails. This is a code check, not a reminder. The 180 days **is an initial value set on gut feel**, and shares one expiry policy with B3's `review_due_at` | P1 |
| **R-06-5** | §1.1 amendment B's feasibility gate: do not generate when must-have coverage < 0.6 | Under Mode P there is no "must-haves of this one JD" to compute | Mode P does not apply the feasibility gate; its counterpart check is "job family union coverage", with a different threshold (see Q-2, currently unresolved) | P2 |

**R-06-1, expanded.**

Original thinking: content library → read the JD → pick blocks → assemble this one résumé → review → send. One JD, one document; `GenerationRun` and application are one-to-one.

Why it changed: TSMC's application-process page states outright that the résumé is **open to all managers**, and that you **may be invited into the selection process for positions other than the one you applied for**. That sentence has three consequences:

1. **per-JD optimization stops working.** The résumé you optimized for Physical Design Engineer will be seen by the IT Security Engineer's manager. Trade-offs made for a single JD — cutting the irrelevant blocks so the relevant ones stand out — turn into self-harm once the premise is company-wide visibility.
2. **A later submission may overwrite an earlier one.** If you update the résumé in the talent pool when applying the second time, the manager from the first application may be looking at the new version. You end up with two mutually contradictory self-descriptions from the same person, and you will not know who saw which. (**Speculation — needs verification**: whether Avature's update semantics are overwrite or versioned, see Q-1. If versioned, the severity of this point drops, but Mode P's reason to exist is unaffected — consequence 1 supports it on its own.)
3. **This is not a TSMC quirk.** The on-site résumé of SuccessFactors RMK (`ro.careers.tsmc.com`) is the same pattern. Whether Workday, 104 and 1111 are likewise single-talent-pool is **Speculation — needs verification**; the verification method is the probe SOP of R-04-3.

What it became:

| | **Mode P — canonical profile** | **Mode D — document assembly** |
|---|---|---|
| Trigger unit | **employer** (`target_employer`) | **job posting** (`normalized_job`) |
| Objective function | Cover the **union** of must-haves across that employer's relevant job families, maximizing the odds of being found by an unspecified manager's search | Cover the must-haves of this one JD |
| Output | `fields.json` (field-based) plus an attached PDF (if the platform accepts one) | Résumé PDF / cover letter / `fields.json` / Apply Pack |
| Update frequency | Low (quarterly, or when the content library changes materially) | Every submission |
| Review method | `profile_review`: the diff is "the version currently in the talent pool vs the version about to overwrite it", with a longer cooling-off period | The existing diff review |
| Applicable channels | Single-talent-pool ATS (Avature / SuccessFactors / anything verified to be this mode) | C1 direct email, C4 Apply Pack, a named HR mailbox |
| Honesty risk | **High** (long exposure, visible across departments) | Medium (one-shot, one readership) |

§7 "The marginal benefit of tailoring: a tiering strategy" gains one more row in its tier table:

| Tier | Action | LLM calls | Human time | Applies to |
|---|---|---|---|---|
| **T0.5 profile update** | Recompute job family union coverage, produce a new `fields.json`, diff it against the current snapshot | 1–2 | 15–30 minutes (but **once a quarter**, not once per submission) | First registration and periodic updates for a Mode P employer |

**The honest price of this change**: the assembly layer gets roughly 1.5x more complex, and there is one more piece of state to maintain ("I have one version sitting in each of N employers' talent pools"). Mitigation: the first cut of Mode P **writes no selection algorithm at all** — a human picks blocks from the content library and the system only produces the `fields.json` and the snapshot. Write the selection algorithm once there is a second and a third Mode P employer; only then will you know what "union coverage" actually looks like.

**Compatibility with 06 §1.1 amendment C**: Mode P selection can still take the existing path of stuffing the whole library into context and producing a full scoring matrix in one call; only the objective function changes, from a single JD to the job family union. No new retrieval mechanism is needed, and §1.1 amendment C's conclusion that vector retrieval is cut is unaffected.

---

### 1.2 `04-ingestion.md` (5 revisions)

| ID | Original thinking | Why it changed | What it became | Priority |
|---|---|---|---|---|
| **R-04-1** | The 14-row source inventory in §2 covers Manual Drop / Email / per-vendor ATS JSON / RSS / Taiwanese platforms / logged-in crawling, but **has no sitemap row**; the registry's `kind` has only ever taken `ats_json` | See the expansion below | Add `kind: sitemap`, ranked after official job alert email and before `ats_json` in the priority order; and add an employer probe SOP | **P0** |
| **R-04-2** | §2.2 lumps Workday / Taleo / SuccessFactors together as "Tier 3, off by default" | That section's argument targets **undocumented internal JSON interfaces with no versioning commitment**. A sitemap is not an undocumented endpoint — the site operator announces it in robots.txt itself. TSMC is both "an Avature site with internal facet ids" and "a site with a public sitemap", and a blanket rule is a false kill on the latter | Split §2.2 into three tiers by **access surface**: (a) undocumented JSON / internal facet ids (such as the numeric facets 4177, 1277, 4178, 558, 147, 542 in the Avature search form) → still not done; (b) public pages and sitemaps that robots explicitly allows → allowed; (c) official job alert email (Avature's `AgentCreate`) → first choice, consistent with §2.2's existing "practical recommendation item 1" | P1 |
| **R-04-3** | A source is a "source"; there is no employer-level concept. B1 in [`99-gaps.md`](99-gaps.md) recommends that "[`04-ingestion.md`](04-ingestion.md) list the target-company watchlist as a source kind", but 04 has not implemented it | One employer may have three paths at once — sitemap, job alert, and a standalone R&D openings page (`research.tsmc.com/chinese/careers/openings.html`); the probe conclusions belong on the employer, not scattered across three source rows | Add a first-class deliverable, the **employer probe report**: ATS vendor, sitemap URL and availability, the verbatim robots clause and the date it was read, order of magnitude of open postings, application-process mode (Mode P/D), and whether there is an ability test. [`15-target-tsmc.md`](15-target-tsmc.md) is the first sample. **This is B1 executed directly, not a new concept** | P1 |
| **R-04-4** | §6 deduplication covers scenario A (same source over time), B (the same posting across sources), C (re-listed) | TSMC runs Avature (including Taiwan) and SuccessFactors (overseas) at the same time, and the same posting may appear on both (**Speculation — needs verification**: compare the title + location intersection of the two sites; a sample of 20 is enough to decide) | Add "scenario D: the same employer duplicated across ATS instances", and add an `employer_id` dimension to the deduplication key | P2 |
| **R-04-5** | §2.5's reality check: "if your target market is local Taiwan and the postings are concentrated on 104, then the ATS integrations of §2.1 are nearly useless to you" | The **trigger condition** for that judgement is too coarse. TSMC proves that a large Taiwanese employer may also run an international ATS and publish a sitemap. The degradation condition should be "after probing 20–30 target employers, fewer than N are usable", not "the target market is Taiwan" | Make the degradation condition observable: once the watchlist probe is done, count how many employers fall into each of "has a sitemap / has a job alert / manual only", and size the ingestion layer investment from that. The original conclusion (degrade to email plus manual) is kept as one of the branches | P2 |

**R-04-1, expanded.** A sitemap beats crawling the search page on four dimensions at once. This is not a marginal improvement:

| Dimension | Crawling the search page | sitemap | Evidence |
|---|---|---|---|
| **Completeness** | You paginate yourself, and may still miss rows | Authoritative index | The 774 `/JobDetail/` entries in the zh_TW sitemap **match exactly** the 774 the search page reports (Measured) |
| **Incremental detection** | You must fetch the full text to know whether anything changed | Every URL carries `<lastmod>` | All 815 URLs have a lastmod (Measured; whether lastmod's **semantics** can be trusted, see Q-4) |
| **Legality** | Gray (an unauthorized access pattern) | **The site operator's own invitation** | robots.txt says `Allow: /careers` in plain text and lists `Sitemap:` (Measured) |
| **Request volume** | 78 requests (pagination hard-capped at 10; `jobRecordsPerPage=100` returns the same as `=10`) | **1 request** | Measured |

New source registry kind (fields follow the existing YAML structure of §2.1):

```yaml
- id: tsmc_sitemap_zhtw
  kind: sitemap                      # new kind
  access_mode: feed                  # maps to 02 §5.6; a sitemap is feed semantics, not manual_assisted
  employer_id: tsmc                  # new field, points at target_employer
  index_url: "https://careers.tsmc.com/careers/sitemap_index.xml"
  locale_sitemap: "zh_TW"            # four locale sub-sitemaps: de_DE / ja_JP / zh_TW / en_US
  url_filter: "/careers/JobDetail/"  # 774/815
  incremental_by: lastmod            # lastmod | always_full | etag (pending Q-4)
  robots_allow_verified_at: "2026-09-16"
  robots_excerpt: "Allow: /careers ; Disallow: /careers/*qtvc="
  rate: { min_interval_s: 5, concurrency: 1 }
  tier: A
  verified_at: "2026-09-16"          # §2.1 rule: if unverified, enabled must be false
  enabled: true
  tos_note: "ledger:tsmc-2026-09-16" # points at the source ledger in document 10
  injection_risk: low                # see R-05-4
  source_trust: verified_employer    # see R-05-2
```

The probe SOP (repeatable against any employer, about 10 minutes, sitting alongside §2.1's existing "ATS endpoint verification method"):

```bash
# 1. robots.txt: look for the Sitemap: directive; if absent, downgrade this source to job alert or manual
curl -s https://careers.example.com/robots.txt

# 2. Fetch the sitemap index and list the sub-sitemaps (usually by locale or by section)
curl -s https://careers.example.com/careers/sitemap_index.xml

# 3. Fetch the target locale's sub-sitemap; count total URLs and those matching the job posting pattern
curl -s ".../zh_TW/careers/sitemap.xml" | grep -c "<loc>"
curl -s ".../zh_TW/careers/sitemap.xml" | grep -c "/JobDetail/"

# 4. Compare against the posting count the search UI reports -> if they match, the sitemap is the authoritative index
# 5. Check whether <lastmod> is present -> decides the incremental strategy
# 6. Copy the verbatim robots.txt text and the date read into the source ledger in document 10
```

The comparison in step 4 is what decides whether this sitemap can serve as the sole input, and it cannot be skipped. **It is also the concrete form of recommended next step 6 in [`99-gaps.md`](99-gaps.md)** — it swaps "does a Greenhouse endpoint exist", a whole-internet question you can never finish verifying, for "how many of the 30 companies I care about can be polled at low frequency", a question you can finish in one afternoon.

---

### 1.3 `08-delivery-tracking.md` (4 revisions)

| ID | Original thinking | Why it changed | What it became | Priority |
|---|---|---|---|---|
| **R-08-1** | §8.1: C3 Playwright semi-automated form filling costs ≈ 720 minutes in year one, nets 4.5 minutes saved per submission, and breaks even only at **160 submissions a year on a single ATS**; conclusion, "skip it outright in v1" | See the expansion below | The conclusion **splits into two independent decisions** (form auto-fill / PDF rendering), and **the existing C4 Apply Pack is extended** (no new channel tier) | P1 |
| **R-08-2** | §5.5 decides ghosted with per-channel `D_suspect` / `D_ghost` dual thresholds; for large-company ATS (C3/C4) these are **21/45 days** | TSMC's own text, "the selection process averages two to four weeks", refers to **the whole selection process** (questionnaire, English test, one or two interviews), not the time to first reply. **The existing 45-day `D_ghost` already covers that span; the numbers do not need to change.** What is actually missing is the mechanism: there is nowhere to record that different employers have different process lengths | Add `target_employer.suspect_after_days` / `ghosted_after_days` as **override fields**, defaulting to §5.5's per-channel values. TSMC keeps the defaults 21/45, and the probe report separately records "employer states a selection process of 2–4 weeks" for a human to read | P2 |
| **R-08-3** | §3.2 preflight checks "do not submit twice to the same job posting" | On a single-talent-pool ATS, multiple applications to the same employer share one résumé and one candidate record, and the other side **can see how many postings you applied to**. "The same job posting" is not a fine enough granularity to describe the problem | Add an "employer-level submission frequency check" to preflight: a cap on the number of submissions within `employer_cooldown_days`. This also **promotes D2 in [`99-gaps.md`](99-gaps.md) from P1 to P0** — because F1 turns it from "you might be seen" into "you are told in writing that you will be seen" | **P0** |
| **R-08-4** | §1.1's state machine essentially ends at "reply received" (this is A1 in [`99-gaps.md`](99-gaps.md), and A1 already assigns the fix to 08) | TSMC's measured process gives A1 a concrete shape: fill in the résumé → questionnaire / English test → one or two interviews → reference check → offer | Extend the state machine with `screening / assessment / interviewing / reference_check / offer / closed` (A1's own text suggests `screening / interviewing / offer / closed`; the two extra states here are `assessment` and `reference_check`); the `assessment` state is bound to the new red line in R-10-1 | P1 |

**R-08-1, expanded.** The original cost model has two systematic biases:

*Overstated on the cost side* — the model implicitly assumes that every use of C3 has to deal with login state. F3 shows the user already has a dedicated Chrome (a job-search-only instance that can persist logged-in session state long-term), which turns the login cost from per-use into one-time.

*Undercounted on the benefit side* — the model counts only the minutes saved on form filling, and counts **PDF rendering** not at all. [`11-tech-stack-roadmap.md`](11-tech-stack-roadmap.md) §3 originally used `docxtpl` plus headless LibreOffice for PDF conversion. If Playwright is already in the dependency tree, the HTML template → PDF path lets you drop LibreOffice, a heavyweight dependency. The point is this: **PDF rendering is used by every single submission, not only the handful C3 happens to hit**, so it is not bound by the 160-submission threshold at all.

What it became — two independent decisions:

| | **Decision A: use Playwright to auto-fill ATS forms** | **Decision B: use Playwright for PDF rendering** |
|---|---|---|
| Conclusion | **Do not do it** (unchanged) | **Do it** (pending Q-5's verification of the dependency cost) |
| Rationale | The 160-submission threshold still holds. And Avature's application process includes a questionnaire and an English test, hitting §8.2's downgrade conditions squarely: "there is a multi-step questionnaire" and "getting these wrong is expensive, so a human should be thinking about them anyway" | Every submission uses it, independent of how often C3 is used; and it issues no requests to any external domain, so ToS risk is zero |
| Bound by the 160-submission threshold | Yes | **No** |
| Conflicts with existing documents | None | **Two, see R-02-2 and the note on R-04-2** |

**Decision B's conflicts have to be stated out loud, not quietly worked around**:

- The comment in [`02-architecture.md`](02-architecture.md) §6 states that `delivery/gate.py` is "the only module in the whole system allowed to import `smtplib` / `playwright`", enforced by import-linter in CI. Using Playwright in the render layer violates that outright. The handling is in R-02-2.
- The parenthetical in [`04-ingestion.md`](04-ingestion.md) §2.6 notes that "Playwright still appears in this system, but **only in the delivery layer**". That sentence has to be rewritten to "only in the delivery layer and the render layer, and the render layer may not issue requests to external domains".

**No new channel tier.** The first draft proposed a C3′ where "the human drives and the machine watches", but §2.4's **C4 Apply Pack already is that thing** — it produces a local web page with one copy button per field in `form-fields.md`, and only writes the Submission once the "I have sent it" button at the bottom of the page is pressed. Conjuring one more tier out of thin air would only turn the channel table into four and a half. The right move is to **extend C4** in three ways:

1. The field set of `form-fields.md` is driven by `ats_profile` (R-06-3) rather than generic guesswork.
2. Add a prompt to "screenshot the `ApplicationConfirmation` page", as a candidate reconciliation record for D1 (see Q-7).
3. C4 currently describes only a one-off submission to a job posting; it must explicitly cover **Mode P profile registration** — which is likewise "a human pasting it in, in their own browser".

This item also settles **contradiction §3** in [`99-gaps.md`](99-gaps.md) (three coexisting positions on Playwright): it is neither "do it" nor "do not do it", it is **adjudicated separately per use** — form filling no, rendering yes, ingestion never.

---

### 1.4 `05-scoring-triage.md` (5 revisions)

| ID | Original thinking | Why it changed | What it became | Priority |
|---|---|---|---|---|
| **R-05-1** | The pipeline is Stage 0 hard rules → JD parsing → Stage 2 coarse screening → Stage 3 six-facet deep scoring, **with one set of rubric anchors shared end to end** | The six facet anchors mean different things across job families. Among TSMC's 21 Job Categories, the `skill_match` anchors for IT Security Engineer and Physical Design Engineer cannot be shared; without routing first, one shared anchor set systematically favors one of them | Insert **`role_class` routing** after Stage 0 and before JD parsing. Deterministic rules come first (job title keywords + the job category facet the ATS provides — TSMC hands you 21 classes at zero cost), and the small model is used only when no rule matches. `role_class` decides which anchor set and which `target_profile` to use. This also partly resolves **A3 (multiple personas)** in [`99-gaps.md`](99-gaps.md) | P1 |
| **R-05-2** | There is no source-trust or authenticity check | career-ops' Block G (scam / ghost job detection) is worth copying, but **belongs somewhere else**: it treats G as one block of the LLM evaluation, whereas we should build it as a deterministic gate in Stage 0 | See the expansion below | P1 |
| **R-05-3** | §6.2 is quota-mode-first, with `T_l` clamped by the `[35, 60]` guardrail. Contradiction §6 in [`99-gaps.md`](99-gaps.md) notes that the precedence between capacity and score is unsettled | career-ops' "do not apply below 4.0/5" is an explicit **absolute floor**, justified by "a job seeker's time and a recruiter's time are equally finite" — which lines up exactly with this system's product principle 4, except that this system has no floor at all today, only a ranking | See the expansion below | **P0** |
| **R-05-4** | C1 in [`99-gaps.md`](99-gaps.md) (prompt injection) is an open security gap, with one uniform treatment | A sitemap source's threat model differs from a public aggregator's: the source domain is verified, and the only party who can change the JD body is the employer itself | Tag `injection_risk: low \| high` in the source registry. Only `high` (aggregators, unknown URLs pasted in by hand, content forwarded by headhunters) turns on the expensive defenses (an extra schema validation pass, mandatory evidence string matching); `low` runs the standard defenses. **Tiering the defenses is not the same as weakening them** — the standard defenses are always on | P1 |
| **R-05-5** | Everything arriving via sitemap is a "job posting" | TSMC has a permanent "Register for the TSMC talent pool" entry at jobId=562 (Posted 2023-09-01); it is not a job posting but the entrance to Mode P. Scoring it as a posting wastes calls, and because its lastmod never changes it will keep re-entering the queue | Add `posting_kind: job \| talent_pool \| evergreen`. `talent_pool` routes straight into the Mode P flow and never enters the scoring pipeline | P1 |

**R-05-2, expanded.** Build the authenticity screen as a deterministic Stage 0 check, not as an LLM evaluation block:

| Check | Verdict | Why it is deterministic |
|---|---|---|
| Is the source domain the employer's official domain | `source_trust: verified_employer \| aggregator \| unknown` | This is a metadata comparison, not a semantic judgement |
| Does it come from a probed sitemap / official ATS | Same as above | Same as above |
| Is there a parseable, named employer entity | pass / flag | String matching |
| Is the salary anomalously above the band for that `role_class` | flag | Numeric comparison |
| Does it ask for payment, personal financial information, or private contact over a messaging app | **hard reject** | Keyword dictionary |

The rationale: ghost jobs and scam postings hurt this system by (a) **consuming review slots** and (b) **leaking personal data**, and both should be blocked before an LLM token is spent. For a first-tier source like TSMC, this gate passes immediately, at zero cost.

**The honest limit**: this gate only stops third parties impersonating an employer. It does not stop a ghost job posted by the real employer (the hire is already decided internally, or the posting is left up permanently to harvest the talent pool). That is a semantic and temporal problem that deterministic checks cannot touch; all you get is a flag from weak signals such as a `lastmod` that never changes. Do not claim this gate solves ghost jobs.

**R-05-3, expanded — the three-layer order, settled:**

```
(1) Veto layer: hard-rule gate + authenticity screen (R-05-2)
        ↓ only what passes goes on
(2) Floor layer: the absolute score floor, score_floor
        Anything below score_floor never enters the queue; a slot is left empty even when quota has room
        ↓ only what passes goes on
(3) Quota layer: rank by score and take the top N (N = weekly_review_capacity)
        T_l = the Nth score; if T_l falls below score_floor, score_floor wins
        (the result is a queue smaller than quota, and that is deliberate)
```

In one line: **quota decides how many slots there are, the floor decides whether a slot stays empty, and the floor takes precedence over capacity.**

> **A note on symbol naming**: do not reuse the letter `F`. [`07-review-gate.md`](07-review-gate.md) §5.3 already uses `F` for "the add-fact escape hatch in the factual assertion check", and a name collision inside one document set causes real misreadings. This document uses `score_floor` throughout.

Why adopt career-ops' spirit of a threshold but not carry over its number: 4.0/5 is **a score on someone else's rubric**, and transplanting it directly is false precision. This system's `score_floor` should be calibrated backwards from the 20 manual submissions of Phase 0 (method: score those 20 after the fact and take the upper edge of the scores of the ones you now regret sending).

Until that calibration is done, `score_floor` provisionally takes the existing lower `T_l` guardrail of **35**. **This must be honestly labeled as a placeholder stacked on a placeholder** — §6.2 already admits that 35 and 60 "are initial values set on gut feel, with no data behind them". Promoting a number that admits it has no basis into a "floor" without annotating it would let it gradually acquire, across the later documents, an authority it does not deserve.

This item also requires a wording correction to core claim 1 of [`00-overview.md`](00-overview.md) — see R-00-2.

---

### 1.5 `11-tech-stack-roadmap.md` (6 revisions)

| ID | Original thinking | Why it changed | What it became | Priority |
|---|---|---|---|---|
| **R-11-1** | Phase 1 = **single-source** ingestion + parsing + scoring + CLI, "pick the ATS used by whichever kind of company you submitted to most in Phase 0", presumed to be Greenhouse/Lever | See the expansion below | Phase 1 = **a single-employer vertical**, driven end to end through one employer | **P0** |
| **R-11-2** | The data layer is all SQLite; §16 already settled "`content/` under version control, `data/` not" | career-ops uses no DB at all, relying on Markdown tables + YAML + TSV. That counterexample deserves to be taken seriously: its persistence is more transparent, diffs better, and is easier to edit in an editor | See the expansion below | P1 |
| **R-11-3** | Phase 0's DoD has three items, all about the content library and the manual baseline | C2 (repo leakage) in [`99-gaps.md`](99-gaps.md) and recommended next step 5 both explicitly require this to be written into the Phase 0 DoD, and "there is only one chance to get it right" | Add a fourth item to the Phase 0 DoD: "the three-zone directories of [`13-repo-layout.md`](13-repo-layout.md) exist, the `.gitignore` allowlist is in place, the pre-commit scan is installed, and **the remote ownership of `content/` has been ruled on**". See the expansion below | **P0** |
| **R-11-4** | §3's technology-selection table: documents are produced with `docxtpl` plus a hand-built Word template, PDFs via headless LibreOffice | R-08-1 decision B puts Playwright into the render layer | Change the selection table into a side-by-side evaluation: HTML template + Chromium printing vs `docxtpl` + LibreOffice. **Speculation — needs verification**: whether Playwright can point `channel` or `executable_path` at the existing `App\Chrome-bin\chrome.exe` (153.0.8010.37) instead of downloading its own bundled Chromium, and whether that version is inside Playwright's supported range (verification method in [`14-browser-automation.md`](14-browser-automation.md)). **Do not delete LibreOffice from the selection table before that is verified** | P2 |
| **R-11-5** | There is no discussion of agent-native architecture | career-ops' Agent Skill Standard (`.agents/skills/` as the single entry point, symlinked into each vendor's CLI directory) is designed for a product layered on top of a CLI agent, and does not suit an application with a DB, schema constraints and scheduling | **Not adopted as architecture.** But copy one small thing: write §16's `prompts/` and the rubric anchors as Markdown any CLI agent can read, so that Phase 0 (the phase with no code) can run the process manually with a CLI agent. Phase 0 is thereby upgraded from "purely manual" to "agent-assisted manual" **without adding a single line of code**. Symlinks on Windows require developer mode or administrator rights, which is a further incidental reason not to adopt the symlink scheme | P2 |
| **R-11-6** | Phase 3 = multi-source + email parsing + status tracking | If Phase 1 is an employer vertical, the correct extension for Phase 3 is "employers 2–5", not "more source kinds" | Change Phase 3 to "horizontal replication: employers 2–5"; keep email parsing and status tracking (they are independent of employer count), and demote multi-source aggregation (RSS aggregators) to optional or cut it outright (see section 5) | P1 |

**R-11-1, expanded.** Three reasons, each standing on its own:

1. **The risk is in the wrong place.** The Greenhouse/Lever endpoints are still one of the "three big open questions" in [`00-overview.md`](00-overview.md) §6, and Phase 1's own scope paragraph is tagged "the endpoint shape of both, whether a key is needed, rate limits, and the uses ToS permits all need verification". Binding Phase 1 to something unverified puts the largest uncertainty at the start of the critical path. TSMC's sitemap has been measured and works: 774 entries carrying lastmod, explicitly allowed by robots.
2. **The slicing produces wasted work.** Slicing by "one source" means you finish the ingestion layer and the scoring layer, hit Mode P at the delivery end, and then go back and redo the assembly layer. Slicing by "one employer" forces you to touch every link of the end-to-end chain in week one, including the one most easily underestimated: **the application-process mode**.
3. **Product principle 4, carried up to the roadmap level, says depth before breadth.** If "fewer but better" only governs which job postings you pick and not the order in which you build, you are treating the principle as a slogan.

What Phase 1 becomes:

- **Scope**: sitemap polling → JobDetail fetch → parsing → `role_class` routing → scoring → CLI review → **a human completing one Mode P profile registration in the dedicated Chrome**.
- **The DoD keeps its original three items**: precision@10 ≥ 6, false negatives in the sample ≤ 1, per-posting decision time -50%, plus "10 submissions actually sent".
- **The DoD gains one more**: the target employer's talent pool holds a canonical profile assembled from this system's material, and the local machine holds its full snapshot (`employer_profile_state`).
- **Added to this phase's drop list**: other employers, other source kinds (the original list already contained "multi-source"; this only tightens the definition).

**An honest objection**: pinning Phase 1 to one company means that if that company is not somewhere you actually want to work, the entire phase is spent writing code for a target you do not care about, and it will produce a pile of code that only means anything to Avature. **Adoption condition**: bind to TSMC only if TSMC really is inside your top-5 targets; otherwise swap in your top-1 employer, with exactly the same method (run R-04-3's probe SOP first). See also Q-8: you must first draw the line for "which parts have to be generic from day one".

**R-11-3, expanded — an existing contradiction that has to be ruled on now.**

Item 2 of §16's "three deliberate structural decisions" recommends: `content/` holds the full résumé, salary expectations and visa status, so "**the local git repo should have no remote**".

But C2 in [`99-gaps.md`](99-gaps.md) records that this repo already has the remote `git@github.com:rojarsmith/ai-career.git`, and that `.gitignore` currently blocks only `doc/analysis-and-planning/`.

These two cannot both be true. One has to be picked before three-zone governance (R-02-1) lands:

| Option | Approach | Price |
|---|---|---|
| **A (recommended)** | Move `content/` and `data/` out of this repo entirely, into another git repo on the same machine with **no remote**; `ai-career` holds only code and system configuration | Two repos to back up separately; the cross-repo paths have to go into `config.toml` |
| B | Keep a single repo and rely on the `.gitignore` allowlist to block `content/` and `data/` | One `git add -f` or one misconfigured hook breaks it, and it is **irreversible** |
| C | Make the repo private and accept the risk | A private repo is still the cloud; it conflicts with the spirit of product principle 5, as §16 has already argued |

The failure mode of option B and the failure mode of option A are asymmetric: one mistake with B is a permanent leak, one mistake with A is one missing backup. **This is P0, and it must be decided before the first line of real data lands.**

**R-11-2, expanded — a hybrid, with the division of labor nailed down:**

> **Written by a human, needs git history, needs editing in an editor → files (YAML/Markdown); written by a machine, needs querying and constraints → SQLite.**

| Files (version-controlled, authored by a human) | SQLite (not version-controlled, authored by the machine) |
|---|---|
| The `content/` content library, `profile.yaml` | `job_posting` / `normalized_job` / `scoring_run` |
| The `target_employer` watchlist and probe reports | `application` / `review_task` / `submission` |
| source registry | `task_queue` / the event stream |
| `prompts/`, rubric anchors | LLM call retention and cost accounting |
| The **answer text** of `application_question` | Usage records and links for `application_question` |

**Why it cannot all be Markdown**: the core mechanism of [`03-data-model.md`](03-data-model.md) is the `NOT NULL` foreign key on `submission.approved_review_id` plus a `BEFORE INSERT` trigger — the only structural line of defense for product principle 1 (human-in-the-loop cannot be skipped) at the **database layer**. Markdown cannot enforce it.

Worth noting: career-ops **does not need** this mechanism, because it states flatly that it "never submits an application on your behalf" — it outsources the human-in-the-loop guarantee to "the system simply has no ability to send". That is a perfectly legitimate and considerably simpler design. This system chose to keep the ability to send (C1 direct email), and the price is that it has to carry this constraint itself. **This trade-off should be written into [`00-overview.md`](00-overview.md), because it is the most fundamental divergence between the two systems and one of the main sources of this system's complexity.**

One thing to adopt from career-ops at the same time: the idea of `cv.md` as the single source of truth. §16's `content/` already has this structure; what is missing is a directional declaration — **the `content_block` in the DB is a derivative of `content/`, not the truth; the DB can be deleted wholesale and rebuilt**. This also fixes an implicit assumption in [`03-data-model.md`](03-data-model.md) (treating the DB as the substance of the content library), and gives §12's restore drill an explicit success criterion: after deleting `data/` and rebuilding, every fact in `content/` is still there.

---

### 1.6 `03-data-model.md` (5 revisions)

| ID | Revision | Why | Priority |
|---|---|---|---|
| **R-03-1** | New entities (see the table below) | Carries R-06-1 / R-04-3 / R-05-1 and A1 / A3 / D2 from [`99-gaps.md`](99-gaps.md) | **P0** |
| **R-03-2** | The foreign key semantics of `application.normalized_job_id` have to change | See the expansion below | **P0** |
| **R-03-3** | ATS questionnaire answers must go through the same `artifact_block_usage` provenance as résumé bullets | Otherwise the questionnaire becomes a back door around the honesty principle — free text, reviewed by no one, and the answers retained by the employer long-term: exactly the intersection of the three worst conditions | P1 |
| **R-03-4** | Add `usable_in: [resume, profile, questionnaire, interview]` to `content_block` | Not every block belongs in a canonical profile that **the whole company** will see (the F1 consequence in R-06-1); it is also orthogonal to but complementary with `disclosure_level` in B4 of [`99-gaps.md`](99-gaps.md) | P2 |
| **R-03-5** | Add `posting_kind` and `role_class` to `normalized_job` | Carries R-05-5 and R-05-1 | P1 |

The list of new entities:

| Entity | Purpose | Originating requirement |
|---|---|---|
| `target_employer` | watchlist + employer probe report: ATS vendor, sitemap URL, robots re-check date, application mode (P/D), `suspect_after_days` / `ghosted_after_days` overrides, `employer_cooldown_days`, `assessment_windows` | B1 / R-04-3 / R-08-2 / R-08-3 / R-10-1 |
| `canonical_profile` + `canonical_profile_version` | Mode P's canonical profile and its versions | R-06-1 |
| `employer_profile_state` | The snapshot of "this profile version is currently sitting in this employer's talent pool" | R-06-2 |
| `profile_submission` | Mode P's send record, alongside `submission`, and **equally requires `approved_review_id` NOT NULL** | R-06-1 / R-07-1 |
| `application_question` + `answer_block` | The ATS questionnaire bank. Step two of TSMC's process says outright "fill in the relevant application questionnaire for the position", and these answers recur across submissions and must stay consistent | A1 / [`15-target-tsmc.md`](15-target-tsmc.md) |
| `interview_story` | A STAR + Reflection story bank, accumulated across applications | A1 / career-ops |
| `comp_research` | Compensation research, hung off `role_class` or `employer` | career-ops / A1 |
| `role_class` | Role classification and its corresponding rubric anchor set; many-to-one with A3's `target_profile` | R-05-1 / A3 |

**Note**: this table adds eight entities, the largest structural expansion in this batch. It **does not mean all eight have to be built in Phase 1** — Phase 1 needs only five: `target_employer`, `canonical_profile`, `employer_profile_state`, `profile_submission`, `role_class`. `application_question`, `interview_story` and `comp_research` belong to A1's post-submission stage and come after Phase 3. Defining the schema first and creating the tables later is fine; the reverse is not.

**R-03-2, expanded.** Originally `APPLICATION ||--o{ NORMALIZED_JOB`: one submission corresponds to one job posting. Under Mode P, one profile registration may correspond to **0** concrete postings (pure talent pool registration, such as jobId=562) or to **N** of them (after registering you are invited to interview for positions you never applied to — F1's own text says this happens).

It becomes: `application.mode` enumerates `profile | document`, `normalized_job_id` becomes nullable, and a CHECK constraint expresses "when `mode='document'`, `normalized_job_id` must be NOT NULL".

**This is the schema change in this batch most prone to rework, and it is worth making now.** Once the `application` table holds data and the foreign key is NOT NULL, a later migration has to backfill the existing rows, and "which Mode P profile does this Mode D application correspond to" cannot be reconstructed after the fact.

---

### 1.7 `10-risk-compliance.md` (5 revisions)

| ID | Revision | Why | Priority |
|---|---|---|---|
| **R-10-1** | **New red line: AI must not take an employer's ability tests on your behalf** | See the expansion below | **P0** |
| **R-10-2** | Make red line 10 (no real personal data or credentials in the git repo) executable | Carries **C2** from [`99-gaps.md`](99-gaps.md); the substantive design lives in [`13-repo-layout.md`](13-repo-layout.md), while 10 owns the rule list and the checkpoints and records the outcome of R-11-3's remote ruling | **P0** |
| **R-10-3** | Add a section, "the personal-data consequences of a single-talent-pool ATS" | §3.1 is about what you are holding (other people's personal data). F1 exposes the reverse problem: **how far what you hand over spreads**. TSMC says outright "open to all TSMC managers" | P1 |
| **R-10-4** | Add a TSMC entry to the source ledger | This is the first entry backed by evidence (verbatim robots.txt, date read 2026-09-16, sitemap URL, re-check due date), and it doubles as the sample of the ledger format. It is also the first piece of real data for E2 "assumption and source ledger" in [`99-gaps.md`](99-gaps.md) | P1 |
| **R-10-5** | Give §2.4 "do not fight the platform" a positive formulation as well | Today the rules and the red lines are all prohibitions, with nothing about what is encouraged. An explicit Allow in robots.txt plus a volunteered sitemap is the site operator's **invitation** — a judgement that directly drives the source priority order (R-04-1) | P2 |

**R-10-1, expanded.** Step two of TSMC's application process includes "an English test, or proof of proficiency".

Proposed clause:

> **No test, coding test, online assessment or aptitude test administered by an employer to evaluate the candidate's own ability may, under any circumstances, be answered, hinted at, or assisted in real time by this system or by any LLM.**

**Why this has to be a red line rather than a guideline**: it is isomorphic to existing red line 3 (do not put false data in an application form's factual fields) — **a test score is a factual claim about you**, and having an AI take it is forging that fact. It is also one of the few kinds of cheating that surfaces three months after you start, where the consequence is not rejection but termination.

The line between allowed and not allowed:

| Allowed | Not allowed |
|---|---|
| Practice and preparation **before** the test (separated in time from the real test) | Assistance of any kind **during** the test |
| Review and shoring up knowledge **after** the test | Answering on your behalf, real-time hints, reading the screen contents |
| Recording "this company has an English test" in the probe report | Collecting or circulating test question banks |

**By mechanism, not self-discipline**: `target_employer.assessment_windows` records the test windows, and within those windows every assist feature for that employer is disabled; the Apply Pack and the profile page display the test policy notice.

**Honestly admitting what this mechanism cannot stop**: someone determined to cheat can simply open another window, and this system cannot and should not monitor the user's screen. This red line does exactly two things — **it stops the system from casually offering the capability**, and it takes an explicit position in the design. Unlike the other items under §4.2 "hold it with mechanism, not self-discipline", this one's mechanism strength is the weakest tier (the kind [`07-review-gate.md`](07-review-gate.md) §10.3 calls "friction that can be bypassed without noticing"). The documents should label it that way instead of pretending it is as solid as the NOT NULL foreign key on `approved_review_id`.

---

### 1.8 `02-architecture.md` (4 revisions)

| ID | Revision | Why | Priority |
|---|---|---|---|
| **R-02-1** | The three places where the three data zones (private / derived / system) affect the architecture | See the expansion below | P1 |
| **R-02-2** | §6's "sole egress" constraint has to be restated | `delivery/gate.py` was the only module in the whole system allowed to import `smtplib` / `playwright`, enforced by import-linter in CI. R-08-1 decision B puts Playwright into the render layer | P1 |
| **R-02-3** | Add a sitemap adapter to the L0 node of §2.1's data flow diagram; §5.6's `access_mode` table confirms that sitemap falls under `feed` | Carries R-04-1. A sitemap is an announcement file meant to be read by machines, semantically the same class as RSS, so no new `access_mode` value is needed | P2 |
| **R-02-4** | Add a `notifier` to the cross-cutting components | Carries **D3** from [`99-gaps.md`](99-gaps.md) (how the system reaches the user); D3's own text assigns the fix to 02's cross-cutting components or to 07. Implemented as a daily digest plus a read-only `aicareer status` CLI summary | P2 |

**R-02-1, expanded.** [`13-repo-layout.md`](13-repo-layout.md) splits the data into three zones: **private** (personal, never leaves the machine, never enters git) / **derived** (rebuildable, does not enter git) / **system** (enters git). This refines §16's existing binary of "`content/` version-controlled, `data/` not" — `content/` is the private zone, and `data/` splits into the derived zone and credential state (see Q-6). It affects 02 in three places:

1. **§2.2's process and deployment view** needs a "filesystem partitioning" item, alongside "the three clocks".
2. **D6 (secrets go neither into the DB nor into the repo) widens from "secrets" to "the three zones"** — secrets (API keys, passwords) are only one subset of the private zone, which also contains the entire content library, headhunters' names and mailboxes, and the submission records.
3. **The LLM Gateway's responsibilities (D5) gain egress classification**: every call must tag which zone the outbound data belongs to, and any egress of private-zone data leaves an auditable record at the gateway.

Point 3 has a side benefit: it gives **contradiction §9** in [`99-gaps.md`](99-gaps.md) (principle 5, local-first, vs prompt caching) **a place to be handled**. Prompt caching is, in essence, "the entire content library (the private zone) residing long-term on the vendor's side", which is an egress policy decision at the LLM Gateway, not a one-line open verification item inside [`06-content-assembly.md`](06-content-assembly.md). **But note: giving it a place is not the same as ruling on it.** 99-gaps asks for it to be escalated to 00 and ruled on explicitly, and this batch has not done that.

**R-02-2, expanded.** The value of the original constraint is that it is **statically checkable** — import-linter runs in CI and does not rely on anyone's self-discipline. The new constraint has to preserve as much of that property as possible.

Two layers:

> ### ⚠ The static layer of R-02-2 has been superseded by ruling A2
>
> This scheme leaves **JD snapshot evidence with no lawful home**: a snapshot has to load remote http(s), but `gate.py` is the delivery layer and `render/pdf.py` is restricted to `file://`. The final choice is a `browser/` package plus three sub-modules that do not import each other. **The behavioral layer below (a route handler aborting non-`file://` requests + test assertions) remains in force**, applied to `browser/render.py`.
>
> **Also: `delivery/` is wrong**; the actual directory name is `deliver/`. See [17-decisions.md](17-decisions.md#a2--a-browser-package-with-three-submodules-that-cannot-import-each-other).

```
Static layer (import-linter, CI-enforced)      ← superseded by A2, see above
  Modules allowed to import smtplib:    deliver/gate.py            ← unchanged
  Modules allowed to import playwright: deliver/gate.py, render/pdf.py
  render/pdf.py may not import any network client (httpx / requests / smtplib)

Behavioral layer (test-enforced)
  render/pdf.py's browser context may load only file:// and 127.0.0.1
  Method: attach a route handler to the context, abort every request that is not file:// / not 127.0.0.1
  Test assertion: when rendering a template containing an external <img src="https://...">, that request is aborted
```

**Speculation — needs verification**: whether Playwright's `context.route()` can intercept sub-resource requests inside a `file://` page (interception behavior for ordinary `http(s)` is documented; the `file://` case has not been verified by this project). Verification method: write a minimal template containing an external image, attach a route handler, and assert that the handler is called and that the image renders empty. If it cannot be intercepted, the fallback is to statically scan the template before rendering and reject any resource reference that is not a relative path — that is pure string checking and is guaranteed to work.

**Record the price honestly**: the static constraint loosens from one module to two, and gets weaker; the behavioral constraint rests on tests rather than a linter, and fails the moment someone breaks the test. That is the real price of R-08-1 decision B, and 02 should say so rather than writing down only the benefits.

---

### 1.9 `00` / `01` / `07` / `09` (10 revisions)

| ID | Document | The original situation | What it became | Priority |
|---|---|---|---|---|
| **R-00-1** | 00 | Core claim 4: "Playwright semi-automated form filling does not pay off at personal volumes (a single ATS needs 160+ submissions a year to recoup it), so v1 skips it outright" | Rewrite as two decisions: **form auto-fill is not done (the 160-submission threshold holds); PDF rendering is done (not bound by that threshold)**. And note that the "human drives, machine supplies" capability is carried by the existing C4 Apply Pack, with no new channel tier | **P0** |
| **R-00-2** | 00 | Core claim 1: "the score only ranks, capacity draws the line" | Add a sentence: **"but the floor takes precedence over capacity — anything below `score_floor` stays out of the queue even when slots are free."** (R-05-3) | P1 |
| **R-00-3** | 00 | Core claim 2: "the content library is the asset" | Add a sentence: **"the content library has two output forms — per-JD document assembly, and the per-employer canonical profile. On a single-talent-pool ATS the latter is the primary one."** (R-06-1) | P1 |
| **R-00-4** | 00 | E1 in [`99-gaps.md`](99-gaps.md) requires 00 to carry an "explicitly-not-doing list", but 00's current eight sections (§1–§8) **have no such section**; the closest thing is §14 "global drop list" in [`11-tech-stack-roadmap.md`](11-tech-stack-roadmap.md) | **Add a section**, with this batch's four items as its first contents: AI taking ability tests, a TUI review interface, the Agent Skill Standard architecture, and per-JD résumé tailoring on a single-talent-pool ATS. Merge in the existing items of 11 §14 at the same time, so that "explicitly not doing" has exactly one place where it is defined | P1 |
| **R-00-5** | 00 | E1 and recommended next step 2 equally require 00 to carry a "shared constants register", which **also does not exist today** | **Add a section**, with this first set of constants: `t_triage`, `t_full_review`, `weekly_review_capacity`, `employer_cooldown_days`, `profile_refresh_days`, `score_floor`, `assessment_blackout`, plus §5.5's ghosted dual thresholds. Tag every constant "measured / placeholder" | P1 |
| **R-00-6** | 00 | The second of §6's three big open questions: "what is the real state of ATS public job posting endpoints and their ToS?" | **Partly answered**: TSMC's sitemap has been measured, works, and is explicitly allowed by robots (Greenhouse/Lever remain unverified). The question should be rewritten as "**how many of the 20–30 employers on my watchlist offer a sitemap or a job alert?**" — a concrete question you can finish verifying in one afternoon, rather than a whole-internet question you can never finish | P1 |
| **R-01-1** | 01 | §6 lists seven breakdown points of the analogy | Add an **eighth breakdown point**: the bidding domain has nothing like a "single talent pool" — every bid is an independent document package, and there is no "last time's bid sitting at the client and being read by another department". Mode P has **no counterpart at all** in the bidding domain, which directly overturns the assumption that proposal assembly and résumé assembly are isomorphic | P1 |
| **R-07-1** | 07 | `review_task.kind` covers only T1 triage and T2 full review; §3.3's cooling-off period defaults to 12h | Add `profile_review`: the diff is not "the previous version vs this version of the application documents" but "**the version currently in the talent pool vs the version about to overwrite it**". The cooling-off period extends to 48h for Mode P (one profile change takes effect for the long term and cannot be withdrawn). The `expedite` mechanism for skipping the cooling-off period should be disabled outright under Mode P — Mode P has no deadline, so `expedite` has no legitimate justification | P1 |
| **R-07-2** | 07 | The review UI handles résumé diffs and cover letters | Bring questionnaire answers (R-03-3) into the same UI, running the same factual assertion check and the same `F` escape hatch logging | P2 |
| **R-09-1** | 09 | The funnel uses submission count as its denominator | The funnel has to accommodate Mode P: one profile registration **is not a submission** in the funnel, yet it may produce inbound approaches. A separate `inbound_from_talent_pool` count is needed — **this is the only metric that can measure whether Mode P works**. Without it, the investment in Mode P can never be tested, and Mode P is the most expensive revision in this batch | P1 |

---

## 2. Status Check on the P0 Gaps in `99-gaps.md`

| Gap | Before this batch | Now | Who carries it | What is still missing |
|---|---|---|---|---|
| **A1** No owner for the post-submission stage | Still missing | **Partly solved** | [`15-target-tsmc.md`](15-target-tsmc.md) supplies a concrete process (questionnaire / English test / 1–2 interviews / reference check / 2–4 weeks on average); R-03-1 adds `application_question`, `interview_story`, `comp_research`; R-08-4 extends the state machine | **A turnaround-time mechanism for answering replies** is still entirely absent (A1's own text notes this is the only link with explicit time pressure). The formal definition of the state machine has to be written into 08 |
| **A2** No owner for the referral channel | Still missing | **Still missing** | None | This batch did not touch it at all. An honest addition: [`12-reference-career-ops.md`](12-reference-career-ops.md) shows that career-ops' A–H framework **has no referral block either**. That means the blind spot is not uniquely ours, but **it does not mean it is unimportant** — item 1 of the counterargument in [`00-overview.md`](00-overview.md) §7 ("if you have 20 former colleagues you can approach, those 30 hours should go into coffee meetings") is still the single strongest objection in the whole document set |
| **B1** No capture planning | Still missing | **Solved at the design level** | The `target_employer` watchlist in [`13-repo-layout.md`](13-repo-layout.md) + the employer probe report in [`15-target-tsmc.md`](15-target-tsmc.md) + R-04-3's probe SOP + R-11-1 binding all of Phase 1 to capture | Only **execution** is left: actually list 20–30 companies and run the probe SOP once against each. This is precisely recommended next step 6 in 99-gaps |
| **C1** JD sent straight to the LLM with no prompt injection handling | Still missing | **Partly solved** | R-05-4 adds tiering (`source_trust` / `injection_risk`) so defense cost matches risk; R-05-2's authenticity gate blocks a portion of the sources | **The actual prompt structure is still unwritten**: the full JD wrapped in a delimited data block, the system prompt declaring it untrusted data, schema validation forced on the output. Those three have to be written into 05 §3.3. C1's own text already points out that "an evidence citation must string-match successfully against the original JD" — a mechanism 05 already has — is the most effective line of defense; it simply was never argued as a security mechanism, and that needs adding too |
| **C2** Repo leakage protection | Still missing | **Partly solved at the design level** | Three-zone governance in [`13-repo-layout.md`](13-repo-layout.md) + R-11-3 (written into the Phase 0 DoD) + R-10-2 (the rule list) + R-02-1 (architectural effects) | Besides execution there is now also **a decision not yet ruled on**: the `content/` remote ownership contradiction R-11-3 exposes (§16 recommends no remote vs the repo already having a GitHub remote). **There is only one chance to get this right**, and it sits in batch 0 |
| **D1** Crash-consistency and reconciliation for sending | Still missing | **Still missing, and now more complicated** | None | This batch did not touch it. And R-06-1 makes it harder: a Mode P "send" is a human clicking in a browser, the system cannot see the outcome, and there is no way to define when the intent log should be written (see Q-7) |

Non-P0 items this batch happened to handle along the way:

- **D2** (same-company throttling): settled by R-08-3, and **promoted from P1 to P0** because of F1.
- **D3** (how the system reaches the user): R-02-4 gives it a component slot; the design is still unwritten.
- **Contradiction §3** (three positions on Playwright): R-08-1 adjudicates separately per use, so the three documents can be brought into line.
- **Contradiction §6** (capacity vs score): settled by R-05-3 as the three-layer order.
- **Contradiction §9** (local-first vs prompt caching): R-02-1 gives it a place to be handled (the LLM Gateway's egress policy), but it is **not yet ruled on**, and what 99-gaps asks for is a ruling inside 00.

**Untouched**: contradiction §1 (review time differing by 5–10x, which 99-gaps flags as "the highest priority of all the corrections" and as recommended next step 1), contradictions §2, §4, §5, §7, §8, and the document governance gaps E2/E3 (E1 is partly carried by R-00-4 / R-00-5).

**Contradiction §1 is still the first priority across the whole document set, and this batch has not moved it half a step.** That has to be recorded honestly — because 49 revisions look like a lot and easily create the illusion of good progress. Yet solving §1 needs no design at all, only manually completing 3 submissions end to end and timing them.

---

## 3. New Open Questions Produced by This Batch

| # | Question | Why it matters | How to verify |
|---|---|---|---|
| **Q-1** | Are Avature's profile update semantics **overwrite** or **versioned**? When applying to a second posting, do you submit a fresh résumé or reuse the one in the talent pool? | It decides whether Mode P is "a one-time registration" or "something to consider updating on every submission", and directly drives when R-06-2's snapshot mechanism fires | Create an account in the dedicated Chrome, log in, and observe how `ApplicationForm` behaves on a second application (**without actually sending**). ⚠️ **Creating the account has to be done by the user personally, by hand** — [`04-ingestion.md`](04-ingestion.md) §2.6 explicitly forbids automatically registering accounts or automatically accepting terms of service |
| **Q-2** | How does a Mode P canonical profile pick blocks? "Cover the job family union" across 21 categories may amount to "no emphasis at all" | R-06-1 defines the mode only, not the algorithm. There is currently no rule whatsoever for the trade-off between focus and coverage | Do Q-10 first; once you know how many relevant postings there actually are and how many categories they span, decide the real size of the union |
| **Q-3** | Do `ro.careers.tsmc.com` (SuccessFactors) and the main Avature site share one candidate identity? | If not, overseas postings need a second profile, and Mode P goes from "one per employer" to "**one per ATS instance**", forcing a change to R-03-1's `canonical_profile` primary key design | The same manual observation as Q-1; check whether a login carries across the two sites |
| **Q-4** | Can the semantics of the sitemap's `<lastmod>` be trusted? Does a change mean the JD content changed, or only that it was re-published? | If not, R-04-1's incremental strategy falls back to "fetch the full text and compare hashes", request volume goes from 1 back to 774, and one of the sitemap's biggest advantages disappears | Fetch the sitemap for 7 consecutive days while also fetching the full text of 20 of those URLs and hashing them; compare how often lastmod changes agree with hash changes |
| **Q-5** | Can Playwright reuse the existing Chrome 153.0.8010.37 instead of downloading its own bundled Chromium? Is that version inside the supported range? | It affects the size of the dependency tree and R-11-4's selection conclusion. **If it cannot**, Playwright pulls in a second Chromium and decision B's rationale of "removing the heavyweight LibreOffice dependency" is badly weakened | See [`14-browser-automation.md`](14-browser-automation.md) |
| **Q-6** | Should the dedicated Chrome's profile directory (`Data\profile` by PortableApps convention, **not yet created**) be backed up, and how? | It will hold login cookies, which amount to credentials. The three zones of [`13-repo-layout.md`](13-repo-layout.md) may need a fourth category, **credential state** — it is neither private data (it is rebuildable) nor derived data (rebuilding is expensive and needs a human), and it must never enter git | Define the zones in [`13-repo-layout.md`](13-repo-layout.md) first, then come back and decide |
| **Q-7** | How is D1 (send reconciliation) done under Mode P? The send is a human clicking in a browser, and the system cannot see the outcome | D1 is a P0 gap, and Mode P makes it harder. Rely on a screenshot of the `ApplicationConfirmation` page? On a confirmation email? Either can be missed | After sending, observe whether there is a confirmation email (parseable) and a confirmation page (screenshottable), and take whichever is reliable; if neither is, fall back to C4's existing "the human clicks 'I have sent it'" mechanism, and admit that it is not reconciliation, only a declaration |
| **Q-8** | Once Phase 1 is bound to a single employer, when does generality come back? | If all of Phase 1 is bespoke, Phase 3 amounts to a rewrite and R-11-1's benefit is eaten | **Proposed line (needs confirmation)**: the source adapter interface, the `normalized_job` schema and the rubric anchor format **must be generic from day one**; fetching details, field mappings and the application-process mode **may be bespoke** |
| **Q-9** | What does career-ops' "≥4.0/5 or do not apply" correspond to after this system's six-facet weighting? | R-05-3's `score_floor` currently uses the placeholder 35, and 35 is itself the lower guardrail edge that 05 §6.2 admits was "set on gut feel" | Score Phase 0's 20 manual submissions after the fact and take the upper edge of the scores of the ones you now regret sending |
| **Q-10** | Of the target employer's 774 job postings, how many are genuinely relevant to the user after `role_class` routing? | **This is the number this batch should compute first.** If it is a single digit, the Mode P canonical profile is the only meaningful output for this employer and **the entire scoring layer is close to useless against this employer** — in which case R-11-1's Phase 1 scope has to shrink drastically | Pull down the 774 JD titles and categories and scan the distribution by hand. Doable in one afternoon |

---

## 4. Revised Recommended Order of Execution

### Batch 0: do these five things first (no code at all, an estimated one to two evenings)

| # | Action | Corresponds to | Done criterion |
|---|---|---|---|
| 0.1 | **Rule on review time**: manually complete 3 submissions end to end with a stopwatch, and define `t_triage` and `t_full_review` | 99-gaps contradiction §1, recommended next step 1 | Both constants have measured values. **This is the item 99-gaps flags as the first priority, and no other revision in this document is more important than it** |
| 0.2 | **Compute Q-10's number**: pull down the 774 JobDetail URLs from the zh_TW sitemap, take the titles and categories, and scan the distribution by hand | Q-10 | You can state "N are relevant to me, spread across M categories" |
| 0.3 | **Decide whether the target employer really is in your top-5** | The premise of R-11-1 | The top-5 employer list is written down. If TSMC is not on it, swap in someone else; the method is unchanged |
| 0.4 | **Rule on the remote ownership of `content/`**, and build the repo's three zones, the `.gitignore` allowlist and the pre-commit scan | C2 / R-11-3 / R-10-2 | One of R-11-3's three options is chosen and all four checks pass. **There is only one chance to get it right, and it must happen before the first line of real data enters the DB** |
| 0.5 | **Create the target employer account in the dedicated Chrome (by hand)**, and observe Q-1 and Q-3 | Q-1 / Q-3 / Q-6 | You can answer "is the profile overwritten or versioned" and "do the two ATSs share one identity" |

**0.2 is the gate.** If N is a single digit, jump straight to the failure criterion in section 5 and do not enter batch 1.
**0.4 is irreversible.** It sits here not because it is the most important, but because getting it wrong cannot be undone.

### Batch 1: P0 document revisions (no code)

In dependency order:

1. **R-06-1** (the Mode P / Mode D dual mode) — the root of the other revisions, change it first
2. **R-03-1 + R-03-2** (new entities, `application` foreign key semantics) — carries R-06-1, and is the spot most prone to rework
3. **R-04-1** (sitemap as a first-class source) — independent, can run in parallel
4. **R-05-3** (the floor takes precedence over capacity) — independent, can run in parallel
5. **R-10-1** (the ability test red line) — independent, can run in parallel
6. **R-10-2** (the repo leakage rule list) — carries the outcome of 0.4's ruling
7. **R-08-3** (employer-level submission frequency, D2 promoted to P0) — depends on `target_employer` from R-03-1
8. **R-11-1 + R-11-3** (bind Phase 1 to an employer vertical, the Phase 0 DoD) — depends on the results of 0.2 and 0.3
9. **R-00-1** (rewrite core claim 4) — change it last, because it summarizes the other revisions

### Batch 2: Phase 0 execution + P1 revisions

- **Execution**: 20–30 fact fragments in the content library, 20 manual submissions with timing (which also settles Q-9), and a 20–30 company watchlist with the probe SOP run once against each (B1)
- **P1 revisions**: R-06-2/3/4, R-04-2/3, R-05-1/2/4/5, R-03-3/5, R-08-1/4, R-10-3/4, R-02-1/2, R-11-2/6, R-07-1, R-09-1, R-00-2/3/4/5/6, R-01-1
- **Handled at the same time**: C1's actual prompt structure (05 §3.3)

### Batch 3: Phase 1 (a single-employer vertical)

Follow R-11-1's scope and DoD. Keep verifying Q-4, Q-5 and Q-7 throughout.

### Batch 4: P2 revisions and Phase 2

R-06-5, R-04-4/5, R-03-4, R-08-2, R-10-5, R-02-3/4, R-11-4/5, R-07-2.

**A reminder that runs through all of it**: the anti-procrastination check in [`11-tech-stack-roadmap.md`](11-tech-stack-roadmap.md) §15 matters more after this batch — this document lists 49 revisions, editing documents is far more comfortable than writing code, and editing documents does not get your résumé in front of anyone. Of §15's seven lines of defense, the one whose spirit should be switched on right now is "document revisions do not count as progress".

---

## 5. An Honest Section: Does This Batch Make the Project Better or Worse

### First, the admission: this batch is a net increase in complexity

The Mode P/D dual mode, three-zone data governance, eight new entities, role classification routing, two Playwright uses, the questionnaire bank, ability test blackout windows — each has a reason on its own, and together they push a project already estimated at **125–180 person-hours** further up.

A rough estimate of the extra hours for this batch's P0 + P1 revisions:

| Item | Increment |
|---|---|
| Mode P data model + snapshot + `profile_review` | 8–12 hours |
| The `target_employer` entity + probe report + employer-level preflight | 4–6 hours |
| sitemap adapter + deduplication scenario D | 3–5 hours |
| `role_class` routing + grouped rubric anchors | 4–6 hours |
| Three-zone governance + pre-commit + repo restructuring | 2–4 hours |
| **Total** | **21–33 hours** |

This means the counterargument in [`00-overview.md`](00-overview.md) §7 ("on paper, this project probably loses money") holds **more strongly after this batch, not less**. The break-even point used to be 90–150 submissions; now it moves up. That should not be papered over by the "the plan is more complete now" feeling that 49 revisions produce.

### But four of them are "cheap to change now, expensive to change later"

| Revision | Cost of changing now | Cost of changing later |
|---|---|---|
| **R-06-1** (Mode P) | Edit one section of one document | The assembly layer and the review UI are rebuilt from scratch — and you only find out after you have already sent 20 submissions |
| **R-03-2** (`application` foreign key semantics) | Edit one line of schema | The migration has to backfill existing rows, and "which Mode P does this Mode D correspond to" cannot be reconstructed after the fact |
| **R-11-1** (phase order) | Edit one table | You finish the ingestion layer and the scoring layer before hitting Mode P, and part of the first two phases is wasted |
| **R-11-3** (the `content/` remote ruling) | Edit one line of `.gitignore` and set `git remote` once | **Irreversible.** A commit on GitHub may already have been indexed even after you delete it |

These four do not add scope; **they turn rework into design, ahead of time**. They are the only unconditionally worthwhile part of this batch. The other 45 can all be vetoed and the project still stands.

### Scope worth cutting right now (concrete recommendations)

1. **Cut Phase 3's "multi-source" ambition.** If Phase 1's employer vertical works, the marginal cost of a second employer sits mostly in probing plus field mapping, not in the ingestion architecture. Change Phase 3 to "employers 2–5" (R-11-6). **RSS aggregators are not done at all** — [`04-ingestion.md`](04-ingestion.md) §2.3 itself says of them "low data quality, extremely high overlap between aggregators, greatly amplified deduplication pressure", and most of the postings they bring you can see on the employer's own site anyway.
2. **Confirm that cover letters and the Chinese/English dual track are deferred on the phase table too.** The "do not do this yet" list in [`06-content-assembly.md`](06-content-assembly.md) §10 **already** contains cover letter generation and the Chinese/English dual track, so this is not newly cut scope — the problem is that 11's phase table is not aligned with it, which makes it easy to build them in passing during implementation. An extra new reason: if all five of your top target employers are single-talent-pool ATSs, **there may be no field to put a cover letter in at all** (**Speculation — needs verification**: check during probing whether `ApplicationForm` has a free-text cover letter field). TSMC's zh_TW site already has 774 openings; the first round does not need an English variant.
3. **Raise the entry bar for the Phase 4 analytics layer.** Mode P makes the denominator "submission count" blurrier (how many submissions is one profile registration?), and the statistical base is thinner than [`09-analytics-feedback.md`](09-analytics-feedback.md) §4 assumes. Recommendation: change every denominator threshold in 09 explicitly to "**Mode D submission count**" — Mode P's effect can only be observed separately through R-09-1's `inbound_from_talent_pool`, and must not be mixed into the same funnel.
4. **Cut `scarcity(role_family)` and anything that needs cross-quarter statistics.** [`07-review-gate.md`](07-review-gate.md) §4.1 already cut it once, but R-05-1's `role_class` routing will tempt you to pick it back up ("we have classes now, so we can compute scarcity"). Do not — classification makes the sample in each cell smaller, not larger.
5. **Define the three entities `application_question` / `interview_story` / `comp_research`, but do not create the tables.** They belong to A1's post-submission stage and Phase 1 uses none of them. R-03-1 lists eight entities at once, which is very easy to read as "all eight have to be built".

**Not cut**: the content library, fact provenance (`artifact_block_usage`), the approval gate (`approved_review_id` + nonce), three-zone data governance. These four are the structural carriers of the product principles; cut them and this is not this system any more, it is something else.

### An honest failure criterion

If **Q-10 in batch 0 comes back with "only 3 of the target employer's postings are relevant to me"**, the correct response is **not** to shrink Phase 1's scope, but to admit something larger:

> **The evaluation layer has no value in your target market.**

This is exactly the mirror image of open question 3 in [`00-overview.md`](00-overview.md) §6 (if prevalence exceeds 50%, stop building) — the original worry was "too many are worth applying to, so triage is meaningless", and what you may actually hit is "too few are relevant, so triage has nothing to screen". Both cases lead to the same conclusion.

The right move at that point is to shrink the entire project down to three things:

```
content library  +  Mode P profile generator  +  C4 Apply Pack
```

Roughly **20–30 person-hours**, and it may well be enough. No scoring layer, no quota, no task queue, no analytics layer.

**This possibility is far from small.** For a job seeker with one specific background, it is entirely normal for a company with 774 openings to have a single-digit number of relevant ones. It is worth spending an afternoon counting first, rather than 30 hours writing code first.

---

## Related Documents

| Document | This document's relationship to it |
|---|---|
| [`00-overview.md`](00-overview.md) | R-00-1 ~ R-00-6 (6 revisions): wording corrections to core claims 1, 2 and 4, a new explicitly-not-doing list and constants register, a rewrite of §6 question 2 |
| [`01-domain-mapping.md`](01-domain-mapping.md) | R-01-1 (1 revision): an eighth breakdown point (the single talent pool has no counterpart in the bidding domain) |
| [`02-architecture.md`](02-architecture.md) | R-02-1 ~ R-02-4 (4 revisions): three-zone data governance, restating the sole-egress constraint, sitemap adapter, notifier |
| [`03-data-model.md`](03-data-model.md) | R-03-1 ~ R-03-5 (5 revisions): eight new entities, `application.mode` and the foreign key semantics |
| [`04-ingestion.md`](04-ingestion.md) | R-04-1 ~ R-04-5 (5 revisions): sitemap as a first-class source, tiering enterprise ATSs by access surface, the employer probe report |
| [`05-scoring-triage.md`](05-scoring-triage.md) | R-05-1 ~ R-05-5 (5 revisions): role routing, the authenticity gate, `score_floor` taking precedence over capacity |
| [`06-content-assembly.md`](06-content-assembly.md) | R-06-1 ~ R-06-5 (5 revisions): **the largest revision in this batch**, the Mode P / Mode D dual mode |
| [`07-review-gate.md`](07-review-gate.md) | R-07-1 ~ R-07-2 (2 revisions): the `profile_review` review kind, the 48h cooling-off period, `expedite` disabled under Mode P |
| [`08-delivery-tracking.md`](08-delivery-tracking.md) | R-08-1 ~ R-08-4 (4 revisions): splitting the Playwright decision, extending C4, employer-level throttling and SLA overrides, extending the state machine |
| [`09-analytics-feedback.md`](09-analytics-feedback.md) | R-09-1 (1 revision): the funnel accommodates Mode P, `inbound_from_talent_pool` |
| [`10-risk-compliance.md`](10-risk-compliance.md) | R-10-1 ~ R-10-5 (5 revisions): the ability test red line, repo leakage, the personal-data consequences of the talent pool, the source ledger |
| [`11-tech-stack-roadmap.md`](11-tech-stack-roadmap.md) | R-11-1 ~ R-11-6 (6 revisions): binding Phase 1 to an employer vertical, the hybrid data layer, the Phase 0 DoD and the remote ruling |
| [`99-gaps.md`](99-gaps.md) | Section 2 checks the status of each P0 gap, item by item |
| [`12-reference-career-ops.md`](12-reference-career-ops.md) | The source of F4; where the arguments for R-05-1/2/3 and R-11-2/5 come from |
| [`13-repo-layout.md`](13-repo-layout.md) | The substantive design behind R-02-1, R-10-2 and R-11-3 |
| [`14-browser-automation.md`](14-browser-automation.md) | The source of F3; where the arguments for R-08-1, R-11-4, Q-5 and Q-6 come from |
| [`15-target-tsmc.md`](15-target-tsmc.md) | The source of F1 and F2; where the arguments for R-06-1, R-04-1, R-08-4 and R-10-1 come from |

---

## Open Verification Items

The facts cited in this document fall into two classes. The first (the content and counts of TSMC's robots.txt and sitemap, the verbatim application process text, the path and version of the dedicated Chrome, the description in career-ops' README, and the original text of the sections of 00–11) was checked on the ground on 2026-09-16 and can be cited directly. Below are the items that are **not yet checked and that would change this document's conclusions**.

| # | Open verification item | Which revisions it affects | Verification method | What happens if the answer is no |
|---|---|---|---|---|
| V1 | Whether Avature profile update semantics are overwrite or versioned | R-06-1 consequence 2, R-06-2, Q-1 | The user creates an account **by hand** and logs into the dedicated Chrome, then observes how `ApplicationForm` behaves on a second application (without sending) | Mode P's reason to exist is still supported independently by F1 consequence 1, but when the R-06-2 snapshot fires has to change |
| V2 | Whether Avature and SuccessFactors (`ro.careers.tsmc.com`) share one candidate identity | R-03-1's `canonical_profile` primary key, Q-3 | Same as V1; check whether a login carries across the two sites | `canonical_profile` goes from "one per employer" to "one per ATS instance" |
| V3 | Whether the sitemap `<lastmod>` faithfully reflects changes to the JD body | R-04-1's incremental strategy, Q-4 | Fetch the sitemap for 7 consecutive days while hashing the full text of 20 URLs, and compare the agreement rate | The incremental strategy falls back to full-text hash comparison, and request volume goes from 1 back to 774 |
| V4 | Whether Playwright can point `channel` / `executable_path` at `App\Chrome-bin\chrome.exe` (153.0.8010.37), and whether that version is inside the supported range | R-08-1 decision B, R-11-4, Q-5 | See [`14-browser-automation.md`](14-browser-automation.md) | Decision B pulls in a second Chromium, the "remove LibreOffice" rationale weakens, and the selection should stay with `docxtpl` |
| V5 | Whether Playwright's `context.route()` can intercept sub-resource requests from a `file://` page | R-02-2's behavioral-layer constraint | A minimal template with an external `<img>`, a route handler attached, asserting the request is aborted | Fall back to a static template scan before rendering (rejecting non-relative-path resources), which is guaranteed to work but weaker |
| V6 | Whether Workday / 104 / 1111 are likewise the "single talent pool, résumé visible company-wide" mode | The generality of R-06-1 consequence 3, the value range of R-06-3's `ats_profile` | Run R-04-3's probe SOP against each platform and read their application instruction pages word by word | Mode P's applicability narrows to Avature/SuccessFactors, but the TSMC vertical is unaffected |
| V7 | Whether TSMC's `ApplicationForm` has a free-text cover letter field | Section 5 recommendation 2 (the new reason for deferring cover letters) | Check the form's field list during probing | If the field exists, the reason for deferring cover letters reverts to 06 §10's original one (verify the selection path first), and gets weaker |
| V8 | Whether a parseable confirmation email arrives after sending, and whether the `ApplicationConfirmation` page is reliably screenshottable | Q-7, D1's reconciliation under Mode P | Observe both on the first real send | Fall back to C4's existing "the human clicks I have sent it", explicitly admitting that it is a declaration, not reconciliation |
| V9 | Whether the postings on the Avature and SuccessFactors sites overlap | R-04-4's deduplication scenario D | Compare title + location across the two sites, sample of 20 | Scenario D does not exist and R-04-4 is withdrawn outright |
| V10 | The actual wording of `careers.tsmc.com`'s terms of use (not robots.txt) on automated access | R-04-1's `enabled: true`, R-10-4's ledger entry | Read the site's terms of service word by word in the sections on automated programs, crawlers, reproduction and database extraction, and copy the verbatim text and clause numbers into the ledger of document 10 | **This is the only item that could void R-04-1 in its entirety.** robots.txt permission is not ToS permission; where they conflict, ToS governs, and the source is downgraded to job alert email |

> **V10 outranks every other open verification item.** Core claim 8 of [`00-overview.md`](00-overview.md) defines "do not fight the platform" as a structural constraint written into the data tables, and by §2.1's rule `source_registry`'s `enabled: true` requires `verified_at` and `tos_note` to be in place at the same time. The example YAML in this document says `enabled: true`, but until V10 is done that should be `false`. This is an inconsistency of this document's own, deliberately left in place and flagged here rather than quietly corrected.
