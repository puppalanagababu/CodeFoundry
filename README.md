# CodeFoundry -- Software Engineering Readiness & Simulation Platform

> **"Practice Software Engineering. Not Just Coding."**

---

## 1. Project Overview

**Codefoundry** is a production-grade software engineering simulation platform designed to evaluate real-world engineering competency. Unlike traditional competitive-programming platforms that focus purely on algorithmic puzzle-solving in single files, Codefoundry immerses developers in realistic multi-file codebases.

Engineers investigate real repositories, diagnose structural defects, patch API endpoints, remediate security vulnerabilities, optimize algorithmic bottlenecks, run tests, and submit production-ready solutions through an automated evaluation and skill-scoring pipeline.

---

## 2. Problem Statement

There is a significant gap between algorithmic interview preparation and daily software engineering reality:

| Traditional Coding Platforms | Real-World Software Engineering | Codefoundry Approach |
| :--- | :--- | :--- |
| Single-file isolated functions | Multi-file modular architectures | Multi-file repository workspace |
| Standard array/string algorithms | Real APIs, auth, serialization, and DB models | Practical architectural scenarios |
| Synthetic inputs/outputs | Edge cases, security exploits, performance constraints | Deterministic grading with hidden edge workloads |
| Memorized algorithmic tricks | Debugging, system design, security, and refactoring | Multi-dimensional skill profiling |

---

## 3. Key Features

- **JWT-Based Authentication**: Secure registration, login, token refresh, and user session management.
- **Interactive Multi-File Workspace**: Monaco code editor with file-tree navigation, multi-tab editing, syntax highlighting, and instant state recovery via `sessionStorage`.
- **Repository-Style Challenges**: Multi-file projects featuring domain models, business services, HTTP handlers, and test suites.
- **Docker Sandbox Execution**: Isolated, resource-constrained container runtime for safe code execution and verification.
- **Hidden Test Cases & Authoritative Grading**: Server-authoritative test execution preventing test tampering and cheat vulnerabilities.
- **Asynchronous Evaluation Pipeline**: Non-blocking submission queuing via **Celery + Redis**, providing real-time evaluation polling.
- **Multi-Dimensional Skill Scoring**: Automated, deterministic evaluation across Problem Solving, Debugging, Security, and Performance.
- **Challenge Progress & History Tracking**: User-scoped tracking of attempt counts, best scores, solved statuses, and submission archives.
- **Strict User Isolation**: Strict ownership enforcement ensuring submissions, evaluations, and progress metrics are private to each user.

---

## 4. How It Works

```text
Student / Candidate
       │
       ▼
Selects Challenge from Catalog
       │
       ▼
Inspects Multi-File Workspace (Monaco Editor)
       │
       ▼
Edits Source Code & Clicks "Run Code" / "Submit Solution"
       │
       ▼
FastAPI REST API receives POST /api/submissions/ (Status: PENDING)
       │
       ▼
Dispatches Task to Redis Queue (evaluate_submission.delay)
       │
       ▼
Celery Worker consumes task & spins up Docker Sandbox
       │
       ▼
Docker Container mounts repository in /workspace (Isolated, Network-Disabled)
       │
       ▼
Runs Test Suite & Benchmarks against hidden workloads
       │
       ▼
EvaluationService computes Score & Multi-Dimensional Skill Breakdown
       │
       ▼
Results persisted in PostgreSQL & Polled by Frontend via GET /api/submissions/<id>/
```

---

## 5. Challenge Types

Codefoundry categorizes real-world engineering tasks into distinct challenge types:

- `BUG_FIX`: Root-cause diagnosis and regression fixing in existing legacy modules.
- `API`: Implementation and correction of RESTful endpoints, serializers, query parameters, and response structures.
- `SECURITY`: Access control auditing, authorization enforcement, and vulnerability remediation.
- `PERFORMANCE`: Algorithmic refactoring, time/space complexity optimization, and high-throughput data processing.

---

## 6. Flagship Challenges

