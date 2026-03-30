from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.security import get_current_user_id
from app.schemas.strategies import StrategyGenerateRequest, StrategyGenerateResponse
from app.services.strategy_service import generate_strategies

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.post("/generate", response_model=StrategyGenerateResponse)
def generate_strategy(
    payload: StrategyGenerateRequest,
    _: int = Depends(get_current_user_id),
) -> StrategyGenerateResponse:
    scenarios, model_used = generate_strategies(payload.idea)
    return StrategyGenerateResponse(scenarios=scenarios, model_used=model_used)
