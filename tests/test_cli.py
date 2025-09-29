import pytest
import os, sys
import cli

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture(autouse=True)
def clear_cache_and_repo():
    cli._repo_issues_cache.clear()
    cli._current_repo = None
    yield
    cli._repo_issues_cache.clear()
    cli._current_repo = None


def test_list_issues(monkeypatch, capsys):
    fake_issues = {
        "issues": [
            {"number": 1, "title": "Bug A", "state": "open", "url": "http://x/1"},
            {"number": 2, "title": "Bug B", "state": "closed", "url": "http://x/2"},
        ]
    }
    monkeypatch.setattr(cli, "_get", lambda path: fake_issues)

    cli.list_issues("my-repo")
    out = capsys.readouterr().out
    assert "Issues for repo 'my-repo':" in out
    assert "Bug A" in out
    assert "Bug B" in out
    # and that cache was filled
    assert 1 in cli._repo_issues_cache["my-repo"]


def test_show_issue(monkeypatch, capsys):
    fake_issue = {
        "number": 1,
        "title": "Bug A",
        "state": "open",
        "url": "http://x/1",
        "body": "This is a bug"
    }
    monkeypatch.setattr(cli, "_get", lambda path: fake_issue)

    cli.show_issue("my-repo", 1)
    out = capsys.readouterr().out
    assert "#1 [open] Bug A" in out
    assert "This is a bug" in out

def test_scope_and_execute_batch_all(monkeypatch, capsys):
    fake_resp = {
        "repo": "my-repo",
        "total_selected": 2,
        "succeeded": 1,
        "failed": 1,
        "results": [
            {"issue_number": 1, "status": "success", "scoped": {}, "executed": {"branch_name": "fix-a"}},
            {"issue_number": 2, "status": "failed", "error": "boom"},
        ]
    }
    monkeypatch.setattr(cli.requests, "post", lambda url, json=None, timeout=None: type("Resp", (), {
        "status_code": 200,
        "json": lambda self=fake_resp: fake_resp,
        "raise_for_status": lambda self=fake_resp: None
    })())

    cli.scope_and_execute_batch("my-repo", issue_numbers=None, all_flag=True)
    out = capsys.readouterr().out
    assert "Scope & Execute (batch) for ALL issues" in out
    assert "Selected issues: 2   Succeeded: 1   Failed: 1" in out
    assert "Issue #1: success" in out
    assert "Branch: fix-a" in out
    assert "Issue #2: failed" in out
    assert "Error: boom" in out


def test_scope_and_execute_batch_selected(monkeypatch, capsys):
    fake_resp = {
        "repo": "my-repo",
        "total_selected": 1,
        "succeeded": 1,
        "failed": 0,
        "results": [
            {"issue_number": 3, "status": "success", "scoped": {}, "executed": {"branch_name": "fix-c"}},
        ]
    }
    monkeypatch.setattr(cli.requests, "post", lambda url, json=None, timeout=None: type("Resp", (), {
        "status_code": 200,
        "json": lambda self=fake_resp: fake_resp,
        "raise_for_status": lambda self=fake_resp: None
    })())

    cli.scope_and_execute_batch("my-repo", issue_numbers=[3], all_flag=False)
    out = capsys.readouterr().out
    assert "Scope & Execute (batch) for my-repo: [3]" in out
    assert "Selected issues: 1   Succeeded: 1   Failed: 0" in out
    assert "Issue #3: success" in out
    assert "Branch: fix-c" in out