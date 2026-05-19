from __future__ import annotations

from pathlib import Path

import pandas as pd


REFINERY_COLUMN_ALIASES = {
    "ID": ["ID", "id", "Refinery #ID", "Refinery # ID"],
    "Name": ["Name"],
    "Country": ["Country"],
    "State": ["State"],
    "Owner": ["Owner", "Primary Owner"],
}

PETCHEM_COLUMN_ALIASES = {
    "ID": ["ID", "id", "PetchemID", "Petchem ID"],
    "Name": ["Name", "Company"],
    "Country": ["Country"],
    "Owner": ["Owner", "Ownership"],
    "Location": ["Location"],
    "Region": ["Region", "TRACE region"],
}


def read_table(path: str | Path, sheet_name: str | None = None) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        if sheet_name is None:
            return pd.read_excel(path)
        return pd.read_excel(path, sheet_name=sheet_name)

    raise ValueError(f"Unsupported file type: {path}")


def write_table(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == ".csv":
        df.to_csv(path, index=False)
        return

    df.to_excel(path, index=False)


def load_tag_profile(path: str | Path) -> pd.DataFrame:
    df = read_table(path)
    required = {"tag category", "tag", "phrase"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Tag profile is missing required columns: {sorted(missing)}")
    df = df.rename(columns={"tag category": "tag_cat"})
    return df[["tag_cat", "tag", "phrase"]].copy()


def _rename_columns(df: pd.DataFrame, aliases: dict[str, list[str]]) -> pd.DataFrame:
    renamed = df.copy()
    rename_map: dict[str, str] = {}
    for canonical_name, options in aliases.items():
        for option in options:
            if option in renamed.columns:
                rename_map[option] = canonical_name
                break
    return renamed.rename(columns=rename_map)


def normalize_asset_columns(df: pd.DataFrame, asset_type: str) -> pd.DataFrame:
    aliases = REFINERY_COLUMN_ALIASES if asset_type == "refinery" else PETCHEM_COLUMN_ALIASES
    return _rename_columns(df, aliases)


def load_asset_frames(asset_path: str | Path, requested_asset_types: list[str] | None = None) -> dict[str, pd.DataFrame]:
    asset_path = Path(asset_path)
    suffix = asset_path.suffix.lower()

    if suffix not in {".xlsx", ".xls"}:
        raise ValueError(f"Unsupported asset file type: {asset_path}")

    workbook = pd.ExcelFile(asset_path)
    frames: dict[str, pd.DataFrame] = {}

    if "Refining" in workbook.sheet_names:
        frames["refinery"] = normalize_asset_columns(pd.read_excel(asset_path, sheet_name="Refining"), "refinery")
    if "Petrochemical" in workbook.sheet_names:
        frames["petchem"] = normalize_asset_columns(pd.read_excel(asset_path, sheet_name="Petrochemical"), "petchem")

    if frames:
        return frames

    raise ValueError("No valid asset sheets found in the workbook.")
