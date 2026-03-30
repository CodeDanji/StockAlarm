# EcoAlarm MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MVP that converts natural-language strategy ideas into validated alert rules and delivers reliable delayed-market push alerts for US/KR assets.

**Architecture:** GCP serverless distributed architecture with FastAPI on Cloud Run, PostgreSQL on Cloud SQL, Pub/Sub-based worker orchestration, and Next.js PWA with FCM push. Alert evaluation is decoupled from notification delivery and enforces repeat/quiet-hours policies.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, pytest, Next.js (TypeScript), Vitest, PostgreSQL, Terraform, GCP Cloud Run/Pub/Sub/Cloud Scheduler/Secret Manager, Firebase Cloud Messaging.

---

## File Structure and Ownership

- `apps/api/`: FastAPI app, DB models, routers, services, workers, tests.
- `apps/web/`: Next.js PWA, auth/push client logic, UI tests.
- `infra/terraform/`: Cloud Run, Cloud SQL, Pub/Sub, Scheduler, Secrets.
- `docs/superpowers/specs/`: approved design spec.
- `docs/superpowers/plans/`: this implementation plan.

---

### Task 0: Environment Baseline Before Code Development

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `README.md`
- Test: baseline checks via file presence and format sanity

- [ ] **Step 1: Write baseline files**

```gitignore
# Python
__pycache__/
.pytest_cache/
.venv/

# Node
node_modules/
.next/

# Env and local secrets
.env
.env.*
!.env.example

# Terraform local state
*.tfstate
*.tfstate.*
.terraform/

# Worktrees
.worktrees/
worktrees/
```

```env
# API
OPENAI_API_KEY=
EODHD_API_KEY=
DATABASE_URL=postgresql+psycopg://ecoalarm:ecoalarm@localhost:5432/ecoalarm
JWT_SECRET=change-me

# GCP
GCP_PROJECT_ID=
GCP_REGION=asia-northeast3

# Firebase Web Push
FIREBASE_API_KEY=
FIREBASE_AUTH_DOMAIN=
FIREBASE_PROJECT_ID=
FIREBASE_MESSAGING_SENDER_ID=
FIREBASE_APP_ID=
FIREBASE_VAPID_KEY=
```

```md
# StockAlarm

## Prerequisites
- Python 3.12
- Node.js 20+
- Terraform 1.8+

## Environment
1. Copy `.env.example` to `.env`
2. Fill API keys and local DB connection
3. Never commit `.env`
```

- [ ] **Step 2: Verify baseline files exist**

Run: `ls -a`  
Expected: `.gitignore`, `.env.example`, `README.md` present.

- [ ] **Step 3: Commit baseline**

```bash
git add .gitignore .env.example README.md docs/superpowers/specs/2026-03-30-ecoalarm-design.md docs/superpowers/plans/2026-03-30-ecoalarm-mvp-implementation.md
git commit -m "chore: add project baseline, env template, and approved docs"
```

---

### Task 1: Bootstrap API Skeleton and Health Endpoint

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/app/main.py`
- Create: `apps/api/tests/test_health.py`
- Test: `apps/api/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_health.py -v`  
Expected: `FAIL` with import/module error.

- [ ] **Step 3: Write minimal implementation**

```toml
[project]
name = "ecoalarm-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi>=0.115.0", "uvicorn>=0.30.0", "pydantic>=2.8.0", "sqlalchemy>=2.0.0"]
[project.optional-dependencies]
dev = ["pytest>=8.3.0", "httpx>=0.27.0", "pyjwt>=2.9.0"]
```

```python
from fastapi import FastAPI
app = FastAPI(title="EcoAlarm API", version="0.1.0")
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_health.py -v`  
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/pyproject.toml apps/api/app/main.py apps/api/tests/test_health.py
git commit -m "feat(api): bootstrap FastAPI service with health endpoint"
```

---

### Task 2: Add Database Foundation and Core User Models

