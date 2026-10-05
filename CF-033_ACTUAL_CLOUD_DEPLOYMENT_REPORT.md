# CF-033 Actual Cloud Deployment Report

## 1. Deployment Target

- **Current Repository State**: All core platform components (FastAPI backend, PostgreSQL relational schema, Redis broker, Celery worker, Docker sandbox execution engine, and React/Vite single-page frontend) are fully built, locally smoke-tested (19/19 live student journey stages passed, 6/6 failure path scenarios verified), and passing 194/194 automated backend tests.
- **Cloud Provider Status**: **NO CLOUD PROVIDER CONFIGURED IN REPOSITORY**.
- **Requirement**: The repository contains universal deployment guides (`docs/DEPLOYMENT.md`) and container specifications, but no external cloud provider (AWS, GCP, Azure, DigitalOcean, Railway, Render, Fly.io, etc.), remote server IP/host, or API deployment credentials have been provided by the project owner.

---

## 2. Infrastructure

| Component | Provider | Status | Operational Notes |
|---|---|---|---|
| **FastAPI Backend** | *Pending Provider Selection* | `READY FOR PROVISIONING` | Configured for ASGI Uvicorn (`app.main:app`) on port `8000`. |
| **PostgreSQL Database** | *Pending Provider Selection* | `READY FOR PROVISIONING` | Schema head `c8b1a4f02e9d`, challenge seeder verified idempotent. |
| **Redis Broker / Cache** | *Pending Provider Selection* | `READY FOR PROVISIONING` | Universal RESP2/RESP3 protocol compatibility configured. |
| **Celery Worker** | *Pending Provider Selection* | `READY FOR PROVISIONING` | Background worker consuming `app.tasks.evaluation_tasks.evaluate_submission`. |
| **Docker Sandbox** | *Pending Provider Selection* | `PREREQUISITE REQUIRED` | Requires host Docker daemon access (`/var/run/docker.sock`) and `python:3.11-slim`. |
| **React/Vite Frontend** | *Pending Provider Selection* | `READY FOR PROVISIONING` | Production static bundle built under `frontend/dist/` (70 modules transformed). |

---

## 3. Environment Configuration

The production environment configuration template (`.env.example`) has been verified and structured into required categories:

```bash
# --- Security & Core Settings ---
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<GENERATE_64_CHAR_RANDOM_SECRET>
ALLOWED_HOSTS=app.codefoundry.dev,api.codefoundry.dev
CORS_ALLOWED_ORIGINS=https://app.codefoundry.dev

# --- Managed PostgreSQL Database ---
DATABASE_URL=postgresql://codefoundry_user:<SECURE_DB_PASSWORD>@<DB_HOST>:5432/codefoundry

# --- Managed Redis Store ---
REDIS_URL=redis://<REDIS_HOST>:6379/1
CELERY_BROKER_URL=redis://<REDIS_HOST>:6379/0
CELERY_RESULT_BACKEND=redis://<REDIS_HOST>:6379/0

# --- Frontend SPA (Vite) ---
VITE_API_BASE_URL=https://api.codefoundry.dev/api
```

- **Credential Safety**: No production passwords, secret keys, or database URLs are hardcoded in the codebase, frontend bundle, or Git repository history.

---

## 4. Database Deployment

- **Migration Tooling**: Managed via **Alembic** (`backend/alembic/`).
- **Current Migration Head**: `c8b1a4f02e9d` (Initial application schema preserving historical Django lineage `bdb7e77e43d1`).
- **Seeding Script**: `python -m app.scripts.seed_challenges` is verified 100% idempotent.
- **Cloud Action Required**: Once managed PostgreSQL instance is provisioned by the project owner, run:
  ```bash
  alembic upgrade head
  python -m app.scripts.seed_challenges
  ```

---

## 5. Redis Deployment

