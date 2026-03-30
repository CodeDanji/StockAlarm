from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.security import get_current_user_id
from app.db.session import SessionLocal
from app.models.alert_rule import AlertRule
from app.schemas.alerts import AlertCreateRequest, AlertResponse
from app.services.usage_service import assert_can_create_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreateRequest,
    user_id: int = Depends(get_current_user_id),
) -> AlertResponse:
    with SessionLocal() as db:
        try:
            assert_can_create_alert(db, user_id=user_id, active=payload.active)
        except LookupError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        except PermissionError as exc:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=str(exc),
            ) from exc

        row = AlertRule(
            user_id=user_id,
            name=payload.name,
            condition_dsl=payload.condition_dsl,
            mode=payload.mode,
            cooldown_minutes_market=payload.cooldown_minutes_market,
            active=payload.active,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return AlertResponse(
            id=row.id,
            name=row.name,
            mode=row.mode,
            active=row.active,
        )


@router.get("", response_model=list[AlertResponse])
def list_alerts(user_id: int = Depends(get_current_user_id)) -> list[AlertResponse]:
    with SessionLocal() as db:
        rows = db.scalars(select(AlertRule).where(AlertRule.user_id == user_id)).all()
        return [
            AlertResponse(
                id=row.id,
                name=row.name,
                mode=row.mode,
                active=row.active,
            )
            for row in rows
        ]
