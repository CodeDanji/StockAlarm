from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.security import get_current_user_id
from app.db.session import SessionLocal
from app.models.device import Device
from app.schemas.devices import DeviceRegisterRequest, DeviceRegisterResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/register", response_model=DeviceRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    payload: DeviceRegisterRequest,
    user_id: int = Depends(get_current_user_id),
) -> DeviceRegisterResponse:
    with SessionLocal() as db:
        row = Device(user_id=user_id, fcm_token=payload.fcm_token, platform=payload.platform)
        db.add(row)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="device token already registered",
            ) from exc
        db.refresh(row)
        return DeviceRegisterResponse(id=row.id, fcm_token=row.fcm_token)
