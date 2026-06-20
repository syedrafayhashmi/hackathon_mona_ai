# Mona AI Enterprise Operations Hub

A hackathon-ready B2B operations dashboard covering ten AI workflows across finance, staffing, compliance, hiring, marketing intelligence, pricing, and secure applicant processing.

## Run locally with Docker

1. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` if live Gemini analysis is required.
2. Run `docker compose up --build`.
3. Open `http://localhost:3000`.

The supplied fixtures work without Gemini. External email, SMS, and price publication actions are always simulated and require approval.

## Gemini model routing

- `models/gemini-3.5-flash`: invoice and permit validation, CV/certificate review, secure email reasoning, interview questions, pricing, and product-gap analysis.
- `models/gemini-3.1-flash-lite`: classification, invoice field extraction, document-type detection, email triage, and batch extraction.
- `models/gemini-3.1-flash-image`: reel visuals, product mockups, and safe-zone previews.
- `models/gemini-embedding-2`: CV/job, product, vendor, invoice, and customer-segment similarity representations.

Deterministic code remains authoritative for dates, staffing eligibility, pricing limits, and security actions.

## Development

- API: create a virtual environment, install `apps/api/requirements.txt`, then run `cd apps/api && python -m uvicorn app.main:app --reload`
- Web: `cd apps/web && npm install && npm run dev`
- Tests: `cd apps/api && pytest`

Data in `data/raw` is immutable. Generated transactions, video artifacts, and demo state are written outside that directory.
