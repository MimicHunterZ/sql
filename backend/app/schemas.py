from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class GameSummary(BaseModel):
    appid: int
    name: str
    current_ccu: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    positive_ratio: Optional[float] = None
    price_usd: Optional[float] = None
    is_free: Optional[bool] = None
    current_cny: Optional[float] = None
    current_discount: Optional[int] = None


class TrendPoint(BaseModel):
    ts: datetime
    ccu: int


class TrendResponse(BaseModel):
    appid: int
    name: str
    points: List[TrendPoint]


class PredictRequest(BaseModel):
    gameId: int
    discount_rate: float = Field(ge=0, le=100)
    update_quality: float = Field(ge=0, le=10)


class PredictPoint(BaseModel):
    day_offset: int
    predicted_ccu: int


class PredictResponse(BaseModel):
    appid: int
    name: str
    base_mean: float
    discount_rate: float
    update_quality: float
    points: List[PredictPoint]


class OverviewResponse(BaseModel):
    monitored_games: int
    top_game_appid: Optional[int] = None
    top_game_name: Optional[str] = None
    top_game_ccu: Optional[int] = None
    warning: str
