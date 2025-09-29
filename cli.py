import os, sys, time, textwrap, threading, json, requests
from itertools import cycle

BASE_URL = os.getenv("SERVER_URL", "http://127.0.0.1:8000").rstrip("/")

_repo_issues_cache = {}  

_current_repo = None

def _require_repo():
    if not _current_repo:
        print(" No repo selected. Use `use <repo>` first.")
        return None
    return _current_repo

# helpers
def _url(path: str) -> str:
    return f"{BASE_URL}/{path.lstrip('/')}"

def _get(path: str):
    resp = requests.get(_url(path))
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail) 
    return resp.json()

def _post(path: str, json=None, timeout=None):
    resp = requests.post(_url(path), json=json, timeout=timeout)
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(detail) 
    return resp.json()

# pretty printing helpers
def _print_rule(char="-", width=80):
    print(char * width)

def _start_spinner(message: str, interval: float = 0.12):
    """
    Start a spinner in a background thread. Returns a (stop_event, thread).
    Fake effect of progress in the terminal:))
    """
    stop_event = threading.Event()

    def run():
        for ch in cycle("|/-\\"):
            if stop_event.is_set():
                break
            sys.stdout.write(f"\r{message} {ch}")
            sys.stdout.flush()
            time.sleep(interval)

        sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
        sys.stdout.flush()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return stop_event, t

def _print_issue_result(r: dict):
    n = r.get("issue_number")
    status = r.get("status") or "success"  # batch has status, single-issue implies success
    print(f"Issue #{n}: {status}")

    # Scoper Output
    scoped = r.get("scoped") or {}
    s_struct = scoped.get("structured_output") or scoped

    summary    = s_struct.get("summary")
    confidence = s_struct.get("confidence_score", s_struct.get("confidence"))
    aplan      = s_struct.get("action_plan")

    if summary:
        print("  • Summary:")
        for line in textwrap.wrap(summary, width=74):
            print("    ", line)
    if confidence:
        print(f"  • Confidence: {confidence}")
    if isinstance(aplan, list):
        print(f"  • Plan steps: {len(aplan)}")

    # Implementer output ---
    executed = r.get("executed") or {}
    e_struct = executed.get("structured_output") or executed

    pr_url  = e_struct.get("pull_request_url") or e_struct.get("pr_url")
    branch  = e_struct.get("branch_name")
    files   = e_struct.get("files_created") or e_struct.get("files_changed")
    commits = e_struct.get("commits")

    if pr_url:
        print(f"  • Pull Request: {pr_url}")
    if branch:
        print(f"  • Branch: {branch}")
    if files:
        if isinstance(files, list):
            print("  • Files:")
            for f in files[:8]:
                print("     -", f)
            if len(files) > 8:
                print(f"     - …and {len(files)-8} more")
        else:
            print(f"  • Files: {files}")
    if commits:
        print("  • Commits:")
        for c in (commits[:5] if isinstance(commits, list) else [commits]):
            line = c if isinstance(c, str) else json.dumps(c)
            print("     -", line.strip()[:200])

    _print_rule()


# CLI commands
def list_issues(repo: str):
    try:
        data = _get(f"{repo}/issues")
    except RuntimeError as e:
        print(f" Error: {e}")
        return

    issues = data.get("issues")
    if not issues:
        msg = data.get("message", "No issues found.")
        print(msg)
        return

    issues_sorted = sorted(issues, key=lambda x: x["number"])
    _repo_issues_cache[repo] = {it["number"]: it for it in issues_sorted}

    print(f"\nIssues for repo '{repo}':")
    _print_rule()
    for issue in issues_sorted:
        print(f"#{issue['number']:<5} [{issue['state']:<6}] {issue['title']}")
        print(f"     URL: {issue['url']}")
    _print_rule()


def show_issue(repo: str, issue_number: int):
    try:
        issue = _get(f"{repo}/issues/{issue_number}")
    except RuntimeError as e:
        print(f" Error: {e}")
        return

    title = issue["title"]
    state = issue["state"]
    body = issue.get("body") or "(no body)"
    url = issue["url"]

    print(f"\n#{issue_number} [{state}] {title}")
    _print_rule("=")
    print(textwrap.fill(body, width=78))
    _print_rule("=")
    print("URL:", url, "\n")

