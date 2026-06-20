from __future__ import annotations

import asyncio
import logging
import mimetypes
import re
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from .config import (
    ALLOWED_EXTENSIONS, ARTIFACT_ROOT, GEMINI_FAST_MODEL, GEMINI_IMAGE_MODEL,
    GEMINI_MAX_CONCURRENCY, MAX_UPLOAD_BYTES,
)
from .gemini import GeminiGenerationError, GeminiRateLimitError, GeminiUnavailableError, gemini
from .graph import run_agent_workflow
from .models import AuditEvent, FileStatus, RunRecord
from .store import clear_runs, get_run, init_db, list_runs, save_run
from .workflows import (
    AIWorkflowValidationError, MODULES, PARALLEL_PROBLEMS, build_single_file_task,
    build_single_upload_task, execute_workflow, merge_file_results, module_by_id, source_files,
)

logger = logging.getLogger("mona.orchestrator")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Mona AI Enterprise Operations API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "gemini": gemini.available,
        "agents": gemini.available,
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "models": {"agent": GEMINI_FAST_MODEL, "image": GEMINI_IMAGE_MODEL},
    }


@app.get("/api/modules")
def modules() -> list[dict[str, object]]:
    return [module.model_dump() for module in MODULES]


@app.get("/api/runs")
def runs() -> list[RunRecord]:
    return [run for run in list_runs() if run.agent_generated]


async def _gather_and_merge(problem_id: str, prepared: list[tuple[str, object]]):
    """Run a prepared list of (name, task | exception) — one Gemini agent each — then merge.

    Uses asyncio.gather over asyncio.to_thread so blocking SDK calls run in parallel.
    A single file failing is captured per file and never aborts the batch.
    """
    semaphore = asyncio.Semaphore(GEMINI_MAX_CONCURRENCY)
    logger.info(
        "orchestrator.fan_out | problem=%s | files=%d | max_concurrency=%d",
        problem_id, len(prepared), GEMINI_MAX_CONCURRENCY,
    )

    async def process(name: str, task: object):
        if isinstance(task, Exception):
            return name, task
        async with semaphore:
            try:
                return name, await asyncio.to_thread(run_agent_workflow, task)
            except Exception as exc:  # isolate per-file failure from the batch
                return name, exc

    settled = await asyncio.gather(*(process(name, task) for name, task in prepared))
    result, confidence, decision, requires_approval, file_statuses, events = merge_file_results(
        problem_id, GEMINI_MAX_CONCURRENCY, settled
    )
    completed = sum(1 for status in file_statuses if status.status == "completed")
    failed = sum(1 for status in file_statuses if status.status == "failed")
    logger.info("orchestrator.merge | problem=%s | completed=%d | failed=%d", problem_id, completed, failed)
    return result, confidence, decision, requires_approval, file_statuses, events


async def _run_parallel(problem_id: str, fixture_id: str, form_data: str):
    """Fan out one Gemini agent per organizer source file (batch fixtures)."""
    paths = source_files(problem_id)
    if not paths:
        raise AIWorkflowValidationError(f"No source files found for problem {problem_id}")
    prepared: list[tuple[str, object]] = []
    for path in paths:
        try:
            prepared.append((path.name, build_single_file_task(problem_id, fixture_id, path, form_data=form_data)))
        except AIWorkflowValidationError as exc:
            prepared.append((path.name, exc))  # unreadable file → isolated failure
    return await _gather_and_merge(problem_id, prepared)


async def _run_parallel_uploads(problem_id: str, fixture_id: str, form_data: str,
                                uploads: list[tuple[str, bytes, str | None]]):
    """Fan out one Gemini agent per uploaded file, then merge into one batch result."""
    prepared: list[tuple[str, object]] = []
    for name, content, mime in uploads:
        try:
            prepared.append((name, build_single_upload_task(problem_id, fixture_id, name, content, mime, form_data=form_data)))
        except AIWorkflowValidationError as exc:
            prepared.append((name, exc))
    return await _gather_and_merge(problem_id, prepared)