| Challenge Title | Type | Difficulty | Core Engineering Competency |
| :--- | :--- | :--- | :--- |
| **Fix the Broken Calculator** | `BUG_FIX` | Beginner | Operator precedence, division-by-zero handling, and parser debugging. |
| **The Missing API Data** | `API` | Intermediate | REST serialization, query parameter handling, and collection response contracts. |
| **The Exposed Admin Endpoint** | `SECURITY` | Intermediate | Role-based access control (RBAC), token authorization, and privilege escalation prevention. |
| **The Slow Report Generator** | `PERFORMANCE` | Intermediate | Refactoring $O(T \times U)$ quadratic lookups to $O(T + U)$ hash mappings under 128MB limits. |

---

## 7. Technology Stack

### Backend
- **FastAPI** (High-performance asynchronous Python REST API framework)
- **SQLAlchemy** (Robust SQL toolkit & Object-Relational Mapper)
- **Pydantic v2** (Strict data validation & serialization schemas)
- **PostgreSQL 16+** (Relational storage & persistence)
- **Alembic** (Database schema migrations authority)
- **Celery** (Distributed asynchronous evaluation task queue)
- **Redis 7+** (Message broker, result backend, and token blacklist)
- **PyJWT & Passlib** (Stateless authentication, PBKDF2 compatibility, token rotation)

### Frontend
- **React 18** & **Vite**
- **Monaco Editor** (`@monaco-editor/react`)
- **Vanilla CSS** (Custom responsive design system)
- **Lucide Icons**

### Sandbox & Infrastructure
- **Docker Engine** (`python:3.11-slim` runtime)
- **Uvicorn** (Production ASGI server)
- **Nginx** (Reverse proxy & static SPA serving)

---

## 8. Security Architecture

The sandbox execution environment enforces strict multi-layered isolation:

- **Network Disabled**: Containers are executed with `network_disabled=True` to prevent data exfiltration or external socket calls.
- **Unprivileged Execution**: `privileged=False` and all Linux kernel capabilities dropped (`cap_drop=['ALL']`).
- **No New Privileges**: `security_opt=['no-new-privileges:true']` blocks privilege escalation exploits.
- **Resource Constraints**: Strict limits on memory (`128MB`), CPU (`1.0 CPU`), process IDs (`pids_limit=64`), and execution timeout (`5.0s`).
- **Canonical Path Traversal Guards**: Strict verification that all file paths remain within the ephemeral `/workspace` mount.
- **Server-Authoritative Test Protection**: Hidden test files and expected outputs are never exposed to client-side code.
- **Strict User Isolation**: Multi-tenant authorization checks ensure users cannot access other developers' submissions or metrics.

---

## 9. Skill Measurement System

Codefoundry evaluates performance across six core software engineering dimensions:

1. **Problem Solving**: Verified functional correctness against baseline and hidden test suites.
2. **Debugging**: Precision of fixes in bug-fix scenarios, penalizing collateral regressions.
3. **Security**: Proper authorization checks, token validation, and rejection of unauthorized inputs.
4. **Performance**: Algorithmic efficiency, execution speed, and memory usage under high-volume workloads.
5. **Code Quality**: *(Reserved for future automated linting/static analysis integration)*.
6. **Testing**: *(Reserved for future candidate test-authoring challenge types)*.

---

## 10. System Architecture

```text
                      +------------------------------------------+
                      |               Client Browser             |
                      |    (React 18 + Vite + Monaco Workspace)  |
                      +------------------------------------------+
                                           │
                                     HTTPS / JSON
                                           │
                                           ▼
                      +------------------------------------------+
                      |            Nginx Reverse Proxy           |
                      |  (Static SPA Assets + /api/ Proxy Pass)  |
                      +------------------------------------------+
                                           │
                                           ▼
                      +------------------------------------------+
                      |         FastAPI ASGI App (Uvicorn)       |
                      |  (Auth, Challenges, Submissions, Eval)   |
                      +--------------------+---------------------+
                                           │
                       ┌───────────────────┴───────────────────┐
                       ▼                                       ▼
            +--------------------+                  +--------------------+
            | PostgreSQL 16+     |                  | Redis Broker 7+    |
            | (Entities, Scores) |                  | (Task Queue)       |
            +--------------------+                  +---------+----------+
                                                              │
                                                              ▼
                                                    +--------------------+
                                                    |   Celery Worker    |
                                                    | (Evaluation Engine)|
                                                    +---------+----------+
                                                              │
                                                              ▼
                                                    +--------------------+
                                                    |   Docker Sandbox   |
                                                    | (python:3.11-slim) |
                                                    +--------------------+
```

