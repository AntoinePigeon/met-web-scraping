import pandas as pd

df = pd.read_csv("data/MetObjects.txt", nrows=200)
sample = df[df["Is Public Domain"]].head(20)
sample.to_csv("tests/fixtures/met_sample.csv", index=False)