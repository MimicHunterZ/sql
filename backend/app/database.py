from __future__ import annotations

from datetime import datetime, timezone

from pymongo import ASCENDING, MongoClient

from .config import settings


client = MongoClient(settings.mongo_uri)
db = client[settings.mongo_db]

game_info_col = db["game_info"]
ccu_col = db["ccu_timeseries"]


def ensure_indexes() -> None:
    game_info_col.create_index([("appid", ASCENDING)], unique=True, name="uniq_appid")
    ccu_col.create_index([("appid", ASCENDING), ("ts", ASCENDING)], unique=True, name="uniq_appid_ts")
    ccu_col.create_index([("ts", ASCENDING)], name="idx_ts")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
