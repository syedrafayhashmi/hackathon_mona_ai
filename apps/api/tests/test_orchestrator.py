import asyncio
import json
import re

import pytest

from app import gemini as gemini_module
from app import main
from app.gemini import GeminiGenerationError, GeminiRateLimitError, _is_rate_limit
from app.gemini import gemini


def _single_row_payload(prompt: str, attachments, *, use_case: str = "workflow"):
    columns = json.loads(re.search(r"exactly these keys: (\[[^\]]+\])", prompt).group(1))
    # Simulate one invoice file failing to prove failures are isolated per file.
    if "10_dell_hardware" in prompt:
        raise RuntimeError("simulated extraction failure")
    return {
        "summary": "ok",
        "rows": [{column: "value" for column in columns}],
        "evidence": ["evidence"],
        "warnings": [],
        "review": {"decision": "review", "owner": "Ops", "risk": "Low"},
        "confidence": 0.9,
        "decision": "Route invoice",
        "requires_approval": True,
    }


@pytest.fixture
def fake_single(monkeypatch):
    monkeypatch.setattr(gemini, "generate_workflow", _single_row_payload)


def test_invoices_processed_in_parallel_with_per_file_status(fake_single):
    result, confidence, decision, _approval, file_statuses, events = asyncio.run(
        main._run_parallel("1", "invoice-batch", "{}")
    )
    # 10 organizer invoices; one simulated failure must not abort the batch.
    assert len(file_statuses) == 10
    assert sum(s.status == "completed" for s in file_statuses) == 9
    assert sum(s.status == "failed" for s in file_statuses) == 1
    assert len(result.table.rows) == 9  # one row per completed file, order preserved
    assert any(e.stage == "Orchestrator · Fan-out" for e in events)
    assert any(e.stage == "Orchestrator · Merge" for e in events)
    assert 0 <= confidence <= 1


def test_rate_limit_detection():
    assert _is_rate_limit(RuntimeError("429 RESOURCE_EXHAUSTED"))
    assert _is_rate_limit(RuntimeError("Quota exceeded for quota metric"))
    assert not _is_rate_limit(RuntimeError("invalid argument"))
    assert issubclass(GeminiRateLimitError, GeminiGenerationError)


def test_gemini_retries_then_raises_rate_limit(monkeypatch):
    calls = {"n": 0}

    class _Models:
        def generate_content(self, **kwargs):
            calls["n"] += 1
            raise RuntimeError("429 Too Many Requests RESOURCE_EXHAUSTED")

    class _Client:
        models = _Models()

    monkeypatch.setattr(gemini, "client", _Client())
    monkeypatch.setattr(gemini_module.time, "sleep", lambda *_: None)  # no real backoff waiting
    monkeypatch.setattr(gemini_module, "GEMINI_MAX_RETRIES", 2)

    with pytest.raises(GeminiRateLimitError):
        gemini.generate_workflow('Problem ID: 1\nexactly these keys: ["A"]', None, use_case="test")
    assert calls["n"] == 3  # 1 initial attempt + 2 retries
