from datetime import timedelta
from uuid import uuid4

import pytest

from horde.core.models import Job, JobState, utcnow
from horde.jobs.queue import InMemoryJobQueue


def make_job():
    return Job(project_id=uuid4(), target="example.com", tool="dns")


def test_claim_and_complete():
    queue = InMemoryJobQueue()
    job = queue.enqueue(make_job())
    claimed = queue.claim("worker-1")
    assert claimed and claimed.id == job.id and claimed.state is JobState.CLAIMED
    queue.mark_running(job.id, "worker-1")
    queue.complete(job.id, "worker-1")
    assert queue.get(job.id).state is JobState.SUCCEEDED


def test_expired_lease_is_requeued_until_attempts_exhausted():
    queue = InMemoryJobQueue()
    job = queue.enqueue(make_job())
    queue.claim("worker-1")
    job.lease_expires_at = utcnow() - timedelta(seconds=1)
    assert queue.recover_expired() == 1
    assert queue.get(job.id).state is JobState.QUEUED


def test_retries_are_bounded():
    queue = InMemoryJobQueue()
    job = queue.enqueue(make_job())
    job.max_attempts = 1
    queue.claim("worker-1")
    queue.fail(job.id, "worker-1", "bad", retry=True)
    assert queue.get(job.id).state is JobState.FAILED


def test_duplicate_job_id_is_rejected():
    queue = InMemoryJobQueue()
    job = make_job()
    queue.enqueue(job)
    with pytest.raises(ValueError, match="already exists"):
        queue.enqueue(job.model_copy(deep=True))


def test_stale_worker_cannot_complete_reclaimed_job():
    queue = InMemoryJobQueue()
    job = queue.enqueue(make_job())
    queue.claim("worker-1")
    job.lease_expires_at = utcnow() - timedelta(seconds=1)
    queue.recover_expired()
    queue.claim("worker-2")
    with pytest.raises(PermissionError):
        queue.complete(job.id, "worker-1")
    assert queue.get(job.id).worker_id == "worker-2"
