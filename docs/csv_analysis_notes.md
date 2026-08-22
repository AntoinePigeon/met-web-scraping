# Notes

**Some notes I took while analysing the data from the CSV dump**

### Link
The metropolitan museum of art [official page](https://www.metmuseum.org/fr?gad_source=1&gad_campaignid=22380952476&gbraid=0AAAAACr7WOkjtBpxiMjj5ArOFs-BjXZLW&gclid=Cj0KCQjwkOvTBhDgARIsAKUNyRtA0DMnFfFOnc3_xGqN23rNO8UqoSo_I88GpjRUm9wm4hWmZpx1YAQaAiJkEALw_wcB) \
Check out the [GitHub page](https://github.com/metmuseum/openaccess?tab=readme-ov-file) page \
[Download](https://github.com/metmuseum/openaccess/blob/master/MetObjects.csv) the csv

---

The CSV has **612 687 lines**, is comma-separated values and is **303M**. \
Has 484 956 rows and 54 columns

### Every column with dtype and non-null count

| Index | Column | Non-Null Count | Dtype |
|---|---|---|---|
| 0 | Object Number | 484 956 | str |
| 1| Is Highlight | 484 956 | bool |
| 2 | Is Timeline Work | 484 956 | bool |
| 3 | Is Public Domain | 484 956 | bool |
| 4 | Object ID | 484 956 | int64 |
| 5 | Gallery Number | 49 541 | object |
| 6 | Department | 484 956 | str |
| 7 | AccessionYear | 481 094 | object |
| 8 | Object Name | 482 690 | str |
| 9 | Title | 456 153 | str |
| 10 | Culture | 208 190 | str |
| 11 | Period | 91 143 | object |
| 12 | Dynasty | 23 201 | str |
| 13 | Reign | 11 236 | str |
| 14 | Portfolio | 26 514 | str |
| 15 | Constituent ID | 282 513 | object |
| 16 | Artist Role | 282 513 | str |
| 17 | Artist Prefix | 282 513 | str |
| 18 | Artist Display Name | 282 513 | str |
| 19 | Artist Display Bio | 280 423 | str |
| 20 | Artist Suffix | 282 465 | str |
| 21 | Artist Alpha Sort | 282 513 | str |
| 22 | Artist Nationality | 282 513 | str |
| 23 | Artist Begin Date | 282 513 | str |
| 24 | Artist End Date | 282 513 | str |
| 25 | Artist Gender | 106 482 | str |
| 26 | Artist ULAN URL | 227 441 | str |
| 27 | Artist Wikidata URL | 224 202 | str |
| 28 | Object Date | 471 525 | str |
| 29 | Object Begin Date | 484 956 | int64 |
| 30 | Object End Date | 484 956 | int64 |
| 31 | Medium | 477 741 | str |
| 32 | Dimensions | 409 898 | str |
| 33 | Credit Line | 484 305 | str |
| 34 | Geography Type | 59 959 | str |
| 35 | City | 32 754 | str |
| 36 | State | 2 621 | str |
| 37 | County | 8 559 | str |
| 38 | Country | 76 007 | str |
| 39 | Region | 31 500 | str |
| 40 | Subregion | 22 143 | str |
| 41 | Locale | 15 739 | str |
| 42 | Locus | 7 518 | str |
| 43 | Excavation | 16 571 | str |
| 44 | River | 2 092 | str |
| 45 | Classification | 406 239 | str |
| 46 | Rights and Reproduction | 24 529 | str |
| 47 | Link Resource | 484 956 | str |
| 48 | Object Wikidata URL | 69 154 | str |
| 49 | Metadata Date | 0 | float64 |
| 50 | Repository | 484 956 | str |
| 51 | Tags | 192 455 | str |
| 52 | Tags AAT URL | 192 455 | str |
| 53 | Tags Wikidata URL | 192 455 | str |

### How many of the seven geography columns have all seven empty
**Geography Type, City, State, County, Country, Region, Subregion** \
\
I wanted to verify if those rows were worth keeping. I realize that there were mostly empty. \
\
**387 042/484 956 -> 79.80%**

### Fraction of my 126 original scraped objects are Highlight compare to American wing and the whole collection

I originaly scrape the first three pages of the American Wing and I found that the first items the website show you are mostly Highlight.

| Population | Number of rows | Highlight rate |
|---|---|---|
| Whole collection | 484 656 | 0.57% |
| American Wing | 18 532 | 2.34% |
| Original | 126 | 57.7% |
