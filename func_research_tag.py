from __future__ import annotations
import pandas as pd

def get_programs(tag_profile_path: str = "tagProfile.xlsx") -> pd.Series:
    try:
        df = pd.read_excel(tag_profile_path)
    except FileNotFoundError:
        return pd.Series(dtype="object")

    if "cost_center" in df.columns:
        programs = df["cost_center"].dropna().astype(str).sort_values().drop_duplicates()
        print("Programs in local tag profile:")
        print(programs)
        return programs

    print("No 'cost_center' column found in the local tag profile.")
    return pd.Series(dtype="object")


def research_tag(df: pd.DataFrame, target_program: str, ref_tags: pd.DataFrame):
    if "cost_center" not in ref_tags.columns:
        raise ValueError(
            "Local research_tag requires a ref_tags dataframe with a 'cost_center' column."
        )

    matches = ref_tags[ref_tags["cost_center"] == target_program].copy()
    print(f"Local-only research_tag matched {len(matches)} rows for {target_program}.")
    return df.copy(), matches
