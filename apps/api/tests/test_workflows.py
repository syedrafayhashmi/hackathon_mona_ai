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
    if problem_id == "9":
        row.update({
            "Rank": 1,
            "Need": "Callus",
            "Format": "Device",
            "Competitors": "Scholl, Hansaplast Foot Expert",
            "Allgäuer": "Absent",
            "Category size": 80,
            "Margin": 65,
            "Brand fit": 70,
            "Score": 0,
        })
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


def test_product_gap_prompt_uses_complete_catalogue_and_exact_grid():
    task = workflows.build_agent_task("9", "competitor-matrix")

    assert "section 2 as authoritative" in task.prompt
    assert "callus, dry skin, cold feet, heavy legs, spider veins, muscle pain, joint, recovery" in task.prompt
    assert "cream, gel, spray, bath, foam, balm, device" in task.prompt
    assert "Urea-Fußschaum means dry skin × foam is not absent" in task.prompt
    assert "the matrix does not prove recovery × device" in task.prompt
    assert "Category size × Margin × Brand fit / 10000" in task.prompt


def test_product_gap_rows_are_ranked_by_normalized_product():
    payload = {
        "summary": "Supported white-space cells.",
        "rows": [
            {
                "Rank": 1,
                "Need": "heavy legs",
                "Format": "bath",
                "Competitors": "Kneipp",
                "Allgäuer": "None",
                "Category size": 60,
                "Margin": 70,
                "Brand fit": 80,
                "Score": 99,
            },
            {
                "Rank": 2,
                "Need": "callus",
                "Format": "device",
                "Competitors": "Scholl, Hansaplast Foot Expert",
                "Allgäuer": "Absent",
                "Category size": 90,
                "Margin": 80,
                "Brand fit": 75,
                "Score": 1,
            },
        ],
        "evidence": ["Competitor and catalogue evidence checked."],
        "warnings": ["Category scores are indicative."],
        "review": {"decision": "Review", "owner": "Product Strategy", "risk": "Medium"},
        "confidence": 0.9,
        "decision": "Review ranked cells",
        "requires_approval": True,
    }

    result, *_ = workflows.result_from_agent_payload("9", payload)

    assert [row["Rank"] for row in result.table.rows] == [1, 2]
    assert [row["Need"] for row in result.table.rows] == ["Callus", "Heavy legs"]
    assert [row["Score"] for row in result.table.rows] == [54, 34]
    assert result.table.rows[1]["Allgäuer"] == "Absent"


def test_product_gap_rejects_present_or_limited_allgaeuer_coverage():
    payload = {
        "summary": "Invalid candidate.",
        "rows": [{
            "Rank": 1,
            "Need": "dry skin",
            "Format": "foam",
            "Competitors": "Allpresan",
            "Allgäuer": "Limited",
            "Category size": 90,
            "Margin": 85,
            "Brand fit": 75,
            "Score": 83,
        }],
        "evidence": ["Allgäuer catalogue lists Urea-Fußschaum."],
        "warnings": [],
        "review": {"decision": "Reject", "owner": "Product Strategy", "risk": "Medium"},
        "confidence": 0.9,
        "decision": "Reject invalid white-space cell",
        "requires_approval": True,
    }

    with pytest.raises(workflows.AIWorkflowValidationError, match="not white space"):
        workflows.result_from_agent_payload("9", payload)


def test_static_product_gap_source_filters_unsupported_cells_and_aligns_decision():
    task = workflows.build_agent_task("9", "competitor-matrix")
    payload = {
        "summary": "Promotes unsupported recovery cells.",
        "rows": [
            {
                "Rank": 1,
                "Need": "recovery",
                "Format": "spray",
                "Competitors": "Retterspitz",
                "Allgäuer": "Absent",
                "Category size": 85,
                "Margin": 70,
                "Brand fit": 80,
                "Score": 48,
            },
            {
                "Rank": 2,
                "Need": "callus",
                "Format": "device",
                "Competitors": "Scholl, Hansaplast Foot Expert",
                "Allgäuer": "Absent",
                "Category size": 70,
                "Margin": 60,
                "Brand fit": 75,
                "Score": 32,
            },
        ],
        "evidence": ["Unvalidated model evidence."],
        "warnings": ["Scores are synthetic."],
        "review": {"decision": "Build recovery spray", "owner": "Product Strategy", "risk": "Medium"},
        "confidence": 0.95,
        "decision": "Build recovery spray",
        "requires_approval": True,
    }

    result, confidence, decision, _ = workflows.result_from_agent_payload(
        "9", payload, source_text=task.source_text
    )

    assert [(row["Need"], row["Format"]) for row in result.table.rows] == [("Callus", "Device")]
    assert confidence == 0.85
    assert "Callus × Device" in result.summary
    assert "Callus × Device" in decision
    assert "Build recovery spray" not in result.review["decision"]
    assert all("recovery spray" not in warning.lower() for warning in result.warnings)
    assert any("Removed unsupported recovery × spray" in warning for warning in result.warnings)
    assert any("Mobil Eisspray akut" in item for item in result.evidence)


def test_static_product_gap_source_restores_omitted_validated_cell():
    task = workflows.build_agent_task("9", "competitor-matrix")
    payload = {
        "summary": "Only unsupported cell returned.",
        "rows": [{
            "Rank": 1,
            "Need": "recovery",
            "Format": "spray",
            "Competitors": "Retterspitz",
            "Allgäuer": "Absent",
            "Category size": 85,
            "Margin": 70,
            "Brand fit": 80,
            "Score": 48,
        }],
        "evidence": ["Unvalidated model evidence."],
        "warnings": [],
        "review": {"decision": "Build recovery spray", "owner": "Product Strategy", "risk": "Medium"},
        "confidence": 0.95,
        "decision": "Build recovery spray",
        "requires_approval": True,
    }

    result, _, decision, _ = workflows.result_from_agent_payload(
        "9", payload, source_text=task.source_text
    )

    assert result.table.rows == [workflows._STATIC_GAP_FALLBACK]
    assert "Callus × Device" in decision
    assert any("indicative fallback scores" in warning for warning in result.warnings)


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
