from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv


load_dotenv()


def _parse_csv_to_int_list(raw: str) -> List[int]:
    result: List[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            result.append(int(token))
        except ValueError:
            continue
    return result


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    mongo_db: str
    target_app_ids: List[int]
    allowed_origins: List[str]
    http_proxy: str


def get_settings() -> Settings:
    target_default = "730,570,578080,271590,1172470,440,252490,4000"
    origins_default = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:5174,http://localhost:5174"

    return Settings(
        mongo_uri=os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017"),
        mongo_db=os.getenv("MONGO_DB", "steam_hot_games"),
        target_app_ids=_parse_csv_to_int_list(os.getenv("TARGET_APP_IDS", target_default)),
        allowed_origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS", origins_default).split(",") if x.strip()],
        http_proxy=os.getenv("HTTP_PROXY", ""),
    )


settings = get_settings()