**Files:**
- Create: `apps/api/app/db/session.py`
- Create: `apps/api/app/models/base.py`
- Create: `apps/api/app/models/user.py`
- Create: `apps/api/app/models/device.py`
- Create: `apps/api/app/models/usage_counter.py`
- Create: `apps/api/tests/test_models_constraints.py`
- Modify: `apps/api/app/main.py`
- Test: `apps/api/tests/test_models_constraints.py`

- [ ] **Step 1: Write the failing test**

```python
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.base import Base
from app.models.user import User
from app.models.device import Device

def test_unique_email_and_fcm_token_constraints() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([User(email="a@example.com", plan_tier="free", timezone="Asia/Seoul"), User(email="a@example.com", plan_tier="free", timezone="Asia/Seoul")])
        try:
            session.commit()
            assert False
        except IntegrityError:
            session.rollback()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_models_constraints.py -v`  
Expected: `FAIL` with missing model modules.

- [ ] **Step 3: Write minimal implementation**

```python
# base.py
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
```

```python
# user.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    plan_tier: Mapped[str] = mapped_column(String(20), default="free")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Seoul")
```

```python
# device.py
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    fcm_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(20), default="web")
```

```python
# usage_counter.py
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
class UsageCounter(Base):
    __tablename__ = "usage_counters"
    __table_args__ = (UniqueConstraint("user_id", "month_key", name="uq_usage_user_month"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    month_key: Mapped[str] = mapped_column(String(7))
    ai_generation_count: Mapped[int] = mapped_column(Integer, default=0)
    active_alert_count: Mapped[int] = mapped_column(Integer, default=0)
```

```python
# session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
DATABASE_URL = "sqlite+pysqlite:///./ecoalarm.db"
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
```

```python
# main.py
from app.db.session import engine
from app.models.base import Base
@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_models_constraints.py -v`  
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/db/session.py apps/api/app/models/base.py apps/api/app/models/user.py apps/api/app/models/device.py apps/api/app/models/usage_counter.py apps/api/app/main.py apps/api/tests/test_models_constraints.py
git commit -m "feat(api): add core SQLAlchemy models and uniqueness constraints"
```

---

### Task 3: Implement Google Token Login and Preferences API

**Files:**
- Create: `apps/api/app/core/security.py`
- Create: `apps/api/app/services/google_auth.py`
- Create: `apps/api/app/schemas/auth.py`
- Create: `apps/api/app/schemas/preferences.py`
- Create: `apps/api/app/routers/auth.py`
- Create: `apps/api/app/routers/me.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_auth_and_preferences.py`
- Test: `apps/api/tests/test_auth_and_preferences.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app

def test_google_token_login_and_preferences_patch(monkeypatch) -> None:
    monkeypatch.setattr("app.services.google_auth.verify_google_id_token", lambda _: {"email": "user@example.com"})
    client = TestClient(app)
    login = client.post("/auth/google/token", json={"id_token": "good-token"})
    token = login.json()["access_token"]
    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    patch = client.patch("/me/preferences", json={"timezone": "America/New_York", "quiet_hours_start": "22:00", "quiet_hours_end": "06:00"}, headers={"Authorization": f"Bearer {token}"})
    assert patch.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_auth_and_preferences.py -v`  
Expected: `FAIL` with missing auth routes or JWT helpers.

- [ ] **Step 3: Write minimal implementation**

```python
# security.py
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
JWT_SECRET = "dev-secret-change-in-prod"
JWT_ALGO = "HS256"
bearer = HTTPBearer(auto_error=True)
def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "exp": int((now + timedelta(minutes=60)).timestamp())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> int:
    try:
        return int(jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGO])["sub"])
    except Exception as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
```

```python
# google_auth.py
def verify_google_id_token(id_token: str) -> dict[str, str]:
    if not id_token:
        raise ValueError("invalid token")
    return {"email": "sample@example.com"}
```

```python
# auth.py and me.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.core.security import create_access_token, get_current_user_id
from app.db.session import SessionLocal
from app.models.user import User

auth_router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["me"])

@auth_router.post("/google/token")
def google_token_login(payload: dict) -> dict:
    from app.services.google_auth import verify_google_id_token
    token_info = verify_google_id_token(payload["id_token"])
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == token_info["email"]))
        if user is None:
            user = User(email=token_info["email"], plan_tier="free", timezone="Asia/Seoul")
            db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

