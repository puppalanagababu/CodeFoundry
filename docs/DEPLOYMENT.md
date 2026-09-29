# CodeFoundry Production Deployment & Architecture Guide

This document outlines the production architecture, service startup sequence, environment configuration, and operational requirements for deploying the **FastAPI backend** alongside the **React SPA frontend** and **Celery worker services**.

---

## 1. System Architecture Overview

```
                          [ Client Browser ]
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
       [ React Static Assets (Nginx/CDN) ]   [ Reverse Proxy / HTTPS Gateway ]
                                                  │
                                                  ▼
                                       [ FastAPI App (Uvicorn) ]
                                        (Port 8000 / ASGI Server)
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    ▼                             ▼                             ▼
        [ PostgreSQL Database ]          [ Redis Server ]             [ Docker Engine ]
         (Port 5432 / DB Engine)        (DB 0: Celery Broker)       (Sandboxed Container)
                                        (DB 1: Cache/Blacklist)                 ▲
                                                  │                             │
                                                  ▼                             │
                                     [ Celery Async Worker ] ───────────────────┘
                                      (evaluate_submission)
```

---

## 2. Infrastructure Prerequisites

1. **PostgreSQL Database** (v14+ recommended):
   - Stores user accounts, challenges, submissions, evaluations, and achievements.
   - Requires persistent disk storage.
2. **Redis In-Memory Data Store** (v6+ / v7+):
   - Database `0`: Celery Task Broker and Result Backend.
   - Database `1`: Token blacklist and API rate-limiting cache.
3. **Docker Engine / Container Runtime**:
   - Required for isolated code execution sandboxes.
   - Base image required on host: `python:3.11-slim`.
4. **Python Runtime**:
   - Python 3.11+ environment with dependencies installed from `requirements.txt`.
5. **Node.js**:
   - Node.js 18+ for building the React frontend (`npm run build`).

---

## 3. Production Service Startup Order

To prevent connection failures and startup errors, initialize services in the following order:

1. **PostgreSQL Database**
   ```bash
   # Verify PostgreSQL is accepting connections
   pg_isready -h 127.0.0.1 -p 5432
   ```
2. **Redis Store**
   ```bash
   # Verify Redis connectivity
   redis-cli -h 127.0.0.1 -p 6379 ping
   ```
3. **Docker Daemon**
   ```bash
   # Verify Docker engine is running
   docker info
   # Pre-pull execution sandbox image
   docker pull python:3.11-slim
   ```
4. **FastAPI Application Server (Uvicorn)**
   ```bash
   # Linux / Container Production (with multiple workers behind reverse proxy)
   cd backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips='*'
   ```
5. **Celery Evaluation Worker**
   ```bash
   # Linux / Container Production
   cd backend
   celery -A app.celery_app.celery_app worker -l info -c 4 --max-tasks-per-child 100

   # Windows Local Development
   celery -A app.celery_app.celery_app worker -l info -P solo
   ```
6. **Frontend Static SPA (Vite / Nginx)**
   ```bash
   cd frontend
   npm run build
   # Serve dist/ via Nginx / Cloudflare Pages / S3
   ```

---

## 4. Environment Variables Reference

All sensitive values must be configured via environment variables or a secured `.env` file:

| Variable | Description | Example (Safe Placeholder) |
| :--- | :--- | :--- |
| `SECRET_KEY` | Cryptographic key for JWT and session tokens | `CHANGE_ME_IN_PRODUCTION_MIN_50_CHARS` |
| `DEBUG` | Enable debug logging / verbose database echo | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed host header domains | `app.codefoundry.dev,api.codefoundry.dev` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of trusted frontend origins | `https://app.codefoundry.dev` |
| `DATABASE_URL` | Complete PostgreSQL connection string | `postgresql://user:pass@127.0.0.1:5432/codefoundry` |
| `DB_HOST` / `DB_PORT` | Fallback database host & port | `127.0.0.1`, `5432` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Fallback database credentials | `codefoundry`, `codefoundry_user`, `password` |
| `REDIS_URL` | Redis cache & token blacklist URL | `redis://127.0.0.1:6379/1` |
| `CELERY_BROKER_URL` | Celery message broker Redis connection URL | `redis://127.0.0.1:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery task result backend URL | `redis://127.0.0.1:6379/0` |
| `VITE_API_BASE_URL` | Frontend API gateway endpoint (Client-exposed) | `https://api.codefoundry.dev/api` |

---

## 5. Security & Sandbox Constraints

The Docker execution sandbox enforces strict hardware and access limits during evaluation:
- `network_disabled=True` (no inbound or outbound socket access)
- `privileged=False` (unprivileged execution)
- `cap_drop=["ALL"]` (all Linux kernel capabilities dropped)
- `security_opt=["no-new-privileges:true"]`
- `mem_limit="128m"` / `memswap_limit="128m"`
- `nano_cpus=1_000_000_000` (1.0 CPU cap)
- `pids_limit=64` (fork-bomb prevention)
- Per-test execution timeout enforcement with process termination.
- Path traversal protection via `os.path.commonpath` canonical containment check.

---

## 6. Django Retirement & Migration Note

The legacy Django backend has been permanently retired from CodeFoundry:
- **FastAPI** is now the sole backend runtime powering all REST API endpoints.
- Django rollback is no longer supported; legacy Django runtime code and configurations have been removed.
- Historical Django migration files are preserved strictly for audit and database lineage evidence under `backend/legacy_django_migrations/`.
- Future schema migrations are managed exclusively by **Alembic** (`backend/alembic/`).