def scope_and_execute_batch(repo: str, issue_numbers: list[int] | None, all_flag: bool):
    heading = (f"Scope & Execute (batch) for ALL issues in '{repo}'"
               if all_flag else f"Scope & Execute (batch) for {repo}: {issue_numbers}")
    print(heading)

    body = {"all": bool(all_flag)}
    if not all_flag:
        body["issues"] = issue_numbers

    path = f"{repo}/issues/scope-and-execute-batch"
    full_url = _url(path)
    print(f"(POST {full_url})")

    stop_event, spin_thread = _start_spinner("Working with Devin (this can take a while)…")

    try:
        resp = requests.post(full_url, json=body, timeout=None)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            stop_event.set(); spin_thread.join()
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            print(f" Error {resp.status_code}: {detail}")
            return
        data = resp.json()
    except requests.exceptions.ConnectTimeout:
        stop_event.set(); spin_thread.join()
        print(" Error: connect timeout")
        return
    except requests.exceptions.ConnectionError as e:
        stop_event.set(); spin_thread.join()
        print(f" Error: cannot reach server ({e}).")
        return
    except requests.exceptions.ReadTimeout:
        stop_event.set(); spin_thread.join()
        print(" Error: batch took too long (read timeout).")
        return
    except Exception as e:
        stop_event.set(); spin_thread.join()
        print(f" Unexpected error: {e}")
        return
    finally:
        stop_event.set(); spin_thread.join()

    print(f"Finished scope & execute batch for repo '{repo}'\n")
    
    total_selected = data.get("total_selected")
    succeeded = data.get("succeeded")
    failed = data.get("failed")
    results = data.get("results") or []

    print(f"Selected issues: {total_selected}   Succeeded: {succeeded}   Failed: {failed}")
    _print_rule()

    for r in results:
        _print_issue_result(r)

def repl():
    HELP_TEXT = (
        "Commands:\n"
        "  use <repo>                       - ALWAYS RUN FIRST. You can use 'github-issues' if you've set GITHUB_OWNER ='ntua-el19128' \n"
        "  list                             - List issues for a repo (GET /{repo}/issues)\n"
        "  show <issue_number>              - show details for an issue (GET /{repo}/issues/{issue_number})\n"
        "  resolve all                      - scope + execute all issues via Devin (Post /{repo}/issues/{issue_number}/scope-and-execute-batch)\n"
        "  resolve <n1> <n2> ...            - scope + execute #n issues via Devin (Post /{repo}/issues/{issue_number}/scope-and-execute-batch)\n"
        "  help                             - list of all cli commands\n"
        "  exit                             - exit cli\n"
    )

    print("Simple GitHub Issues CLI")
    print("Server:", BASE_URL)
    print(HELP_TEXT)

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "exit":
            print("Check the Frontend!")
            break

        # NEW: help command
        if cmd == "help":
            print(HELP_TEXT)
            continue

        try:
            if cmd == "list" and len(parts) == 1:
                repo = _require_repo()
                if repo: list_issues(repo)

            elif cmd == "show" and len(parts) == 2:
                repo = _require_repo()
                if repo:
                    issue_num = int(parts[1])
                    show_issue(repo, issue_num)

            elif cmd == "resolve":
                repo = _require_repo()
                if repo:
                    tokens = parts[1:]
                    if tokens[0].lower() == "all" and len(tokens) == 1:
                        scope_and_execute_batch(repo, issue_numbers=None, all_flag=True)
                    else:
                        try:
                            nums = [int(t) for t in tokens]
                        except ValueError:
                            print(" Issue numbers must be integers, or use 'all'.")
                            continue
                        scope_and_execute_batch(repo, issue_numbers=nums, all_flag=False)
            elif cmd == "use" and len(parts) == 2:
                global _current_repo
                candidate = parts[1]
                try:
                    
                    data = _get(f"{candidate}/issues")
                    _current_repo = candidate
                    print(f" Current repo set to: {_current_repo}")
                except Exception as e:
                    print(f" Error: repo '{candidate}' not found or inaccessible ({e})")

            else:
                print(" Unknown command or wrong arguments. Type 'help' for commands or 'exit' to quit.")
        except ValueError:
            print(" Issue number must be an integer.")


if __name__ == "__main__":
    repl()
