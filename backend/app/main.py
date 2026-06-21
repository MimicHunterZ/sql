from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

MOCK_DIR = pathlib.Path(__file__).resolve().parents[1] / "data"


def _load_mock(filename: str) -> Any:
    with open(MOCK_DIR / filename, encoding="utf-8") as f:
        return json.load(f)

from .config import settings
from .database import db, ensure_indexes
from .schemas import (
    GameSummary,
    OverviewResponse,
    PredictPoint,
    PredictRequest,
    PredictResponse,
    TrendPoint,
    TrendResponse,
)
from .services.predictor import predict_next_7_days, predict_monthly_to_dec2026, weighted_moving_average
from .services.seed import seed_if_empty
from .services.queries import (
    get_game_name,
    get_latest_ccu_map,
    get_monitored_count,
    get_recent_n_points,
    get_top_game,
    get_trend_points,
    list_games,
)


app = FastAPI(title="Steam Hot Games Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    ensure_indexes()
    # Seed MongoDB from JSON files if collections are empty (fresh install)
    seed_if_empty(db)
    import subprocess, sys, threading
    from .services.queries import get_monitored_count
    if get_monitored_count() == 0:
        script = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "ingest_steam_data.py")
        threading.Thread(target=lambda: subprocess.run([sys.executable, script]), daemon=True).start()


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/games", response_model=List[GameSummary])
def api_games() -> List[GameSummary]:
    latest_map = get_latest_ccu_map()
    games = list_games()
    price_docs = {
        str(p["appid"]): p
        for p in db["price_history"].find(
            {},
            {"_id": 0, "appid": 1, "is_free": 1, "current_cny": 1, "current_discount": 1},
        )
    }
    result: list[GameSummary] = []
    for g in games:
        appid = int(g["appid"])
        price = price_docs.get(str(appid), {})
        result.append(
            GameSummary(
                appid=appid,
                name=str(g.get("name") or f"App {appid}"),
                current_ccu=latest_map.get(appid),
                tags=g.get("tags") or [],
                positive_ratio=g.get("positive_ratio"),
                price_usd=g.get("price_usd"),
                is_free=price.get("is_free"),
                current_cny=price.get("current_cny"),
                current_discount=price.get("current_discount"),
            )
        )
    result.sort(key=lambda x: x.current_ccu or 0, reverse=True)
    return result


@app.get("/api/trend/{game_id}", response_model=TrendResponse)
def api_trend(game_id: int, days: int = Query(default=30, ge=1, le=120)) -> TrendResponse:
    points = get_trend_points(game_id, days)
    if not points:
        raise HTTPException(status_code=404, detail="No trend data found for this game")
    return TrendResponse(
        appid=game_id,
        name=get_game_name(game_id),
        points=[TrendPoint(ts=p["ts"], ccu=int(p["ccu"])) for p in points],
    )


@app.post("/api/predict", response_model=PredictResponse)
def api_predict(payload: PredictRequest) -> PredictResponse:
    recent = get_recent_n_points(payload.gameId, 7)
    if not recent:
        raise HTTPException(status_code=400, detail="No historical data found for this game")
    # 数据不足3点时，用已有数据重复填充
    while len(recent) < 3:
        recent = [recent[0]] + recent

    preds = predict_next_7_days(recent, payload.discount_rate, payload.update_quality)
    return PredictResponse(
        appid=payload.gameId,
        name=get_game_name(payload.gameId),
        base_mean=weighted_moving_average(recent),
        discount_rate=payload.discount_rate,
        update_quality=payload.update_quality,
        points=[PredictPoint(day_offset=i + 1, predicted_ccu=v) for i, v in enumerate(preds)],
    )


@app.get("/api/overview", response_model=OverviewResponse)
def api_overview() -> OverviewResponse:
    latest_map = get_latest_ccu_map()
    monitored = get_monitored_count()

    top_appid, top_ccu = get_top_game(latest_map)
    top_name = get_game_name(top_appid) if top_appid is not None else None

    warning = "normal"
    if top_ccu is not None and top_ccu > 1_000_000:
        warning = "high_peak_risk"
    elif top_ccu is not None and top_ccu > 500_000:
        warning = "attention"

    return OverviewResponse(
        monitored_games=monitored,
        top_game_appid=top_appid,
        top_game_name=top_name,
        top_game_ccu=top_ccu,
        warning=warning,
    )


