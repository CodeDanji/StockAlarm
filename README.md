# StockAlarm

## Prerequisites
- Python 3.12
- Node.js 20+
- Terraform 1.8+
- Docker
- gcloud CLI

## Environment
1. Copy `.env.example` to `.env`.
2. Fill API keys, Google client ID, and database connection.
3. Never commit `.env`.
4. Set `INTERNAL_DISPATCH_TOKEN` and worker job names for internal dispatch.
5. Copy `infra/terraform/terraform.tfvars.example` to `infra/terraform/terraform.tfvars`.
6. Fill all required Terraform runtime values and image URLs.

## Local Run
- API: `cd apps/api && uvicorn app.main:app --reload`
- Web: `cd apps/web && npm run dev`

## Preflight Check (No Deploy)
- `python scripts/preflight_config.py`

## Verification
- Backend tests: `cd apps/api && python -m pytest -v`
- Frontend tests: `cd apps/web && npm run test:ci -- alert-list.test.tsx`
- Terraform validation: `cd infra/terraform && terraform init && terraform validate`

## Deployment Preparation (Values Required Later)
- API image uses `apps/api/Dockerfile`.
- Worker jobs run via `python -m app.workers.runner --worker <ingestor|evaluator|digest>`.
- If `dispatcher_push_endpoint_base` is empty, Terraform uses the Cloud Run API service URI automatically.
