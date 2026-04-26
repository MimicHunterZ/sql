from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import ensure_indexes
from .schemas import (
    GameSummary,
    OverviewResponse,
    PredictPoint,
    PredictRequest,
    PredictResponse,
    TrendPoint,
    TrendResponse,
)
from .services.predictor import predict_next_7_days, weighted_moving_average
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
    result: list[GameSummary] = []
    for g in games:
        appid = int(g["appid"])
        result.append(
            GameSummary(
                appid=appid,
                name=str(g.get("name") or f"App {appid}"),
                current_ccu=latest_map.get(appid),
                tags=g.get("tags") or [],
                positive_ratio=g.get("positive_ratio"),
                price_usd=g.get("price_usd"),
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
