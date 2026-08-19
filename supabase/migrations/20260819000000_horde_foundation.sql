-- HORDE V2: all application tables live in a dedicated schema and are deny-by-default.
create schema if not exists horde;

create table if not exists horde.schema_version (
  version integer primary key,
  applied_at timestamptz not null default now()
);

create table if not exists horde.projects (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  description text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists horde.authorized_scopes (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references horde.projects(id) on delete cascade,
  kind text not null check (kind in ('domain','subdomain','ip','cidr','url','url_subtree')),
  value text not null,
  label text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  unique(project_id, kind, value)
);

create table if not exists horde.tools (
  name text primary key,
  adapter text not null unique,
  enabled boolean not null default true,
  config jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists horde.agents (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references horde.projects(id) on delete cascade,
  name text not null,
  generation integer not null default 1 check (generation > 0),
  status text not null default 'provisioning' check (status in ('provisioning','ready','active','degraded','retiring','retired','failed')),
  health_score integer not null default 100 check (health_score between 0 and 100),
  cycles_completed integer not null default 0,
  successful_jobs integer not null default 0,
  failed_jobs integer not null default 0,
  consecutive_failures integer not null default 0,
  max_cycles integer not null default 1000 check (max_cycles > 0),
  heartbeat_at timestamptz,
  parent_id uuid references horde.agents(id),
  successor_id uuid references horde.agents(id),
  created_at timestamptz not null default now(),
  retired_at timestamptz,
  unique(project_id, name, generation)
);

create table if not exists horde.jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references horde.projects(id) on delete cascade,
  target text not null,
  tool text not null references horde.tools(name),
  options jsonb not null default '{}'::jsonb,
  state text not null default 'queued' check (state in ('queued','claimed','running','succeeded','failed','cancelled')),
  attempt_count integer not null default 0 check (attempt_count >= 0),
  max_attempts integer not null default 3 check (max_attempts between 1 and 10),
  lease_expires_at timestamptz,
  worker_id text,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists horde.observations (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references horde.projects(id) on delete cascade,
  job_id uuid references horde.jobs(id) on delete set null,
  kind text not null,
  target text not null,
  fingerprint text not null,
  normalized jsonb not null,
  raw jsonb,
  observed_at timestamptz not null default now(),
  unique(project_id, kind, fingerprint)
);

create table if not exists horde.findings (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references horde.projects(id) on delete cascade,
  fingerprint text not null,
  title text not null,
  severity text not null check (severity in ('info','low','medium','high')),
  description text not null,
  status text not null default 'open' check (status in ('open','acknowledged','resolved')),
  created_at timestamptz not null default now(),
  resolved_at timestamptz,
  unique(project_id, fingerprint)
);

create table if not exists horde.tickets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references horde.projects(id) on delete cascade,
  fingerprint text not null,
  kind text not null check (kind in ('bug','enhancement','maintenance','retirement','security')),
  title text not null,
  description text not null,
  status text not null default 'open' check (status in ('open','resolved')),
  created_at timestamptz not null default now(),
  resolved_at timestamptz,
  unique(project_id, fingerprint)
);

create table if not exists horde.agent_events (
  id bigint generated always as identity primary key,
  agent_id uuid not null references horde.agents(id) on delete cascade,
  job_id uuid references horde.jobs(id) on delete set null,
  event text not null,
  duration_ms integer,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists jobs_claim_idx on horde.jobs(state, lease_expires_at, created_at);
create index if not exists scopes_project_active_idx on horde.authorized_scopes(project_id, active);
create index if not exists events_agent_created_idx on horde.agent_events(agent_id, created_at desc);

alter table horde.schema_version enable row level security;
alter table horde.projects enable row level security;
alter table horde.authorized_scopes enable row level security;
alter table horde.tools enable row level security;
alter table horde.agents enable row level security;
alter table horde.jobs enable row level security;
alter table horde.observations enable row level security;
alter table horde.findings enable row level security;
alter table horde.tickets enable row level security;
alter table horde.agent_events enable row level security;

-- No anon/authenticated policies are created. The service role is the only runtime writer.
create or replace function horde.claim_job(p_worker_id text, p_lease_seconds integer default 60)
returns setof horde.jobs
language plpgsql
security definer
set search_path = horde, pg_catalog
as $$
begin
  return query
  with candidate as (
    select id from horde.jobs
    where state = 'queued'
    order by created_at
    for update skip locked
    limit 1
  )
  update horde.jobs j
  set state = 'claimed', attempt_count = attempt_count + 1,
      worker_id = p_worker_id, lease_expires_at = now() + make_interval(secs => p_lease_seconds), updated_at = now()
  from candidate where j.id = candidate.id
  returning j.*;
end;
$$;

create or replace function horde.recover_expired_jobs()
returns integer
language plpgsql
security definer
set search_path = horde, pg_catalog
as $$
declare recovered integer;
begin
  update horde.jobs set state = case when attempt_count < max_attempts then 'queued' else 'failed' end,
    worker_id = null, lease_expires_at = null, last_error = 'lease expired; recovered', updated_at = now()
  where state in ('claimed','running') and lease_expires_at < now();
  get diagnostics recovered = row_count;
  return recovered;
end;
$$;

insert into horde.schema_version(version) values (1) on conflict do nothing;
