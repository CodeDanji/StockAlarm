from fastapi import FastAPI

from app.db.session import engine
from app.models.base import Base
from app.routers.alerts import router as alerts_router
from app.routers.auth import router as auth_router
from app.routers.me import router as me_router

# Import models so SQLAlchemy registers the table metadata before create_all().
import app.models.alert_rule  # noqa: F401
import app.models.device  # noqa: F401
import app.models.rule_state  # noqa: F401
import app.models.usage_counter  # noqa: F401
import app.models.user  # noqa: F401

app = FastAPI(title="EcoAlarm API", version="0.1.0")


@app.on_event("startup")
def create_database_schema() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(me_router)
app.include_router(alerts_router)
