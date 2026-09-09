# Met Art API: Project Log

A running record of decisions, findings, and reasoning for the Met Art API project.
Kept alongside the code so the *why* survives as well as the *what*.

**Repo:** [AntoinePigeon/met-web-scraping](https://github.com/AntoinePigeon/met-web-scraping)
**Last updated:** 2026-09-04

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
| 4 | Bulk load 248,325 rows | Next |
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

### Known broken on `main`

`ArtworkResponse` still references `object_id` and `maker`. `transform.py` and `database.py`
still write `curatorial_department` and `geography`.

**A schema change was merged without the dependent code.** This violates "main is always
deployable" and is recorded here rather than quietly fixed, because it is the failure mode that
makes schema changes frightening in real systems. The two standard defences are keeping the
whole change on one branch until every piece works, or making schema changes
backward-compatible so old code keeps running during the transition.

### Documentation gap

The `404` shows as `Undocumented` in Swagger. FastAPI generates the schema from the decorator
and cannot know about an exception raised at runtime. To be addressed with the rest of the
status-code work in Milestone 5.

---

## 8. Next steps

**Immediate:** branch `fix/api-schema-alignment`. Update `ArtworkResponse` to the contract
fields, and decide deliberately which of the 32 columns belong in a response. Not all of them.
Six location columns will be ~80% null and six artist columns will be pipe-delimited strings.
The table stores everything; the response is a choice.

**Milestone 4:** extract adapter for the CSV, transform (type casts, dimension parsing,
empty-string normalisation), the validation gate, and the bulk load.

The current loader does `INSERT ... ON CONFLICT DO UPDATE` row by row through the ORM. At 126
rows that is instant. At 248,325 it will be unusably slow: one round trip plus ORM object
construction per row. Three techniques to evaluate, in increasing order of speed and decreasing
order of convenience: batched inserts, SQLAlchemy Core instead of the ORM, and Postgres `COPY`.

**Get correctness first on a small slice, measure, then optimise.** The naive approach being
correct but a thousand times too slow is the most common shape of performance problem, and
picking a technique before running the load once is how this milestone eats a week.

---

## 9. Working principles established

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

### Recurring traps

- **Working directory and `__file__` path resolution.** Hit five times. Moving a file changes the meaning of every self-relative path inside it.
- **`python file.py` vs `python -m package.module`.** The first puts the *script's* directory on `sys.path`, the second puts the *current working directory* there. Once a project has packages, module mode is the only consistent invocation.
- **Forgetting to activate `.venv`.** macOS ships no `python` command, only `python3`, so `command not found: python` is a reliable tell.
- **Confusing the SQLAlchemy model with the Pydantic model.** Made twice. Fixed structurally by naming (`Artworks` vs `ArtworkResponse`) rather than by resolving to be more careful.

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

## 10. Deployment

Undecided, deferred to Milestone 11. Preference is free or very cheap.

The decision has two halves that are often conflated: **hosting the app** (cheap or free in many
places) and **hosting a persistent database** (where free tiers expire, sleep, or wipe). A common
pattern for this situation is a free app host plus a separately managed Postgres free tier, so
the two failure modes are decoupled.

Because a free-tier database may be wiped, the pipeline being idempotent and fully reproducible
from committed source data is a real asset rather than a nicety.

---

## 11. README obligations

Carried from the original project plan, to be satisfied before this is considered done:

- An architecture diagram
- An "index choices and why" section
- `EXPLAIN` output for one query, before and after adding an index
- One-command run instructions
- The selection-bias finding, stated as a measured result
- The quarantine rate and its error taxonomy
- A note that `Classification` is 100% null for American Wing objects
