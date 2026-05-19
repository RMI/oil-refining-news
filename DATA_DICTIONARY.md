# Data Dictionary

This document describes the `.xlsx`, `.xls`, and `.csv` files read or written by `main.py`.

## Files In Scope

- Asset input file passed to `--asset-file`
- Tag profile file passed to `--tag-profile`
- Output file passed to `--output`

## Asset Input File

Purpose: provides the refinery and/or petchem asset records used to build Google News search keywords and asset tags.

Supported formats:

- `.xlsx`
- `.xls`

Workbook behavior:

- If the workbook contains a `Refining` sheet, that sheet is treated as refinery input.
- If the workbook contains a `Petrochemical` sheet, that sheet is treated as petrochemical plant input.


### Refinery Asset Fields

Required for refinery input:

| Field | Required | Description |
| --- | --- | --- |
| `ID` | Yes | Unique refinery identifier. |
| `Name` | Yes | Refinery name used to generate Google News search keywords. |

Optional refinery fields:

| Field | Required | Description |
| --- | --- | --- |
| `Country` | No | Country filter field used when `--geography` is provided. |
| `State` | No | Geographic subdivision for the refinery record. |
| `Owner` | No | Primary owning company for the refinery asset. |

Notes:

- All refinery columns are converted into candidate asset tags during processing, not just the required fields.
- The `Name` value is shortened to the first `name_tolerance` words when building one set of name-based tags. `name_tolerance` can be set in your configuration file or left as the default value of 2.
- Legacy aliases mapped to this schema include `Refinery #ID`, `Refinery # ID`, `id`, and `Primary Owner`.

### Petchem Asset Fields

Required for petchem input:

| Field | Required | Description |
| --- | --- | --- |
| `ID` | Yes | Unique petchem asset identifier. |
| `Name` | Yes | Petrochemical company label used to generate Google News search keywords. |

Optional petchem fields:

| Field | Required | Description |
| --- | --- | --- |
| `Country` | No | Country filter field used when `--geography` is provided. |
| `Owner` | No | Full ownership mix for the facility. |
| `Location` | No | City/State/Geographic subdivision of the facility. |
| `Region` | No | Climate TRACE Region of the facility. |

Notes:

- The pipeline uses `Name` values as Google News search keywords.
- `ID`, `Name`, and `Country` are used to build asset tags when present.
- Legacy aliases mapped to this schema include `PetchemID`, `Petchem ID`, `Company`, `Ownership`, and `TRACE region`.

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
| `asset_type` | Yes | Asset type processed for the row: `refinery` or `petchem`. |
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
| `asset_id` | Sometimes | Asset identifier extracted when the row matched a refinery or petchem asset-name/company tag. |
| `asset_name` | Sometimes | Asset or company name extracted from the matched asset tag. |
| `asset_country` | Sometimes | Asset country tag match carried through when present in the tag reference. |
| `asset_owner` | Sometimes | Asset owner tag match carried through when present in the tag reference. |
| `asset_state` | Sometimes | Refinery state tag match carried through when present in the tag reference. |
| `asset_location` | Sometimes | Petchem location tag match carried through when present in the tag reference. |
| `asset_region` | Sometimes | Petchem region tag match carried through when present in the tag reference. |
| Other `asset_*` or custom tag category columns | Sometimes | Intermediate category match columns may appear depending on which tag categories survive post-processing. |

Notes:

- Output columns depend partly on the input asset columns and required tag profile categories.
- The pipeline removes several internal helper columns before writing output, including `id`, `desc_match`, and `value`.

## Sample Files In This Repo

These sample files help illustrate the supported shapes:

- `OG_AssetsFull.xlsx`
  - Legacy `RefiningAsset` columns: `Refinery #ID`, `Name`, `Country`, `State`, `Primary Owner`
  - Legacy `SteamCracker` columns: `PetchemID`, `Country`, `Company`, `Ownership`, `Location`, `TRACE region`
  - Canonical equivalents: `ID`, `Name`, `Country`, `State`, `Owner` for refinery and `ID`, `Name`, `Country`, `Owner`, `Location`, `Region` for petchem
- `tagProfile.xlsx`
  - Columns: `tag`, `phrase`, `tag category`
- `Tag Profile_emissionMitigation.xlsx`
  - Columns: `tag category`, `tag`, `phrase`
