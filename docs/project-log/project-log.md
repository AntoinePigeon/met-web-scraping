# Met Art API: Project Log

A running record of decisions, findings, and reasoning for the Met Art API project.
Kept alongside the code so the *why* survives as well as the *what*.

**Repo:** [AntoinePigeon/met-web-scraping](https://github.com/AntoinePigeon/met-web-scraping)
**Last updated:** 2026-09-11

---

## 1. What this project is

An end-to-end data engineering vertical slice:

```
scraper / bulk CSV  ->  ETL pipeline  ->  PostgreSQL  ->  FastAPI  ->  Docker  ->  CI  ->  deploy
```

The API is not the interesting part on its own. The interesting part is that it is fed by a
real pipeline over real, messy, public-domain museum data, and that every schema and design
decision below was driven by measurement rather than assumption.

**Portfolio goal:** a live, documented, containerised API with interactive OpenAPI docs that
someone can open, query, and get real data back from.

### Stack

Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PostgreSQL, Docker, docker-compose,
pytest, GitHub Actions.

### Planned endpoints

| Endpoint | Notes |
|---|---|
| `GET /health` | Liveness plus a real database check |
| `GET /artworks/{id}` | Single record |
| `GET /artworks` | Pagination, filtering by artist / year range / medium |
| `GET /stats/by-century` | Raw SQL, window functions |
| `GET /stats/by-maker` | Raw SQL, window functions |
| `POST /admin/refresh` | API-key protected, triggers the pipeline |

### Explicit anti-goals

- No blanket `async`. Use it where there is real I/O concurrency and be able to justify it.
- No `create_all()` as a schema strategy. Migrations, properly.
- Not everything through the ORM. At least three hand-written analytical queries.
- Not another CRUD app. The pipeline underneath is the story.

---

## 2. Milestone status

| # | Milestone | Status |
|---|---|---|
| 0 | Data inventory and extract contract | Done |
| 1 | First FastAPI endpoint, `/docs` renders | Done |
| 2 | Pydantic response model, real DB read | Done |
| 3 | Alembic migrations | Done |
| 4 | Bulk load 248,325 rows | Next | In progress
| 5 | REST design: pagination, filtering, status codes, versioning | |
| 6 | Raw SQL analytics, `EXPLAIN ANALYZE`, index choices | |
| 7 | Auth: API key, then JWT | |
| 8 | Async where it is justified | |
| 9 | Structured logging, real `/health` | |
| 10 | Integration tests against a containerised Postgres | |
| 11 | Docker, deploy, README | |

**Milestones 3 and 5 were deliberately swapped.** Pagination over 126 rows demonstrates
nothing, and index experiments on a table that fits in a handful of pages will not even use
the index. Milestone 0 also produced concrete schema changes that made Alembic worth doing
immediately rather than as an abstract exercise. Sequencing follows evidence.

**Milestone 4 progress:** the API response model and the validation gate are done. The extract
adapter, transform, and load remain.

---

## 3. Data source decision

Three possible extract paths were evaluated before writing any loading code.

| Source | Cost to fetch | Freshness | Field depth | Fragility |
|---|---|---|---|---|
| **Bulk CSV** | 1 request, whole collection | Periodic snapshot | Wide, flat | Low |
| **Open Access API** | 1 request *per object* | Live | Widest, structured | Low |
| **Original scraper** | 1 request per results page | Live | Narrowest | High |

These are not three ways to do the same job. They run at different times for different reasons:

- **CSV is the backfill.** One request, 484,956 rows. This is how the database gets populated.
- **API is the incremental refresh.** Fetch single objects by ID. This is what `POST /admin/refresh` will use. Never used to load the full collection, which would be 484,956 HTTP requests.
- **Scraper is the validation source.** Scrape a small sample, pull the same objects from the other two, diff them, report drift.

**Decision:** build the CSV path only for now. API and scraper adapters come later as separate
milestones, and both must produce the shape defined in `docs/extract-contract.md`.

### A concurrency problem worth noting

The Met's API asks callers to stay under 80 requests per second. A sequential Python loop
manages maybe 5 to 20. Pulling any meaningful number of objects through the API is therefore a
genuine, non-contrived I/O-bound concurrency problem, and it is the justification for `async`
in Milestone 8. The plan is to run a fixed batch sequentially, then concurrently with a rate
limiter, and publish both wall-clock times.

---

## 4. Milestone 0 findings

All figures below were produced by `scripts/explore_csv.py` against the full 303MB dump.

### 4.1 Selection bias, measured

The original scrape walked pages 1 to 3 of a relevance-sorted American Wing search, giving 126
records. The bulk dump contains an `Is Highlight` flag, which allowed the sampling frame to be
tested directly.

| Population | Highlight rate |
|---|---|
| Whole collection (484,956) | 0.57% |
| American Wing (18,532) | 2.34% |
| Original 126 scraped rows | **57.1%** |

The sample is roughly **24x enriched** in highlighted works relative to its own department, and
about **100x** relative to the museum. Record completeness was correspondingly inflated: 11%
missing artist names in the sample against 35% across the wing.

Separately, the American Wing is itself about **4x more highlighted** than the museum average.
That is a fact about curation, not about the scraper.

### 4.2 Bias is dimension-specific

The same sample was checked on a second dimension:

| Century | Sample (126) | American Wing (18,532) |
|---|---|---|
| 1800s | 59.5% | 57.2% |
| 1700s | 17.5% | 25.7% |
| 1900s | 16.7% | 11.9% |
| 1600s | 5.5% | 4.6% |

Within about 2.3 points on the largest bucket. **The same sample is badly biased on one
dimension and roughly representative on another.**

The honest claim is therefore not "the sample was biased." It is: the scrape over-sampled
highlighted works by roughly 24x and understated missingness threefold, but its temporal
distribution tracked the population closely. **Selection bias must be characterised per field,
not globally.**

### 4.3 Column profiling

| Finding | Consequence |
|---|---|
| `Medium`: 3,776 distinct in the wing, top 20 cover 45.8% | Substring search, not a dropdown |
| Exact match on `Glass` returns 150 objects; substring `glass` returns 872 in the top 20 alone | Measured justification for substring filtering |
| `Object Name`: 1,441 distinct in the wing but **28,631** museum-wide | Re-measure after any scope change |
| `Classification`: 16% null museum-wide, **100% null in the American Wing** | Real finding, not a load bug. Must be documented for consumers |
| 79.8% of the collection has **all seven** geography columns empty | Geography cannot be a headline filter. Keep it, document the coverage |
| **10.17%** of objects have pipe-delimited multiple artists across six parallel columns | A one-to-many relationship the CSV could not express |
| `Object Number`: **3,300 duplicates**, max length **53** | The existing `VARCHAR(32) UNIQUE` schema was wrong on both counts |
| `AccessionYear` read as `object` dtype | Caused by exactly **two rows** holding full ISO dates instead of years |

### 4.4 Date anomalies

`Object Begin Date` spans **-400,000 to 5,000**. Both extremes were inspected individually.

- **-400,000 is correct data.** A Lower Paleolithic hand axe, with `Object Date` reading `ca. 400,000-240,000 B.C.` and a matching end date. Quarantining it would discard the museum's oldest holdings.
- **5,000 is a real error.** A bell with begin 5000, end 1, and display text reading `ancient?`. Almost certainly a missing negative sign.

This produced a better validation rule than any arbitrary year bound:

```
year_start <= year_end
```

An **internal consistency check** rather than an external plausibility bound. It passes the hand
axe and catches the bell, and it requires no assumption about what dates are believable.

**147 rows fail it (0.059% of 248,472). 116 of those are Egyptian Art**, where BCE dating
conventions break down. Five distinct error classes were identified: transposition, century
number written instead of the year, missing BCE sign, wrong field entirely, and zero as a
sentinel. Only the first is mechanically fixable.

**Decision: quarantine all 147.** Correcting classes 2 to 5 requires interpreting free text,
and publishing values that differ from the Met's would make this API silently disagree with its
authoritative source.

### 4.5 Row count

```
484,956  ->  public domain filter  ->  248,472  ->  year rules  ->  248,325
```

---

## 5. The extract contract

`docs/extract-contract.md` is committed and defines 32 fields with name, type, source column,
nullability, and notes.

Its header states that v1 defines the CSV mapping, and that API and scraper adapters must
produce the same field names and types with their own mappings documented separately. That
framing is deliberate: **a document describing one implementation is documentation, a document
that constrains all future implementations is an interface.**

### Architectural decision: normalise at the boundary

Each extract source normalises to a common shape before handing off. `transform.py` never
learns which source ran.

This mirrors a pattern already used in the `aws-cost-report` project, where the analysis code
receives a fixed `date / service / cost` shape and does not care whether it came from generated
test data or from live AWS. The Met calls a field `artistDisplayName`. That is their vocabulary,
and it should die at the boundary.

### Deferred: artist normalisation

10.17% of objects have multiple artists packed into pipe-delimited strings across six columns.
That is a one-to-many relationship the source system could not express in a flat CSV format.

**Decision: build the flat table first**, preserving the pipe-delimited columns as raw source
data, then normalise into an `artists` table plus a link table as a later Alembic migration.
Shipping flat and then normalising in a migration is what real systems do, and it is a better
story than pretending the schema was right first try.

---

## 6. Schema history

Three migrations, all verified in both directions with an empty autogenerate drift check.

### Migration 1: create `artworks`

Captures the schema as it existed, including the two things already known to be wrong. The
point of a migration history is that the before state is recorded, not silently corrected.

### Migration 2: widen `object_number`, drop UNIQUE

| Change | Driven by |
|---|---|
| `VARCHAR(32)` to `TEXT` | Max observed length is 53 |
| Drop UNIQUE constraint | 3,300 duplicates at full scale |

**This migration's downgrade is not safely reversible once real data is loaded**, for two
independent reasons: narrowing to `VARCHAR(32)` fails on 53-character values, and recreating
the UNIQUE constraint fails on 3,300 duplicates.

The downgrade currently succeeds against the 126-row sample. That is not evidence it is safe.
It means the current data happens not to trigger either failure. **"Works today" and "correct in
general" are different claims**, and the distinction is recorded in the migration file itself.

### Migration 3: align schema with the extract contract

- **Four renames:** `object_id` to `id`, `object_number` to `number`, `maker` to `artist_name`, `curatorial_department` to `department`
- **One drop:** `geography`
- **Eighteen adds:** `highlight`, `classification`, `name`, `year_end`, six artist fields, six location fields, `rights`, `link`, `accession_year`

**Autogenerate cannot detect renames.** It sees a dropped column and an added column, which is
an identical diff to a drop-plus-add but destroys the data. All four renames had to be
hand-collapsed from generated pairs into single `op.alter_column(..., new_column_name=...)`
calls. This is the reason generated migrations are read line by line rather than skimmed.

**Three columns needed to be `NOT NULL` on a table that already held 126 rows**, which Postgres
refuses in a single step. Handled with the standard pattern:

```
add nullable  ->  backfill with op.execute()  ->  enforce NOT NULL
```

| Column | Backfill |
|---|---|
| `highlight` | `server_default=sa.false()`, default dropped afterwards so the column matches the model |
| `link` | Computed by concatenating the Met's fixed URL prefix with `id` |
| `year_end` | Copied from `year_start`, matching the Met's own single-year convention |

**A backfill value must be derivable from data already held, or be an honest statement about
absence.** The first draft of this migration carried Alembic's tutorial default,
`server_default='active'`, on all three. On the integer columns it would have crashed. On `link`
it would have **succeeded**, filling every row with the literal string `active` as its URL. A
migration that fails loudly is recoverable. One that writes plausible garbage and reports
success is not.

### Ordering

Statement order inside `upgrade()` matters. The `link` backfill references `id`, so the renames
must run before the `UPDATE`. Downgrades reverse the upgrade sequence: drop new columns first,
then reverse renames, then restore what was dropped.

### The drift check

```bash
alembic revision --autogenerate -m "drift check"
```

If the generated `upgrade()` is empty, the model and the database agree exactly. Delete the file
afterwards. **Three sources of truth (model, migrations, contract) is zero sources of truth**,
and this ten-second check makes disagreement visible before it compounds.

---

## 7. API state

Working:

- `GET /health` returns `{"status": "ok"}`
- `GET /artworks/{object_id}` returns 200 with a real record, or 404 with `{"detail": "Artwork not found"}`
- `/docs` renders a real response schema

Patterns in use:

- `Session.get()` for primary key lookups (SQLAlchemy 2.0, not legacy `Model.query`)
- `Depends(get_db)` with a `try` / `finally` generator, guaranteeing the session closes even if the endpoint raises
- `ConfigDict(from_attributes=True)` so Pydantic can read ORM object attributes
- `HTTPException` raised, not an error dict returned. A 200 carrying an error body breaks every client that reads status codes

### The response model: 32 columns to 20 fields

`ArtworkResponse` was realigned to the contract on `fix/api-schema-alignment`, and narrowed
deliberately rather than mirroring the table.

**The asymmetry runs in opposite directions at the two layers.** The table captures wide,
because a column not captured requires re-extracting 484,956 rows. The response exposes narrow,
because every field published is a commitment that cannot be withdrawn without a version bump.
Adding a field later is free and backward-compatible.

| Excluded | Reason |
|---|---|
| Six location columns | 79.8% of the collection has all seven geography fields empty, and `department` plus `culture` already carry the geographic signal |
| Five artist columns | 10.17% of objects pack multiple artists into pipe-delimited strings across six parallel columns. Publishing them pushes an unparseable burden onto every consumer |
| `rights` | 248,471 of 248,472 rows are null. Effectively absent, not constant. The initial reading was "one constant value" and was wrong, though the resulting action was the same |
| `accession_year` | Does not help a reader understand the object, and `credit_line` usually carries it |

**Kept deliberately:** `dimensions` and `date`, the Met's raw display strings, alongside the
parsed numeric columns. The parser discards information a human reader needs. `ca. 1914–15`
becomes 1914 and 1915, and publishing 1914 alone is false precision about a date the museum
itself marked uncertain.

The first criterion used for these two was "hard to filter on," which was wrong. **Filtering
happens in SQL against table columns, before serialisation, whether or not a field appears in
the response.** The correct question is what the parsed version loses.

### A backfill publishing plausible wrong data

Object 632 (a Wistarburgh bottle) returns:
"date": "1738–ca. 1777"
"year_start": 1738
"year_end": 1738

The Met says 1738 to roughly 1777. The API says 1738. `year_end` came from migration 3's
backfill, which copied `year_start` into a new `NOT NULL` column because the old scraper never
captured an end date.

**This is not missing data, it is wrong data, and nothing in the response marks it as
synthetic.** A consumer filtering `year_start <= 1750 AND year_end >= 1770` would not find this
bottle and would have no way to know why. The 126 rows are replaced by the CSV load, but the
general problem stands: a backfilled value and a real one are indistinguishable downstream.

This is the same failure the `link` backfill would have caused had `server_default='active'`
survived. **A migration that fails loudly is recoverable. One that writes plausible garbage and
reports success is not.**

### Still broken on `main`

`pipeline/transform.py` and `pipeline/database.py` still write `curatorial_department` and
`geography`. Left intentionally, since both files are rewritten by the extract and transform
work. `main` is not fully deployable until then.

### Documentation gap

The `404` shows as `Undocumented` in Swagger. FastAPI generates the schema from the decorator
and cannot know about an exception raised at runtime. To be addressed with the rest of the
status-code work in Milestone 5.

---

## 8. The validation gate, measured

`pipeline/validate.py` was written against the original 126 American Wing rows. Before extending
it to 248,472, every rule in it was measured against the full dump as a pandas mask, and the
rejection count recorded beside the rule in code.

**Rules were measured, not reviewed.** A boolean mask over the DataFrame answers "what would this
rule reject?" in seconds, without the adapter existing. Whatever survived that scrutiny was
written into the gate.

### The rule that would have deleted a third of the museum

```python
if record["year_start"] < 1500: ...
```

**84,365 rows fail it. 33.9% of the public-domain set.** Measured 2026-09-10.

| Department | Rows below 1500 |
|---|---|
| Greek and Roman Art | 29,864 |
| Egyptian Art | 12,268 |
| Islamic Art | 9,842 |
| Asian Art | 7,680 |
| Medieval Art | 6,382 |
| Ancient Near Eastern Art | 6,184 |
| Arts of Africa, Oceania, and the Americas | 5,568 |
| The Cloisters | 1,969 |

This is not a rule with a high rejection rate. **It deletes entire departments.** These are the
Met's core holdings, not data errors.

The bound was never correct even for its stated scope: **the American Wing itself has 14 rows
below 1500**, and the original 126 happened to contain none of them. The rule was correct for
the *sample*, which is a smaller and more accidental thing than the department.

This is the Milestone 0 selection-bias finding appearing in a second place. Section 4.1 measured
bias in what the sample said about the data. This is bias in **what the sample permitted the
rules to assume**. Deleted.

### Century sentinels are a source convention, not an error

`Object End Date` above 2000 returns 20 rows. All are plausible restoration or contemporary
dates except two:

| Value | `Object Date` | `year_start` | Reading |
|---|---|---|---|
| 2870 | `1850–70` | 1850 | Typo for 1870 |
| 2099 | `Modern` | 1950 | Century sentinel for an open-ended work |

Checking the pattern confirms it. **6,983 rows with `year_end` 1899 read "19th century". 278 rows
at 1999 read "20th century".** The Met encodes an open interval by ending it at the century
boundary.

**Both wrong-looking rows pass the `year_start <= year_end` consistency check**, because 2870
follows 1850 perfectly well. This is the structural blind spot of a consistency rule: it cannot
catch an error that lands inside the range the other field permits. The check remains correct and
is now known to be incomplete.

**Decision: add `year_end <= current_year`, quarantining both.** 2099 is a known false positive,
documented rather than carved out. One conventionally-correct row in 248,325 is an acceptable
cost, and a bound expressed as an exception list for a pattern observed once (n=1 at 2099) would
be weaker than the plain rule.

### Required fields

Seven contract columns are `NOT NULL`. All seven return **zero nulls**, in the public-domain set
and in the full 484,956. Measured 2026-09-10.

`id`, `number`, `highlight`, `department`, `year_start`, `year_end`, `link`

**A rule that rejects nothing is still a result**, provided the zero is known rather than
assumed. The rules stay, so a malformed record from a future adapter is quarantined instead of
crashing the load.

One caveat: these counts depend on `read_csv(na_values=["", " ", "N/A", "-"])` in the
exploration script. **The normalisation lives in the reader, not in the data.** The extract
adapter has to make the same promise, or the gate will be validating something with different
assumptions than the ones measured here.

### Dimension bounds: a known-unknown

The original check asserted `0 < value <= 2000` cm. **It cannot be measured pre-transform**,
because `height_cm`, `width_cm` and `depth_cm` do not exist in the source. Only the `Dimensions`
display string does.

The 2000 cm ceiling was set against 126 American Wing objects. The Met holds the Temple of
Dendur. Commented out with a `TODO` and re-measured once the transform runs at scale.

### Gate design

`check_record` returns a list of error strings rather than a boolean, and `validate_records`
returns `(valid, invalid)` with the identifier attached to each failure. A boolean cannot produce
the five-class error taxonomy the README owes.

Two bugs found during the rewrite, both on the **error-handling path**:

- The null guard covered `year_start` but not `year_end`, so a null end date raised `TypeError`
  instead of quarantining. Check 1 appends an error and continues, so later checks do run on
  records already known to be broken.
- The quarantine report indexed `rec["id"]` directly, crashing on exactly the record Check 1 had
  just flagged as missing `id`. Fixed, then reintroduced one key over with `rec["number"]`.

**The same bug appeared in three places across three passes.** Unstructured null handling makes
every access point an independent decision, so fixing one teaches nothing about the others. The
structural answer is to make absence impossible past a boundary rather than to guard everywhere.

### Tooling

The repo is now an installable project: `pyproject.toml` declaring `api` and `pipeline` as
packages, `pip install -e .`, and Ruff configured with `E`, `F`, `I`.

This closed the `ModuleNotFoundError` trap, hit three times in one session through three
different surfaces: the uvicorn invocation, bare `pytest`, and the VS Code play button. **Same
`sys.path` rule each time.** Declaring the project once removes the need to remember the right
invocation, which is the same problem `WORKDIR` and `pip install .` solve in a container.

`tests/test_validate.py` was asserting on the string `"out of range"`, which the rewritten gate
never produces. **A suite testing deleted rules is worse than no suite**, because it fails and
sends you to the wrong file. Rewritten to cover all four active rules plus the happy path.

---

## 9. Next steps

**Done:** the API response model (`fix/api-schema-alignment`) and the validation gate
(`feat/validation-rules`).

**Immediate:** branch `feat/csv-extract-adapter`. Read `MetObjects.txt`, produce the shape
defined in `docs/extract-contract.md`, prove it on a slice of a few hundred rows. Re-read the
contract first: it was written at Milestone 0, before the century sentinels, before the 1500
bound was deleted, and before the response model narrowed to 20 fields.

The empty-string normalisation currently lives in a `read_csv` call in the exploration script.
The adapter must carry the same guarantee, or the required-field counts above do not apply to
what the gate actually sees.

**Then:** transform (type casts, dimension parsing, empty-string normalisation), and the bulk
load.

The current loader does `INSERT ... ON CONFLICT DO UPDATE` row by row through the ORM. At 126
rows that is instant. At 248,325 it will be unusably slow: one round trip plus ORM object
construction per row. Three techniques to evaluate, in increasing order of speed and decreasing
order of convenience: batched inserts, SQLAlchemy Core instead of the ORM, and Postgres `COPY`.

**Get correctness first on a small slice, measure, then optimise.** The naive approach being
correct but a thousand times too slow is the most common shape of performance problem, and
picking a technique before running the load once is how this milestone eats a week.

---

## 10. Working principles established

**Verify before fixing.** Confirm a hypothesis with a print or a query before changing code.
Several times this session the first hypothesis was wrong and the check cost ten seconds.

**Inspect before processing.** `ls -lh`, `file`, `head`, `wc -l` before loading anything. Note
that `wc -l` returned 612,687 for a file with 484,956 rows: the difference is newlines inside
quoted fields, and reporting a row count from `wc -l` on a quoted CSV would have been wrong.

**Check the denominator.** Two rate errors this session came from dividing by the wrong
population. "11.32% of what?" has an answer, and it was the wrong population.

**Rates, not counts,** when comparing populations of different sizes.

**Test failure paths deliberately**, and test the rollback, not just the migration.

**Read tracebacks bottom-up**, and skip framework frames to find your own code. A 60-line
traceback usually has three lines of signal.

**Timebox investigations.** A documented known-unknown is a professional outcome. The CSV
parser bug (valid input, C parser defect with `usecols` plus embedded newlines) was diagnosed,
worked around with `engine="python"`, documented, and closed.

**Know when a document is finished.** The extract contract took five review passes with
diminishing returns. It crossed the "good enough to build on" line two revisions before the
last one.

**Validate the validators.** Every rule in a data-quality gate carries a measured rejection count
and the date it was measured. A rule without one is a guess promoted to policy by the fact that
it is in the codebase. A rule that quarantines a whole category is not catching errors, it is
expressing an assumption about scope.

**State the finding in words before acting on it.** The `rights` column was read as "one constant
value" when it was actually "empty except for one row." Opposite facts, identical action, and
nothing about the correct outcome signalled that the reasoning had failed. Being right by
accident is indistinguishable from being right until the next decision resting on the same fact.

**Presence and validity are separate questions.** `NOT NULL` is justified by zero nulls. It says
nothing about whether the values are correct. The same split appears in Pydantic as `str | None`
versus `= None`, and in pandas as the fact that a null can never fail a comparison, only an
explicit `.isna()`.

**Test failure paths, and read the response body field by field.** Object 632's wrong `year_end`
would pass a status-code test and a schema-validation test. The bug lives in the gap between "the
shape is correct" and "the values are true," which is where most real data incidents happen.

### Recurring traps

- **Working directory and `__file__` path resolution.** Hit five times. Moving a file changes the meaning of every self-relative path inside it.
- **`python file.py` vs `python -m package.module`.** The first puts the *script's* directory on `sys.path`, the second puts the *current working directory* there. Once a project has packages, module mode is the only consistent invocation.
- **Forgetting to activate `.venv`.** macOS ships no `python` command, only `python3`, so `command not found: python` is a reliable tell.
- **Confusing the SQLAlchemy model with the Pydantic model.** Made twice. Fixed structurally by naming (`Artworks` vs `ArtworkResponse`) rather than by resolving to be more careful.
- **Partial defensive coding.** A null guard applied to one operand of a comparison. The guard that *was* written creates confidence the case is handled, so reviewers skim past it.

### Environment

New Apple Silicon Mac mini, migrated from an Intel iMac. Every virtual environment broke
(`incompatible architecture (have 'x86_64', need 'arm64')`), Homebrew moved from `/usr/local` to
`/opt/homebrew`, Postgres had to be reinstalled, and one repo lost its `.git` folder entirely in
the file copy and was recovered by cloning from GitHub.

**Everything that survived was in git. Everything at risk was not.** Source, templates and
committed uploads came through fine. Local databases, `.env` files, and one uncommitted script
did not.

This is the motivating experience for Docker. A `docker-compose.yml` declaring Postgres would
have eliminated every hour of that debugging, and by Milestone 11 each line of it will be
solving a problem already met by hand.

---

## 11. Deployment

Undecided, deferred to Milestone 11. Preference is free or very cheap.

The decision has two halves that are often conflated: **hosting the app** (cheap or free in many
places) and **hosting a persistent database** (where free tiers expire, sleep, or wipe). A common
pattern for this situation is a free app host plus a separately managed Postgres free tier, so
the two failure modes are decoupled.

Because a free-tier database may be wiped, the pipeline being idempotent and fully reproducible
from committed source data is a real asset rather than a nicety.

---

## 12. README obligations

Carried from the original project plan, to be satisfied before this is considered done:

- An architecture diagram
- An "index choices and why" section
- `EXPLAIN` output for one query, before and after adding an index
- One-command run instructions
- The selection-bias finding, stated as a measured result
- The quarantine rate and its error taxonomy
- A note that `Classification` is 100% null for American Wing objects
- The 1500-bound finding: a validation rule that would have quarantined 33.9% of the collection, with the department breakdown
- The century-sentinel convention (1899 / 1999 / 2099) and the decision to quarantine 2099 as a known false positive
- Why the response model exposes 20 of 32 columns, and why `dimensions` and `date` are kept as strings alongside the parsed values
