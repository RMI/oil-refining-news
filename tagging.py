from __future__ import annotations

import re

import numpy as np
import pandas as pd


def _normalize_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str)


def _tag_category_name(column_name: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z]+", "_", str(column_name).strip()).strip("_").lower()
    return f"asset_{normalized}"


def build_petchem_inputs(
    df: pd.DataFrame,
    geography: list[str] | None = None,
    name_tolerance: int = 2,
) -> tuple[list[str], pd.DataFrame]:
    petchem = df.copy()
    required = {"ID", "Name"}
    missing = required.difference(petchem.columns)
    if missing:
        raise ValueError(f"Petchem input is missing required columns: {sorted(missing)}")
    if geography and "Country" in petchem.columns:
        petchem = petchem[petchem["Country"].isin(geography)]

    tag_columns = ["ID", "Name"]
    if "Country" in petchem.columns:
        tag_columns.append("Country")
    if "Owner" in petchem.columns:
        tag_columns.append("Owner")
    if "Location" in petchem.columns:
        tag_columns.append("Location")
    if "Region" in petchem.columns:
        tag_columns.append("Region")

    tags = petchem[tag_columns].copy()
    tags["Name"] = tags["Name"].astype(str).str.split().str[:name_tolerance].str.join(" ")
    tags = tags.melt(id_vars="ID", var_name="tag_name", value_name="phrase").drop_duplicates(
        subset="phrase"
    )
    tags["tag_cat"] = tags["tag_name"].apply(_tag_category_name)
    tags["tag"] = tags["phrase"].astype(str)
    tags.rename(columns={"ID": "id"}, inplace=True)
    name_mask = tags["tag_cat"] == "asset_name"
    tags.loc[name_mask, "tag"] = tags.loc[name_mask, "id"].astype(str) + "_" + tags.loc[
        name_mask, "tag"
    ]
    tags["phrase"] = tags["phrase"].astype(str).str.lower()

    keywords = petchem["Name"].dropna().astype(str).drop_duplicates().tolist()
    return keywords, tags[["id", "tag_cat", "tag", "phrase"]]


def build_refinery_inputs(
    df: pd.DataFrame,
    geography: list[str] | None = None,
    name_tolerance: int = 2,
) -> tuple[list[str], pd.DataFrame]:
    refineries = df.copy()
    required = {"ID", "Name"}
    missing = required.difference(refineries.columns)
    if missing:
        raise ValueError(f"Refinery input is missing required columns: {sorted(missing)}")
    if geography and "Country" in refineries.columns:
        refineries = refineries[refineries["Country"].isin(geography)]

    keywords = refineries["Name"].dropna().astype(str).drop_duplicates().tolist()
    refineries["Name"] = refineries["Name"].astype(str).str.split().str[:name_tolerance].str.join(" ")

    tags = refineries.melt(id_vars="ID", var_name="tag_name", value_name="phrase").drop_duplicates(subset="phrase")
    tags["tag_cat"] = tags["tag_name"].apply(_tag_category_name)
    tags["tag"] = tags["phrase"].astype(str)
    tags.dropna(subset=["phrase"], inplace=True)
    tags["phrase"] = tags["phrase"].astype(str).str.lower()
    tags.rename(columns={"ID": "id"}, inplace=True)
    name_mask = tags["tag_cat"] == "asset_name"
    tags.loc[name_mask, "tag"] = tags.loc[name_mask, "id"].astype(str) + "_" + tags.loc[name_mask, "tag"]

    return keywords, tags[["id", "tag_cat", "tag", "phrase"]]


def combine_tag_sources(asset_tags: pd.DataFrame, extra_tags: pd.DataFrame | None) -> pd.DataFrame:
    if extra_tags is None:
        return asset_tags.copy()

    tag_ref = pd.concat([asset_tags, extra_tags.copy()], ignore_index=True)
    tag_ref["phrase"] = tag_ref["phrase"].fillna("").astype(str).str.lower()
    return tag_ref


