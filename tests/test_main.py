import pytest
import sys, os
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app, _repo_issues_cache
# send requests to the app without running a server
client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_cache():
    _repo_issues_cache.clear()
    yield
    _repo_issues_cache.clear()

def test_get_issues_success(monkeypatch):
    """
    1) given a repo with issues including a pull request
    2) call GET /{repo}/issues
    3) we should only get back real issues (PRs are filtered out)
    """
    fake_issues = [
        {"number": 1, "title": "Bug A", "state": "open", "html_url": "http://x/1"},
        {"number": 2, "title": "PR B", "state": "open", "html_url": "http://x/2", "pull_request": {}},
    ]
    # fetch_issues replaced with a fake one that returns our data
    monkeypatch.setattr("app.main.fetch_issues", lambda repo: fake_issues)

    response = client.get("/my-repo/issues")
    assert response.status_code == 200
    data = response.json()

    # Should only include Bug A
    assert "issues" in data
    assert len(data["issues"]) == 1
    assert data["issues"][0]["title"] == "Bug A"


def test_get_issue_not_found(monkeypatch):
    """
    1) given a repo that exists but has no issues
    2) call GET /{repo}/issues/{issue_number}
    3) we should get a 404 Not Found
    """
    monkeypatch.setattr("app.main.fetch_issues", lambda repo: [])
    response = client.get("/my-repo/issues/1")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_scope_and_execute_batch_all(monkeypatch):
    """
    1) given a repo with multiple issues
    2) call POST /{repo}/issues/scope-and-execute-batch with all=True
    3) only real issues are processed, PRs are skipped
    """
    fake_issues = [
        {"number": 1, "title": "Bug A", "state": "open", "html_url": "http://x/1"},
        {"number": 2, "title": "PR B", "state": "open", "html_url": "http://x/2", "pull_request": {}},
    ]
    monkeypatch.setattr("app.main.fetch_issues", lambda repo: fake_issues)
    _repo_issues_cache["my-repo"] = {i["number"]: i for i in fake_issues}

    fake_scope = {"action_plan": ["step 1", "step 2"]}
    fake_execute = {"branch": "fix-bug-a"}
    mock_devin = AsyncMock()
    mock_devin.scope_issue.return_value = fake_scope
    mock_devin.implement_issue.return_value = fake_execute
    app.state.devin = mock_devin

    response = client.post(
        "/my-repo/issues/scope-and-execute-batch",
        json={"all": True}
    )
    assert response.status_code == 200
    data = response.json()

    # One succeeded - one skipped (PR)
    assert data["succeeded"] == 1
    assert data["failed"] == 0
    assert len(data["results"]) == 1
    assert data["results"][0]["issue_number"] == 1



@pytest.mark.asyncio
async def test_scope_and_execute_batch_selected(monkeypatch):
    """
    1) given a repo with multiple issues
    2) call POST /{repo}/issues/scope-and-execute-batch with an explicit list
    3) only those issues are processed
    """
    fake_issues = [
        {"number": 1, "title": "Bug A", "state": "open", "html_url": "http://x/1"},
        {"number": 2, "title": "Bug B", "state": "open", "html_url": "http://x/2"},
    ]
    monkeypatch.setattr("app.main.fetch_issues", lambda repo: fake_issues)
    _repo_issues_cache["my-repo"] = {i["number"]: i for i in fake_issues}

    fake_scope = {"action_plan": ["do something"]}
    fake_execute = {"branch": "fix-bug-b"}
    mock_devin = AsyncMock()
    mock_devin.scope_issue.return_value = fake_scope
    mock_devin.implement_issue.return_value = fake_execute
    app.state.devin = mock_devin

    response = client.post(
        "/my-repo/issues/scope-and-execute-batch",
        json={"all": False, "issues": [2]}
    )
    assert response.status_code == 200
    data = response.json()

    # Only issue 2 was processed
    assert data["succeeded"] == 1
    assert data["failed"] == 0
    assert data["results"][0]["issue_number"] == 2
    assert data["results"][0]["status"] == "success"
