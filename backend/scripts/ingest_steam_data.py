from __future__ import annotations

import logging
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from pymongo import MongoClient, UpdateOne

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("steam_ingestion")


STEAM_CURRENT_PLAYERS_API = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
STEAMSPY_APPDETAILS_API = "https://steamspy.com/api.php?request=appdetails&appid={appid}"
STEAMSPY_TOP100_API = "https://steamspy.com/api.php?request=top100in2weeks"
STEAM_STORE_APPDETAILS_API = "https://store.steampowered.com/api/appdetails?appids={appid}&l=english"
STEAMDB_APP_URL = "https://steamdb.info/app/{appid}/"
STORE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}


def get_http_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    adapter = requests.adapters.HTTPAdapter(max_retries=2)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    if settings.http_proxy:
        session.proxies = {"http": settings.http_proxy, "https": settings.http_proxy}
    return session


def floor_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def to_float_or_none(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        fv = float(v)
        if math.isnan(fv) or math.isinf(fv):
            return None
        return fv
    except (TypeError, ValueError):
        return None


def fetch_current_ccu(session: requests.Session, appid: int) -> Optional[int]:
    url = STEAM_CURRENT_PLAYERS_API.format(appid=appid)
    try:
        resp = session.get(url, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        value = payload.get("response", {}).get("player_count")
        if value is None:
            return None
        return int(value)
    except Exception as exc:
        logger.warning("Failed CCU fetch for %s: %s", appid, exc)
        return None


def fetch_top100_appids(session: requests.Session, limit: int = 20) -> List[int]:
    try:
        resp = session.get(STEAMSPY_TOP100_API, timeout=20)
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [int(v["appid"]) for v in list(data.values())[:limit] if v.get("appid")]
    except Exception as exc:
        logger.info("SteamSpy top100 skip: %s", exc)
        return []


def parse_tags_from_steamspy(raw_tags: Any) -> List[str]:
    if isinstance(raw_tags, dict):
        return [str(k) for k in raw_tags.keys()][:20]
    return []


def fetch_steamspy_details(session: requests.Session, appid: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    url = STEAMSPY_APPDETAILS_API.format(appid=appid)
    try:
        resp = session.get(url, headers=STORE_HEADERS, timeout=20)
        if resp.status_code != 200:
            return result
        data = resp.json()

        positive = int(data.get("positive") or 0)
        negative = int(data.get("negative") or 0)
        total = positive + negative
        ratio = (positive / total) if total > 0 else None

        result = {
            "name": data.get("name"),
            "owners_estimate": data.get("owners"),
            "positive_ratio": ratio,
            "tags": parse_tags_from_steamspy(data.get("tags")),
        }
    except Exception as exc:
        logger.info("SteamSpy detail skip %s: %s", appid, exc)
    return result


def fetch_store_details(session: requests.Session, appid: int) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    url = STEAM_STORE_APPDETAILS_API.format(appid=appid)
    try:
        resp = session.get(url, headers=STORE_HEADERS, timeout=20)
        if resp.status_code != 200:
            return result
        payload = resp.json().get(str(appid), {})
        if not payload.get("success"):
            return result
        data = payload.get("data", {})

        genres = data.get("genres") or []
        tags = [g.get("description") for g in genres if g.get("description")]

        price_obj = data.get("price_overview") or {}
        final_cents = to_float_or_none(price_obj.get("final"))
        price_usd = (final_cents / 100.0) if final_cents is not None else None

        result = {
            "name": data.get("name"),
            "tags": tags[:20],
            "price_usd": price_usd,
            "release_date": (data.get("release_date") or {}).get("date"),
            "current_price_usd": price_usd,
        }
    except Exception as exc:
        logger.info("Steam Store detail skip %s: %s", appid, exc)
    return result


STEAMCHARTS_APP_URL = "https://steamcharts.com/app/{appid}"


def fetch_steamcharts_history(session: requests.Session, appid: int) -> List[Dict[str, Any]]:
    import re, subprocess
    url = STEAMCHARTS_APP_URL.format(appid=appid)
    results = []
    try:
        proxy = settings.http_proxy
        cmd = ["curl", "-s", "--max-time", "20", "-H", f"User-Agent: {STORE_HEADERS['User-Agent']}"]
        if proxy:
            cmd += ["--proxy", proxy]
        cmd.append(url)
        html = subprocess.check_output(cmd, timeout=25).decode("utf-8", errors="ignore")
        rows = re.findall(r'<td[^>]*>(.*?)</td>', html, re.DOTALL)
        i = 0
        while i + 4 < len(rows):
            month_raw = re.sub(r'<[^>]+>', '', rows[i]).strip()
            avg_raw = rows[i + 1].strip()
            peak_raw = rows[i + 4].strip()
            if re.match(r'\w+ \d{4}', month_raw):
                try:
                    ts = datetime.strptime(month_raw, "%B %Y").replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0,
                        tzinfo=timezone.utc
                    )
                    avg = int(float(avg_raw.replace(",", "")))
                    peak = int(peak_raw.replace(",", ""))
                    results.append({"ts": ts, "avg_ccu": avg, "peak_ccu": peak})
                except (ValueError, AttributeError):
                    pass
            i += 5
    except Exception as exc:
        logger.info("SteamCharts history skip %s: %s", appid, exc)
    return results


def build_game_info_doc(appid: int, ccu: int, now: datetime, spy: Dict[str, Any], store: Dict[str, Any], steamdb_peak: Optional[int] = None) -> Dict[str, Any]:
    name = store.get("name") or spy.get("name") or f"App {appid}"

    tags = []
    if store.get("tags"):
        tags = store["tags"]
    elif spy.get("tags"):
        tags = spy["tags"]

    positive_ratio = spy.get("positive_ratio")
    price_usd = store.get("price_usd")

    doc: Dict[str, Any] = {
        "appid": appid,
        "name": name,
        "tags": tags,
        "owners_estimate": spy.get("owners_estimate"),
        "positive_ratio": positive_ratio,
        "price_usd": price_usd,
        "release_date": store.get("release_date"),
        "current_ccu": ccu,
        "last_synced_at": now,
        "steamdb_peak_ccu": steamdb_peak,
        "source_status": {
            "ccu": "ok",
            "steamspy": "ok" if spy else "degraded",
            "store": "ok" if store else "degraded",
        },
    }
    return doc


def run_once() -> None:
    client = MongoClient(settings.mongo_uri)
    db = client[settings.mongo_db]
    game_info_col = db["game_info"]
    ccu_col = db["ccu_timeseries"]

    try:
        game_info_col.create_index([("appid", 1)], unique=True)
    except Exception:
        pass
    try:
        ccu_col.create_index([("appid", 1), ("ts", 1)], unique=True)
        ccu_col.create_index([("ts", 1)])
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    ts_hour = floor_to_hour(now)

    session = get_http_session()
    ccu_ops: List[UpdateOne] = []
    info_ops: List[UpdateOne] = []

    # 合并配置列表 + SteamSpy top20 热门游戏
    top_ids = fetch_top100_appids(session, limit=20)
    all_appids = list(dict.fromkeys(settings.target_app_ids + top_ids))
    logger.info("Monitoring %s games (config=%s, top100=%s)", len(all_appids), len(settings.target_app_ids), len(top_ids))

    success_count = 0
    for appid in all_appids:
        ccu = fetch_current_ccu(session, appid)
        if ccu is None:
            continue

        spy = fetch_steamspy_details(session, appid)
        store = fetch_store_details(session, appid)
        info_doc = build_game_info_doc(appid, ccu, now, spy, store)

        # SteamCharts 历史月度数据
        history = fetch_steamcharts_history(session, appid)
        for h in history:
            ccu_ops.append(UpdateOne(
                {"appid": appid, "ts": h["ts"]},
                {"$set": {"appid": appid, "ts": h["ts"], "ccu": h["avg_ccu"], "peak_ccu": h["peak_ccu"], "source": "steamcharts_monthly"}},
                upsert=True,
            ))

        ccu_ops.append(
            UpdateOne(
                {"appid": appid, "ts": ts_hour},
                {
                    "$set": {
                        "appid": appid,
                        "ts": ts_hour,
                        "ccu": ccu,
                        "source": "steam_official",
                        "captured_at": now,
                    }
                },
                upsert=True,
            )
        )

        info_ops.append(
            UpdateOne(
                {"appid": appid},
                {
                    "$set": info_doc,
                    "$min": {"historical_lowest_price": info_doc["price_usd"]} if info_doc.get("price_usd") is not None else {},
                },
                upsert=True,
            )
        )
        success_count += 1

    if ccu_ops:
        ccu_col.bulk_write(ccu_ops, ordered=False)
    if info_ops:
        game_info_col.bulk_write(info_ops, ordered=False)

    logger.info("Ingestion completed. success=%s total=%s", success_count, len(settings.target_app_ids))


if __name__ == "__main__":
    run_once()
