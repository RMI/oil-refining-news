# Data Dictionary

This document describes the `.xlsx`, `.xls`, and `.csv` files read or written by `main.py`.

## Files In Scope

- Asset input file passed to `--asset-file`
- Tag profile file passed to `--tag-profile`
- Output file passed to `--output`

## Asset Input File

Purpose: provides the refinery and/or petchem asset records used to build Google News search keywords and asset tags.

Supported formats:

- `.xlsx` or `.xls`
- `.csv`

Workbook behavior:

- If the workbook contains a `RefiningAsset` sheet, that sheet is treated as refinery input.
- If the workbook contains a `SteamCracker` sheet, that sheet is treated as petchem input.
- If neither sheet exists, the first sheet is loaded and the asset type is inferred from its columns.

CSV behavior:

- A CSV must contain columns that allow the pipeline to infer either refinery or petchem input.

### Refinery Asset Fields

Required for refinery input:

| Field | Required | Description |
| --- | --- | --- |
| `Refinery #ID` | Yes for workbook/CSV refinery inputs unless the file already uses `id` | Unique refinery identifier. Placeholder: confirm whether this is an internal master asset ID. |
| `id` | Yes for refinery inputs that do not use `Refinery #ID` | Normalized refinery identifier used internally by the pipeline. Placeholder: confirm whether partners should ever supply this directly. |
| `Name` | Yes | Refinery name used to generate Google News search keywords. Placeholder: confirm whether this should be the common site name, legal entity name, or another naming convention. |

Optional refinery fields observed in sample workbook:

| Field | Required | Description |
| --- | --- | --- |
| `Country` | No | Country filter field used when `--geography` is provided. |
| `State` | No | Placeholder: geographic subdivision for the refinery record. |
| `Primary Owner` | No | Placeholder: primary owning company for the refinery asset. |

Notes:

- All refinery columns are converted into candidate asset tags during processing, not just the required fields.
- The `Name` value is shortened to the first `name_tolerance` words when building one set of name-based tags.

### Petchem Asset Fields

Required for petchem input:

| Field | Required | Description |
| --- | --- | --- |
| `PetchemID` | Yes | Unique petchem asset identifier. Placeholder: confirm whether this is an internal master asset ID. |
| `Company` | Yes | Company or asset label used to generate Google News search keywords. Placeholder: confirm the intended naming convention for external partners. |

Optional petchem fields observed in sample workbook:

| Field | Required | Description |
| --- | --- | --- |
| `Country` | No | Country filter field used when `--geography` is provided. |
| `Ownership` | No | Placeholder: ownership description for the petchem asset. |
| `Location` | No | Placeholder: asset location description. |
| `TRACE region` | No | Placeholder: region classification used by the source dataset. |

Notes:

- The pipeline uses `Company` values as Google News search keywords.
- `PetchemID`, `Company`, and `Country` are used to build asset tags when present.

## Tag Profile File

Purpose: supplies the required tag categories, output tags, and match phrases that are combined with asset-derived tags before matching articles.

Supported formats:

- `.xlsx`
- `.xls`
- `.csv`

Required fields:

| Field | Required | Description |
| --- | --- | --- |
| `tag_cat` | Yes | Tag category name. This becomes a column in the intermediate tagged article dataframe. Placeholder: confirm the standard category naming conventions partners should follow. |
| `tag` | Yes | Output tag value written into the final `tags` field when the phrase matches. Placeholder: confirm formatting rules such as spaces, casing, and separators. |
| `phrase` | Yes | Match phrase searched for in article title and description text. Matching is case-insensitive. Placeholder: confirm whether phrases should be exact names, aliases, keywords, or all of the above. |

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
| `asset_Name` | Sometimes | Asset or company name extracted from the matched asset tag. Placeholder: confirm whether this output label should remain `asset_Name` for both refinery and petchem rows. |
| `asset_Country` | Sometimes | Asset country tag match carried through when present in the tag reference. |
| Other `asset_*` or custom tag category columns | Sometimes | Intermediate category match columns may appear depending on which tag categories survive post-processing. Placeholder: confirm which of these should be considered supported output fields for partners. |

Notes:

- Output columns depend partly on the input asset columns and required tag profile categories.
- The pipeline removes several internal helper columns before writing output, including `id`, `desc_match`, and `value`.

## Sample Files In This Repo

These sample files help illustrate the supported shapes:

- `OG_AssetsFull.xlsx`
  - `RefiningAsset` columns: `Refinery #ID`, `Name`, `Country`, `State`, `Primary Owner`
  - `SteamCracker` columns: `PetchemID`, `Country`, `Company`, `Ownership`, `Location`, `TRACE region`
- `tagProfile.xlsx`
  - Columns: `tag`, `phrase`, `tag_cat`
- `Tag Profile_emissionMitigation.xlsx`
  - Columns: `tag_cat`, `tag`, `phrase`
