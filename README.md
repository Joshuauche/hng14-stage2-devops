HNG14 Stage 2 — Job Processing System
A containerised job processing system with a Node.js frontend, Python/FastAPI backend, Python worker, and Redis queue.

Prerequisites
ToolMinimum versionDocker24.xDocker Composev2.20+Git2.x

Quick Start (clean machine)
1. Clone the repository
bashgit clone <your-fork-url>
cd hng14-stage2-devops
2. Create your environment file
bashcp .env.example .env
Edit .env and set a strong REDIS_PASSWORD. Never commit this file.
3. Build and start the stack
bashdocker compose up -d --build
4. Verify everything is healthy
bashdocker compose ps
All four services (redis, api, worker, frontend) should show healthy status.
5. Open the dashboard
Navigate to http://localhost:3000 in your browser.

What a successful startup looks like
NAME                STATUS
stage2-redis        running (healthy)
stage2-api          running (healthy)
stage2-worker       running (healthy)
stage2-frontend     running (healthy)
The frontend at http://localhost:3000 shows a Job Processor Dashboard. Clicking Submit New Job creates a job, and within a few seconds the status updates from queued → processing → completed.

Environment variables
VariableRequiredDescriptionREDIS_PASSWORDYesPassword for Redis. Must match across all services.FRONTEND_PORTNoHost port to expose the frontend on (default: 3000).

Service ports
ServiceInternal portExposed to hostFrontend3000${FRONTEND_PORT} (default 3000)API8000Not exposed — internal onlyRedis6379Not exposed — internal only

Useful commands
bash# View logs for all services
docker compose logs -f

# View logs for a single service
docker compose logs -f api

# Stop the stack (preserves volumes)
docker compose down

# Stop and remove all volumes
docker compose down -v

# Rebuild a single service after code changes
docker compose up -d --build api

Running tests locally
bashcd api
pip install -r requirements.txt pytest pytest-cov
pytest tests/ -v --cov=main --cov-report=term-missing

CI/CD Pipeline
The GitHub Actions pipeline runs on every push in strict order:
lint → test → build → security scan → integration test → deploy

lint: flake8 (Python), eslint (JS), hadolint (Dockerfiles)
test: pytest with Redis mocked; coverage report uploaded as artifact
build: all three images built, tagged with git SHA and latest, pushed to local registry
security scan: Trivy scans all images; fails pipeline on any CRITICAL finding
integration test: full stack started inside the runner; a real job is submitted and polled to completed
deploy: runs on main branch pushes only; performs a rolling update — new container must pass health check within 60 seconds before old one is stopped

A failure at any stage prevents subsequent stages from running.
