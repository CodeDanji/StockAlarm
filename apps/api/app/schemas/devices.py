from __future__ import annotations

from pydantic import BaseModel


class DeviceRegisterRequest(BaseModel):
    fcm_token: str
    platform: str = "web"


class DeviceRegisterResponse(BaseModel):
    id: int
    fcm_token: str
