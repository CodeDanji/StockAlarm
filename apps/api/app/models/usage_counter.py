from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UsageCounter(Base):
    __tablename__ = "usage_counters"
    __table_args__ = (UniqueConstraint("user_id", "month_key", name="uq_usage_user_month"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    month_key: Mapped[str] = mapped_column(String(7))
    ai_generation_count: Mapped[int] = mapped_column(Integer, default=0)
    active_alert_count: Mapped[int] = mapped_column(Integer, default=0)