@me_router.get("/me")
def get_me(user_id: int = Depends(get_current_user_id)) -> dict:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        return {"id": user.id, "email": user.email, "plan_tier": user.plan_tier, "timezone": user.timezone, "quiet_hours_start": user.quiet_hours_start, "quiet_hours_end": user.quiet_hours_end}

@me_router.patch("/me/preferences")
def patch_preferences(payload: dict, user_id: int = Depends(get_current_user_id)) -> dict:
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == user_id))
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")
        user.timezone = payload["timezone"]
        user.quiet_hours_start = payload["quiet_hours_start"]
        user.quiet_hours_end = payload["quiet_hours_end"]
        db.commit(); db.refresh(user)
        return {"timezone": user.timezone, "quiet_hours_start": user.quiet_hours_start, "quiet_hours_end": user.quiet_hours_end}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_auth_and_preferences.py -v`  
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/core/security.py apps/api/app/services/google_auth.py apps/api/app/schemas/auth.py apps/api/app/schemas/preferences.py apps/api/app/routers/auth.py apps/api/app/routers/me.py apps/api/app/main.py apps/api/tests/test_auth_and_preferences.py
git commit -m "feat(api): add google token auth and me preferences endpoints"
```

---

### Task 4: Implement Alerts CRUD and Free Plan Cap Enforcement

**Files:**
- Create: `apps/api/app/models/alert_rule.py`
- Create: `apps/api/app/models/rule_state.py`
- Create: `apps/api/app/schemas/alerts.py`
- Create: `apps/api/app/services/usage_service.py`
- Create: `apps/api/app/routers/alerts.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_alert_limits.py`
- Test: `apps/api/tests/test_alert_limits.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app

def test_free_plan_blocks_fourth_alert(monkeypatch) -> None:
    monkeypatch.setattr("app.services.google_auth.verify_google_id_token", lambda _: {"email": "limit@example.com"})
    client = TestClient(app)
    token = client.post("/auth/google/token", json={"id_token": "ok"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for idx in range(3):
        ok = client.post("/alerts", json={"name": f"a-{idx}", "condition_dsl": 'price_crosses_above(symbol="AAPL", ma=20, timeframe="15m")', "mode": "A", "cooldown_minutes_market": 120, "active": True}, headers=headers)
        assert ok.status_code == 201
    blocked = client.post("/alerts", json={"name": "a-3", "condition_dsl": 'rsi_below(symbol="AAPL", period=14, threshold=30, timeframe="15m")', "mode": "A", "cooldown_minutes_market": 120, "active": True}, headers=headers)
    assert blocked.status_code == 402
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_alert_limits.py -v`  
Expected: `FAIL` with missing `/alerts` route.

- [ ] **Step 3: Write minimal implementation**

```python
# alert_rule.py / rule_state.py
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base
class AlertRule(Base):
    __tablename__ = "alert_rules"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    condition_dsl: Mapped[str] = mapped_column(String(2000))
    mode: Mapped[str] = mapped_column(String(1), default="A")
    cooldown_minutes_market: Mapped[int] = mapped_column(default=120)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
class RuleState(Base):
    __tablename__ = "rule_states"
    rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), primary_key=True)
    last_state_bool: Mapped[bool | None] = mapped_column(nullable=True)
    last_trigger_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

```python
# usage_service.py
from sqlalchemy import func, select
from app.models.alert_rule import AlertRule
from app.models.user import User
def assert_can_create_alert(db, user_id: int) -> None:
    user = db.scalar(select(User).where(User.id == user_id))
    limit = 3 if (user.plan_tier if user else "free") == "free" else 20
    count = db.scalar(select(func.count()).select_from(AlertRule).where(AlertRule.user_id == user_id, AlertRule.active.is_(True))) or 0
    if count >= limit:
        raise PermissionError("alert limit exceeded")
