import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = os.getenv("GITHUB_OWNER")

BASE_URL = "https://api.github.com"


def _headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def fetch_issues(repo: str):
    """Fetch list of issues for the repo."""
    url = f"{BASE_URL}/repos/{OWNER}/{repo}/issues"
    try:
        response = requests.get(url, headers=_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            raise ValueError(f" Repository '{repo}' not found")
        else:
            raise RuntimeError(
                f"GitHub API error {e.response.status_code if e.response else '???'}: {e}"
            )
        

