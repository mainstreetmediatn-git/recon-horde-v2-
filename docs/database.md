# Database

Apply `supabase/migrations/20260819000000_horde_foundation.sql` to the dedicated HORDE project. The migration is idempotent for tables, indexes, functions, and the schema version row. All application tables use RLS with no public policies; the service role is the runtime boundary.

After applying migrations, run Supabase security and performance advisors. Review any warning before enabling production execution. The worker should compare its expected schema version with `horde.schema_version` during startup.