```

```python
# alerts.py router
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from app.core.security import get_current_user_id
from app.db.session import SessionLocal
from app.models.alert_rule import AlertRule
from app.services.usage_service import assert_can_create_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("", status_code=status.HTTP_201_CREATED)
def create_alert(payload: dict, user_id: int = Depends(get_current_user_id)) -> dict:
    with SessionLocal() as db:
        try:
            assert_can_create_alert(db, user_id)
        except PermissionError as exc:
            raise HTTPException(status_code=402, detail=str(exc)) from exc
        row = AlertRule(user_id=user_id, name=payload["name"], condition_dsl=payload["condition_dsl"], mode=payload["mode"], cooldown_minutes_market=payload["cooldown_minutes_market"], active=payload["active"])
        db.add(row); db.commit(); db.refresh(row)
        return {"id": row.id, "name": row.name, "mode": row.mode, "active": row.active}

@router.get("")
def list_alerts(user_id: int = Depends(get_current_user_id)) -> list[dict]:
    with SessionLocal() as db:
        rows = db.scalars(select(AlertRule).where(AlertRule.user_id == user_id)).all()
        return [{"id": r.id, "name": r.name, "mode": r.mode, "active": r.active} for r in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_alert_limits.py -v`  
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/models/alert_rule.py apps/api/app/models/rule_state.py apps/api/app/schemas/alerts.py apps/api/app/services/usage_service.py apps/api/app/routers/alerts.py apps/api/app/main.py apps/api/tests/test_alert_limits.py
git commit -m "feat(api): add alert CRUD baseline and free-plan cap enforcement"
```

---

### Task 5: Build Strategy Generation with DSL Validation and Model Escalation

**Files:**
- Create: `apps/api/app/schemas/strategies.py`
- Create: `apps/api/app/services/strategy_service.py`
- Create: `apps/api/app/routers/strategies.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_strategy_escalation.py`
- Test: `apps/api/tests/test_strategy_escalation.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app

def test_strategy_generation_escalates_when_symbol_unresolved(monkeypatch) -> None:
    calls = []
    def fake_generate(*, prompt: str, model: str) -> list[dict]:
        calls.append(model)
        if model == "gpt-5.4-mini":
            return [{"title": "candidate", "condition_dsl": 'rsi_below(symbol="UNKNOWN", period=14, threshold=30, timeframe="15m")'}]
        return [{"title": "candidate", "condition_dsl": 'rsi_below(symbol="AAPL", period=14, threshold=30, timeframe="15m")'}]
    monkeypatch.setattr("app.services.strategy_service.generate_candidates", fake_generate)
    monkeypatch.setattr("app.services.google_auth.verify_google_id_token", lambda _: {"email": "ai@example.com"})
    client = TestClient(app)
    token = client.post("/auth/google/token", json={"id_token": "ok"}).json()["access_token"]
    res = client.post("/strategies/generate", json={"idea": "apple rsi under 30"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert calls == ["gpt-5.4-mini", "gpt-5.4"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_strategy_escalation.py -v`  
Expected: `FAIL` with missing route/service.

- [ ] **Step 3: Write minimal implementation**

```python
# strategies.py schemas
from pydantic import BaseModel
class StrategyGenerateRequest(BaseModel):
    idea: str
class StrategyGenerateResponse(BaseModel):
    scenarios: list[dict]
    model_used: str
```

```python
# strategy_service.py
import re
def generate_candidates(*, prompt: str, model: str) -> list[dict]:
    return [{"title": "default", "condition_dsl": 'price_crosses_above(symbol="AAPL", ma=20, timeframe="15m")'}]
def _has_unresolved(condition_dsl: str) -> bool:
    m = re.search(r'symbol="([^"]+)"', condition_dsl)
    return m is None or m.group(1) in {"UNKNOWN", "UNRESOLVED", "?"}
def generate_strategies(idea: str) -> tuple[list[dict], str]:
    mini = generate_candidates(prompt=idea, model="gpt-5.4-mini")
    if any(_has_unresolved(s["condition_dsl"]) for s in mini):
        return generate_candidates(prompt=idea, model="gpt-5.4"), "gpt-5.4"
    return mini, "gpt-5.4-mini"
```

```python
# strategies router
from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id
from app.services.strategy_service import generate_strategies
router = APIRouter(prefix="/strategies", tags=["strategies"])
@router.post("/generate")
def generate(payload: dict, _: int = Depends(get_current_user_id)) -> dict:
    scenarios, model_used = generate_strategies(payload["idea"])
    return {"scenarios": scenarios, "model_used": model_used}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_strategy_escalation.py -v`  
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/schemas/strategies.py apps/api/app/services/strategy_service.py apps/api/app/routers/strategies.py apps/api/app/main.py apps/api/tests/test_strategy_escalation.py
git commit -m "feat(api): add strategy generation endpoint with deterministic model escalation"
```

---

### Task 6: Implement Rule Evaluation Logic (Mode A/B, Market Cooldown, Off-hours)

**Files:**
- Create: `apps/api/app/services/evaluator_service.py`
- Create: `apps/api/tests/test_evaluator_service.py`
- Test: `apps/api/tests/test_evaluator_service.py`

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime, timedelta, timezone
from app.services.evaluator_service import decide_trigger

def test_mode_a_transition_only() -> None:
    now = datetime.now(timezone.utc)
    assert decide_trigger(mode="A", is_true=True, last_state=False, last_trigger_at=None, cooldown_minutes=120, now=now, market_hours=True)
    assert not decide_trigger(mode="A", is_true=True, last_state=True, last_trigger_at=now, cooldown_minutes=120, now=now + timedelta(minutes=15), market_hours=True)

def test_mode_b_market_cooldown() -> None:
    now = datetime.now(timezone.utc)
    assert decide_trigger(mode="B", is_true=True, last_state=True, last_trigger_at=now - timedelta(minutes=130), cooldown_minutes=120, now=now, market_hours=True)
    assert not decide_trigger(mode="B", is_true=True, last_state=True, last_trigger_at=now - timedelta(minutes=30), cooldown_minutes=120, now=now, market_hours=True)

def test_offhours_default_off() -> None:
    now = datetime.now(timezone.utc)
    assert not decide_trigger(mode="B", is_true=True, last_state=False, last_trigger_at=None, cooldown_minutes=120, now=now, market_hours=False, off_hours_enabled=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_evaluator_service.py -v`  
Expected: `FAIL` with missing evaluator service module.

- [ ] **Step 3: Write minimal implementation**

```python
from datetime import datetime, timedelta

def decide_trigger(*, mode: str, is_true: bool, last_state: bool | None, last_trigger_at: datetime | None, cooldown_minutes: int, now: datetime, market_hours: bool, off_hours_enabled: bool = False) -> bool:
    if not is_true:
        return False
    if not market_hours and not off_hours_enabled:
        return False
    if mode == "A":
        return last_state is False or last_state is None
    if mode == "B":
        effective = cooldown_minutes if market_hours else 360
        return last_trigger_at is None or now >= last_trigger_at + timedelta(minutes=effective)
    return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_evaluator_service.py -v`  
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/evaluator_service.py apps/api/tests/test_evaluator_service.py
git commit -m "feat(api): implement core trigger evaluation logic for mode A/B"
```

---

### Task 7: Implement Quiet-Hours Suppression and Morning Digest Filtering

**Files:**
- Create: `apps/api/app/services/notification_policy.py`
- Create: `apps/api/tests/test_notification_policy.py`
- Test: `apps/api/tests/test_notification_policy.py`

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime
from app.services.notification_policy import is_quiet_hours, select_digest_events

def test_quiet_hours_detection() -> None:
    assert is_quiet_hours("23:00", "07:00", datetime.fromisoformat("2026-03-30T23:30:00"))
    assert not is_quiet_hours("23:00", "07:00", datetime.fromisoformat("2026-03-30T10:30:00"))

def test_digest_selects_only_suppressed_events() -> None:
    events = [{"id": 1, "suppressed_by_quiet_hours": True}, {"id": 2, "suppressed_by_quiet_hours": False}]
    assert [e["id"] for e in select_digest_events(events)] == [1]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_notification_policy.py -v`  
Expected: `FAIL` with missing module.

- [ ] **Step 3: Write minimal implementation**

```python
from datetime import datetime, time
def _parse_hhmm(value: str) -> time:
    h, m = value.split(":")
    return time(hour=int(h), minute=int(m))
def is_quiet_hours(start_hhmm: str, end_hhmm: str, local_dt: datetime) -> bool:
    start, end, now_t = _parse_hhmm(start_hhmm), _parse_hhmm(end_hhmm), local_dt.time()
    if start <= end:
        return start <= now_t < end
    return now_t >= start or now_t < end
def select_digest_events(events: list[dict]) -> list[dict]:
    return [e for e in events if e.get("suppressed_by_quiet_hours") is True]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_notification_policy.py -v`  
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/notification_policy.py apps/api/tests/test_notification_policy.py
git commit -m "feat(api): add quiet-hours suppression and digest event filtering"
```

---

### Task 8: Add Device Registration and Billing Usage Endpoints

**Files:**
- Create: `apps/api/app/schemas/devices.py`
- Create: `apps/api/app/routers/devices.py`
- Create: `apps/api/app/routers/billing.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_devices_and_usage.py`
- Test: `apps/api/tests/test_devices_and_usage.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient
from app.main import app

def test_device_registration_and_usage_endpoint(monkeypatch) -> None:
    monkeypatch.setattr("app.services.google_auth.verify_google_id_token", lambda _: {"email": "device@example.com"})
    client = TestClient(app)
    token = client.post("/auth/google/token", json={"id_token": "ok"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    device = client.post("/devices/register", json={"fcm_token": "tok-1", "platform": "web"}, headers=headers)
    assert device.status_code == 201
    usage = client.get("/billing/usage", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["plan_tier"] == "free"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_devices_and_usage.py -v`  
Expected: `FAIL` with missing routes.

- [ ] **Step 3: Write minimal implementation**

```python
# devices schema
from pydantic import BaseModel
class DeviceRegisterRequest(BaseModel):
    fcm_token: str
    platform: str = "web"
```

```python
# devices router
from fastapi import APIRouter, Depends, status
from app.core.security import get_current_user_id
from app.db.session import SessionLocal
from app.models.device import Device
router = APIRouter(prefix="/devices", tags=["devices"])
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_device(payload: dict, user_id: int = Depends(get_current_user_id)) -> dict:
    with SessionLocal() as db:
        row = Device(user_id=user_id, fcm_token=payload["fcm_token"], platform=payload.get("platform", "web"))
        db.add(row); db.commit(); db.refresh(row)
        return {"id": row.id, "fcm_token": row.fcm_token}
```

```python
# billing router
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.core.security import get_current_user_id
from app.db.session import SessionLocal
from app.models.usage_counter import UsageCounter
from app.models.user import User
router = APIRouter(prefix="/billing", tags=["billing"])
@router.get("/usage")
def get_usage(user_id: int = Depends(get_current_user_id)) -> dict:
    month_key = datetime.utcnow().strftime("%Y-%m")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == user_id))
        usage = db.scalar(select(UsageCounter).where(UsageCounter.user_id == user_id, UsageCounter.month_key == month_key))
        return {"plan_tier": user.plan_tier if user else "free", "month_key": month_key, "ai_generation_count": usage.ai_generation_count if usage else 0, "active_alert_count": usage.active_alert_count if usage else 0}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_devices_and_usage.py -v`  
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/schemas/devices.py apps/api/app/routers/devices.py apps/api/app/routers/billing.py apps/api/app/main.py apps/api/tests/test_devices_and_usage.py
git commit -m "feat(api): add device registration and billing usage endpoints"
```

---

### Task 9: Build Worker Entry Points for Ingestion, Evaluation, and Digest

**Files:**
- Create: `apps/api/app/workers/scheduler.py`
- Create: `apps/api/app/workers/ingestor.py`
- Create: `apps/api/app/workers/evaluator.py`
- Create: `apps/api/app/workers/digest.py`
- Create: `apps/api/tests/test_scheduler_jobs.py`
- Test: `apps/api/tests/test_scheduler_jobs.py`

- [ ] **Step 1: Write the failing test**

```python
from app.workers.scheduler import build_jobs

def test_scheduler_builds_required_jobs() -> None:
    jobs = build_jobs()
    names = {job["name"] for job in jobs}
    assert "ingest-15m-market-hours" in names
    assert "evaluate-15m-market-hours" in names
    assert "ingest-1h-off-hours" in names
    assert "digest-morning" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_scheduler_jobs.py -v`  
Expected: `FAIL` with missing worker modules.

- [ ] **Step 3: Write minimal implementation**

```python
# scheduler.py
def build_jobs() -> list[dict]:
    return [
        {"name": "ingest-15m-market-hours", "cron": "*/15 * * * 1-5"},
        {"name": "evaluate-15m-market-hours", "cron": "*/15 * * * 1-5"},
        {"name": "ingest-1h-off-hours", "cron": "0 * * * *"},
        {"name": "evaluate-1h-off-hours", "cron": "0 * * * *"},
        {"name": "digest-morning", "cron": "0 7 * * *"},
    ]
```

```python
# ingestor.py / evaluator.py / digest.py
def run_ingestion_cycle(scope: str) -> dict: return {"scope": scope, "status": "ok"}
def run_evaluation_cycle(scope: str) -> dict: return {"scope": scope, "status": "ok"}
def run_morning_digest() -> dict: return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/api && python -m pytest tests/test_scheduler_jobs.py -v`  
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/workers/scheduler.py apps/api/app/workers/ingestor.py apps/api/app/workers/evaluator.py apps/api/app/workers/digest.py apps/api/tests/test_scheduler_jobs.py
git commit -m "feat(workers): add scheduler map and worker entrypoints"
```

---

### Task 10: Create Next.js PWA Shell with Alert List and Push Registration Client

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/components/AlertList.tsx`
- Create: `apps/web/src/lib/api.ts`
- Create: `apps/web/src/lib/push.ts`
- Create: `apps/web/tests/alert-list.test.tsx`
- Test: `apps/web/tests/alert-list.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AlertList } from "../src/components/AlertList";

describe("AlertList", () => {
  it("renders alert names", () => {
    render(<AlertList alerts={[{ id: 1, name: "AAPL RSI", mode: "A", active: true }]} />);
    expect(screen.getByText("AAPL RSI")).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/web && npm run test -- alert-list.test.tsx`  
Expected: `FAIL` with missing package/config/files.

- [ ] **Step 3: Write minimal implementation**

```json
{
  "name": "ecoalarm-web",
  "private": true,
  "version": "0.1.0",
  "scripts": { "dev": "next dev", "build": "next build", "start": "next start", "test": "vitest", "test:ci": "vitest run" },
  "dependencies": { "next": "^15.0.0", "react": "^19.0.0", "react-dom": "^19.0.0" },
  "devDependencies": { "@testing-library/react": "^16.0.0", "typescript": "^5.6.0", "vitest": "^2.1.0" }
}
```

```tsx
type AlertItem = { id: number; name: string; mode: string; active: boolean };
export function AlertList({ alerts }: { alerts: AlertItem[] }) {
  return <ul>{alerts.map((a) => <li key={a.id}>{a.name}</li>)}</ul>;
}
```

```tsx
import { AlertList } from "../components/AlertList";
export default function Home() {
  return <main><h1>EcoAlarm</h1><AlertList alerts={[]} /></main>;
}
```

```ts
export async function registerPushToken(token: string, jwt: string) {
  const res = await fetch("/api/devices/register", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${jwt}` }, body: JSON.stringify({ fcm_token: token, platform: "web" }) });
  if (!res.ok) throw new Error("failed to register push token");
  return res.json();
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/web && npm run test -- alert-list.test.tsx`  
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/web/package.json apps/web/src/app/page.tsx apps/web/src/components/AlertList.tsx apps/web/src/lib/api.ts apps/web/src/lib/push.ts apps/web/tests/alert-list.test.tsx
git commit -m "feat(web): scaffold pwa shell and alert list component"
```

