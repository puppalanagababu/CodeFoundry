
# DevForge — 3–5 Minute Demonstration Guide & Interview Playbook

---

## 1. Demo Objective

**DevForge** is a software engineering readiness and simulation platform that trains and evaluates developers using realistic multi-file repositories rather than isolated algorithmic puzzles. It combines an interactive Monaco workspace with an asynchronous, Docker-sandboxed evaluation engine that deterministically measures problem solving, debugging, security, and performance.

---

## 2. Recommended Demo Challenge

**Challenge**: `Fix the Broken Calculator`  
**Difficulty**: Beginner  
**Type**: `BUG_FIX`

### Why this is the best demo challenge:
1. **Instantly Intuitive**: Everyone understands arithmetic operator precedence and division-by-zero.
2. **True Software Engineering**: Demonstrates navigating a multi-file repo (`app/calculator.py`, `app/main.py`, `tests/test_calculator.py`).
3. **Shows the Feedback Loop**: Demonstrates submitting broken code $\to$ partial credit / failure $\to$ inspecting test results $\to$ applying the fix $\to$ passing with 100/100.
4. **Highlights Async Architecture**: Cleanly showcases non-blocking UI polling, Celery background worker execution, and Docker sandbox isolation in real time.

---

## 3. High-Level Demo Flow

```text
Landing / Login
     ↓
Dashboard (Skill Profile + Stats)
     ↓
Challenge Catalog (9 Seeded Scenarios)
     ↓
Challenge Details & README
     ↓
Monaco Code Workspace
     ↓
Run Code (Sandbox Execution)
     ↓
Submit Initial Broken Solution
     ↓
Asynchronous Evaluation & Polling
     ↓
Inspect Test Failures & Diagnostics
     ↓
Apply Bug Fix in app/calculator.py
     ↓
Submit Corrected Solution
     ↓
PASSED (100/100) + Skill Radar Update
     ↓
Challenge Progress Updated
```

---

## 4. Exact Demo Script (Step-by-Step)

| # | Presenter Action | What Appears on Screen | Spoken Script (Say This) |
|---|---|---|---|
| **1** | Open landing page (`http://localhost:5173`) and log in. | Modern dark-mode UI with hero, skill metrics, and active session. | *"DevForge is a software engineering readiness platform. Instead of solving synthetic algorithm puzzles in a single file, developers work inside realistic multi-file codebases to fix bugs, optimize bottlenecks, and secure APIs."* |
| **2** | Navigate to **Dashboard**. | User stats, activity history, and multi-dimensional skill radar chart. | *"The dashboard visualizes a developer's real engineering capabilities across problem solving, debugging, security, and performance based on deterministic test results."* |
| **3** | Click **Challenges** in navbar. | Challenge catalog showing 9 categorized challenges (`BUG_FIX`, `API`, `SECURITY`, `PERFORMANCE`). | *"Our challenge catalog covers realistic day-to-day scenarios—from patching API response contracts to eliminating quadratic bottlenecks in report generators."* |
| **4** | Select **Fix the Broken Calculator**. | Challenge details page with README requirements, difficulty tag, and repository file tree. | *"Let's open 'Fix the Broken Calculator'. You can see the full engineering requirements and repository structure. Test files are marked readonly to protect grading integrity."* |
| **5** | Click **Open in Workspace**. | Multi-tab Monaco editor loaded with `app/calculator.py`, `app/main.py`, and test files. | *"This is the interactive Monaco workspace. Notice how we can switch between modules, inspect helper classes, and review existing tests just like a real IDE."* |
| **6** | Click **Run Code**. | Output terminal displays test execution output via Docker runner. | *"When I click 'Run Code', DevForge spins up an isolated Docker container with strict CPU and memory limits to execute our code and stream the output back in real time."* |
| **7** | Click **Submit Solution** (with starter code). | Status badge turns yellow (`PENDING`), UI begins polling every 2s. | *"When we click 'Submit Solution', FastAPI creates a submission record and asynchronously dispatches a background task to Celery via Redis. The UI remains completely responsive."* |
| **8** | Wait for evaluation (2–3 seconds). | Status badge updates to red (`FAILED`), Score: `80/100`, detailed breakdown of passing and failing test cases. | *"The Celery worker mounted our code into a network-disabled Docker container and evaluated it against hidden test suites. The submission failed the precedence test case `2 + 3 * 4`."* |
| **9** | Edit `app/calculator.py` with the precedence fix. | Replace sequential evaluation with operator precedence stack logic. | *"Now let's apply the fix by implementing standard operator precedence handling in `app/calculator.py`."* |
| **10** | Click **Submit Solution** again. | Submits new revision, enters `PENDING`, polls Celery task. | *"Let's submit the corrected solution."* |
| **11** | Evaluation completes. | Status updates to green (`PASSED`), Score: `100/100`, 10/10 tests passed, execution time & memory metrics displayed. | *"All 10 test cases passed! The evaluation engine recorded the execution time, memory usage, and verified functional correctness."* |
| **12** | Return to **Dashboard** / **Progress**. | Skill radar chart updates with improved Debugging/Problem Solving scores; Challenge status marked `SOLVED`. | *"Returning to the dashboard, our skill radar chart and challenge progress have dynamically updated to reflect our verified solution."* |

