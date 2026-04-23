import logging
import os
import signal
import time

import redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", None)

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
)

running = True


def handle_shutdown(signum, frame):
    global running
    logging.info("Shutdown signal received, stopping worker...")
    running = False


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


def process_job(job_id: str):
    logging.info(f"Processing job {job_id}")
    print(f"Processing job {job_id}")
    r.hset(f"job:{job_id}", "status", "processing")
    time.sleep(2)
    r.hset(f"job:{job_id}", "status", "completed")
    logging.info(f"Done: {job_id}")
    print(f"Done: {job_id}")


logging.info("Worker started, waiting for jobs...")
while running:
    try:
        job = r.brpop("jobs", timeout=5)
        if job:
            _, job_id = job
            process_job(job_id)
    except redis.exceptions.ConnectionError as e:
        logging.error(f"Redis connection error: {e}. Retrying in 5 seconds...")
        time.sleep(5)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

logging.info("Worker shut down cleanly.")
