import pandas as pd

df = pd.read_csv("data/MetObjects.txt", 
                    na_values=["", " ", "N/A", "-"])
public_df = df[df["Is Public Domain"] == True]
aw = df[df["Department"] == "The American Wing"]

# if record.get(col) <= 0 or record.get(col) > 2000:

# year_start <= year_end translation
fails_year_order = public_df["Object End Date"] < public_df["Object Begin Date"]
print(f"Found {fails_year_order.sum()} records with end year < start year")

# the 1500 bound for year_start
fails_year_bound = public_df["Object Begin Date"] < 1500
print(f"Found {fails_year_bound.sum()} records with start year < 1500")
print(public_df[fails_year_bound]["Department"].value_counts())

# dimension sanity check (not possible for now)

# Dimension bounds (<= 0, > 2000) cannot be measured pre-transform. 
# The parsed columns do not exist in the source. 
# Bounds were set against 126 American Wing objects and must be re-measured after the transform runs at scale.

# dimension_cols = ["Height (cm)", "Width (cm)", "Depth (cm)"]
# for col in dimension_cols:
#     fails_dimension = (public_df[col] <= 0) | (public_df[col] > 2000)
#     print(f"Found {fails_dimension.sum()} records with implausible {col}")
#     print(public_df[fails_dimension]["Department"].value_counts())

# Required fields check
fails_id_field = public_df["Object ID"].isna().sum()
fails_number_field = public_df["Object Number"].isna().sum()
fails_highlight_field = public_df["Is Highlight"].isna().sum()
fails_department_field = public_df["Department"].isna().sum()
fails_year_start_field = public_df["Object Begin Date"].isna().sum()
fails_year_end_field = public_df["Object End Date"].isna().sum()
fails_link_field = public_df["Link Resource"].isna().sum()
print(f"Found {fails_id_field} records with missing Object ID")
print(f"Found {fails_number_field} records with missing Object Number")
print(f"Found {fails_highlight_field} records with missing Is Highlight")
print(f"Found {fails_department_field} records with missing Department")
print(f"Found {fails_year_start_field} records with missing Object Begin Date")
print(f"Found {fails_year_end_field} records with missing Object End Date")
print(f"Found {fails_link_field} records with missing Link Resource")
