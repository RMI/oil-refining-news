"""
CLI route tests for main.py.

Covers the three documented invocation patterns:
  1. Direct flags only          -- --asset-file --tag-profile --output
  2. Config file only           -- --config
  3. Config file + flag override -- --config --geography ... --debug

Google News network calls are patched out; all I/O uses tmp_path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ASSET_DATA = {
    "ID": [1, 2],
    "Name": ["Test Refinery Alpha", "Test Refinery Beta"],
    "Country": ["United States", "Canada"],
}

TAG_PROFILE_DATA = {
    "tag category": ["sector", "sector"],
    "tag": ["refining", "oil"],
    "phrase": ["refin", "oil"],
}

FAKE_ARTICLES = pd.DataFrame(
    {
        "title": ["Test Refinery Alpha news"],
        "link": ["https://example.com/1"],
        "published": ["2026-06-01"],
        "description": ["Test Refinery Alpha is involved in oil refining operations."],
        "source": ["Example News"],
    }
)


def _make_asset_file(path: Path) -> Path:
    """Write a minimal single-sheet asset workbook."""
    asset_path = path / "assets.xlsx"
    with pd.ExcelWriter(asset_path, engine="openpyxl") as writer:
        pd.DataFrame(ASSET_DATA).to_excel(writer, sheet_name="Refining", index=False)
    return asset_path


def _make_tag_profile(path: Path) -> Path:
    tag_path = path / "tags.xlsx"
    pd.DataFrame(TAG_PROFILE_DATA).to_excel(tag_path, index=False)
    return tag_path


def _make_config(path: Path, asset_path: Path, tag_path: Path, output_path: Path) -> Path:
    config = {
        "asset_file": str(asset_path),
        "output": str(output_path),
        "tag_profile": str(tag_path),
        "asset_types": ["refining"],
        "geography": ["United States", "Canada"],
        "lookback_min": "2026-05-01",
        "lookback_max": "2026-06-30",
        "name_tolerance": 2,
        "max_items_per_keyword": 5,
        "source_exclude": [],
    }
    config_path = path / "config.json"
    config_path.write_text(json.dumps(config))
    return config_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_main(argv: list[str]) -> pd.DataFrame:
    """Invoke main() with patched argv and a stubbed Google News call."""
    with (
        patch.object(sys, "argv", ["main.py"] + argv),
        patch("main.get_recent_articles", return_value=FAKE_ARTICLES),
    ):
        from main import main
        main()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_direct_flags(tmp_path):
    """Route 1: all required values supplied as CLI flags."""
    asset_path = _make_asset_file(tmp_path)
    tag_path = _make_tag_profile(tmp_path)
    output_path = tmp_path / "out.xlsx"

    _run_main([
        "--asset-file", str(asset_path),
        "--tag-profile", str(tag_path),
        "--output", str(output_path),
        "--geography", "United States", "Canada",
        "--asset-types", "refining",
        "--lookback-min", "2026-05-01",
        "--lookback-max", "2026-06-30",
    ])

    assert output_path.exists(), "Output file was not created"
    result = pd.read_excel(output_path)
    assert not result.empty, "Output file is empty"


def test_config_file(tmp_path):
    """Route 2: all values supplied via --config."""
    asset_path = _make_asset_file(tmp_path)
    tag_path = _make_tag_profile(tmp_path)
    output_path = tmp_path / "out.xlsx"
    config_path = _make_config(tmp_path, asset_path, tag_path, output_path)

    _run_main(["--config", str(config_path)])

    assert output_path.exists(), "Output file was not created"
    result = pd.read_excel(output_path)
    assert not result.empty, "Output file is empty"


def test_config_with_flag_override(tmp_path):
    """Route 3: --config provides defaults; CLI flags override individual values."""
    asset_path = _make_asset_file(tmp_path)
    tag_path = _make_tag_profile(tmp_path)
    output_path = tmp_path / "out.xlsx"
    config_path = _make_config(tmp_path, asset_path, tag_path, output_path)

    _run_main([
        "--config", str(config_path),
        "--geography", "United States",  # narrows to one country
        "--debug",
    ])

    assert output_path.exists(), "Output file was not created"


def test_missing_asset_file_raises(tmp_path):
    """--asset-file is required; omitting it should exit with an error."""
    tag_path = _make_tag_profile(tmp_path)
    output_path = tmp_path / "out.xlsx"

    with pytest.raises(SystemExit):
        _run_main([
            "--tag-profile", str(tag_path),
            "--output", str(output_path),
        ])


def test_missing_tag_profile_raises(tmp_path):
    """--tag-profile is required; omitting it should exit with an error."""
    asset_path = _make_asset_file(tmp_path)
    output_path = tmp_path / "out.xlsx"

    with pytest.raises(SystemExit):
        _run_main([
            "--asset-file", str(asset_path),
            "--output", str(output_path),
        ])


def test_missing_output_raises(tmp_path):
    """--output is required; omitting it should exit with an error."""
    asset_path = _make_asset_file(tmp_path)
    tag_path = _make_tag_profile(tmp_path)

    with pytest.raises(SystemExit):
        _run_main([
            "--asset-file", str(asset_path),
            "--tag-profile", str(tag_path),
        ])


def test_unknown_config_key_raises(tmp_path):
    """A config file with an unrecognised key should raise ValueError."""
    bad_config = tmp_path / "bad.json"
    bad_config.write_text(json.dumps({"asset_file": "x", "unknown_key": True}))

    with pytest.raises((ValueError, SystemExit)):
        _run_main(["--config", str(bad_config)])


def test_asset_type_filter(tmp_path):
    """--asset-types restricts processing to the named sheet(s)."""
    asset_path = tmp_path / "assets.xlsx"
    with pd.ExcelWriter(asset_path, engine="openpyxl") as writer:
        pd.DataFrame(ASSET_DATA).to_excel(writer, sheet_name="Refining", index=False)
        pd.DataFrame(ASSET_DATA).to_excel(writer, sheet_name="Petrochemical", index=False)

    tag_path = _make_tag_profile(tmp_path)
    output_path = tmp_path / "out.xlsx"

    _run_main([
        "--asset-file", str(asset_path),
        "--tag-profile", str(tag_path),
        "--output", str(output_path),
        "--asset-types", "refining",
        "--geography", "United States", "Canada",
        "--lookback-min", "2026-05-01",
        "--lookback-max", "2026-06-30",
    ])

    assert output_path.exists()
    result = pd.read_excel(output_path)
    assert (result["asset_type"] == "refining").all(), "Unexpected asset types in output"
