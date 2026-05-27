from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from google_news import get_recent_articles
from input_loader import load_asset_frames, load_tag_profile, normalize_asset_type_name, write_table
from tagging import (
    build_asset_inputs,
    combine_tag_sources,
    post_process_matches,
    tag_articles,
)


DEFAULT_GEOGRAPHY = ["United States of America", "United States", "Mexico", "Canada"]
DEFAULT_SOURCE_EXCLUDE = [
    "BioMed Central"
]


@dataclass
class PipelineConfig:
    asset_file: str
    output: str
    tag_profile: str
    asset_types: list[str] | None
    geography: list[str]
    lookback_min: str
    lookback_max: str
    name_tolerance: int
    max_items_per_keyword: int
    source_exclude: list[str]
    debug: bool


def default_lookback_min() -> str:
    return (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")


def default_lookback_max() -> str:
    return date.today().strftime("%Y-%m-%d")


def load_config_file(path: str | None) -> dict:
    if path is None:
        return {}

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)

    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must contain a JSON object: {config_path}")

    allowed_keys = {
        "asset_file",
        "output",
        "tag_profile",
        "asset_types",
        "geography",
        "lookback_min",
        "lookback_max",
        "name_tolerance",
        "max_items_per_keyword",
        "source_exclude",
        "debug",
    }
    unknown_keys = sorted(set(loaded).difference(allowed_keys))
    if unknown_keys:
        raise ValueError(f"Unsupported config keys in {config_path}: {unknown_keys}")

    return loaded


def build_argument_defaults(config_values: dict) -> dict:
    return {
        "asset_file": config_values.get("asset_file"),
        "output": config_values.get("output"),
        "tag_profile": config_values.get("tag_profile"),
        "asset_types": config_values.get("asset_types"),
        "geography": config_values.get("geography", DEFAULT_GEOGRAPHY),
        "lookback_min": config_values.get("lookback_min", default_lookback_min()),
        "lookback_max": config_values.get("lookback_max", default_lookback_max()),
        "name_tolerance": config_values.get("name_tolerance", 2),
        "max_items_per_keyword": config_values.get("max_items_per_keyword", 10),
        "source_exclude": config_values.get("source_exclude", DEFAULT_SOURCE_EXCLUDE),
        "debug": config_values.get("debug", False),
    }


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
    asset_frames = load_asset_frames(config.asset_file, requested_asset_types=config.asset_types)
    extra_tags = load_tag_profile(config.tag_profile)

    requested_types = (
        [normalize_asset_type_name(asset_type) for asset_type in config.asset_types]
        if config.asset_types
        else list(asset_frames.keys())
    )
    final_frames: list[pd.DataFrame] = []

    for asset_type in requested_types:
        if asset_type not in asset_frames:
            print(f"Skipping asset type '{asset_type}' because it was not found in the input file.")
            continue

        asset_df = asset_frames[asset_type]
        keywords, asset_tags = build_asset_inputs(
            asset_df,
            geography=config.geography,
            name_tolerance=config.name_tolerance,
            asset_label=asset_type.title(),
        )

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
            source_exclude=config.source_exclude,
        )
        processed.insert(0, "asset_type", asset_type)
        final_frames.append(processed)

    if not final_frames:
        return pd.DataFrame()

    final_df = pd.concat(final_frames, ignore_index=True)
    final_df = final_df.drop_duplicates(subset=["title", "url"], keep="first")
    write_table(final_df, config.output)
    return final_df


def build_parser(defaults: dict) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local-only Google News RSS tagging pipeline for sector-based asset workbooks."
    )
    parser.add_argument("--config", help="Optional path to a JSON config file for default pipeline settings.")
    parser.add_argument("--asset-file", default=defaults["asset_file"], help="Path to the asset workbook or CSV input.")
    parser.add_argument("--output", default=defaults["output"], help="Path to the tagged output file (.xlsx or .csv).")
    parser.add_argument(
        "--tag-profile",
        default=defaults["tag_profile"],
        help="Required tag profile file with tag_cat, tag, and phrase columns.",
    )
    parser.add_argument(
        "--asset-types",
        nargs="+",
        default=defaults["asset_types"],
        help="Optional subset of workbook tabs to run, matched case-insensitively.",
    )
    parser.add_argument(
        "--geography",
        nargs="+",
        default=defaults["geography"],
        help="Optional list of countries to retain from the asset input.",
    )
    parser.add_argument(
        "--lookback-min",
        default=defaults["lookback_min"],
        help="Inclusive lower bound for Google News article dates, formatted as YYYY-MM-DD.",
    )
    parser.add_argument(
        "--lookback-max",
        default=defaults["lookback_max"],
        help="Inclusive upper bound for Google News article dates, formatted as YYYY-MM-DD.",
    )
    parser.add_argument(
        "--name-tolerance",
        type=int,
        default=defaults["name_tolerance"],
        help="Number of words to keep for asset-name tag phrases.",
    )
    parser.add_argument(
        "--max-items-per-keyword",
        type=int,
        default=defaults["max_items_per_keyword"],
        help="Maximum RSS items to keep per keyword.",
    )
    parser.add_argument(
        "--source-exclude",
        nargs="+",
        default=defaults["source_exclude"],
        help="Optional list of sources to exclude from the tagged results.",
    )
    debug_group = parser.add_mutually_exclusive_group()
    debug_group.add_argument("--debug", dest="debug", action="store_true", help="Limit keyword processing to the first 5 keywords.")
    debug_group.add_argument("--no-debug", dest="debug", action="store_false", help="Process the full keyword list.")
    parser.set_defaults(debug=defaults["debug"])
    return parser


def main() -> None:
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config")
    config_args, _ = config_parser.parse_known_args(sys.argv[1:])

    file_config = load_config_file(config_args.config)
    args = build_parser(build_argument_defaults(file_config)).parse_args()
    if not args.asset_file:
        raise SystemExit("--asset-file is required either in the CLI or the config file.")
    if not args.output:
        raise SystemExit("--output is required either in the CLI or the config file.")
    if not args.tag_profile:
        raise SystemExit("--tag-profile is required either in the CLI or the config file.")

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
        source_exclude=args.source_exclude,
        debug=args.debug,
    )
    final_df = run_pipeline(config)
    print(f"Pipeline complete. Wrote {len(final_df)} tagged rows to {Path(config.output)}")


if __name__ == "__main__":
    main()
