#!/usr/bin/env python3
"""
merge_save.py — merge scraped SteamCharts data into the project data file.

Usage:
  python3 merge_save.py --data-file backend/data/steamcharts_history.json \
                        --new-data  /tmp/scraped.json

--new-data should be a JSON file with the same structure as steamcharts_history.json:
  { "APP_ID": { "appid": "...", "name": "...", "history": [...] }, ... }

Existing AppIDs are overwritten; all other AppIDs are preserved.
"""
import argparse
import json
import pathlib
import sys


def main():
    parser = argparse.ArgumentParser(description="Merge scraped SteamCharts data")
    parser.add_argument("--data-file", required=True, help="Path to steamcharts_history.json")
    parser.add_argument("--new-data",  required=True, help="Path to scraped JSON (same format)")
    args = parser.parse_args()

    data_file = pathlib.Path(args.data_file)
    new_file  = pathlib.Path(args.new_data)

    if not new_file.exists():
        print(f"ERROR: new-data file not found: {new_file}", file=sys.stderr)
        sys.exit(1)

    new_data = json.loads(new_file.read_text(encoding="utf-8"))
    existing = json.loads(data_file.read_text(encoding="utf-8")) if data_file.exists() else {}

    before = len(existing)
    existing.update(new_data)
    after  = len(existing)

    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    added   = after - before
    updated = len(new_data) - added
    print(f"✓ {data_file}")
    print(f"  {updated} game(s) updated, {added} game(s) added → {after} total")


if __name__ == "__main__":
    main()
