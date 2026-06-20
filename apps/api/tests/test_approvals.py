from app import main
from app.models import AuditEvent, DataTable, RunRecord, WorkflowResult


def test_approval_updates_review_status_cells(monkeypatch):
    run = RunRecord(
        id="invoice-run",
        problem_id="1",
        module_name="Invoice Operations",
        decision="Routing ready",
        result=WorkflowResult(
            summary="Invoice review",
            table=DataTable(
                columns=["Invoice", "Status", "Risk"],
                rows=[{"Invoice": "invoice.pdf", "Status": "Review", "Risk": "Review"}],
            ),
        ),
        audit_events=[AuditEvent(stage="Review", title="Review ready", detail="Ready")],
    )
    saved = []
    monkeypatch.setattr(main, "get_run", lambda run_id: run if run_id == run.id else None)
    monkeypatch.setattr(main, "save_run", saved.append)

    approved = main.approve_run(run.id)

    assert approved.approved is True
    assert approved.status == "approved"
    assert approved.result.table.rows[0]["Status"] == "Approved"
    assert approved.result.table.rows[0]["Risk"] == "Review"
    assert saved == [approved]
