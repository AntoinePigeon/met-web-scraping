# Contract V1

Last updated: 2026-08-21

**v1 defines the CSV mapping. API and scraper adapters must produce these field names and types; their mappings are documented separately.**

---

| Field | Type | Source column | Nullable | Notes |
|---|---|---|---|---|
| id | INTEGER | Object ID | No | Primary key |
| highlight | BOOLEAN | Is Highlight | No | Cast from "True"/"False" |
| department | TEXT | Department | No | |
| title | TEXT | Title | Yes | |
| culture | TEXT | Culture | Yes | |
| medium | TEXT | Medium | Yes | Substring search with a trigram index. |
| classification | TEXT | Classification | Yes | General category of the object. It is 16% null overall but 100% null in the American Wing. |
| dimensions | TEXT | Dimensions | Yes | Raw source string. Parsed into height_cm, width_cm, depth_cm. |
| height_cm | FLOAT | Dimensions | Yes | Extract from dimensions |
| width_cm | FLOAT | Dimensions | Yes | Extract from dimensions |
| depth_cm | FLOAT | Dimensions | Yes | Extract from dimensions |
| number | TEXT | Object Number | No | 3,300 duplicates at full scale. The existing UNIQUE constraint must be dropped. |
| name | TEXT | Object Name | Yes | Describes what the object is (Vase, Side Chair, Teapot). 28,631 distinct at full scale, so substring search rather than a dropdown. |
| date | TEXT | Object Date | Yes | |
| year_start | INTEGER | Object Begin Date | No | Zero nulls |
| year_end | INTEGER | Object End Date | No | Zero nulls |
| artist_name | TEXT | Artist Display Name | Yes | |
| artist_role | TEXT | Artist Role | Yes | |
| artist_bio | TEXT | Artist Display Bio | Yes | |
| artist_nationality | TEXT | Artist Nationality | Yes | |
| artist_birth | TEXT | Artist Begin Date | Yes | |
| artist_death | TEXT | Artist End Date | Yes | |
| credit_line | TEXT | Credit Line | Yes | |
| city | TEXT | City | Yes | |
| state | TEXT | State | Yes | |
| county | TEXT | County | Yes | |
| country | TEXT | Country | Yes | |
| region | TEXT | Region | Yes | |
| subregion | TEXT | Subregion | Yes | |
| rights | TEXT | Rights and Reproduction | Yes | |
| link | TEXT | Link Resource | No | |
| accession_year | INTEGER | AccessionYear | Yes | 1,327 nulls, but the database handles that natively. Read as pandas Int64 to preserve nulls, stored as INTEGER. Two rows contain full ISO dates instead of years. Coerced to NULL at extract time. |

---

### **Excluded columns ->**
1. _Artist identifiers and sort fields_: Prefix, Suffix, Alpha Sort, Gender, ULAN URL, Wikidata URL, Constituent ID
2. _Archaeological location_: Geography Type, Locale, Locus, Excavation, River
3. _Tags and other link_: Tags, Tags AAT URL, Tags Wikidata URL, Object Wikidata URL
4. _Period metadata_: Period, Dynasty, Reign, Metadata Date
5. _Is Public Domain_: used as a load filter, not stored.
6. _Museum data_: Gallery Number, Portfolio, Is Timeline Work, Repository

### **Validation rules ->** \
**Number of rows**: 484,956  →  public domain filter  →  248,472  →  year rules  →  248,325 \
Empty strings and whitespace-only values are normalized to NULL at extract time. \
Quarantine: 147 rows (0.059% of 248,472) fail the year rules. 116 of those are from Egyptian Art, where BCE dating conventions break down. Failing rows are logged and excluded, not silently dropped. \
Only objects satisfying **all three rules** are loaded.:
1. `year_start <= year_end`
2. `year_start <= 2026`
3. is Public Domain

### **Known future changes ->** \
An object can have many artists and the columns are pipe-delimited (10.17% of objects). \
For now, I build the flat table first, with the pipe-delimited artist columns preserved as raw source data. \
Then normalize artists with an Alembic migration that moves the data. Separate artists table plus a link table. Artist becomes a real entity with a typed birth year.