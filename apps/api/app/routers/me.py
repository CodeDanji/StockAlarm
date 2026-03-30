from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.security import get_current_user_id
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.preferences import (
    MeResponse,
    PreferencesPatchRequest,
    PreferencesPatchResponse,
)

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeResponse)
def get_me(user_id: int = Depends(get_current_user_id)) -> MeResponse:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user not found",
            )
        return MeResponse(
            id=user.id,
            email=user.email,
            plan_tier=user.plan_tier,
            timezone=user.timezone,
            quiet_hours_start=user.quiet_hours_start,
            quiet_hours_end=user.quiet_hours_end,
        )


@router.patch("/me/preferences", response_model=PreferencesPatchResponse)
def patch_preferences(
    payload: PreferencesPatchRequest,
    user_id: int = Depends(get_current_user_id),
) -> PreferencesPatchResponse:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user not found",
            )

        if payload.timezone is not None:
            user.timezone = payload.timezone
        if payload.quiet_hours_start is not None:
            user.quiet_hours_start = payload.quiet_hours_start
        if payload.quiet_hours_end is not None:
            user.quiet_hours_end = payload.quiet_hours_end

        db.commit()
        db.refresh(user)

    return PreferencesPatchResponse(
        timezone=user.timezone,
        quiet_hours_start=user.quiet_hours_start,
        quiet_hours_end=user.quiet_hours_end,
    )
