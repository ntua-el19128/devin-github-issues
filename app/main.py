import os, aiohttp
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from starlette.responses import Response

from .github_client import fetch_issues  
from .devin_client import DevinClient

class BatchScopeExecuteRequest(BaseModel):
    all: bool = False                 # run on all 
    issues: Optional[List[int]] = None  # or run on these issue numbers

@asynccontextmanager
async def lifespan(app: FastAPI):
    headers = {"Authorization": f"Bearer {os.getenv('DEVIN_API_KEY')}"}
    app.state.http = aiohttp.ClientSession(headers=headers)
    app.state.devin = DevinClient(app.state.http)
    yield                           
    await app.state.http.close() 

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    # make both origins work with regex ["http://localhost:5173", "http://127.0.0.1:5173"]
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):5173",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_responses(request: Request, call_next):
    response = await call_next(request)

    chunks = [chunk async for chunk in response.body_iterator]
    body = b"".join(chunks)

    try:
        print(f"Response for {request.url}: {body.decode('utf-8', errors='replace')}")
    except Exception:
        print(f"Response for {request.url}: <non-text {len(body)} bytes>")

    return Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=getattr(response, "media_type", None),
    )



# in-memory cache: 
_repo_issues_cache: Dict[str, Dict[int, Dict[str, Any]]] = {}

# endpoints
# list of issues
@app.get("/{repo}/issues")
def get_issues(repo: str):
    try:
        data = fetch_issues(repo)
        _repo_issues_cache[repo] = {issue["number"]: issue for issue in data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not data:
        return {"message": f"The repository '{repo}' has no issues"}

    issues = [

        {"number": issue["number"], 
         "title": issue["title"], 
         "state": issue["state"], 
         "url": issue["html_url"]}

        for issue in data if "pull_request" not in issue
    ]
    return {"issues": issues}

# issue-specific info
@app.get("/{repo}/issues/{issue_number}")
def get_issue(repo: str, issue_number: int):
    try:
        issues = fetch_issues(repo)  # ensures repo exists
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check repo '{repo}': {e}")

    # If repo exists but no issues at all
    if not issues:
        raise HTTPException(
            status_code=404,
            detail=f"The repository '{repo}' has no issues"
        )
    
    repo_cache = _repo_issues_cache.get(repo)
    
    if not repo_cache or issue_number not in repo_cache:
        raise HTTPException(status_code=404, detail="Issue not found. Issue doesn’t exist or call /repo/issues")
    
    
    issue = repo_cache[issue_number]
    if "pull_request" in issue:
        raise HTTPException(status_code=404, detail="This is a pull request, not an issue")
    return {
        "number": issue["number"],
        "title": issue["title"],
        "body": issue.get("body", ""),
        "state": issue["state"],
        "url": issue["html_url"],
    }

# Army of Devins : scope (Devin i.1) and execute (Devin i.2) for all issues or specific number of issues
@app.post("/{repo}/issues/scope-and-execute-batch")
async def scope_and_execute_batch(
    repo: str,
    body: BatchScopeExecuteRequest
):
    try:
        issues = fetch_issues(repo)  # ensures repo exists
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check repo '{repo}': {e}")
    
    # If repo exists but no issues at all
    if not issues:
        raise HTTPException(
            status_code=404,
            detail=f"The repository '{repo}' has no issues"
        )

    repo_cache: Dict[int, Dict[str, Any]] = _repo_issues_cache[repo]

    if body.all:
        targets = [n for n, it in repo_cache.items() if "pull_request" not in it]
        targets.sort()
    else:
        targets = body.issues or []
        
    results = []
    succeeded = failed = 0
    
    for issue_number in targets:
        if not repo_cache or issue_number not in repo_cache:
            raise HTTPException(status_code=404, detail="Issue not found. Issue doesn’t exist or call /repo/issues")
        issue = repo_cache[issue_number] 

        # Skip PRs
        if "pull_request" in issue:
            results.append({
                "issue_number": issue_number,
                "status": "skipped",
                "reason": "pull request"
            })
            continue

        issue_title = issue.get("title", f"Issue #{issue_number}")

        try:
            scoped = await app.state.devin.scope_issue(
                repo=repo,
                issue_number=issue_number,
                issue_title=issue_title,
            )

            action_plan = scoped.get("action_plan") if isinstance(scoped, dict) else None
            if not action_plan or not isinstance(action_plan, list):
                results.append({
                    "issue_number": issue_number,
                    "status": "failed",
                    "error": "Scoper did not return a valid action_plan"
                })
                failed += 1
                continue

            action_plan = [str(s).strip() for s in action_plan if str(s).strip()]

            executed = await app.state.devin.implement_issue(
                repo=repo,
                issue_number=issue_number,
                issue_title=issue_title,
                action_plan=action_plan,
            )

            results.append({
                "issue_number": issue_number,
                "status": "success",
                "scoped": scoped,
                "executed": executed
            })
            succeeded += 1

        except TimeoutError as e:
            results.append({
                "issue_number": issue_number,
                "status": "failed",
                "error": f"Timeout: {e}"
            })
            failed += 1

        except Exception as e:
            results.append({
                "issue_number": issue_number,
                "status": "failed",
                "error": str(e)
            })
            failed += 1

    return {
        "repo": f"{repo}",
        "total_selected": len(targets),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }
