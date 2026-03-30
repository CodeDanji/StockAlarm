from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert_rule import AlertRule
from app.models.user import User


def _alert_limit_for_plan(plan_tier: str) -> int:
    return 3 if plan_tier == "free" else 20


def assert_can_create_alert(db: Session, *, user_id: int, active: bool) -> None:
    if not active:
        return

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise LookupError("user not found")

    active_count = (
        db.scalar(
            select(func.count())
            .select_from(AlertRule)
            .where(AlertRule.user_id == user_id, AlertRule.active.is_(True))
        )
        or 0
    )
    limit = _alert_limit_for_plan(user.plan_tier)
    if active_count >= limit:
        raise PermissionError("alert limit exceeded")
