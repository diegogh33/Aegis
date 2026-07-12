from enum import Enum

from pydantic import BaseModel


class WatchlistStatus(str, Enum):
    CORE = "core"
    CANDIDATE = "candidate"
    REJECTED = "rejected"
    HOLD = "hold"


class WatchlistEntry(BaseModel):
    ticker: str
    status: WatchlistStatus
    notes: str | None = None