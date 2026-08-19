"""Worker orchestration: recover, claim, authorize, execute, normalize, and record."""

import logging
from time import monotonic

from horde.agents.lifecycle import AgentLifecycle
from horde.config import Settings
from horde.core.models import Agent, ExecutionEvent
from horde.jobs.queue import InMemoryJobQueue
from horde.scope.policy import ScopeEngine
from horde.tools import ToolContext, ToolRegistry

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, agent: Agent, queue: InMemoryJobQueue, scopes, registry: ToolRegistry, settings: Settings) -> None:
        self.agent = agent
        self.queue = queue
        self.scopes = scopes
        self.registry = registry
        self.settings = settings
        self.scope_engine = ScopeEngine()
        self.lifecycle = AgentLifecycle()
        self.events: list[ExecutionEvent] = []

    async def run_once(self) -> bool:
        self.queue.recover_expired()
        job = self.queue.claim(str(self.agent.id), lease_seconds=max(30, int(self.settings.tool_timeout_seconds * 2)))
        if job is None:
            self.lifecycle.heartbeat(self.agent, self.agent.health_score)
            return False
        started = monotonic()
        decision = self.scope_engine.check(job.target, self.scopes)
        if not decision.allowed:
            self.queue.fail(job.id, decision.reason, retry=False)
            self.lifecycle.cycle_complete(self.agent, False)
            self.events.append(ExecutionEvent(agent_id=self.agent.id, job_id=job.id, event="scope_denied", details=decision.model_dump()))
            return True
        try:
            self.queue.mark_running(job.id)
            tool = self.registry.get(job.tool)
            if job.tool not in self.settings.tool_allowlist:
                raise PermissionError(f"tool {job.tool!r} is not allowlisted")
            result = await tool.execute(job.target, job.options, ToolContext(
                timeout_seconds=self.settings.tool_timeout_seconds,
                max_output_bytes=self.settings.result_max_bytes,
                execute=self.settings.execute_tools,
            ))
            if result.ok:
                self.queue.complete(job.id)
                self.lifecycle.cycle_complete(self.agent, True)
                event = "job_succeeded"
            else:
                self.queue.fail(job.id, result.error or "tool failed")
                self.lifecycle.cycle_complete(self.agent, False)
                event = "job_failed"
            self.events.append(ExecutionEvent(agent_id=self.agent.id, job_id=job.id, event=event,
                                              duration_ms=round((monotonic() - started) * 1000),
                                              details={"tool": job.tool, "result": result.model_dump(exclude={"raw"})}))
        except Exception as exc:  # worker isolation: one job cannot kill the worker
            logger.exception("job execution failed", extra={"job_id": str(job.id), "agent_id": str(self.agent.id)})
            self.queue.fail(job.id, str(exc))
            self.lifecycle.cycle_complete(self.agent, False)
            self.events.append(ExecutionEvent(agent_id=self.agent.id, job_id=job.id, event="worker_exception",
                                              duration_ms=round((monotonic() - started) * 1000), details={"error": str(exc)}))
        self.lifecycle.heartbeat(self.agent, self.agent.health_score)
        return True
