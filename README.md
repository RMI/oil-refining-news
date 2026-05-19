# Refining News Monitor
Local-only pipeline for identifying Google News RSS articles related to oil refining and petrochemical assets, then tagging those articles with asset and profile tags from Excel or CSV inputs.

## What It Does

The refactored project:

- reads asset inputs from `.xlsx`, `.xls`, or `.csv`
- optionally reads a local tag profile file
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

- Excel workbooks with `RefiningAsset` and/or `SteamCracker` sheets
- CSV files that contain either refinery columns such as `Refinery #ID` and `Name`, or petchem columns such as `PetchemID` and `Company`

Optional tag profile input:

- a local Excel or CSV file with columns `tag_cat`, `tag`, and `phrase`

## Run

Run the supported CLI:

```powershell
python main.py --asset-file .\assets.xlsx --tag-profile .\tag-profile.xlsx --output .\output\tagged-google-news.xlsx
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
- matched asset columns when present

## Notes

- Azure resources and MySQL are no longer required.
- The only supported entry point is `main.py`.
- The project runs fully from local files plus Google News RSS.
