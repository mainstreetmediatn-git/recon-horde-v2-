# Agents and lifecycle

Agents transition through provisioning, ready, active, degraded, retiring, and retired. Health is deterministic and considers heartbeat age, success rate, failures, resource pressure, tool availability, database availability, and queue backlog.

Successors inherit project, role, name, and max-cycle policy, but start with clean transient state. Parent/successor IDs and generation are persisted. Successor creation is bounded by operator lifecycle policy; agents do not create unbounded recursive generations.
