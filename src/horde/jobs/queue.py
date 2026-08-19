"""Lease-aware in-memory queue used for local operation and deterministic tests."""

from datetime import timedelta
from threading import RLock
from uuid import UUID

from horde.core.models import Job, JobState, utcnow


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._jobs: dict[UUID, Job] = {}
        self._lock = RLock()

    def enqueue(self, job: Job) -> Job:
        with self._lock:
            if job.state is not JobState.QUEUED:
                raise ValueError("only queued jobs may be enqueued")
            self._jobs[job.id] = job
            return job

    def recover_expired(self, now=None) -> int:
        now = now or utcnow()
        recovered = 0
        with self._lock:
            for job in self._jobs.values():
                if job.state in (JobState.CLAIMED, JobState.RUNNING) and job.lease_expires_at and job.lease_expires_at <= now:
                    job.state = JobState.QUEUED if job.attempt_count < job.max_attempts else JobState.FAILED
                    job.worker_id = None
                    job.lease_expires_at = None
                    job.last_error = "lease expired; recovered" if job.state is JobState.QUEUED else "lease expired; attempts exhausted"
                    job.updated_at = now
                    recovered += 1
        return recovered

    def claim(self, worker_id: str, lease_seconds: int = 60) -> Job | None:
        with self._lock:
            candidates = sorted((job for job in self._jobs.values() if job.state is JobState.QUEUED), key=lambda item: item.created_at)
            if not candidates:
                return None
            job = candidates[0]
            job.state = JobState.CLAIMED
            job.attempt_count += 1
            job.worker_id = worker_id
            job.lease_expires_at = utcnow() + timedelta(seconds=lease_seconds)
            job.updated_at = utcnow()
            return job

    def mark_running(self, job_id: UUID) -> None:
        with self._lock:
            job = self._jobs[job_id]
            if job.state is not JobState.CLAIMED:
                raise ValueError("job must be claimed before it runs")
            job.state = JobState.RUNNING
            job.updated_at = utcnow()

    def complete(self, job_id: UUID) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.state = JobState.SUCCEEDED
            job.lease_expires_at = None
            job.updated_at = utcnow()

    def fail(self, job_id: UUID, error: str, retry: bool = True) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.last_error = error[:2000]
            job.lease_expires_at = None
            job.worker_id = None
            job.state = JobState.QUEUED if retry and job.attempt_count < job.max_attempts else JobState.FAILED
            job.updated_at = utcnow()

    def get(self, job_id: UUID) -> Job:
        return self._jobs[job_id]

    def list(self, state: JobState | None = None) -> list[Job]:
        with self._lock:
            jobs = list(self._jobs.values())
        return [job for job in jobs if state is None or job.state is state]
