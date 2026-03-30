from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrategyGenerateRequest(BaseModel):
    idea: str


class StrategyCandidate(BaseModel):
    title: str
    condition_dsl: str


class StrategyGenerateResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    scenarios: list[StrategyCandidate]
    model_used: str