@app.post("/api/ingest")
def api_ingest() -> dict:
    import subprocess, sys
    script = str(__import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "ingest_steam_data.py")
    subprocess.Popen([sys.executable, script])
    return {"status": "started"}


# ── Mock-data endpoints (now served from MongoDB) ─────────────────────────────

def _history_from_db(appid: int) -> Optional[Dict]:
    """Query ccu_timeseries for steamcharts monthly history of one game."""
    docs = list(
        db["ccu_timeseries"].find(
            {"appid": appid, "source": "steamcharts_monthly"},
            sort=[("ts", -1)],   # newest first, same order as original JSON
        )
    )
    if not docs:
        return None

    # Game name from game_info (fall back to "App {appid}")
    info = db["game_info"].find_one({"appid": appid}, {"name": 1})
    name = (info or {}).get("name") or f"App {appid}"

    history = []
    for i, doc in enumerate(docs):
        month_str = doc["ts"].strftime("%B %Y")
        # Compute gain_pct dynamically (compare to previous month = next index)
        if i + 1 < len(docs):
            prev = docs[i + 1].get("ccu") or 0
            curr = doc.get("ccu") or 0
            if prev > 0:
                pct = (curr - prev) / prev * 100
                gain_str = f"+{pct:.2f}%" if pct >= 0 else f"{pct:.2f}%"
            else:
                gain_str = "-"
        else:
            gain_str = "-"
        history.append({
            "month":       month_str,
            "avg_players": doc.get("ccu", 0),
            "peak_players":doc.get("peak_ccu", 0),
            "gain_pct":    gain_str,
        })
    return {"appid": str(appid), "name": name, "history": history}


@app.get("/api/history/{game_id}")
def api_history(game_id: str) -> Dict:
    """Return SteamCharts monthly CCU history for one game (from MongoDB)."""
    try:
        appid = int(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="game_id must be numeric")
    result = _history_from_db(appid)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No history data for appid {game_id}")
    return result


@app.get("/api/compare")
def api_compare(ids: str = Query(..., description="Comma-separated appids")) -> List[Dict]:
    """Return monthly CCU history for multiple games (from MongoDB)."""
    result = []
    for token in ids.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            appid = int(token)
        except ValueError:
            continue
        data = _history_from_db(appid)
        if data:
            result.append(data)
    if not result:
        raise HTTPException(status_code=404, detail="None of the requested appids found")
    return result


@app.get("/api/market")
def api_market() -> List[Dict]:
    """Return all CS2 market items summary with category and image (from MongoDB)."""
    items = db["market_items"].find({}, {"_id": 0, "price_history": 0, "icon_url": 0})
    return list(items)


@app.get("/api/market/item")
def api_market_item(name: str = Query(..., description="Item name (URL-decoded)")) -> Dict:
    """Return full price history for a single CS2 market item (from MongoDB)."""
    decoded = unquote(name)
    item = db["market_items"].find_one({"name": decoded}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail=f"Item not found: {decoded}")
    return item


@app.get("/api/gamedetail/{game_id}")
def api_game_detail(game_id: str) -> Dict:
    """Return Steam store details for a game (from MongoDB)."""
    doc = db["game_details"].find_one({"appid": game_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"No detail data for appid {game_id}")
    return doc


@app.get("/api/price/{game_id}")
def api_price(game_id: str) -> Dict:
    """Return CNY price history for a game (from MongoDB price_history collection)."""
    doc = db["price_history"].find_one({"appid": game_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"No price data for appid {game_id}")
    return doc


@app.get("/api/predict/monthly/{game_id}")
def api_predict_monthly(
    game_id: str,
    discount_rate: float = Query(default=20, ge=0, le=100),
    update_quality: float = Query(default=6, ge=0, le=10),
) -> Dict:
    """
    Monthly avg_players predictions through December 2026
    using seasonal decomposition + trend + what-if params (from MongoDB).
    """
    try:
        appid = int(game_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="game_id must be numeric")
    result = _history_from_db(appid)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No history data for appid {game_id}")
    predictions = predict_monthly_to_dec2026(result["history"], discount_rate, update_quality)
    return {
        "appid": game_id,
        "name":  result["name"],
        "predictions": predictions,
    }
