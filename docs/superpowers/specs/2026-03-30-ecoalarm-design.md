# EcoAlarm Service Design

**Date:** 2026-03-30  
**Status:** Draft approved in chat, written for implementation planning

---

## 1. Product Goal and Scope

### Goal
Transform a user's vague investing idea into 2-3 concrete, machine-evaluable alert scenarios and deliver reliable notifications when conditions are met.

### Target User
Intermediate retail investors who understand basic indicators but do not code strategies or run backtesting tools.

### In Scope (MVP)
- Markets: US + KR
- Assets: Stock + ETF + ADR
- Data source: EODHD EOD+Intraday All World Extended
- Notification: PWA push only (FCM)
- Auth: Google sign-in only
- Plans: Free + Pro

### Out of Scope (MVP)
- Auto-trading or broker order execution
- AI stock picking or discretionary portfolio management
- Tick-level, ultra-low-latency scalping workflows

---

## 2. Plan and Monetization Model

### Free
- Active alerts: up to 3
- AI scenario generations: up to 20 per month

### Pro
- Active alerts: up to 20
- AI scenario generations: up to 300 per month
- Advanced alert history and analytics

### Pricing Structure
- Single paid tier (`Free + Pro`) for MVP simplicity
- Upgrade path prepared in API and schema, but pricing page copy can be tuned later

---

## 3. Core User Flow

1. User signs in with Google.
2. User enters a natural-language strategy idea.
3. AI returns 2-3 scenario options with:
   - summary
   - normalized condition expression
   - short risk caveat
4. User selects and optionally edits a scenario.
5. User creates an alert rule.
6. System evaluates by schedule (intraday vs off-hours).
7. If triggered, system sends push notification per repeat and quiet-hours policy.

---

## 4. Alert Policy (Locked Decisions)

### Evaluation cadence
- Market hours: every 15 minutes
- Off-hours: every 1 hour

### Repeat mode (user-selectable)
- Mode A: First trigger only  
  Re-notify only when condition transitions back from false to true.
- Mode B: Cooldown repeat  
  Re-notify while condition remains true, with cooldown in market hours.

### Cooldown
- Market hours cooldown: 2 hours

### Off-hours
- Off-hours alerts default: OFF
- If off-hours alerts are enabled by user:
  - Mode A: same transition rule as market hours
  - Mode B: cooldown repeat with 6-hour off-hours cooldown (anti-spam default)

### Quiet hours
- Default: 23:00-07:00 (user local timezone)
- During quiet hours: suppress immediate push and accumulate events
- Morning digest: one push summary after quiet-hours window
- Digest includes only events that were actually suppressed by quiet-hours policy.

### Channel
- Push only (PWA + FCM)

---

## 5. Architecture (GCP Serverless Distributed)

### Core platform
- Frontend: Next.js PWA
- API service: FastAPI on Cloud Run
- Scheduler: Cloud Scheduler
- Eventing/queue: Pub/Sub + Cloud Tasks
- Database: Cloud SQL (PostgreSQL)
- Push: Firebase Cloud Messaging
- Secrets: Secret Manager
- Observability: Cloud Logging, Error Reporting, Monitoring

### Why this architecture
- Clear separation of API, evaluation, and delivery paths
- Better reliability under bursty workloads than a single-process scheduler
- Good fit for GCP startup credits and incremental scale

---

## 6. Service Components and Responsibilities

### `api-gateway` (FastAPI)
- Auth/session endpoints
- user preferences
- alert CRUD
- usage and plan checks

### `strategy-service`
- natural-language intent parsing
- LLM orchestration (`gpt-5.4-mini` default, `gpt-5.4` escalation)
- output normalization into allowed condition DSL

### `market-ingestor`
- EODHD polling and normalization
- write canonical bar/quote rows
- gap detection and retry

### `signal-evaluator`
- scheduled evaluation runner
- compute indicator values
- evaluate rule DSL
- transition detection and trigger decision

### `notification-service`
- cooldown checks
- quiet-hours gating
- push message generation and send

### `digest-service`
- collects quiet-hours suppressed triggers
- generates morning digest message
- one digest push per quiet-hours cycle

### `billing-usage-service` (MVP-light)
- monthly AI usage counters
- active-alert count limits by plan
- returns upgrade-required state

---

## 7. Data Model (Core Tables)

### `users`
- `id`, `email`, `plan_tier`, `timezone`
- `quiet_hours_start`, `quiet_hours_end`
- `created_at`, `updated_at`

### `devices`
- `id`, `user_id`, `fcm_token`, `platform`
- `last_seen_at`, `is_active`

### `watchlists`
- `id`, `user_id`, `symbol`, `exchange`, `asset_type`

### `alert_rules`
- `id`, `user_id`, `name`
- `condition_dsl`, `mode` (`A` or `B`)
- `cooldown_minutes_market`
- `active`, `created_at`, `updated_at`

### `rule_states`
- `rule_id`, `last_eval_at`
- `last_state_bool`
- `last_trigger_at`, `cool_until`
- `last_price_snapshot`

### `market_bars`
- `symbol`, `exchange`, `timeframe`, `ts`
- `open`, `high`, `low`, `close`, `volume`
- `source`, `ingested_at`

### `alert_events`
- `id`, `rule_id`, `triggered_at`
- `price_snapshot`, `reason_code`
- `delivery_status`, `delivered_at`
- `suppressed_by_quiet_hours`

### `ai_requests`
- `id`, `user_id`, `input_hash`
- `model_used`, `tokens_in`, `tokens_out`, `cost_estimate`
- `created_at`

