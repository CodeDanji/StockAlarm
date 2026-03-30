from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.base import Base
from app.models.device import Device
from app.models.user import User


def test_unique_email_and_fcm_token_constraints() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        u1 = User(email="a@example.com", plan_tier="free", timezone="Asia/Seoul")
        u2 = User(email="a@example.com", plan_tier="free", timezone="Asia/Seoul")
        session.add_all([u1, u2])
        try:
            session.commit()
            assert False, "expected unique email violation"
        except IntegrityError:
            session.rollback()

        session.add(u1)
        session.commit()
        d1 = Device(user_id=u1.id, fcm_token="token-1", platform="web")
        d2 = Device(user_id=u1.id, fcm_token="token-1", platform="web")
        session.add_all([d1, d2])
        try:
            session.commit()
            assert False, "expected unique fcm token violation"
        except IntegrityError:
            session.rollback()