@app.post("/api/runs", response_model=RunRecord)
async def create_run(
    problem_id: str = Form(...),
    fixture_id: str = Form("default"),
    form_data: str = Form("{}"),
    files: list[UploadFile] = File(default=[]),
) -> RunRecord:
    try:
        module = module_by_id(problem_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Unknown module") from exc

    run_id = uuid4().hex[:12]

    # Read + validate every uploaded file (browsers may send empty file parts — skip those).
    uploads: list[tuple[str, bytes, str | None]] = []
    for upload in files:
        if not upload or not upload.filename:
            continue
        name = Path(upload.filename).name
        if Path(name).suffix.lower() not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {name}")
        content = await upload.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"{name} exceeds 20 MB")
        mime = upload.content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
        uploads.append((name, content, mime))

    file_statuses: list[FileStatus] = []
    try:
        if problem_id in PARALLEL_PROBLEMS:
            # Batch problems (invoices, permit set): one Gemini agent per file → one row per file.
            if uploads:
                result, confidence, decision, requires_approval, file_statuses, events = await _run_parallel_uploads(
                    problem_id, fixture_id, form_data, uploads
                )
            else:
                result, confidence, decision, requires_approval, file_statuses, events = await _run_parallel(
                    problem_id, fixture_id, form_data
                )
        else:
            # Everything else: one combined agent call over all uploaded files (or fixture data).
            result, confidence, decision, requires_approval, events = await asyncio.to_thread(
                execute_workflow,
                problem_id,
                fixture_id,
                run_id,
                form_data=form_data,
                uploads=uploads,
            )
    except GeminiUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GeminiRateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except (GeminiGenerationError, AIWorkflowValidationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    run = RunRecord(
        id=run_id,
        problem_id=problem_id,
        module_name=module.name,
        fixture_id=fixture_id,
        confidence=confidence,
        source_mode="gemini",
        agent_generated=True,
        model_usage=[GEMINI_FAST_MODEL],
        decision=decision,
        requires_approval=requires_approval,
        result=result,
        audit_events=events,
        file_statuses=file_statuses,
        status="blocked" if any(event.status == "blocked" for event in events) else "completed",
    )
    save_run(run)
    return run


@app.get("/api/runs/{run_id}", response_model=RunRecord)
def run_detail(run_id: str) -> RunRecord:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/api/runs/{run_id}/events")
async def run_events(run_id: str) -> StreamingResponse:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def stream():
        for event in run.audit_events:
            yield f"event: audit\ndata: {event.model_dump_json()}\n\n"
            await asyncio.sleep(0.18)
        yield "event: complete\ndata: {}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/runs/{run_id}/approve", response_model=RunRecord)
def approve_run(run_id: str) -> RunRecord:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.approved = True
    run.status = "approved"
    for row in run.result.table.rows:
        if row.get("Status") == "Review":
            row["Status"] = "Approved"
    run.audit_events.append(AuditEvent(stage="Approved", title="Human approval recorded", detail="The operator approved the reviewed decision."))
    save_run(run)
    return run


def _rank_value(row: dict) -> int:
    digits = re.sub(r"[^0-9]", "", str(row.get("Rank", "")))
    return int(digits) if digits else 99


def _send_shift_outreach(run: RunRecord) -> None:
    """Problem 2 action: message the top-ranked eligible candidate to cover the gap."""
    rows = run.result.table.rows
    eligible = [r for r in rows if str(r.get("Status", "")).strip().lower().startswith(("elig", "ready"))]
    target = min(eligible or rows, key=_rank_value, default=None)
    if not target:
        run.audit_events.append(AuditEvent(stage="Outreach", title="No eligible staff to contact", detail="The agent found no eligible candidate for this gap.", status="blocked"))
        return
    name = str(target.get("Candidate", "the top candidate"))
    message = str(target.get("Outreach", "")).strip() or f"Hi {name}, are you available to cover the open shift? Please reply to confirm."
    target["Status"] = "Contacted"
    run.audit_events.append(AuditEvent(stage="Outreach sent", title=f"Outreach sent to {name}", detail=message, status="complete"))
    run.audit_events.append(AuditEvent(stage="Outreach", title="Awaiting response", detail="Will escalate to the next-ranked candidate if no confirmation is received.", status="review"))


@app.post("/api/runs/{run_id}/simulate-action", response_model=RunRecord)
def simulate_action(run_id: str) -> RunRecord:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.requires_approval and not run.approved:
        raise HTTPException(status_code=409, detail="Human approval is required first")
    if run.problem_id == "2":
        _send_shift_outreach(run)
    else:
        run.audit_events.append(AuditEvent(stage="Actioned", title="Simulated action completed", detail="No external system was changed."))
    run.status = "actioned"
    save_run(run)
    return run


@app.get("/api/runs/{run_id}/artifacts/{name}")
def artifact(run_id: str, name: str) -> FileResponse:
    base = (ARTIFACT_ROOT / run_id).resolve()
    target = (base / Path(name).name).resolve()
    if base not in target.parents or not target.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(target, filename=target.name)


@app.post("/api/demo/reset")
def reset_demo() -> dict[str, str]:
    clear_runs()
    if ARTIFACT_ROOT.exists():
        for child in ARTIFACT_ROOT.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
    return {"status": "reset"}
