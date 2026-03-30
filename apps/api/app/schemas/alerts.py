from __future__ import annotations

from pydantic import BaseModel, Field


class AlertCreateRequest(BaseModel):
    name: str
    condition_dsl: str
    mode: str = Field(pattern="^[AB]$")
    cooldown_minutes_market: int = Field(default=120, ge=1)
    active: bool = True


class AlertResponse(BaseModel):
    id: int
    name: str
    mode: str
    active: bool
