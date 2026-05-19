from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from google_news import get_recent_articles
from input_loader import load_asset_frames, load_optional_tag_profile, write_table
from tagging import (
    build_petchem_inputs,
    build_refinery_inputs,
    combine_tag_sources,
    post_process_matches,
    tag_articles,
)


DEFAULT_GEOGRAPHY = ["United States of America", "United States", "Mexico", "Canada"]
DEFAULT_SOURCE_EXCLUDE = [
    "BioMed Central",
    "ACS Applied Materials and Interfaces",
    "Springer",
    "Elsevier Journals",
    "Science",
    "The New Yorker",
    "Nature",
    "MIT Sloan Management Review",
]


@dataclass
class PipelineConfig:
    asset_file: str
    output: str
    tag_profile: str | None
    asset_types: list[str] | None
    geography: list[str]
    lookback_min: str
    lookback_max: str
    name_tolerance: int
    max_items_per_keyword: int
    debug: bool


def fetch_google_news(keywords: list[str], lookback_min: str, lookback_max: str, max_items_per_keyword: int) -> pd.DataFrame:
    articles_df = pd.DataFrame()
    for keyword in keywords:
        print(f"Getting Google News for keyword: {keyword}")
        keyword_df = get_recent_articles(
            keyword,
            lookback_min_date=lookback_min,
            lookback_max_date=lookback_max,
            max_items=max_items_per_keyword,
            max_url_length=4000,
        )
        if not keyword_df.empty:
            articles_df = pd.concat([articles_df, keyword_df], ignore_index=True)

    if articles_df.empty:
        return pd.DataFrame(columns=["title", "source", "description", "url", "pubDate"])

    articles_df["pubDate"] = pd.to_datetime(articles_df["published"], errors="coerce").dt.date
    articles_df.rename(columns={"link": "url"}, inplace=True)
    articles_df.drop(columns=["published"], inplace=True)
    articles_df = articles_df.drop_duplicates(subset=["title", "url"])
    return articles_df


def run_pipeline(config: PipelineConfig) -> pd.DataFrame:
    asset_frames = load_asset_frames(config.asset_file)
    extra_tags = load_optional_tag_profile(config.tag_profile)

    requested_types = config.asset_types or list(asset_frames.keys())
    final_frames: list[pd.DataFrame] = []

    for asset_type in requested_types:
        if asset_type not in asset_frames:
            print(f"Skipping asset type '{asset_type}' because it was not found in the input file.")
            continue

        asset_df = asset_frames[asset_type]
        if asset_type == "refinery":
            keywords, asset_tags = build_refinery_inputs(
                asset_df,
                geography=config.geography,
                name_tolerance=config.name_tolerance,
            )
        elif asset_type == "petchem":
            keywords, asset_tags = build_petchem_inputs(
                asset_df,
                geography=config.geography,
                name_tolerance=config.name_tolerance,
            )
        else:
            raise ValueError(f"Unsupported asset type: {asset_type}")

        if config.debug:
            keywords = keywords[:5]

        print(f"Extracting Google News Data for {asset_type}")
        google_df = fetch_google_news(
            keywords=keywords,
            lookback_min=config.lookback_min,
            lookback_max=config.lookback_max,
            max_items_per_keyword=config.max_items_per_keyword,
        )
        if google_df.empty:
            print(f"No Google News results found for {asset_type}.")
            continue

        tag_ref = combine_tag_sources(asset_tags=asset_tags, extra_tags=extra_tags)
        tagged = tag_articles(df=google_df, tag_ref=tag_ref, tag_type="research")
        processed = post_process_matches(
            df=tagged,
            asset_type=asset_type,
            source_exclude=DEFAULT_SOURCE_EXCLUDE,
        )
        processed.insert(0, "asset_type", asset_type)
        final_frames.append(processed)

    if not final_frames:
        return pd.DataFrame()

    final_df = pd.concat(final_frames, ignore_index=True)
    final_df = final_df.drop_duplicates(subset=["title", "url"], keep="first")
    write_table(final_df, config.output)
    return final_df


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local-only Google News RSS tagging pipeline for refinery and petchem asset files."
    )
    parser.add_argument("--asset-file", required=True, help="Path to the asset workbook or CSV input.")
    parser.add_argument("--output", required=True, help="Path to the tagged output file (.xlsx or .csv).")
    parser.add_argument("--tag-profile", help="Optional local tag profile file with tag_cat, tag, and phrase columns.")
    parser.add_argument(
        "--asset-types",
        nargs="+",
        choices=["refinery", "petchem"],
        help="Optional subset of asset types to run.",
    )
    parser.add_argument(
        "--geography",
        nargs="+",
        default=DEFAULT_GEOGRAPHY,
        help="Optional list of countries to retain from the asset input.",
    )
    parser.add_argument(
        "--lookback-min",
        default=(date.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
        help="Inclusive lower bound for Google News article dates, formatted as YYYY-MM-DD.",
    )
    parser.add_argument(
        "--lookback-max",
        default=date.today().strftime("%Y-%m-%d"),
        help="Inclusive upper bound for Google News article dates, formatted as YYYY-MM-DD.",
    )
    parser.add_argument("--name-tolerance", type=int, default=2, help="Number of words to keep for asset-name tag phrases.")
    parser.add_argument("--max-items-per-keyword", type=int, default=10, help="Maximum RSS items to keep per keyword.")
    parser.add_argument("--debug", action="store_true", help="Limit keyword processing to the first 5 keywords.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = PipelineConfig(
        asset_file=args.asset_file,
        output=args.output,
        tag_profile=args.tag_profile,
        asset_types=args.asset_types,
        geography=args.geography,
        lookback_min=args.lookback_min,
        lookback_max=args.lookback_max,
        name_tolerance=args.name_tolerance,
        max_items_per_keyword=args.max_items_per_keyword,
        debug=args.debug,
    )
    final_df = run_pipeline(config)
    print(f"Pipeline complete. Wrote {len(final_df)} tagged rows to {Path(config.output)}")


if __name__ == "__main__":
    main()
