"""
Database seeder — runs on every startup, skips if data already present.

JSON files in data/ are the canonical "seed sources".
On a fresh install (empty MongoDB), this imports everything automatically:
  - steamcharts_history.json  →  ccu_timeseries  (steamcharts_monthly)
  - cs2_market_items.json     →  market_items
  - steam_game_details.json   →  game_details
"""
from __future__ import annotations

import json
import logging
import pathlib
from datetime import datetime

from pymongo.database import Database
from pymongo.errors import BulkWriteError

logger = logging.getLogger(__name__)

MOCK_DIR = pathlib.Path(__file__).resolve().parents[2] / "data"


def _load_mock(filename: str):
    with open(MOCK_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def seed_if_empty(db: Database) -> None:
    """Entry point — call this at application startup."""
    _seed_steamcharts(db)
    _seed_market_items(db)
    _seed_game_details(db)
    _seed_price_history(db)


# ── Steamcharts monthly history ───────────────────────────────────────────────

def _seed_steamcharts(db: Database) -> None:
    ccu_col  = db["ccu_timeseries"]
    info_col = db["game_info"]

    if ccu_col.count_documents({"source": "steamcharts_monthly"}) > 0:
        logger.info("seed: ccu_timeseries already populated, skip")
        return

    logger.info("seed: importing steamcharts_history.json …")
    data = _load_mock("steamcharts_history.json")

    docs = []
    for appid_str, game in data.items():
        appid = int(appid_str)
        name  = game.get("name", f"App {appid}")

        # Upsert game name into game_info
        info_col.update_one(
            {"appid": appid},
            {"$setOnInsert": {"appid": appid, "name": name}},
            upsert=True,
        )

        for row in game.get("history", []):
            try:
                ts = datetime.strptime(row["month"], "%B %Y")
            except (ValueError, KeyError):
                continue
            docs.append({
                "appid":     appid,
                "ts":        ts,
                "ccu":       float(row.get("avg_players", 0)),
                "peak_ccu":  float(row.get("peak_players", 0)),
                "gain_pct":  row.get("gain_pct", ""),
                "source":    "steamcharts_monthly",
            })

    if docs:
        try:
            ccu_col.insert_many(docs, ordered=False)
            logger.info("seed: inserted %d CCU records", len(docs))
        except BulkWriteError as e:
            inserted = e.details.get("nInserted", 0)
            logger.info("seed: inserted %d CCU records (skipped duplicates)", inserted)


# ── CS2 market items ──────────────────────────────────────────────────────────

def _seed_market_items(db: Database) -> None:
    col = db["market_items"]
    if col.count_documents({}) > 0:
        logger.info("seed: market_items already populated, skip")
        return

    logger.info("seed: importing cs2_market_items.json …")
    data = _load_mock("cs2_market_items.json")
    col.insert_many(data)
    col.create_index("name", unique=True, name="uniq_name")
    logger.info("seed: inserted %d market items", len(data))


# ── Steam game details ────────────────────────────────────────────────────────

def _seed_game_details(db: Database) -> None:
    col = db["game_details"]
    if col.count_documents({}) > 0:
        logger.info("seed: game_details already populated, skip")
        return

    logger.info("seed: importing steam_game_details.json …")
    data = _load_mock("steam_game_details.json")
    docs = [{"appid": k, **v} for k, v in data.items()]
    col.insert_many(docs)
    col.create_index("appid", unique=True, name="uniq_appid")
    logger.info("seed: inserted %d game detail records", len(docs))


# ── Steam price history (CNY) ─────────────────────────────────────────────────

def _seed_price_history(db: Database) -> None:
    col = db["price_history"]
    if col.count_documents({}) > 0:
        logger.info("seed: price_history already populated, skip")
        return

    logger.info("seed: importing steam_price_history.json …")
    data = _load_mock("steam_price_history.json")
    docs = list(data.values())
    col.insert_many(docs)
    col.create_index("appid", unique=True, name="uniq_appid")
    logger.info("seed: inserted %d price history records", len(docs))
