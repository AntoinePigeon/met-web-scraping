import pandas as pd


def clean_data(all_artworks):
    """Take raw scraped records and return a cleaned DataFrame."""
    df = pd.DataFrame(all_artworks)

    # Consolidate creator columns into one 'maker'
    df["maker"] = (df["Artist"]
        .combine_first(df["Maker"])
        .combine_first(df["Manufacturer"])
        .combine_first(df["Designer"])
        .combine_first(df["Decorator"])
        .combine_first(df["Architect"])
        .combine_first(df["Founder"]))

    df = df.drop(columns=["Artist", "Maker", "Manufacturer", "Designer",
                        "Decorator", "Architect", "Founder", "Rights and Reproduction"])

    # snake_case column names
    df = df.rename(columns={"Title": "title", "Date": "date", "Geography": "geography",
                            "Culture": "culture", "Medium": "medium", "Dimensions": "dimensions",
                            "Credit Line": "credit_line", "Object Number": "object_number",
                            "Curatorial Department": "curatorial_department", "objectID": "object_id"})

    # Parse year from date text
    df["year_start"] = df["date"].str.extract(r"(\d{4})")
    df["year_start"] = df["year_start"].astype("Int64")

    # Parse dimensions (cm) into numeric columns
    df["dimensions"] = df["dimensions"].str.replace("×", "x")
    df["dimension_cm"] = df["dimensions"].str.extract(r"\(([\d.\sx]+?)\s*cm")
    df[["height_cm", "width_cm", "depth_cm"]] = df["dimension_cm"].str.split("x", expand=True)
    df["height_cm"] = df["height_cm"].astype(float)
    df["width_cm"] = df["width_cm"].astype(float)
    df["depth_cm"] = df["depth_cm"].astype(float)
    df = df.drop(columns=["dimension_cm"])

    return df