---

## 5. Key Technical Architecture Points

- **Frontend (React 18 + Vite + Monaco)**: Single-page application using `@monaco-editor/react` for repository file editing, custom responsive CSS design tokens, and token-based state recovery via `sessionStorage`.
- **Backend API (FastAPI + SQLAlchemy)**: High-performance asynchronous RESTful endpoints with OpenAPI schema documentation, JWT authentication (OAuth2 / PyJWT), repository file trees, challenge metadata, and submission lifecycle management.
- **Task Queue (Celery + Redis)**: Non-blocking asynchronous task execution via `evaluate_submission.delay(submission_id)`, preventing HTTP request timeouts during long evaluations.
- **Relational Storage (PostgreSQL 16+)**: ACID-compliant persistence for users, submissions, structured `Evaluation` records, and raw test run JSON results.
- **Sandbox Execution (Docker Engine)**: Ephemeral container execution using `python:3.11-slim`, mounting repository workspaces into isolated directories with strict capability drops.
- **Deterministic Skill Scoring**: Automated skill breakdown formulas computing multi-dimensional ratings from test case pass rates, penalty factors, and benchmark execution metrics.

---

## 6. Security Architecture & Talking Points

When asked about security and sandbox isolation, highlight these actual implemented protections:

1. **Network Disabled (`network_disabled=True`)**: Container cannot make outbound HTTP/TCP calls, download malicious payloads, or exfiltrate private data.
2. **Unprivileged Execution (`privileged=False`)**: Container runs with standard user rights; no Docker host socket or privileged device access.
3. **All Capabilities Dropped (`cap_drop=['ALL']`)**: Linux kernel capabilities (e.g. `CAP_SYS_ADMIN`, `CAP_NET_RAW`) are completely stripped.
4. **No Privilege Escalation (`security_opt=['no-new-privileges:true']`)**: Processes inside the container cannot gain new privileges via `setuid` binaries.
5. **Resource Limits**: Hard ceilings on memory (`128MB`), CPU (`1.0 CPU`), and process count (`pids_limit=64`) prevent fork bombs and memory exhaustion.
6. **Execution Timeouts (`timeout=5.0s`)**: Runaway infinite loops or $O(N^2)$ algorithms are automatically killed with exit code `124`.
7. **Server-Authoritative Test Protection**: Hidden test cases and expected outputs reside exclusively in the server database and are never sent to the client browser.
8. **Multi-Tenant User Isolation**: Ownership filters in API routers ensure users can only query, run, or inspect their own submissions (attempting to access another user's submission returns `404 Not Found`).

---

## 7. Top 15 Interview Questions & Answers

### Q1: Why did you choose FastAPI and SQLAlchemy for the backend?
> *"FastAPI provides high-performance asynchronous request handling, automatic OpenAPI/Swagger documentation, and native Pydantic data validation with strict type safety. SQLAlchemy gives us an expressive, robust ORM with Alembic managing database migrations."*

### Q2: Why React and Vite for the frontend?
> *"React's component lifecycle made managing multi-tab editor state and real-time polling loops straightforward. Vite provided instant hot module reloading and sub-second production builds without Webpack overhead."*

### Q3: Why did you use Celery and Redis instead of evaluating submissions synchronously?
> *"Running code in Docker containers takes between 500ms and 5 seconds. If evaluated synchronously in the HTTP request thread, concurrent submissions would quickly exhaust WSGI/ASGI worker pools and trigger gateway timeouts. Celery queues tasks in Redis, keeping the API responsive."*

### Q4: Why Docker for execution instead of Python's `subprocess` or `exec`?
> *"Executing untrusted code on the host via `subprocess` or `exec` is dangerous. Docker provides process isolation, cgroup resource limits (CPU/memory/PIDs), filesystem sandboxing, and network isolation that cannot be bypassed from user space."*

### Q5: How are hidden tests protected from candidate inspection?
> *"In DevForge, test cases are marked as visible or hidden in the database. When loading the workspace, hidden tests are excluded from the API payload. During evaluation, tests are mounted server-side and executed inside the container, with only pass/fail booleans returned to the client."*

### Q6: How is user submission isolation enforced?
> *"At the API level, all submission queries filter by the authenticated user ID. If User B attempts to access `/api/submissions/<id>/` belonging to User A, FastAPI returns a `404 Not Found` rather than leaking existence or metadata."*

### Q7: How does the deterministic skill scoring work?
> *"Each challenge maps to a primary skill (e.g. Debugging, Security, Performance). When evaluated, `SkillScoringService` weights functional pass rates against challenge difficulty and execution metrics, computing deterministic scores from 0 to 100 without subjective grading."*

### Q8: How do you measure performance challenges without flaky wall-clock timing?
> *"We benchmark execution time and memory against substantial datasets (e.g. 35,000 records). An $O(N^2)$ quadratic solution reliably hits the 5.0-second container timeout, whereas an $O(N)$ hash-indexed solution completes in $<0.05\text{s}$, producing an unambiguous, deterministic pass/fail boundary."*

### Q9: How does multi-file repository execution work in Docker?
> *"The backend writes validated repository files to an ephemeral temporary host directory with `0o755`/`0o644` permissions, mounts it to `/workspace` in the container, sets `PYTHONPATH=/workspace`, and executes `python -u <entrypoint>`. The directory is cleaned up in a `finally` block."*

### Q10: What happens when user code has an infinite loop or times out?
> *"DockerCodeRunner specifies a timeout on `container.wait(timeout=5)`. When a `ReadTimeout` occurs, the runner catches the exception, issues `container.kill()`, returns exit code `124`, and records `'Execution timed out'` in stderr."*

### Q11: How does the system handle concurrent submissions?
> *"Each submission creates an independent database record with status `PENDING`. Celery distributes the evaluation tasks across worker processes. Each worker mounts a distinct temporary workspace directory and launches an isolated Docker container, preventing collision."*

### Q12: How does the workspace handle browser refreshes during an active submission?
> *"When a submission is dispatched, the frontend stores the submission ID in `sessionStorage`. On page refresh or reconnection, the workspace inspects `sessionStorage`, detects the in-flight evaluation, and immediately resumes the 2-second polling loop."*

### Q13: What was the hardest engineering problem you solved building DevForge?
> *"Ensuring seamless cross-platform stdin streaming and file permissions across Docker container boundaries on both Windows and Linux. On Linux, `tempfile.mkdtemp` created `0o700` directories that unprivileged containers couldn't traverse, and Unix domain sockets lacked `.sendall()`. We built universal streaming socket adapters and host-boundary permission normalizers to make repository execution 100% reliable across environments."*

### Q14: What would you improve or build next?
> *"Adding multi-language execution (TypeScript, Go, Rust), integrating AST-based automated code quality linting, and building a trainer dashboard for batch candidate assessment."*

### Q15: Why is DevForge different from LeetCode or HackerRank?
> *"Traditional platforms test competitive programming algorithms in single functions. DevForge evaluates full-spectrum software engineering—diagnosing legacy bugs across multiple files, adhering to REST API contracts, enforcing access control, and refactoring real performance bottlenecks."*

---

## 8. 30-Second Elevator Pitch

> *"DevForge is a software engineering readiness platform that bridges the gap between competitive coding and real-world development. Instead of isolated puzzle questions, candidates work in a full-fledged multi-file Monaco editor on realistic backend codebases—fixing broken APIs, patching security vulnerabilities, and optimizing performance bottlenecks. Every submission runs in an unprivileged, resource-capped Docker sandbox evaluated asynchronously via Celery and Redis, producing deterministic multi-dimensional skill profiles."*

---

## 9. 2-Minute Technical Summary

> *"DevForge is built with a modern, decoupled architecture designed for high isolation and scalability.*
> 
> *On the frontend, we use React and Vite with the Monaco Editor to provide a full multi-file IDE experience in the browser, featuring syntax highlighting, multi-tab navigation, and session recovery across browser refreshes.*
> 
> *The backend is powered by FastAPI and PostgreSQL (via SQLAlchemy) for high-performance API endpoints, JWT authentication, and challenge metadata management.*
> 
> *The core execution engine is completely asynchronous. When a developer submits a solution, the API records the submission as `PENDING` and pushes a task to Redis. A Celery worker picks up the job, validates file paths to prevent directory traversal, writes the repository to an ephemeral workspace, and mounts it into an unprivileged Docker container running `python:3.11-slim`.*
> 
> *The container runs with all Linux capabilities dropped, networking disabled, and strict limits on CPU, memory, and execution time. The evaluation service executes authoritative test suites, captures stdout, stderr, execution time, and memory usage, and computes deterministic skill scores across Problem Solving, Debugging, Security, and Performance.*
> 
> *The frontend polls the API endpoint every two seconds to display live test diagnostics, execution metrics, and radar chart skill updates."*

---

## 10. Pre-Demo Setup Checklist

Before beginning a live demonstration, ensure all local services are active:

- [ ] **Docker Engine**: Running (`docker info` succeeds, `python:3.11-slim` pulled).
- [ ] **PostgreSQL**: Running on `127.0.0.1:5432` (`codefoundry` database active).
- [ ] **Redis Server**: Running on `127.0.0.1:6379` (`redis-cli ping` returns `PONG`).
- [ ] **Database Migrations**: Up to date (`cd backend && python -m alembic upgrade head`).
- [ ] **FastAPI Backend**: Running in Terminal 1 (`cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`).
- [ ] **Celery Worker**: Running in Terminal 2 (`cd backend && celery -A app.celery_app.celery_app worker -l info -P solo`).
- [ ] **React Frontend**: Running in Terminal 3 (`cd frontend && npm run dev` on `http://localhost:5173`).
- [ ] **Test User Account**: Created and login credentials verified.
- [ ] **Browser**: Clean browser window open at `http://localhost:5173`.
