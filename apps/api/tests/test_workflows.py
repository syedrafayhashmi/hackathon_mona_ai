from app.workflows import execute_workflow
from app.extractors import extract_text
from app.config import GEMINI_EMBEDDING_MODEL, GEMINI_FAST_MODEL, GEMINI_IMAGE_MODEL, GEMINI_MODEL
from pathlib import Path


def test_all_workflows_return_tables():
    for problem_id in map(str, range(1, 11)):
        fixture = "safe-email" if problem_id == "10" else "default"
        result, confidence, decision, requires_approval, events = execute_workflow(problem_id, fixture, f"test-{problem_id}")
        assert result.table.columns
        assert result.table.rows
        assert 0 <= confidence <= 1
        assert decision
        assert requires_approval is True
        assert len(events) >= 4


def test_pricing_stays_inside_band():
    result, *_ = execute_workflow("8", "default", "pricing-test")
    assert all(row["Guardrail"] in {"Pass", "Review"} for row in result.table.rows)


def test_prompt_injection_is_blocked():
    result, _, decision, _, events = execute_workflow("10", "malicious-email", "security-test")
    assert "injection" in result.summary.lower()
    assert any(event.status == "blocked" for event in events)
    assert "criminal" in decision.lower()


def test_pdf_extractor_reads_supplied_invoice():
    path = Path("data/raw/problem_01_invoices/01_stadtwerke_gas_de.pdf")
    text = extract_text(path.name, path.read_bytes())
    assert "Stadtwerke" in text
    assert "258,44" in text


def test_configured_gemini_model_router():
    assert GEMINI_MODEL == "models/gemini-3.5-flash"
    assert GEMINI_FAST_MODEL == "models/gemini-3.1-flash-lite"
    assert GEMINI_IMAGE_MODEL == "models/gemini-3.1-flash-image"
    assert GEMINI_EMBEDDING_MODEL == "models/gemini-embedding-2"
