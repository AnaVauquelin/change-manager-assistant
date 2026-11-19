from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app, get_clean_value

client = TestClient(app)


def test_get_clean_value_string_and_missing():
    fields_def = [{"id": "customfield_101", "name": "NJ Change IDs"}]
    issue = SimpleNamespace(fields=SimpleNamespace(customfield_101="RN-12, ND-05"))
    assert get_clean_value(issue, "NJ Change IDs", fields_def) == "RN-12, ND-05"
    assert get_clean_value(issue, "Unknown Field", fields_def) == ""


def test_get_clean_value_list_and_objects():
    fields_def = [{"id": "customfield_102", "name": "Dependencies NJ"}]
    item1 = SimpleNamespace(value="DEP-1")
    item2 = SimpleNamespace(name="DEP-2")
    issue = SimpleNamespace(fields=SimpleNamespace(customfield_102=[item1, item2, "DEP-3"]))
    assert get_clean_value(issue, "Dependencies NJ", fields_def) == "DEP-1, DEP-2, DEP-3"


@patch("main.JIRA")
def test_get_notes_compliance_policies(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.fields.return_value = [
        {"id": "cf_email", "name": "Email Body"},
        {"id": "cf_nj", "name": "NJ Change IDs"},
        {"id": "cf_dep", "name": "Dependencies NJ"},
    ]

    def make_issue(key, nj_id):
        return SimpleNamespace(
            fields=SimpleNamespace(
                status=SimpleNamespace(name="Approved"),
                summary=f"Summary for {key}",
                cf_email="Formatted release note body",
                cf_nj=nj_id,
                cf_dep="None",
                issuelinks=[],
            )
        )

    mock_jira.issue.side_effect = lambda k: {
        "GK-1": make_issue("GK-1", "RN-10"),
        "GK-2": make_issue("GK-2", "ND-20"),
        "GK-3": make_issue("GK-3", "EX-30"),
    }[k]

    res = client.post("/get-notes", json={"ticket_id": "GK-1, GK-2 GK-3"})
    assert res.status_code == 200
    tickets = res.json()["tickets"]
    assert len(tickets) == 3
    assert "RN" in tickets[0]["policy"]
    assert tickets[0]["subject_ids"] == "[RN-10]"
    assert "ND" in tickets[1]["policy"]
    assert "EX" in tickets[2]["policy"]


@patch("main.JIRA")
def test_extract_nj_ids_deduplication(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.fields.return_value = [{"id": "cf_nj", "name": "NJ Change IDs"}]
    mock_jira.issue.return_value = SimpleNamespace(
        fields=SimpleNamespace(summary="Payment Gateway Update", cf_nj="RN-44")
    )

    res = client.post("/extract-nj-ids", json={"raw_text": "Tickets GK-100 and GK-100 in sprint"})
    assert res.status_code == 200
    data = res.json()["extracted_data"]
    assert len(data) == 1
    assert data[0]["original_id"] == "GK-100"
    assert data[0]["nj_change_id"] == "RN-44"


@patch("main.JIRA")
def test_get_dashboard_stats(mock_jira_cls):
    mock_jira = MagicMock()
    mock_jira_cls.return_value = mock_jira
    mock_jira.search_issues.return_value = SimpleNamespace(total=4)

    res = client.get("/get-dashboard-stats")
    assert res.status_code == 200
    stats = res.json()["stats"]
    assert len(stats) == 5
    assert all(item["count"] == 4 for item in stats)
