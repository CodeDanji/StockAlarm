from fastapi import FastAPI

from app.db.session import engine
from app.models.base import Base

# Import models so SQLAlchemy registers the table metadata before create_all().
import app.models.device  # noqa: F401
import app.models.usage_counter  # noqa: F401
import app.models.user  # noqa: F401

app = FastAPI(title="EcoAlarm API", version="0.1.0")


@app.on_event("startup")
def create_database_schema() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
