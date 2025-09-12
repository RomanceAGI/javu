import os
from rq import Queue
from redis import Redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis = Redis.from_url(REDIS_URL)
q = Queue(
    "javu", connection=redis, default_timeout=int(os.getenv("RQ_JOB_TIMEOUT", "1800"))
)


def enqueue(job_type: str, payload: dict):
    return q.enqueue(
        "javu_agi.runtime.worker.run_job", {"type": job_type, "payload": payload}
    )
