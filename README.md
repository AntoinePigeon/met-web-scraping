# Met Art Pipeline

An end-to-end **ETL pipeline** that scrapes public-domain artwork data from The Metropolitan Museum of Art, cleans and standardizes it, validates it, and loads it into a PostgreSQL database.

Built as a data-engineering portfolio project: web scraping, messy-data wrangling, schema design, idempotent loading, and data-quality validation, all in one pipeline.

---

## What it does

- **Scrapes** artwork records from the Met's online collection using `requests` + `BeautifulSoup`, with a resilient fetch layer (retries, exponential backoff, rate-limit handling).
- **Caches** the raw extract to a JSON file so cleaning and loading can be re-run instantly, without re-hitting the Met.
- **Cleans and standardizes** messy, inconsistent real-world data: consolidates scattered creator fields, parses human-written dates and dual-unit dimension strings into proper typed columns.
- **Designs a schema** and loads the data into PostgreSQL using an **idempotent upsert**, so the pipeline is safe to run repeatedly.
- **Validates** every record through a quality gate before loading, isolating bad rows instead of crashing.
- **Logs** each run to a timestamped file for monitoring.

---

## Architecture

The pipeline follows a clean **Extract → Transform → Validate → Load** flow. Each stage is isolated, so a failure or change in one does not ripple into the others.

```
  EXTRACT            TRANSFORM           VALIDATE            LOAD
  (scrape)     ->    (clean/parse)  ->   (quality gate) ->  (upsert)
  requests           pandas              3 checks           PostgreSQL
  BeautifulSoup                          quarantine bad     idempotent
       |
       v
  raw_artworks.json  (cached raw extract)
```

The **Extract** stage is deliberately decoupled from the rest. It runs rarely and saves its output to `raw_artworks.json`. Every downstream stage reads from that file, so the slow, rate-limited scraping never blocks the fast, iterative cleaning work.

---

## Tech stack

| Layer | Tools |
|-------|-------|
| **Language** | Python 3 |
| **Scraping** | requests, BeautifulSoup |
| **Data cleaning** | pandas, regular expressions |
| **Database** | PostgreSQL, SQLAlchemy 2.0 (declarative models) |
| **Config / secrets** | python-dotenv (environment variables) |
| **Monitoring** | Python `logging` (file + console) |

---

## Key engineering decisions

The interesting part of this project is not the scraping itself, but the decisions that make it reliable and safe to re-run.

**Idempotent loading.** The load uses PostgreSQL's `INSERT ... ON CONFLICT DO UPDATE`. Running the pipeline once inserts the rows; running it again updates existing rows and inserts new ones. Nothing duplicates, nothing crashes. This is what makes the pipeline safe to schedule.

**Resilient scraping.** A single `fetch()` helper wraps every request with retry logic and **exponential backoff**. When the server rate-limits (`429`), the scraper waits (honoring the `Retry-After` header when present) and retries with a growing delay, instead of failing. A `404` is handled separately, since retrying a page that does not exist is pointless.

**Cached raw extract.** The raw scrape is saved to `raw_artworks.json` and committed to the repo. This means anyone can clone the project and run the full transform/load pipeline **without scraping the Met at all**. It is polite to the source and makes the project instantly reproducible.

**Consolidating messy creator data.** The Met labels the creator of an object differently depending on its type (Artist, Maker, Manufacturer, Designer, Architect, and more). No single field is complete. The pipeline **coalesces** these into one clean `maker` column, taking the first available value per record.

**Choosing the easier data to parse.** Dimensions are published in both inches (with fractions) and centimeters (clean decimals). The parser targets the **centimeter** values, avoiding fraction math entirely, and extracts height, width, and depth into separate numeric columns.

**Schema designed for the data, not guessed.** Column types and nullability were set by inspecting the real data (which fields are always present, which are sparse), not by assumption. Free-text fields use `TEXT` (no arbitrary length caps that would break on wordier records). The primary key is the Met's own `objectID`, which is stable and matches their official API.

