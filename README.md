# Recon Horde V2

Recon Horde V2 is a defensive Linux reconnaissance orchestrator for systems the operator owns or is explicitly authorized to assess. It is deny-by-default: every job is checked against an active project scope before an adapter can execute.

## Quick start

```bash
./scripts/bootstrap.sh
source .venv/bin/activate
horde doctor
horde scope check api.example.com --kind domain --value example.com
pytest -q
```

Local execution is dry-run by default. Set `HORDE_EXECUTE_TOOLS=true` only after configuring the dedicated HORDE Supabase project and reviewing scopes. Never expose `SUPABASE_SERVICE_ROLE_KEY` to a client or commit `.env`.

## Architecture

The worker follows `recover → claim → scope-check → allowlist → execute → normalize → complete`. Adapters are Python classes selected by name from a fixed registry; database rows cannot provide shell fragments. The queue uses leases and bounded attempts, and the agent lifecycle tracks health, heartbeat, generation, and successor lineage.

The included migration creates a dedicated `horde` schema in Supabase with RLS enabled on every table, a `FOR UPDATE SKIP LOCKED` claim function, expired-lease recovery, normalized observations, findings, tickets, and durable agent events.

## Configuration

Copy `.env.example` to `.env`. Important controls include `HORDE_TOOL_ALLOWLIST`, `HORDE_TOOL_TIMEOUT_SECONDS`, `HORDE_MAX_CONCURRENT_JOBS`, `HORDE_RESULT_MAX_BYTES`, `HORDE_RETIRE_HEALTH_BELOW`, and `HORDE_AGENT_MAX_CYCLES`. Production startup must provide both Supabase settings when execution is enabled.

## Operations

```bash
horde doctor
horde tools list
horde scope check https://api.example.com/v1 --kind domain --value example.com
horde worker-once --target example.com --tool dns --project-id UUID
```

For Linux deployment, review `deploy/systemd/horde-worker@.service`; for containers, use the hardened `Dockerfile` and `docker-compose.yml`. `scripts/install-tools.sh` detects Debian-family systems and installs only optional packages that are absent.

## Security model

Recon Horde does not implement credential theft, persistence, destructive exploitation, evasion, or arbitrary Internet scanning. Scope decisions are recorded with jobs, tool output is size-limited, subprocesses use argument vectors with no shell, retries are bounded, and agents cannot expand authorization scope autonomously.

See `docs/architecture.md`, `docs/scope.md`, `docs/tools.md`, `docs/database.md`, `docs/agents.md`, `docs/security.md`, and `docs/operations.md`.
