from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.security import get_current_user_id
from app.db.session import SessionLocal
from app.models.usage_counter import UsageCounter
from app.models.user import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/usage")
def get_usage(user_id: int = Depends(get_current_user_id)) -> dict:
    month_key = datetime.now(timezone.utc).strftime("%Y-%m")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user not found",
            )
        usage = db.scalar(
            select(UsageCounter).where(
                UsageCounter.user_id == user_id,
                UsageCounter.month_key == month_key,
            )
        )
        return {
            "plan_tier": user.plan_tier,
            "month_key": month_key,
            "ai_generation_count": usage.ai_generation_count if usage else 0,
            "active_alert_count": usage.active_alert_count if usage else 0,
        }