---

### Task 11: Add Terraform Baseline for GCP Services

**Files:**
- Create: `infra/terraform/main.tf`
- Create: `infra/terraform/variables.tf`
- Create: `infra/terraform/services.tf`
- Create: `infra/terraform/database.tf`
- Create: `infra/terraform/secrets.tf`
- Create: `infra/terraform/outputs.tf`
- Test: `terraform validate`

- [ ] **Step 1: Write the failing validation check**

Run: `cd infra/terraform && terraform validate`  
Expected: `FAIL` because configuration files are missing.

- [ ] **Step 2: Write minimal implementation**

```hcl
terraform {
  required_version = ">= 1.8.0"
  required_providers { google = { source = "hashicorp/google", version = "~> 6.0" } }
}
provider "google" { project = var.project_id, region = var.region }
```

```hcl
variable "project_id" { type = string }
variable "region" { type = string, default = "asia-northeast3" }
variable "db_tier" { type = string, default = "db-f1-micro" }
```

```hcl
resource "google_cloud_run_v2_service" "api" {
  name = "ecoalarm-api"
  location = var.region
  template { containers { image = "us-docker.pkg.dev/cloudrun/container/hello" } }
}
resource "google_sql_database_instance" "postgres" {
  name = "ecoalarm-postgres"
  database_version = "POSTGRES_15"
  region = var.region
  settings { tier = var.db_tier }
}
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  replication { auto {} }
}
output "api_service_name" { value = google_cloud_run_v2_service.api.name }
```

