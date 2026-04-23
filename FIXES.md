BUG 1 — No /health endpoint on API or frontend
File: api/main.py, frontend/app.js
Issue: Docker HEALTHCHECK instructions and depends_on: condition: service_healthy in docker-compose require the containers to expose a health endpoint. Without one, health checks fail and dependent services never start.
Fix: Added GET /health to the API (pings Redis and returns {"status": "ok"}). Added GET /health to the frontend (returns {"status": "ok"}).

BUG 2 — Hardcoded localhost Redis host in API
File: api/main.py, line 8
Original: r = redis.Redis(host="localhost", port=6379)
Issue: localhost resolves to the container itself when running in Docker. The Redis service is on a separate container reachable by its service name (redis). This causes the API to fail to connect to Redis in any containerised environment.
Fix: Changed to read from environment variable: REDIS_HOST = os.environ.get("REDIS_HOST", "redis"). Redis connection now uses host=REDIS_HOST.

BUG 3 — api/.env committed to version control
File: api/.env
Issue: A real .env file containing REDIS_PASSWORD=supersecretpassword123 was committed to the repository. Secrets in version control are a critical security violation — they persist in git history even after deletion.
Fix: Deleted api/.env. Added .env and *.env patterns to .gitignore. Provided /.env.example with placeholder values instead.

BUG 4 — Worker has no error handling for Redis connection failures
File: worker/worker.py
Issue: If Redis became temporarily unavailable, the unhandled ConnectionError would crash the worker process entirely. Docker would restart it, but this causes log noise and potential job loss.
Fix: Wrapped the brpop call in a try/except redis.exceptions.ConnectionError block that logs the error and sleeps 5 seconds before retrying.

BUG 5 — Worker has no signal handling or graceful shutdown
File: worker/worker.py
Issue: The worker ran an infinite while True loop with no signal handling. A SIGTERM from Docker during container stop would kill it mid-job, potentially leaving jobs in a processing state forever with no way to recover.
Fix: Added signal.signal(SIGTERM, ...) and signal.signal(SIGINT, ...) handlers that set a running = False flag. The main loop checks while running: and exits cleanly after the current job finishes.

BUG 6 — Redis password not used in API or worker
File: api/main.py, worker/worker.py
Issue: The .env defined REDIS_PASSWORD but neither the API nor the worker passed it to the Redis client. Any Redis instance configured with requirepass would reject all connections.
Fix: Both services now read REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None) and pass it as password=REDIS_PASSWORD to redis.Redis(...).

BUG 7 — API returns 200 with {"error": "not found"} for missing jobs
File: api/main.py, lines 19–21
Original:
pythonif not status:
    return {"error": "not found"}
Issue: Returning HTTP 200 with an error body is incorrect. Clients (including the integration test) cannot distinguish success from failure by HTTP status code alone.
Fix: Changed to raise HTTPException(status_code=404, detail="Job not found").

BUG 8 — Hardcoded localhost Redis host in worker
File: worker/worker.py, line 6
Original: r = redis.Redis(host="localhost", port=6379)
Issue: Same problem as BUG 2 — localhost does not resolve to the Redis container inside Docker networking.
Fix: Changed to REDIS_HOST = os.environ.get("REDIS_HOST", "redis") and passed it to the Redis constructor.

BUG 9 — Hardcoded localhost API URL in frontend
File: frontend/app.js, line 6
Original: const API_URL = "http://localhost:8000";
Issue: Inside Docker, localhost in the frontend container resolves to the frontend container itself, not the API container. Cross-container communication requires the Docker service name.
Fix: Changed to const API_URL = process.env.API_URL || "http://api:8000"; so it reads from environment at runtime.

BUG 10 — Frontend PORT hardcoded in app.js
File: frontend/app.js, line 21
Original: app.listen(3000, ...)
Issue: Port is hardcoded; cannot be configured via environment variable, which is required when running in containers.
Fix: Changed to const PORT = parseInt(process.env.PORT || "3000", 10) and app.listen(PORT, ...).

BUG 11 — No /health endpoint on API or frontend
File: api/main.py, frontend/app.js
Issue: Docker HEALTHCHECK instructions and depends_on: condition: service_healthy in docker-compose require the containers to expose a health endpoint. Without one, health checks fail and dependent services never start.
Fix: Added GET /health to the API (pings Redis and returns {"status": "ok"}). Added GET /health to the frontend (returns {"status": "ok"}).

BUG 12 — Mismatched Redis queue key between API and worker
File: api/main.py line 13, worker/worker.py line 19
Original (api): r.lpush("job", job_id) — pushes to key "job"
Original (worker): r.brpop("job", timeout=5) — actually this matched, but the key "job" is also used as a prefix for per-job hashes (job:{id}). This is a naming collision risk and non-idiomatic.
Fix: Renamed queue key to "jobs" in both api/main.py (r.lpush("jobs", ...)) and worker/worker.py (r.brpop("jobs", ...)). Per-job hashes remain job:{id}. This separates the queue key from the hash namespace.

BUG 13 — API returns raw bytes from Redis (decode issue)
File: api/main.py, line 20
Original: return {"job_id": job_id, "status": status.decode()}
Issue: The code manually called .decode(), which works when decode_responses=False (the default), but is fragile — if decode_responses=True is set, calling .decode() on a string raises AttributeError. More importantly, the original code would return b'queued' (bytes) if status were ever serialised to JSON directly without the .decode() call.
Fix: Set decode_responses=True on the Redis client so all responses are already strings. Removed the manual .decode() call. Return status directly.