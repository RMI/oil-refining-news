from __future__ import annotations

from datetime import date, timedelta

from main import PipelineConfig, run_pipeline


# Local-only defaults. Update these values or run main.py directly with CLI arguments.
asset_file = "OG_AssetsFull.xlsx"
tag_profile = "tagProfile.xlsx"
output_file = "tempData/tagged_google_news.xlsx"
asset_types = ["refinery", "petchem"]
geography = ["United States of America", "United States", "Mexico", "Canada"]
lookback_min = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
lookback_max = date.today().strftime("%Y-%m-%d")
name_tolerance = 2
max_items_per_keyword = 10
debug = False


if __name__ == "__main__":
    config = PipelineConfig(
        asset_file=asset_file,
        output=output_file,
        tag_profile=tag_profile,
        asset_types=asset_types,
        geography=geography,
        lookback_min=lookback_min,
        lookback_max=lookback_max,
        name_tolerance=name_tolerance,
        max_items_per_keyword=max_items_per_keyword,
        debug=debug,
    )
    run_pipeline(config)
