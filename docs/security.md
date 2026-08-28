# Security

This is an authorized defensive reconnaissance system. Scope is deny-by-default and must be attached to a project. Service-role secrets remain server-side and are redacted from logs. Results and raw data are bounded. The tool registry is explicit, subprocesses are shell-free, and retry/lease behavior is bounded.

Human operator policy overrides automation. Infrastructure mutations are outside the adapter contract and require a separate reviewed workflow.
