from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.auth import GoogleTokenLoginRequest, TokenResponse
from app.services import google_auth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google/token", response_model=TokenResponse)
def google_token_login(payload: GoogleTokenLoginRequest) -> TokenResponse:
    try:
        token_info = google_auth.verify_google_id_token(payload.id_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid google token",
        ) from exc

    email = token_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="email not present in token",
        )

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                plan_tier="free",
                timezone="Asia/Seoul",
                quiet_hours_start="23:00",
                quiet_hours_end="07:00",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))
