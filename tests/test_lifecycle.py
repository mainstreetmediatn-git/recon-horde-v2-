from uuid import uuid4

from horde.agents.health import HealthInputs, score_health
from horde.agents.lifecycle import AgentLifecycle
from horde.core.models import Agent, AgentStatus


def test_health_is_deterministic_and_bounded():
    assert score_health(HealthInputs()) == 100
    assert score_health(HealthInputs(consecutive_failures=10, database_available=False)) < 70


def test_successor_increments_generation_without_transient_state():
    agent = Agent(project_id=uuid4(), name="atlas", generation=1, status=AgentStatus.ACTIVE, consecutive_failures=4)
    successor = AgentLifecycle().create_successor(agent)
    assert agent.status is AgentStatus.RETIRED
    assert successor.generation == 2
    assert successor.parent_id == agent.id
    assert successor.consecutive_failures == 0
    assert successor.status is AgentStatus.READY
