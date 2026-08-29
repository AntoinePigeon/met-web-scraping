import pandas as pd

df = pd.read_csv("data/MetObjects.txt", 
                    na_values=["", " ", "N/A", "-"])
public_df = df[df["Is Public Domain"] == True]
aw = df[df["Department"] == "The American Wing"]