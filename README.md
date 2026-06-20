# Mona AI Enterprise Operations Hub

A hackathon-ready B2B operations dashboard covering ten AI workflows across finance, staffing, compliance, hiring, marketing intelligence, pricing, and secure applicant processing.

## Run locally with Docker

1. Copy `.env.example` to `.env` and add `GEMINI_API_KEY`. Every workflow requires it.
2. Run `docker compose up --build`.
3. Open `http://localhost:3000`.

To use the app from another device on the same network, open
`http://<computer-lan-ip>:3000` on that device. On Windows, find the address
with `ipconfig` and allow inbound TCP port 3000 on private networks if Windows
Firewall blocks the connection.

The API returns `503` when Gemini is unavailable; it does not substitute hardcoded demo results. External email, SMS, and price-publication actions are simulated and require human approval.

## Gemini agent architecture

- Every problem uses the same LangGraph pipeline: intake, security pre-scan, Gemini solve, schema validation, and human review.
- `models/gemini-3.1-flash-lite` produces the table, summary, evidence, confidence, risk and decision in one structured call per run.
- Source documents are parsed locally and image evidence is sent as multimodal input in the same call.
- No Anthropic or Claude API key is used.

Deterministic code is limited to input parsing, prompt-injection checks, output-schema validation, policy guardrails and local artifact rendering. It does not provide substitute business results.

## Parallel batch processing

- Batch workflows (Invoices, Work Permits) fan out **one Gemini agent per file**, run concurrently with an `asyncio` semaphore (`GEMINI_MAX_CONCURRENCY`, default 5).
- Per-file status (`pending → processing → completed → failed`) is tracked and shown in the "Parallel file processing" panel.
- A single failed file is isolated and never aborts the batch; rows map back to each file in original order.

## Rate-limit visibility (Docker logs)

- Every Gemini request logs to stdout (`mona.gemini`): model, agent/use-case, attempt, latency, and outcome.
- `429` / `RESOURCE_EXHAUSTED` / quota errors are logged as `gemini.rate_limit` and retried with bounded exponential backoff (`GEMINI_MAX_RETRIES`, default 4) honoring `retry-after`.
- When retries are exhausted the API returns HTTP `429` and the UI shows a red error toast — no silent failures.
- Watch them live: `docker compose logs -f api`.

## Demo / pitch mode

1. Open `http://localhost:3000`. The top-right badge shows whether Gemini is connected.
2. Left sidebar groups all 10 problems by department. Click any one, then **Run analysis**.
3. Each result proves the customer's checkboxes: the table/cards, the audit trail (which agent ran, on what input), confidence/risk, and a human **Approve → action** gate.
4. Problem 1 (Invoices) and 3 (Work Permits) show the live parallel per-file panel.
5. Problem 10 (Secure Applicant Inbox) demonstrates prompt-injection quarantine and the missing-document checklist.

## Development

- API: create a virtual environment, install `apps/api/requirements.txt`, then run `cd apps/api && python -m uvicorn app.main:app --reload`
- Web: `cd apps/web && npm install && npm run dev`
- Tests: `cd apps/api && pytest`

Data in `data/raw` is immutable. Generated transactions, video artifacts, and demo state are written outside that directory.
