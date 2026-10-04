import pandas as pd


SENTINELS = [
    "dimensions unavailable",
    "n.a.",
    "various",
    "[no dimensions available]",
    "no measurement",
    "various dimensions",
    "dimensions unrecorded",
    "not available"
]

df = pd.read_csv("data/MetObjects.txt", 
                    na_values=["", " ", "N/A", "-"])
public_df = df[df["Is Public Domain"] == True]

dims  = public_df["Dimensions"]
first = dims.str.split("\r\n", n=1).str[0]

is_sentinel   = dims.str.lower().str.strip().isin(SENTINELS)
has_cm        = dims.str.contains("cm", regex=False, na=False)
has_in        = dims.str.contains("in.", regex=False, na=False)
has_mm        = dims.str.contains("mm", regex=False, na=False)
has_set       = dims.str.contains(r"\([a-z]{1,3}\):", na=False)
is_multi      = dims.str.count("cm").fillna(0) >= 2
first_cm      = first.str.contains("cm", regex=False, na=False)
first_overall = first.str.startswith("Overall:", na=False)
first_label   = first.str.contains(r"^[A-Za-z ]+:", na=False)

cases = {}
remaining = pd.Series(True, index=public_df.index)

def claim(name, condition):
    global remaining
    cases[name] = remaining & condition
    remaining = remaining & ~cases[name]

claim("1 null",             dims.isna())
claim("2 sentinel",         is_sentinel)
claim("3 set",              has_cm & has_set)
claim("4 single",           has_cm & ~is_multi)
claim("5 multi overall",    has_cm & is_multi & first_overall)
claim("6 multi component",  has_cm & is_multi & first_label)
claim("7 multi first line", has_cm & is_multi & first_cm)
claim("8 cm other",         has_cm)
claim("9 inches",           has_in)
claim("10 mm",              has_mm)
claim("11 other",           pd.Series(True, index=public_df.index))

for name, mask in cases.items():
    print(f"{name:<20} {mask.sum():>8,}")

total = sum(mask.sum() for mask in cases.values())
print(f"{'total':<20} {total:>8,}")
assert total == len(public_df)

old_set = cases["3 set"].copy()

moved = old_set & ~cases["3 set"]
print(f"left case 3: {moved.sum()}")

for name, mask in cases.items():
    n = (moved & mask).sum()
    if n:
        print(f"  -> {name:<20} {n:>6,}")

print(public_df.loc[moved, "Dimensions"].head(5).tolist())