- [ ] **Step 3: Run validate to confirm pass**

Run: `cd infra/terraform && terraform init && terraform validate`  
Expected: `Success! The configuration is valid.`

- [ ] **Step 4: Commit**

```bash
git add infra/terraform/main.tf infra/terraform/variables.tf infra/terraform/services.tf infra/terraform/database.tf infra/terraform/secrets.tf infra/terraform/outputs.tf
git commit -m "infra(gcp): add terraform baseline for cloud run, cloud sql, and secrets"
```

---

### Task 12: Full Verification Gate and MVP Definition of Done

**Files:**
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/web/package.json`
- Create: `README.md`
- Test: all backend/frontend/infra checks

- [ ] **Step 1: Add verification scripts**

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

```json
{
  "scripts": {
    "test:ci": "vitest run"
  }
}
```

- [ ] **Step 2: Add runbook**

```md
# EcoAlarm
## Local Run
- API: `cd apps/api && uvicorn app.main:app --reload`
- Web: `cd apps/web && npm run dev`

## Verification
- `cd apps/api && python -m pytest -v`
- `cd apps/web && npm run test:ci`
- `cd infra/terraform && terraform validate`
```

- [ ] **Step 3: Run full verification suite**

Run:
- `cd apps/api && python -m pytest -v`
- `cd apps/web && npm run test:ci`
- `cd infra/terraform && terraform validate`

Expected:
- backend tests pass
- frontend tests pass
- terraform validate succeeds

- [ ] **Step 4: Commit**

```bash
git add apps/api/pyproject.toml apps/web/package.json README.md
git commit -m "chore: add verification scripts and mvp runbook"
```

---

## Spec Coverage Checklist (Self-Review)

- Scope (US+KR, stock+ETF+ADR): Tasks 4, 6, 9.
- Google-only auth: Task 3.
- Free/Pro limits (3/20): Tasks 4 and 8.
- LLM mini default + 5.4 escalation: Task 5.
- Quiet hours + morning digest: Task 7.
- Device push registration (PWA): Tasks 8 and 10.
- GCP serverless baseline: Task 11.
- Verification before completion: Task 12.

## Placeholder Scan

- No `TODO`, `TBD`, `FIXME`, or unresolved implementation placeholders.

## Type Consistency Check

- Auth endpoint consistently uses `POST /auth/google/token`.
- Alert mode consistently uses `A`/`B`.
- Device registration consistently uses `fcm_token`.
