import pandas as pd

df_all = pd.read_csv("data/MetObjects.txt")
df = pd.read_csv(
    "data/MetObjects.txt", 
    engine="python", 
    usecols=[
        "Object Number",
        "Is Highlight",
        "Is Public Domain",
        "Object ID",
        "Department",
        "Object Name",
        "Title",
        "Culture",
        "Artist Display Name",
        "Object Date",
        "Object Begin Date",
        "Object End Date",
        "Medium",
        "Dimensions",
        "Credit Line",
        "City",
        "State",
        "Country"
        ],
    dtype={
        "Object Number": str,
        "Is Highlight": bool,
        "Is Public Domain": bool,
        "Object ID": int,
        "Department": str,
        "Object Name": str,
        "Title": str,
        "Culture": str,
        "Artist Display Name": str,
        "Object Date": str,
        "Object Begin Date": int,
        "Object End Date": int,
        "Medium": str,
        "Dimensions": str,
        "Credit Line": str,
        "City": str,
        "State": str,
        "Country": str
        })
american_wing_df = df[df["Department"] == "The American Wing"]
raw_artworks_df = pd.read_json("data/raw_artworks.json")
