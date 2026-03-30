from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MeResponse(BaseModel):
    id: int
    email: str
    plan_tier: str
    timezone: str
    quiet_hours_start: str
    quiet_hours_end: str


class PreferencesPatchRequest(BaseModel):
    timezone: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class PreferencesPatchResponse(BaseModel):
    timezone: str
    quiet_hours_start: str
    quiet_hours_end: str
