# Security Model

CodeRunner Cloud executes untrusted user code inside isolated Docker containers.

## Sandboxing
- Network access is disabled.
- PIDs are limited to prevent fork bombs.
- Containers run as non-root user `1000`.
- All Linux capabilities are dropped (`cap_drop: ALL`).
- No new privileges (`no-new-privileges: true`).
- Read-only filesystem except for isolated `tmpfs` mounts.
