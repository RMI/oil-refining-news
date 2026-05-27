# Refining News Monitor
Local-only pipeline for identifying Google News RSS articles related to oil refining and petrochemical assets, then tagging those articles with asset and profile tags from Excel or CSV inputs. This is a generalized version of a tool utilized by staff at RMI that utilizes reference databases within RMI's Azure environment.

## What It Does

- Reads asset inputs from `.xlsx` or `.xls`
- Reads a required local tag profile file
- Pulls summary content from Google News RSS for each keyword
- Applies local tagging logic
- Writes a tagged output file in Excel or CSV format

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

Required tag profile input:

- a local Excel or CSV file with columns `tag_cat`, `tag`, and `phrase`
- this file is a core part of the tagging workflow and is required for every run

Field-level details for supported input and output files are documented in [DATA_DICTIONARY.md](./DATA_DICTIONARY.md).

## Run

Set your configuration file. Use [pipeline_config.example.json](./pipeline_config.example.json) as a starting point. 

Supported config keys are:

- `asset_file`: File path to asset file
- `output`: Target output filename
- `tag_profile`: Tag profile file path
- `asset_types`: Asset types you want included in the run
- `geography`: Target geographies if providing and asset file with geography included
- `lookback_min`: Start date of your target period
- `lookback_max`: End date of your target period
- `name_tolerance`: How many words from each asset name should be included for keyword searches
- `max_items_per_keyword`: How many search results to return per asset
- `source_exclude`: Names of any publications to exclude from output


Or keep the defaults in a local config file and reference that from the CLI:

```powershell
python main.py --config .\pipeline_config.json
```

Or run the supported CLI with default configuration:

```powershell
python main.py --asset-file .\assets.xlsx --tag-profile .\tag-profile.xlsx --output .\output\tagged-google-news.xlsx
```

CLI flags still override config file values for one-off runs:

```powershell
python main.py --config .\pipeline_config.json --geography "United States" Canada --debug
```



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
