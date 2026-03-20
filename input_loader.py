from __future__ import annotations

from pathlib import Path

import pandas as pd


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


def load_optional_tag_profile(path: str | Path | None) -> pd.DataFrame | None:
    if path is None:
        return None

    df = read_table(path)
    required = {"tag_cat", "tag", "phrase"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Tag profile is missing required columns: {sorted(missing)}")
    return df[["tag_cat", "tag", "phrase"]].copy()


def infer_asset_type(df: pd.DataFrame) -> str:
    columns = set(df.columns)
    if {"PetchemID", "Company"}.issubset(columns):
        return "petchem"
    if {"Refinery #ID", "Name"}.issubset(columns) or {"id", "Name"}.issubset(columns):
        return "refinery"
    raise ValueError(
        "Could not infer asset type from columns. Expected refinery columns like "
        "'Refinery #ID'/'Name' or petchem columns like 'PetchemID'/'Company'."
    )


def load_asset_frames(asset_path: str | Path) -> dict[str, pd.DataFrame]:
    asset_path = Path(asset_path)
    suffix = asset_path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(asset_path)
        return {infer_asset_type(df): df}

    if suffix not in {".xlsx", ".xls"}:
        raise ValueError(f"Unsupported asset file type: {asset_path}")

    workbook = pd.ExcelFile(asset_path)
    frames: dict[str, pd.DataFrame] = {}

    if "RefiningAsset" in workbook.sheet_names:
        frames["refinery"] = pd.read_excel(asset_path, sheet_name="RefiningAsset")
    if "SteamCracker" in workbook.sheet_names:
        frames["petchem"] = pd.read_excel(asset_path, sheet_name="SteamCracker")

    if frames:
        return frames

    first_sheet = workbook.sheet_names[0]
    df = pd.read_excel(asset_path, sheet_name=first_sheet)
    return {infer_asset_type(df): df}