### `usage_counters`
- `user_id`, `month_key`
- `ai_generation_count`
- `active_alert_count`
- `updated_at`

### Required constraints and indexes
- `users`: unique index on `email`
- `devices`: unique index on `fcm_token`
- `rule_states`: primary key on `rule_id`
- `market_bars`: unique composite index on (`symbol`, `exchange`, `timeframe`, `ts`, `source`)
- `usage_counters`: unique composite index on (`user_id`, `month_key`)
- `alert_events`: index on (`rule_id`, `triggered_at`) for timeline queries

---

## 8. API Design (MVP)

### Auth and user
- `POST /auth/google/token` (verify Google ID token, issue first-party session JWT)
- `POST /auth/refresh`
- `GET /me`
- `PATCH /me/preferences`

### Strategy generation
- `POST /strategies/generate`
- `POST /strategies/{id}/refine`

### Alert rules
- `POST /alerts`
- `GET /alerts`
- `PATCH /alerts/{id}`
- `DELETE /alerts/{id}`
- `POST /alerts/{id}/toggle`

### Devices and push
- `POST /devices/register`
- `DELETE /devices/{id}`

### Usage and billing
- `GET /billing/usage`
- `POST /billing/upgrade-intent`

---

## 9. Condition DSL and LLM Safety Boundary

### Boundary rule
LLM is used for interpretation and proposal, not for direct executable logic generation.

### Process
1. Parse user intent with model.
2. Map to strict server-owned DSL schema.
3. Reject unsupported indicators, invalid params, or ambiguous symbol mapping.
4. Return editable structured conditions to user.

### Example expressions
- `price_crosses_above(symbol="AAPL", ma=20, timeframe="15m")`
- `rsi_below(symbol="005930.KS", period=14, threshold=30, timeframe="15m")`
- `macd_signal_cross(symbol="QQQ", fast=12, slow=26, signal=9, timeframe="1h")`

### Model policy
- Default: `gpt-5.4-mini`
- Escalate to `gpt-5.4` when ambiguity or low confidence is detected
- Escalation triggers (deterministic):
  - unresolved ticker mapping after symbol resolver pass
  - unsupported indicator request with conflicting user intent
  - schema validation fails after one auto-repair attempt
  - low-confidence classification score below configured threshold

---

## 10. Cost and Performance Design

### Primary cost drivers
- Cloud SQL instance sizing and uptime
- Cloud Run always-on baseline and burst execution
- EODHD subscription and commercial licensing scope
- LLM token consumption

### Cost control levers
- Free plan caps (3 active alerts, 20 AI generations/month)
- batched symbol evaluation before per-user rule checks
- queue-based backpressure with retry limits
- caching indicator windows to avoid duplicate computation

### Performance objective (MVP)
- Trigger decision latency target: within one evaluation cycle
- Notification send target after trigger decision: under 60 seconds

---

## 11. Security, Compliance, and Data Delay Notice

- Not investment advice disclaimer in onboarding and settings.
- User responsibility acknowledgement for final decision making.
- **Mandatory market data delay notice:** data can be delayed by about 15 minutes depending on exchange/source path.
- Explicit onboarding consent for delayed-data usage.
- Always display `data timestamp` and `evaluated at` in alert detail.
- Include `delay_notice=true` and timestamps in API and push payload.
- Store secrets in Secret Manager only.
- Enforce least-privilege IAM roles.
- Minimize stored personal data and keep audit logs for sensitive actions.

---

## 12. Failure Modes and Edge Cases

### Data gaps or delayed candles
- Mark evaluation as partial
- do not force false trigger
- re-evaluate on next cycle
- attempt bounded backfill for missing windows before final trigger decision

### Duplicate notifications
- idempotency key per (`rule_id`, `bar_ts`, `trigger_type`)
- transactional update of `rule_states`

### Timezone and DST
- user local timezone for quiet-hours policy
- exchange calendar and session windows stored separately

### Push failures
- retry with capped backoff
- deactivate invalid tokens after repeated failures

---

## 13. Initial Repository Structure

```txt
EcoAlarm/
  apps/
    web/                    # Next.js PWA
    api/                    # FastAPI
    workers/
      evaluator/            # condition evaluation
      notifier/             # push, cooldown, quiet-hours
      digest/               # morning digest
      ingestor/             # EODHD ingestion
  packages/
    domain/                 # DSL, entities, validators
    clients/                # EODHD/OpenAI/FCM clients
    observability/          # logging/tracing helpers
  infra/
    terraform/              # GCP IaC
    cloudbuild/             # CI/CD configs
  docs/
    superpowers/
      specs/
      plans/
```

---

## 14. Runtime and Environment Baseline

### Backend
- Python 3.12
- FastAPI + Pydantic
- SQLAlchemy + Alembic
- Uvicorn/Gunicorn for Cloud Run

### Frontend
- Next.js
- PWA service worker
- Firebase SDK for push token handling

### Infra and delivery
- Cloud Run for API and workers
- Cloud Scheduler for periodic jobs
- Pub/Sub + Cloud Tasks for async workflows
- Cloud SQL PostgreSQL
- Artifact Registry + Cloud Build for CI/CD

### Configuration
- Local: `.env` files
- Production: Secret Manager + environment variables via Cloud Run

---

## 15. Success Metrics (MVP)

- Onboarding completion rate
- Time-to-first-alert under 3 minutes median
- Trigger-to-notification delivery success rate
- Duplicate notification rate under agreed threshold
- Quiet-hours compliance rate at 100% by policy
- Free-to-Pro conversion rate trend
