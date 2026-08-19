"""Finite agent lifecycle with bounded successor generation."""

from horde.core.models import Agent, AgentStatus, utcnow


class AgentLifecycle:
    def heartbeat(self, agent: Agent, health: int) -> Agent:
        agent.heartbeat_at = utcnow()
        agent.health_score = max(0, min(100, health))
        if agent.status in (AgentStatus.READY, AgentStatus.DEGRADED) and health >= 70:
            agent.status = AgentStatus.ACTIVE
        elif health < 40 and agent.status in (AgentStatus.READY, AgentStatus.ACTIVE, AgentStatus.DEGRADED):
            agent.status = AgentStatus.DEGRADED
        return agent

    def cycle_complete(self, agent: Agent, succeeded: bool) -> Agent:
        agent.cycles_completed += 1
        if succeeded:
            agent.successful_jobs += 1
            agent.consecutive_failures = 0
        else:
            agent.failed_jobs += 1
            agent.consecutive_failures += 1
        return agent

    def should_retire(self, agent: Agent, health_threshold: int = 40) -> bool:
        return agent.cycles_completed >= agent.max_cycles or agent.health_score < health_threshold or agent.consecutive_failures >= 5

    def create_successor(self, agent: Agent) -> Agent:
        if agent.status in (AgentStatus.RETIRED, AgentStatus.RETIRING):
            raise ValueError("successor already being created")
        agent.status = AgentStatus.RETIRING
        successor = Agent(
            project_id=agent.project_id,
            name=agent.name,
            generation=agent.generation + 1,
            status=AgentStatus.PROVISIONING,
            max_cycles=agent.max_cycles,
            parent_id=agent.id,
        )
        agent.successor_id = successor.id
        successor.status = AgentStatus.READY
        agent.status = AgentStatus.RETIRED
        return successor