---

## 11. Local Development Setup

### Prerequisites
- **Python 3.11+**
- **Node.js 18+** & **npm**
- **Docker Engine** (Running locally)
- **PostgreSQL 16+**
- **Redis 7+**

### 1. Clone the Repository
```bash
git clone https://github.com/puppalanagababu/DevForge.git
cd DevForge
```

### 2. Backend Setup
```bash
# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your local PostgreSQL credentials

# Apply database migrations
cd backend
python -m alembic upgrade head
cd ..

# Pull the Docker execution runtime image
docker pull python:3.11-slim
```

### 3. Run Backend Services (FastAPI)
```bash
# Terminal 1: FastAPI API server
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Celery evaluation worker
cd backend
celery -A app.celery_app.celery_app worker --loglevel=info -P solo
```

### 4. Frontend Setup
```bash
# Terminal 3: React Vite frontend
cd frontend
npm install
npm run dev
```
```
Open `http://localhost:5173` in your browser.

---

## 12. Automated Testing

Codefoundry includes a comprehensive backend test suite covering models, authentication, security logging, rate limiting, password reset, Docker sandbox execution, Celery dispatch, evaluation grading, and user isolation.

To run the full test suite:
```bash
cd backend
python -m pytest tests/
```

---

## 13. Production Deployment Guide

Follow these steps for a secure production deployment:

### 1. Environment Configuration
- Create a production `.env` file based on `.env.example`.
- Ensure `DEBUG=False` and set a cryptographically secure `SECRET_KEY` ($\ge 50$ characters).
- Configure `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` to your production domain(s).

### 2. Infrastructure (PostgreSQL & Redis)
- Provision a dedicated PostgreSQL database and set `DATABASE_URL` (or `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).
- Provision Redis for caching and Celery task queues (`REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`). Ensure Redis is secured and not publicly accessible.

### 3. Database Migrations
```bash
cd backend
python -m alembic upgrade head
```

### 4. Background Workers & Docker Execution
- Start Celery worker: `cd backend && celery -A app.celery_app.celery_app worker -l info --concurrency=4`
- Ensure Docker Engine is running on the host/worker with `python:3.11-slim` pre-pulled (`docker pull python:3.11-slim`).

### 5. Backend ASGI Server
- Run behind Uvicorn with a reverse proxy (Nginx/Caddy/Cloudflare):
  ```bash
  cd backend
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers
  ```

### 6. Frontend Production Build
- Set `VITE_API_BASE_URL=https://api.yourdomain.com/api` and build:
  ```bash
  cd frontend
  npm install
  npm run build
  ```
- Serve `frontend/dist` via Nginx, Caddy, Vercel, or Cloudflare Pages.

### 7. HTTPS & Security Headers
- Ensure TLS/SSL is active (`SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`).


---

## 14. Project Roadmap

The following enhancements are planned for future iterations:

- [ ] **AI-Assisted Code Reviews**: Automated feedback on design patterns, complexity, and idiomatic practices.
- [ ] **Multi-Language Sandbox**: Support for TypeScript, Go, Java, and Rust execution.
- [ ] **Interactive Terminal**: WebSocket-based interactive shell inside sandboxed environments.
- [ ] **Trainer & Recruiter Dashboard**: Batch candidate assessment, custom challenge authoring, and skill analytics.
- [ ] **Automated Code Quality & Test Suite Scoring**: Linter integration and candidate unit test coverage evaluation.

---

## 15. Author

- **GitHub**: [@puppalanagababu](https://github.com/puppalanagababu)
- **Repository**: [https://github.com/puppalanagababu/DevForge](https://github.com/puppalanagababu/DevForge)

---

