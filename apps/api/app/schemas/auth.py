from __future__ import annotations

from pydantic import BaseModel


class GoogleTokenLoginRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