def tag_articles(df: pd.DataFrame, tag_ref: pd.DataFrame, tag_type: str = "research") -> pd.DataFrame:
    required_article_cols = {"title", "source", "description"}
    missing_articles = required_article_cols.difference(df.columns)
    if missing_articles:
        raise ValueError(f"Article dataframe missing required columns: {sorted(missing_articles)}")

    required_tag_cols = {"tag_cat", "tag", "phrase"}
    missing_tags = required_tag_cols.difference(tag_ref.columns)
    if missing_tags:
        raise ValueError(f"Tag dataframe missing required columns: {sorted(missing_tags)}")

    news = df.copy()
    news["title"] = _normalize_text(news["title"])
    news["source"] = _normalize_text(news["source"])
    news["description"] = _normalize_text(news["description"])

    if tag_type.lower() == "news":
        news["desc_match"] = news["description"].str.lower()
    else:
        news["desc_match"] = (news["title"] + " " + news["description"]).str.lower()

    category_columns: list[str] = []

    for category in tag_ref["tag_cat"].dropna().astype(str).unique():
        category_rows = tag_ref[tag_ref["tag_cat"] == category][["tag", "phrase"]].dropna()
        keywords_to_tag = {
            str(row["phrase"]).lower(): str(row["tag"])
            for _, row in category_rows.iterrows()
            if str(row["phrase"]).strip()
        }

        def match_tags(text: str) -> str:
            matches = []
            for keyword, tag in keywords_to_tag.items():
                if keyword in text and tag not in matches:
                    matches.append(tag)
            return ",".join(matches)

        news[category] = news["desc_match"].apply(match_tags)
        category_columns.append(category)

    def join_non_empty_tags(row: pd.Series) -> str:
        values = [str(row[col]).strip(", ") for col in category_columns if str(row[col]).strip(", ")]
        return ",".join(values)

    news["tag"] = news.apply(join_non_empty_tags, axis=1)
    news["tag"] = news["tag"].replace(re.compile(r",{2,}"), ",", regex=True)
    news["tag"] = news["tag"].replace(re.compile(r"(^[,\s]+)|([,\s]+$)"), "", regex=True)
    news["tag_score"] = news[category_columns].apply(
        lambda row: sum(bool(str(value).strip(", ")) for value in row), axis=1
    )
    news["value"] = news["tag_score"]
    return news


def post_process_matches(
    df: pd.DataFrame,
    asset_type: str,
    source_exclude: list[str] | None = None,
    petchem_conditions: str = "steam cracker|Ethylene|Olefin|Petrochemical|Naphtha|Ethane Cracker|Cracker",
    refine_conditions: str = "refinery|refining",
) -> pd.DataFrame:
    result = df.copy()
    result = result.drop_duplicates(subset=["title"])
    result = result[result["tag"].notna() & (result["tag"] != "")]

    if source_exclude and "source" in result.columns:
        result = result[~result["source"].isin(source_exclude)]

    if asset_type == "petchem":
        asset_col = "asset_name"
        if asset_col in result.columns:
            df_asset = result[result[asset_col].fillna("") != ""].copy()
            if not df_asset.empty:
                df_asset[["asset_id", "asset_name"]] = df_asset[asset_col].str.split("_", n=1, expand=True)
                df_asset["asset_name"] = df_asset["asset_name"].str.split("_").str[0]
            else:
                df_asset = pd.DataFrame(columns=result.columns)
        else:
            df_asset = pd.DataFrame(columns=result.columns)

        df_cond = result[result["tag"].str.contains(petchem_conditions, case=False, na=False)].copy()
        df_cond = df_cond[df_cond["tag_score"].fillna(0).astype(int) > 1]
        result = pd.concat([df_asset, df_cond], ignore_index=True).drop_duplicates(subset=["title"])
        if asset_col in result.columns:
            result.drop(columns=[asset_col], inplace=True)

    if asset_type == "refinery":
        asset_col = "asset_name"
        if asset_col in result.columns:
            df_asset = result[result[asset_col].fillna("") != ""].copy()
            if not df_asset.empty:
                df_asset[["asset_id", "asset_name"]] = df_asset[asset_col].str.split("_", n=1, expand=True)
                df_asset["asset_name"] = df_asset["asset_name"].str.split("_").str[0]
            else:
                df_asset = pd.DataFrame(columns=result.columns)
        else:
            df_asset = pd.DataFrame(columns=result.columns)

        df_cond = result[result["tag"].str.contains(refine_conditions, case=False, na=False)].copy()
        if asset_col in df_cond.columns:
            df_cond = df_cond[df_cond[asset_col].fillna("") == ""]
        df_cond = df_cond[df_cond["tag_score"].fillna(0).astype(int) > 1]
        result = pd.concat([df_asset, df_cond], ignore_index=True).drop_duplicates(subset=["title"])

    drops = ["Unnamed: 0", "uid", "id", "ID", "Adaptation", "Emissions", "Technology", "desc_match", "value"]
    result = result.drop(columns=[col for col in drops if col in result.columns], errors="ignore")
    result = result.rename(columns={"tag": "tags"})

    if "tag_score" not in result.columns:
        result["tag_score"] = np.nan

    return result
