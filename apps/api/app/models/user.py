from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    plan_tier: Mapped[str] = mapped_column(String(20), default="free")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Seoul")
    quiet_hours_start: Mapped[str] = mapped_column(String(5), default="23:00")
    quiet_hours_end: Mapped[str] = mapped_column(String(5), default="07:00")
