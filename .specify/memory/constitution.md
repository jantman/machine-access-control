<!--
Sync Impact Report
===================
- Version change: 0.0.0 → 1.0.0 (initial ratification)
- Added principles:
  1. Safety & Reliability (new)
  2. Testing Discipline (new)
  3. Simplicity & YAGNI (new)
  4. Backward Compatibility (new)
  5. Documentation (new)
- Added sections:
  - Operational Standards
  - Quality Gates
  - Governance
- Removed sections: none (initial version)
- Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ no changes needed
    (Constitution Check section is generic; gates derived at plan time)
  - .specify/templates/spec-template.md — ✅ no changes needed
    (spec structure already covers user stories, requirements, success criteria)
  - .specify/templates/tasks-template.md — ✅ no changes needed
    (task phases and test-first guidance align with principles)
- Follow-up TODOs: none
-->

# Decatur Makers Machine Access Control Constitution

## Core Principles

### I. Safety & Reliability

This system controls physical power tools. Failures can cause
injury or equipment damage. All design decisions MUST prioritize
safe defaults:

- Hardware relay states MUST default to **off/disabled** when the
  server is unreachable or in an error state.
- Every code path that controls machine state MUST handle
  exceptions defensively — never leave a relay in an unintended
  state.
- RFID authentication failures MUST deny access (fail-closed),
  not grant it.
- State persistence MUST survive server restarts so running
  machines are not silently abandoned.
- Changes to machine-control logic MUST include tests that
  verify fail-safe behavior under error conditions.

### II. Testing Discipline

Correctness is enforced through automated testing:

- All new server-side logic MUST have corresponding unit or
  integration tests.
- Async endpoints MUST be tested with `pytest-asyncio`.
- Tests MUST NOT make network calls; `pytest-blockage` enforces
  this at the runner level.
- Test fixtures in `tests/fixtures/` MUST be used for
  configuration data — never hard-code config in tests.
- Coverage MUST not decrease on any PR. The project-wide
  threshold is intentionally low during early development but
  MUST only increase over time.

### III. Simplicity & YAGNI

Keep the codebase small and understandable:

- Prefer direct, linear code over abstractions. A few repeated
  lines are better than a premature helper.
- Do not add features, configuration options, or extension points
  that are not required by a current feature spec.
- New dependencies MUST justify their inclusion — prefer the
  standard library or existing dependencies when feasible.
- Remove dead code immediately; do not comment it out or hide it
  behind flags.

### IV. Backward Compatibility

The server and MCUs are deployed independently. Protocol and
configuration changes MUST not break existing deployments:

- The `/machine/update` request/response contract MUST remain
  backward-compatible. New fields are additive and optional.
- `machines.json` and `users.json` schema changes MUST be
  backward-compatible or accompanied by a documented migration
  path.
- Persisted machine state (pickle files) MUST handle missing or
  extra fields gracefully after a server upgrade.
- Breaking changes to the MCU↔server protocol MUST be called out
  explicitly in the feature spec and require a migration plan.

### V. Documentation

Users, administrators, and developers each need clear, accurate
documentation:

- Every feature MUST include user-facing documentation updates
  when it changes behavior visible to makerspace members or
  administrators.
- API endpoints MUST be documented with expected request/response
  formats.
- Configuration options (`machines.json`, `users.json`,
  environment variables) MUST be documented in CLAUDE.md and/or
  project docs when added or changed.
- Developer-facing documentation (setup, testing, architecture)
  MUST stay current — outdated docs are worse than no docs.

## Operational Standards

The system runs in a physical makerspace environment with
real-time requirements:

- **Logging**: All authentication and authorization decisions
  MUST be logged via the `AUTH` logger. Machine state changes
  MUST be logged at INFO level or above.
- **Monitoring**: The `/metrics` Prometheus endpoint MUST expose
  key operational metrics (active machines, authentication
  attempts, error rates).
- **State Persistence**: Machine state MUST be persisted to disk
  on every update. File locking via `filelock` MUST be used for
  all state file operations.
- **Slack Integration**: When configured, Slack notifications
  MUST be sent for machine lockouts, oops-button events, and
  unauthorized access attempts. Slack failures MUST NOT block
  machine operations.
- **Graceful Degradation**: If NeonOne CRM or Slack is
  unreachable, the server MUST continue operating with cached
  user data and skip notifications rather than failing.

## Quality Gates

All contributions MUST pass these gates before merge:

- **Tests**: `nox -s tests` passes with no failures.
- **Type Checking**: `nox -s mypy` reports no new errors.
- **Linting**: `nox -s pre-commit` passes (includes formatting,
  import sorting, and static analysis).
- **Security**: `nox -s safety` reports no new high/critical
  vulnerabilities in dependencies.
- **Coverage**: Coverage percentage MUST not decrease from the
  prior commit on the target branch.
- **Pre-commit Hooks**: All pre-commit hooks MUST pass. Do not
  bypass with `--no-verify`.

## Governance

This constitution is the highest-authority document for
development decisions in this project. When a feature spec,
plan, or task conflicts with a principle stated here, the
constitution wins.

**Amendment process**:
1. Propose the change with rationale in a PR modifying this file.
2. The change MUST include a Sync Impact Report (HTML comment at
   top of this file) documenting version bump, affected
   principles, and template propagation status.
3. Version the constitution using semantic versioning:
   - MAJOR: Principle removed or redefined incompatibly.
   - MINOR: New principle or section added, or material expansion.
   - PATCH: Wording clarifications, typo fixes.

**Compliance review**: Feature specs and implementation plans
MUST include a Constitution Check section that verifies alignment
with these principles before work begins.

**Version**: 1.0.0 | **Ratified**: 2026-03-15 | **Last Amended**: 2026-03-15