- **Role**: Message broker for Celery evaluation tasks (DB 0) and token blacklist / rate-limiting store (DB 1).
- **Engine Version Compatibility**: Universal RESP2/RESP3 fallback configured in `app/celery_app.py` and `app/services/auth_service.py`.
- **Cloud Action Required**: Provision Redis instance (v6+ or v7+) with in-memory persistence (RDB or AOF) and assign `REDIS_URL` / `CELERY_BROKER_URL`.

---

## 6. Celery Worker

- **Task Signature**: `app.tasks.evaluation_tasks.evaluate_submission(submission_id: int)`.
- **Execution Lifecycle**: Dispatches submission state changes (`PENDING` $\to$ `RUNNING` $\to$ `PASSED` / `FAILED` / `ERROR`) with evaluation score generation.
- **Production Startup Command**:
  ```bash
  celery -A app.celery_app.celery_app worker --loglevel=info -c 4 --max-tasks-per-child 100
  ```

---

## 7. Docker Sandbox

- **Runtime Requirement**: The CodeFoundry evaluation service strictly requires access to a Linux container runtime with the Docker daemon (`/var/run/docker.sock`).
- **Security Constraints**:
  - `--network none` (inbound/outbound traffic completely blocked).
  - `--cap-drop=ALL` (all Linux kernel capabilities dropped).
  - `--security-opt no-new-privileges:true`.
  - Memory hard cap: `256m`.
  - CPU quota: `0.5 CPU` (`nano_cpus=500_000_000`).
  - PID limit: `64` processes (prevents fork bombs).
  - Wall-clock timeout: 15s per test execution.
  - Ephemeral workspace cleanup on execution termination.
- **Cloud Platform Constraint**: Serverless container runtimes that disallow Docker socket mounting (e.g. standard AWS Lambda, Google Cloud Run standard without gVisor/sibling containers, basic Vercel) cannot execute the evaluation sandbox. The target deployment must use a **VM (EC2 / Compute Engine / Droplet)**, **Kubernetes cluster with Docker-in-Docker / Kata containers**, or a **Dedicated Container Host (Fly.io with Docker engine, Railway with Docker socket, Render with Docker service)**.

---

## 8. Backend Deployment

- **ASGI Framework**: FastAPI running under Uvicorn with lifespan startup validation.
- **Production Verification**: Lifespan startup check strictly rejects insecure `SECRET_KEY` defaults and asserts `DEBUG=False` in production mode.
- **Endpoints Ready**: `/api/health`, `/api/auth/`, `/api/challenges/`, `/api/submissions/`, `/api/execution/`, `/api/users/`, `/api/dashboard/`, `/api/leaderboard/`.

---

## 9. Frontend Deployment

- **Framework**: React 18 + Vite SPA with Monaco Editor.
- **Production Artifacts**: Generated via `npm run build` into `frontend/dist/`.
- **Bundle Integrity**: 70 modules transformed, 0 build warnings, 0 localhost hardcoded URLs.
- **Routing**: Static SPA routing configured with client-side fallback (`/*` $\to$ `/index.html`).

---

## 10. HTTPS / Domain

- **Status**: **DOMAIN CONFIGURATION PENDING**.
- **DNS Requirements**:
  - Main App: `app.codefoundry.dev` (Points to Frontend CDN / Nginx reverse proxy).
  - API Gateway: `api.codefoundry.dev` (Points to FastAPI Uvicorn backend).
- **TLS Termination**: Automatic Let's Encrypt / Cloudflare SSL termination on port `443`.

---

## 11. Live Student Journey

*(Pre-deployment local staging smoke test verified 19/19 stages with 100% success; cloud production test will execute immediately upon remote target provisioning)*:

