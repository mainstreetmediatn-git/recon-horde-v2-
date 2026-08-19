# Architecture

Projects own scopes, tools, agents, jobs, observations, findings, and tickets. The runtime is split into domain models, a scope engine, adapter registry, lease queue, lifecycle service, and persistence adapter. The in-memory queue is used by local tests; Supabase is the durable production boundary.

The critical execution path has no implicit network target discovery: the job target is explicit, normalized, and authorized before the selected adapter receives it.
