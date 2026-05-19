# Refining News Monitor
Local-only pipeline for identifying Google News RSS articles related to oil refining and petrochemical assets, then tagging those articles with asset and profile tags from Excel or CSV inputs.

## What It Does

- reads asset inputs from `.xlsx`, `.xls`, or `.csv`
- reads a required local tag profile file
- pulls summary content from Google News RSS for each keyword
- applies local tagging logic without Azure, MySQL, or VPN access
- writes a tagged output file in Excel or CSV format

## Setup

1. Create a virtual environment:
   `python -m venv .venv`
2. Activate it in PowerShell:
   `.venv\Scripts\Activate.ps1`
3. Install dependencies:
   `pip install -r requirements.txt`

## Inputs

Supported asset inputs:

- Excel workbooks with `Refinery` and/or `Petchem` sheets
- CSV files that use standardized asset columns such as refinery `ID`, `Name`, `Country`, `State`, `Owner` or petchem `ID`, `Name`, `Country`, `Owner`, `Location`, `Region`
- legacy sheet names such as `RefiningAsset` and `SteamCracker`, and legacy columns such as `Refinery #ID`, `PetchemID`, `Company`, `Primary Owner`, `Ownership`, and `TRACE region`, are still accepted and mapped to the standardized schema automatically

Required tag profile input:

- a local Excel or CSV file with columns `tag_cat`, `tag`, and `phrase`
- this file is a core part of the tagging workflow and is required for every run

Field-level details for supported input and output files are documented in [DATA_DICTIONARY.md](./DATA_DICTIONARY.md).

## Run

Run the supported CLI:

```powershell
python main.py --asset-file .\assets.xlsx --tag-profile .\tag-profile.xlsx --output .\output\tagged-google-news.xlsx
```

Or keep the defaults in a local config file and reference that from the CLI:

```powershell
python main.py --config .\pipeline_config.json
```

CLI flags still override config file values for one-off runs:

```powershell
python main.py --config .\pipeline_config.json --geography "United States" Canada --debug
```

Use [pipeline_config.example.json](./pipeline_config.example.json) as a starting point. Supported config keys are:

- `asset_file`
- `output`
- `tag_profile`
- `asset_types`
- `geography`
- `lookback_min`
- `lookback_max`
- `name_tolerance`
- `max_items_per_keyword`
- `source_exclude`
- `debug`

## Output

The output file includes tagged Google News rows with fields such as:

- `title`
- `source`
- `url`
- `pubDate`
- `description`
- `tags`
- `tag_score`
- matched asset columns such as `asset_id`, `asset_name`, and `asset_country` when present

## Notes

- The only supported entry point is `main.py`.
- The project runs fully from local files plus Google News RSS.
- JSON config files are optional; direct CLI usage still works. However, the config file provides more granular control over the process

## Improvements
- Incorporate paid news API source, such as SerpAPI, to broaden coverage
- Pass results to LLM for review and prioritization before providing output to user
- If using a news source that provides primary source URLs, retrieve larger portion of source text for review and tagging