---

## Data cleaning highlights

Real museum data is inconsistent. A few examples of what the pipeline handles:

- **Dates** like `begun 1795`, `1640–80`, and `ca. 1914–15` are parsed into a queryable integer `year_start` using regex.
- **Dimensions** like `44 3/4 x 23 1/2 x 15 3/4 in. (113.7 x 59.7 x 40 cm)` become three numeric columns (`height_cm`, `width_cm`, `depth_cm`). Two-dimensional objects (paintings) correctly leave depth null.
- **Unicode lookalikes** are normalized (the multiplication sign `×` and the letter `x` are visually identical but different characters, and both appear in the source).
- **Raw source columns are preserved** alongside the parsed ones, so parsing logic can be improved later without re-scraping.

---

## Data quality validation

Before loading, every record passes through a validation gate that runs three checks:

1. **Required fields** are present (the non-nullable columns).
2. **Year sanity**: `year_start` falls within a believable range.
3. **Dimension sanity**: any measurement present is positive and physically plausible.

Records that fail are **isolated and logged**, not dropped silently and not allowed to crash the run. The clean records load; the bad ones are reported. This "quarantine, don't crash" approach is what lets a pipeline keep running unattended.

---

## Project structure

```
met-web-scraping/
├── main.py               # the full pipeline (scrape, clean, validate, load)
├── data/
│   └── raw_artworks.json # cached raw extract (committed for reproducibility)
├── .env                  # DATABASE_URL (not committed)
├── .env.example          # template showing required variables
├── requirements.txt
├── pipeline.log          # run logs (not committed)
└── README.md
└── test-connection.py    # test the connection to the Met website
```

---

## Getting started

**1. Clone the repo**

```bash
git clone https://github.com/AntoinePigeon/met-web-scraping.git
cd met-web-scraping
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Set up PostgreSQL**

Create a local database:

```bash
createdb met_art
```

Then copy the example environment file and fill in your connection string:

```bash
cp .env.example .env
```

`.env` should contain:

```
DATABASE_URL=postgresql+psycopg2://YOUR_USER@localhost:5432/met_art
```

**5. Run the pipeline**

```bash
python main.py
```

The table creates itself on first run, and the pipeline loads from the cached `raw_artworks.json`, so **no scraping is required** to see it work end to end. The scraping stage is included in the code and can be re-enabled to refresh the data.

---

## Data source and legal note

Data comes from **The Metropolitan Museum of Art's** online collection. The Met publishes this collection data under a **Creative Commons Zero (CC0)** public-domain dedication, so it is free to use, store, and share.

The scraper respects the site's `robots.txt` (including its crawl-delay), identifies itself with a normal User-Agent, and paces its requests. Only public, non-personal, factual object data is collected.

---

## What I learned

This project took me from "I can scrape a page" to "I can build a pipeline that survives real-world conditions." Key concepts:

- **ETL architecture** and why decoupling extract from transform matters
- **Resilient networking**: retries, exponential backoff, and reading rate-limit signals
- **Idempotent pipelines**: designing a load that is safe to run repeatedly (`ON CONFLICT DO UPDATE`)
- **Real messy-data wrangling**: coalescing fields, regex parsing, Unicode normalization, and preserving raw source data
- **Schema design** driven by inspecting real data, with SQLAlchemy 2.0 declarative models
- **Data-quality validation** that isolates bad records instead of failing
- **Production hygiene**: environment-based secrets, logging, and reproducibility

---

## Future work

- Split the single script into modules (`scraper.py`, `transform.py`, `database.py`, `validate.py`, `main.py`)
- Schedule the pipeline (cron, GitHub Actions, or AWS Lambda + EventBridge)
- Add a `pytest` suite for the transform and validation logic
- Normalize creators into a separate `artists` table
- Compare scraped values against the Met's official Open Access API as a ground-truth check

---

## License

This project is for personal and educational use. The underlying artwork data is public domain (CC0), courtesy of The Metropolitan Museum of Art.
