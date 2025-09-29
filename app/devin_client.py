import aiohttp, asyncio, os
from typing import Dict, Any, List

API_BASE = "https://api.devin.ai/v1"
OWNER = os.getenv("GITHUB_OWNER")
BASE_URL=f"https://github.com/{OWNER}" # https://github.com/ntua-el19128/{repo_name}/{}.

class DevinClient:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def _create_session(self, prompt: str) -> str:
        async with self.session.post(
            f"{API_BASE}/sessions",
            json={"prompt": prompt},
        ) as resp:
            data = await resp.json()
            if resp.status >= 400:
                raise RuntimeError(f"Devin session creation failed: {data}")
            return data["session_id"]

    # kinda similar to devin api docs poll
    async def _poll(self, session_id: str, max_wait_seconds: int = 600, wait_for_pr: bool = False) -> Dict[str, Any]:
        backoff = 10
        waited = 0
        while True:
            async with self.session.get(f"{API_BASE}/sessions/{session_id}") as r:
                body = await r.json()
                if r.status >= 400:
                    raise RuntimeError(f"Devin poll failed: {body}")

                so = body.get("structured_output")
                if isinstance(so, dict):
                    if wait_for_pr:
                        if (
                            so.get("pull_request_url")
                            or so.get("branch_name")
                            or so.get("commits")
                            or body.get("pull_request")
                        ):
                            return body

                    else:
                        ap = so.get("action_plan")
                        if isinstance(ap, list) and len(ap) > 0:
                            return body

                status = (body.get("status_enum") or body.get("status") or "").lower()
                print(f"[poll] session={session_id} status={status} waited={waited}s")

                if status in {"finished", "expired", "blocked",
                              "suspend_requested", "suspend_requested_frontend"}:
                    return body

            sleep_for = min(backoff, 30)
            await asyncio.sleep(sleep_for)
            waited += sleep_for
            backoff = min(backoff * 2, 30)

            if waited >= max_wait_seconds:
                raise TimeoutError("Devin did not finish in time.")
            
    # Devin 1 : Scoper
    async def scope_issue(self, repo: str, issue_number: int, issue_title: str, max_wait_seconds: int = 600) -> Dict[str, Any]:
        
        repo_url=f"{BASE_URL}/{repo}"

        # devin 1 prompt
        base_prompt = f"""
Hey devin. Your task is to scope the GitHub issue #{issue_number} titled "{issue_title}" in the repository {repo_url}.
Return ONLY valid JSON in this exact shape:
{{
  "issue_number": "{issue_number}",
  "issue_title": "{issue_title}",
  "summary": "<one-sentence scope of the issue>",
  "confidence_score": "Low | Medium | High", 
  "action_plan": [
    "<step 1>",
    "<step 2>",
    "<step 3>"
  ]
}}
"""
        prompt = base_prompt
        sid = await self._create_session(prompt)
        done = await self._poll(sid, max_wait_seconds=max_wait_seconds, wait_for_pr=False)
        return done.get("structured_output", {})

    # Devin 2
    async def implement_issue(self, repo: str, issue_number: int, issue_title: str, action_plan: List[str], max_wait_seconds: int = 900,) -> Dict[str, Any]:
        
        repo_url=f"{BASE_URL}/{repo}"
        plan_lines = "\n".join(f"- {s}" for s in action_plan)

        # Devin 2 prompt
        prompt = f"""
Hey Devin. Your task is to take a given action plan and complete the ticket for the specified repository.
Repo: {repo_url}
Issue #{issue_number} titled: "{issue_title}"


Action plan:
{plan_lines}

Additionally, please:

1) Create and checkout branch: "devin/issue-{issue_number}-[short_title]" (The short_title should be derived from the issue title.)
2) Implement changes with clear commits mentioning "{issue_number}-[short_title]"
3) Push the branch
4) Open a Pull Request referencing the issue number #{issue_number} in the title/body
"""
        sid = await self._create_session(prompt)
        done = await self._poll(sid, max_wait_seconds=max_wait_seconds, wait_for_pr=True)
        return done.get("structured_output", {})
