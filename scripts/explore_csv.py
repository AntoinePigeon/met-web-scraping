import pandas as pd

df = pd.read_csv("data/MetObjects.txt", 
                    na_values=["", " ", "N/A", "-"])
public_df = df["Is Public Domain"]
aw = df[df["Department"] == "The American Wing"]

# print(public_df.info())

mask = public_df["AccessionYear"].notna() & public_df["AccessionYear"].astype(str).str.contains("-")
print(public_df[mask][["Object ID", "AccessionYear"]])