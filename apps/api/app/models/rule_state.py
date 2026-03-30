from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RuleState(Base):
    __tablename__ = "rule_states"

    rule_id: Mapped[int] = mapped_column(
        ForeignKey("alert_rules.id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_state_bool: Mapped[bool | None] = mapped_column(nullable=True)
    last_trigger_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
