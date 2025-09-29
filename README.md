# GitHub Issues Automation Tool with Devin

This project is a take-home demo for Cognition AI.  
It integrates Devin with **GitHub Issues, letting you list, scope, and execute issues automatically.  

---

## Customer Value
Turn backlog issues into one click automation with Devin.  
- Developers get a faster way to resolve issues without leaving their workflow.  
- Teams get visibility and control via a web dashboard, so they can review and execute Devin collaboratively.  
- Backlog items that might sit for weeks can now be scoped, implemented, and turned into pull requests instantly.  

---

## Features
- **List issues** from a GitHub repo.  
- **Scope & Execute issue** → Devin first scopes the issue (summary + action plan) and then executes it (commits + PR).  
- **Batch mode** → run Scope & Execute on all issues, or only selected ones, in one command.  
- **Frontend UI** → dark-themed dashboard.  
- **CLI tool** → terminal client.  

---

## Architecture
- **Backend (FastAPI)**  
  - Endpoints:  
    - `GET /{repo}/issues`  
    - `GET /{repo}/issues/{issue_number}`  
    - `POST /{repo}/issues/scope-and-execute-batch`  
  - caching layer for repo issues.  

- **Clients**  
  - **CLI**: terminal client  
  - **Frontend**: React + Vite dark-themed dashboard.  

- **Deployment**  
  - Docker + docker-compose: start backend, frontend, and CLI together.  

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/ntua-el19128/devin-github-issues.git
cd devin-github-issues
```

### 2. Create .env file
```bash
GITHUB_TOKEN=your_github_pat
GITHUB_OWNER=your_github_username_or_org
DEVIN_API_KEY=your_devin_api_key
```
For testing, you can set GITHUB_OWNER=ntua-el19128 and use the dummy repo github-issues.

### 3. Run with Docker
```bash
docker compose up --build
```
- **Backend: http://localhost:8000**
- **Frontend: http://localhost:5173**
- **CLI:**
```bash
docker compose run cli
```
---

## Usage
## CLI
- `use <repo>` → select repository.  
- `list` → list open issues.  
- `show <issue_number>` → show details for an issue.  
- `resolve all` → scope & execute all issues.  
- `resolve <n1> <n2> ...` → scope & execute selected issues.  
- `help` → list commands.  
- `exit` → quit CLI.

### Frontend
- Enter repo name → fetch issues.  
- **Scope & Execute** → run Devin on a single issue.  
- **Scope & Execute Selected** → run Devin on multiple chosen issues.  
- **Scope & Execute All** → run Devin on the entire backlog.  
- Click an issue → view its full description before execution.  

---

## Tests
Basic-minimal backend and CLI tests are included.    
For production, we would need to extend into CI/CD with GitHub Actions.  

---

## Notes
- Each issue uses **two Devin sessions**: one for scoping, one for execution.  
- Errors (e.g. invalid repo, session limits) are surfaced clearly back to the user.  
