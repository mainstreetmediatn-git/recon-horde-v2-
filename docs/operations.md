# Operations

Run `horde doctor` before enabling a worker. Inspect writable data paths, Supabase credentials, schema version, adapter availability, and container/runtime permissions. Use the systemd unit for restart backoff and filesystem hardening. On shutdown, stop claiming jobs, let active work finish or expire its lease, and recover expired jobs on the next start.

Keep concurrency and rate limits conservative for authorized networks. Monitor stale leases, queue growth, empty tool output, timeout rates, and health decline; these should become maintenance tickets rather than triggering automatic infrastructure changes.
