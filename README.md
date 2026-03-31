# StockAlarm

## Prerequisites
- Python 3.12
- Node.js 20+
- Terraform 1.8+

## Environment
1. Copy `.env.example` to `.env`.
2. Fill API keys, `GOOGLE_CLIENT_ID`, and local database connection.
3. Never commit `.env`.

## Local Run
- API: `cd apps/api && uvicorn app.main:app --reload`
- Web: `cd apps/web && npm run dev`

## Verification
- Backend tests: `cd apps/api && python -m pytest -v`
- Frontend tests: `cd apps/web && npm run test:ci -- alert-list.test.tsx`
- Terraform validation: `cd infra/terraform && terraform init && terraform validate`
