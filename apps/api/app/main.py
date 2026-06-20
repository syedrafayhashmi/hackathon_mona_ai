from __future__ import annotations

import asyncio
import mimetypes
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from .config import ALLOWED_EXTENSIONS, ARTIFACT_ROOT, GEMINI_FAST_MODEL, GEMINI_IMAGE_MODEL, MAX_UPLOAD_BYTES
from .gemini import GeminiGenerationError, GeminiUnavailableError, gemini
from .models import AuditEvent, RunRecord
from .store import clear_runs, get_run, init_db, list_runs, save_run
from .workflows import AIWorkflowValidationError, MODULES, execute_workflow, module_by_id


app = FastAPI(title="Mona AI Enterprise Operations API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


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
    return list_runs()


@app.post("/api/runs", response_model=RunRecord)
async def create_run(
    problem_id: str = Form(...),
    fixture_id: str = Form("default"),
    form_data: str = Form("{}"),
    file: UploadFile | None = File(None),
) -> RunRecord:
    try:
        module = module_by_id(problem_id)
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="Unknown module") from exc

    run_id = uuid4().hex[:12]
    upload_name: str | None = None
    upload_content: bytes | None = None
    upload_mime: str | None = None
    if file:
        suffix = Path(file.filename or "upload").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=415, detail="Unsupported file type")
        upload_content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(upload_content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File exceeds 20 MB")
        upload_name = Path(file.filename or "upload").name
        upload_mime = file.content_type or mimetypes.guess_type(upload_name)[0] or "application/octet-stream"

    try:
        result, confidence, decision, requires_approval, events = await asyncio.to_thread(
            execute_workflow,
            problem_id,
            fixture_id,
            run_id,
            form_data=form_data,
            upload_name=upload_name,
            upload_content=upload_content,
            upload_mime=upload_mime,
        )
    except GeminiUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (GeminiGenerationError, AIWorkflowValidationError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    run = RunRecord(
        id=run_id,
        problem_id=problem_id,
        module_name=module.name,
        fixture_id=fixture_id,
        confidence=confidence,
        source_mode="gemini",
        model_usage=[GEMINI_FAST_MODEL],
        decision=decision,
        requires_approval=requires_approval,
        result=result,
        audit_events=events,
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


@app.post("/api/runs/{run_id}/simulate-action", response_model=RunRecord)
def simulate_action(run_id: str) -> RunRecord:
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.requires_approval and not run.approved:
        raise HTTPException(status_code=409, detail="Human approval is required first")
    run.status = "actioned"
    run.audit_events.append(AuditEvent(stage="Actioned", title="Simulated action completed", detail="No external system was changed."))
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