| Stage | Action | Staging Result | Cloud Deployment Status |
|---|---|---|---|
| 1 | Register | `PASSED` | Pending Cloud Provisioning |
| 2 | Login | `PASSED` | Pending Cloud Provisioning |
| 3 | Dashboard | `PASSED` | Pending Cloud Provisioning |
| 4 | Browse Challenges | `PASSED` | Pending Cloud Provisioning |
| 5 | Challenge Detail | `PASSED` | Pending Cloud Provisioning |
| 6 | Workspace | `PASSED` | Pending Cloud Provisioning |
| 7 | Sandbox Run | `PASSED` | Pending Cloud Provisioning |
| 8 | Submit Solution | `PASSED` | Pending Cloud Provisioning |
| 9 | Celery Polling | `PASSED` | Pending Cloud Provisioning |
| 10 | Docker Execution | `PASSED` | Pending Cloud Provisioning |
| 11 | Score Calculation | `PASSED` | Pending Cloud Provisioning |
| 12 | Skill Breakdown | `PASSED` | Pending Cloud Provisioning |
| 13 | History | `PASSED` | Pending Cloud Provisioning |
| 14 | Progress | `PASSED` | Pending Cloud Provisioning |
| 15 | Achievements | `PASSED` | Pending Cloud Provisioning |
| 16 | Skill Profile | `PASSED` | Pending Cloud Provisioning |
| 17 | Leaderboard | `PASSED` | Pending Cloud Provisioning |
| 18 | Public Profile | `PASSED` | Pending Cloud Provisioning |
| 19 | Token Refresh | `PASSED` | Pending Cloud Provisioning |

---

## 12. Failure Tests

*(Staging validation confirmed all 6 error recovery scenarios)*:
- **Incorrect Solution**: Scored 0, evaluation completed with failed test assertions.
- **Syntax Error**: Evaluated cleanly with stderr captured, zero server crash.
- **Timeout / Loop**: Terminated safely by sandbox timeout.
- **Token Refresh**: Rotated refresh token successfully issued new access token.
- **Non-Existent Resource**: Returned canonical 404 JSON error response.
- **Unauthorized Access**: Returned HTTP 401 / 403.

---

## 13. Security Verification

- **Sandbox Network Lockdown**: Verified (`network_disabled=True`).
- **Privilege Dropping**: Non-root execution with `cap-drop=ALL` and `no-new-privileges`.
- **Secret Isolation**: Secrets managed exclusively via runtime environment variables.
- **Token Invalidation**: Blacklisted JWTs stored in Redis preventing replay attacks.
- **CORS & Host Whitelisting**: Strict origin controls without wildcard bypass.

---

## 14. Issues

| ID | Severity | Component | Issue | Blocking? |
|---|---|---|---|---|
| **ISSUE-01** | P1 | Cloud Infrastructure | No cloud hosting target / credentials configured in repository. | **Yes (Cloud Deployment Blocked)** |

---

## 15. External Configuration Remaining

To complete live cloud provisioning, the project owner must provide or configure:

1. **Cloud Hosting Target**: Select and provide target platform access (e.g. AWS EC2/ECS, GCP Compute/GKE, DigitalOcean Droplet/App Platform, Render, Railway, or Fly.io).
2. **Managed PostgreSQL**: Connection string (`DATABASE_URL`) with user credentials and database created.
3. **Managed Redis**: Connection string (`REDIS_URL` / `CELERY_BROKER_URL`).
4. **Docker Host Support**: Provision host environment with Docker daemon access enabled for sandbox execution.
5. **Domain Name & DNS**: Point domain (e.g. `codefoundry.dev`) and API subdomain (`api.codefoundry.dev`) to host IP / load balancer.
6. **Production Secret Key**: Supply a 64+ character random cryptographic string for `SECRET_KEY`.

---

## 16. Final Status

# **BLOCKED — PROVIDER CONFIGURATION REQUIRED**

The CodeFoundry platform is completely prepared, hardened, and verified for production deployment. Actual deployment is awaiting the project owner's choice of cloud provider, host credentials, managed PostgreSQL/Redis instances, and domain DNS setup.
