# Data Dictionary

This document describes the `.xlsx`, `.xls`, and `.csv` files read or written by `main.py`.

## Files In Scope

- Asset input file passed to `--asset-file`
- Tag profile file passed to `--tag-profile`
- Output file passed to `--output`

## Input Workbook

Purpose: provides sector asset records used to build Google News search keywords and asset tags.

Supported formats:

- `.xlsx`
- `.xls`

Workbook behavior:

- Each worksheet is treated as a separate asset type.
- Asset type names are normalized from worksheet names to lowercase for matching and output, so `Refinery`, `REFINERY`, and `refinery` are treated the same.

### Input Workbook Extensibility

- This product was originally designed for monitoring operational changes at refining and petrochemical facilities. Additional tabs can be added to the input file as long as they follow the field requirements detailed below.
- You can control the specific tabs included in a tool run by specifying target worksheet names in the `asset_types` field of your config file.



## Input Workbook Fields

*Note: All sectors are referred to generically as "asset" in this section.*

### Required Fields

| Field | Required | Description |
| --- | --- | --- |
| `ID` | Yes | Unique asset identifier. |
| `Name` | Yes | Asset name used to generate Google News search keywords. |

### Optional Fields

| Field | Required | Description |
| --- | --- | --- |
| `Ownership` | No | Primary owning company for the asset. |
| `Country` | No | Country filter field used when `--geography` is provided. This field is required to enable country-level filtering of assets. |
| `Subdivision` | No | Geographic subdivision for the asset, such as a state or province. |
| `TRACE Region` | No | Region assigned to the country by the Climate TRACE team. |

### Notes:

- All asset columns are converted into candidate asset tags during processing, not just the required fields.
- The `Name` value is used in full for keyword creation and shortened to the first `name_tolerance` words only for asset-name tag phrases. `name_tolerance` can be set in your configuration file or left as the default value of 2.
- Optional fields are utilized as additional tags after asset names are used to search for content. For example, if your input file contains "Imperial Oil Sarnia Refinery" as `Name` and "ExxonMobil" as `Ownership`, default behavior will search for "Imperial Oil" content, and then use "ExxonMobil" as a tag to search for in the returned results.


## Tag Profile File

Purpose: supplies the required tag categories, output tags, and match phrases that are combined with asset-derived tags before matching articles.

Supported formats:

- `.xlsx`
- `.xls`
- `.csv`

Required fields:

| Field | Required | Description |
| --- | --- | --- |
| `tag category` | Yes | Tag category name. This becomes a column in the intermediate tagged article dataframe. New categories can be added, as necessary. |
| `tag` | Yes | Output tag value written into the final `tags` field when the phrase matches. |
| `phrase` | Yes | Match phrase searched for in article title and description text. Matching is case-insensitive. Phrases should be subsets or aliases of a tag to increase the likelihood of a match. |

Notes:

- The pipeline lowercases `phrase` values before matching.
- Additional columns are ignored by `main.py`.

## Output File

Purpose: contains the tagged Google News results written by the pipeline.

Supported formats:

- `.xlsx`
- `.csv`

Core output fields:

| Field | Expected | Description |
| --- | --- | --- |
| `asset_type` | Yes | Asset type processed for the row, based on the normalized worksheet name. |
| `title` | Yes | Google News article title. |
| `source` | Yes | Google News source or publisher name. |
| `description` | Yes | Cleaned Google News article summary text. |
| `url` | Yes | Article URL from the Google News RSS entry. |
| `pubDate` | Yes | Article publication date normalized by the pipeline. |
| `tags` | Yes | Comma-separated tags matched from asset fields and required tag profile phrases. |
| `tag_score` | Yes | Count of tag categories that produced at least one match for the row. |

Conditional output fields:

| Field | Expected | Description |
| --- | --- | --- |
| `asset_id` | Sometimes | Asset identifier extracted when the row matched an asset-name tag. |
| `asset_name` | Sometimes | Asset or company name extracted from the matched asset tag. |
| `asset_country` | Sometimes | Asset country tag match carried through when present in the tag reference. |
| `asset_owner` | Sometimes | Asset owner tag match carried through when present in the tag reference. |
| `asset_subdivision` | Sometimes | Asset subdivision tag match carried through when present in the tag reference. |
| `asset_region` | Sometimes | Climate TRACE region tag match carried through when present in the tag reference. |
| Other `asset_*` or custom tag category columns | Sometimes | Intermediate category match columns may appear depending on which tag categories survive post-processing. |

*Note: Output columns depend partly on the input asset columns and required tag profile categories.*

## Sample Files In This Repo

These sample files help illustrate the supported shapes:

- `AssetInput.xlsx`
  - Example sector columns: `ID`, `Name`, `Ownership`, `Country`, `Geographic Subdivision`, `TRACE Region`
- `tagProfile.xlsx`
  - Columns: `tag`, `phrase`, `tag category`
