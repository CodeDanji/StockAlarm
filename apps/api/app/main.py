from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import engine
from app.models.base import Base
from app.routers.alerts import router as alerts_router
from app.routers.auth import router as auth_router
from app.routers.billing import router as billing_router
from app.routers.devices import router as devices_router
from app.routers.me import router as me_router
from app.routers.strategies import router as strategies_router

# Import models so SQLAlchemy registers the table metadata before create_all().
import app.models.alert_rule  # noqa: F401
import app.models.device  # noqa: F401
import app.models.rule_state  # noqa: F401
import app.models.usage_counter  # noqa: F401
import app.models.user  # noqa: F401

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="EcoAlarm API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(me_router)
app.include_router(alerts_router)
app.include_router(strategies_router)
app.include_router(devices_router)
app.include_router(billing_router)
