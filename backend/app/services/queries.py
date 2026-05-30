from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

from ..database import ccu_col, game_info_col


def get_latest_ccu_map() -> Dict[int, int]:
    pipeline = [
        {"$sort": {"appid": 1, "ts": -1}},
        {
            "$group": {
                "_id": "$appid",
                "ccu": {"$first": "$ccu"},
            }
        },
    ]
    docs = list(ccu_col.aggregate(pipeline))
    return {int(d["_id"]): int(d["ccu"]) for d in docs}


def list_games() -> List[dict]:
    return list(game_info_col.find({}, {"_id": 0}))


def get_monitored_count() -> int:
    return int(game_info_col.count_documents({}))


def get_game_name(appid: int) -> str:
    doc = game_info_col.find_one({"appid": appid}, {"_id": 0, "name": 1})
    if doc and doc.get("name"):
        return str(doc["name"])
    return f"App {appid}"


def get_trend_points(appid: int, days: int) -> List[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    cursor = ccu_col.find(
        {"appid": appid, "ts": {"$gte": since}},
        {"_id": 0, "ts": 1, "ccu": 1},
    ).sort("ts", 1)
    return list(cursor)


def get_recent_n_points(appid: int, n: int = 7) -> List[int]:
    since = datetime.now(timezone.utc) - timedelta(days=n)
    docs = list(
        ccu_col.find({"appid": appid, "ts": {"$gte": since}}, {"_id": 0, "ccu": 1}).sort("ts", 1)
    )
    return [int(d["ccu"]) for d in docs]


def get_top_game(latest_map: Dict[int, int]) -> Tuple[int | None, int | None]:
    if not latest_map:
        return None, None
    appid = max(latest_map, key=latest_map.get)
    return appid, latest_map[appid]
