import json
import re
from pathlib import Path

import pytest

from app import workflows
from app.config import GEMINI_FAST_MODEL, GEMINI_IMAGE_MODEL
from app.extractors import extract_text
from app.gemini import gemini
from app.workflows import execute_workflow


def _fake_agent_result(prompt: str, attachments, *, use_case: str = "workflow"):
    problem_id = re.search(r"Problem ID: (\d+)", prompt).group(1)
    columns_text = re.search(r"exactly these keys: (\[[^\]]+\])", prompt).group(1)
    columns = json.loads(columns_text)
    row = {column: "AI value" for column in columns}
    if problem_id == "8":
        row.update({"Adjustment": "+8%", "Guardrail": "Pass"})
    if problem_id == "10":
        row.update({
            "Attachment": "criminal_report.txt",
            "Type": "Criminal record",
            "Present": "No",
            "Security": "Injection blocked",
            "Status": "Quarantined",
        })
    return {
        "summary": "Gemini generated this workflow result from the supplied source.",
        "rows": [row],
        "evidence": ["Source evidence evaluated by the Gemini agent."],
        "warnings": ["Prompt injection blocked."] if problem_id == "10" else [],
        "review": {"decision": "Human review", "owner": "Operations", "risk": "Medium"},
        "confidence": 0.93,
        "decision": "Request a valid criminal record" if problem_id == "10" else "Review AI result",
        "requires_approval": True,
    }


@pytest.fixture(autouse=True)
def fake_gemini(monkeypatch):
    monkeypatch.setattr(gemini, "generate_workflow", _fake_agent_result)
    monkeypatch.setattr(workflows, "_create_artifacts", lambda *args: None)


def test_all_workflows_use_agent_and_return_tables():
    for problem_id in map(str, range(1, 11)):
        fixture = "safe-email" if problem_id == "10" else "default"
        result, confidence, decision, requires_approval, events = execute_workflow(problem_id, fixture, f"test-{problem_id}")
        assert result.table.columns
        assert result.table.rows
        assert 0 <= confidence <= 1
        assert decision
        assert requires_approval is True
        assert any(event.stage == "Gemini Agent · Solve" for event in events)


def test_pricing_stays_inside_band():
    result, *_ = execute_workflow("8", "default", "pricing-test")
    assert all(row["Guardrail"] in {"Pass", "Review"} for row in result.table.rows)


def test_prompt_injection_is_blocked_before_agent_result_is_accepted():
    result, _, decision, _, events = execute_workflow("10", "malicious-email", "security-test")
    assert any("inject" in warning.lower() for warning in result.warnings)
    assert any(event.status == "blocked" for event in events)
    assert "criminal" in decision.lower()


def test_pdf_extractor_reads_supplied_invoice():
    path = Path("../../data/raw/problem_01_invoices/01_stadtwerke_gas_de.pdf")
    text = extract_text(path.name, path.read_bytes())
    assert "Stadtwerke" in text
    assert "258,44" in text


def test_configured_gemini_agent_models():
    assert GEMINI_FAST_MODEL == "models/gemini-3.1-flash-lite"
    assert GEMINI_IMAGE_MODEL == "models/gemini-3.1-flash-image"
