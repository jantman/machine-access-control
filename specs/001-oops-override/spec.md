# Feature Specification: Oops/Lockout Override Login

**Feature Branch**: `001-oops-override`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Certain specific members who are responsible for repairing machines need a way to activate machines without clearing oops or maintenance lockout, to eliminate confusion caused by un-oops'ed / un-locked-out notifications and to ensure that broken machines don't end up accidentally cleared as part of the troubleshooting/repair process."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Override Login on Oopsed Machine (Priority: P1)

A designated repair member arrives at a machine that has been oopsed (reported as broken). They insert their RFID card. Instead of the normal behavior of clearing the oops state and showing "Welcome, [name]", the machine activates with the oops state preserved underneath. The LCD displays "OVERRIDE BY [name]" to make it visually clear this is not a normal login. A notification is sent to the Slack control channel indicating an override login occurred. No notification is sent to the oops channel (avoiding the confusing "un-oops" message). When the repair member removes their card, the machine returns to its oopsed state -- relay off, oops LED on, LCD showing the oops message -- as if they were never there.

**Why this priority**: This is the core use case. Repair members currently must clear the oops state to test machines, which generates confusing Slack notifications and risks leaving broken machines in a "cleared" state if they forget to re-oops.

**Independent Test**: Can be fully tested by having an override-authorized user insert their RFID into an oopsed machine, verifying the machine activates without clearing oops, and confirming the machine returns to oopsed state when the card is removed.

**Acceptance Scenarios**:

1. **Given** a machine is in oopsed state and a user with oops override authorization inserts their RFID, **When** the system processes the update, **Then** the machine relay is activated, the LCD displays "OVERRIDE BY [preferred name]", the oops state is preserved (not cleared), and the machine state reflects an override login.
2. **Given** a machine is in override login state (from an oopsed machine) and the override user removes their RFID, **When** the system processes the update, **Then** the machine relay is deactivated, the oops state is restored (oops LED on, LCD shows oops message), and no "un-oops" notification is sent.
3. **Given** a machine is in oopsed state and a normal user (without override authorization) inserts their RFID, **When** the system processes the update, **Then** the existing behavior is unchanged (oops is cleared, normal login proceeds).

---

### User Story 2 - Override Login on Locked-Out Machine (Priority: P1)

A repair member arrives at a machine that has been locked out by an admin. They insert their RFID card. The machine activates with the lockout state preserved underneath, LCD shows "OVERRIDE BY [name]", and a Slack control channel notification is sent. When the card is removed, the machine returns to its locked-out state.

**Why this priority**: Lockout override is equally important as oops override -- both are states that indicate the machine should not be used by normal members, but repair members need access.

**Independent Test**: Can be fully tested by having an override-authorized user insert their RFID into a locked-out machine, verifying the machine activates without clearing lockout, and confirming the machine returns to locked-out state when the card is removed.

**Acceptance Scenarios**:

1. **Given** a machine is in locked-out state and a user with oops override authorization inserts their RFID, **When** the system processes the update, **Then** the machine relay is activated, the LCD displays "OVERRIDE BY [preferred name]", the lockout state is preserved, and the machine state reflects an override login.
2. **Given** a machine is in override login state (from a locked-out machine) and the override user removes their RFID, **When** the system processes the update, **Then** the machine relay is deactivated, the lockout state is restored, and no "unlock" notification is sent.

---

### User Story 3 - Slack Notification for Override Login (Priority: P2)

When a repair member performs an override login, a notification is posted to the Slack control channel (admin-only channel) indicating that an override login was performed, on which machine, and by whom. No notification is posted to the oops channel, preventing confusion among general members.

**Why this priority**: Visibility into override usage is important for accountability and coordination, but the feature works without it.

**Independent Test**: Can be tested by performing an override login and verifying the correct Slack message appears in the control channel and no message appears in the oops channel.

**Acceptance Scenarios**:

1. **Given** an override login is performed, **When** the system processes the login, **Then** a notification is posted to the Slack control channel with the machine name, user name, and indication that it was an override login.
2. **Given** an override login is performed on an oopsed machine, **When** the system processes the login, **Then** no notification is posted to the oops channel.
3. **Given** an override login ends (card removed), **When** the system processes the removal, **Then** no "un-oops" or "unlock" notification is posted to the oops channel.

---

### User Story 4 - NeonOne CRM Integration for Override Authorization (Priority: P2)

The oops override capability is controlled by a configurable field in NeonOne CRM. The neongetter tool pulls this field for each user and includes it in the user data. The field name defaults to "OOPS_OVERRIDE" but is configurable via a new `oops_override_field` setting in the neongetter configuration.

**Why this priority**: The Neon integration is the mechanism by which override authorization is granted, but during initial development, static test data can be used.

**Independent Test**: Can be tested by configuring the neongetter with the override field, running it against test data, and verifying the resulting users.json includes the override authorization for the appropriate users.

**Acceptance Scenarios**:

1. **Given** a NeonOne account has the OOPS_OVERRIDE field set to a truthy value, **When** neongetter runs, **Then** the user's data in users.json includes an indication that they have override authorization.
2. **Given** the neongetter config specifies a custom `oops_override_field` name, **When** neongetter runs, **Then** it uses the specified field name instead of the default "OOPS_OVERRIDE".
3. **Given** a NeonOne account does not have the override field set, **When** neongetter runs, **Then** the user's data does not include override authorization.

---

### User Story 5 - Override Login in Prometheus Metrics (Priority: P3)

The override login state is exposed via Prometheus metrics so it can be monitored and alerted on. A new per-machine metric indicates whether the machine is currently in an override login state.

**Why this priority**: Metrics are important for observability but are not critical to the core override functionality.

**Independent Test**: Can be tested by performing an override login and scraping the metrics endpoint to verify the new metric is present and correctly reflects the override state.

**Acceptance Scenarios**:

1. **Given** a machine is in override login state, **When** the metrics endpoint is scraped, **Then** the override login metric for that machine reads 1.
2. **Given** a machine is not in override login state, **When** the metrics endpoint is scraped, **Then** the override login metric for that machine reads 0.

---

### User Story 6 - Documentation Updates (Priority: P2)

All relevant documentation is updated to reflect the new override login feature, covering three audiences: administrators, users/operators, and developers.

**Why this priority**: Documentation is essential for the feature to be usable and maintainable, but not required for the core functionality to work.

**Independent Test**: Can be verified by reviewing documentation for completeness and accuracy against the implemented feature.

**Acceptance Scenarios**:

1. **Given** the feature is implemented, **When** an administrator reads the admin documentation, **Then** they can understand: the new `machine_override_login_state` Prometheus metric, what override login means in the Grafana dashboard context, and how the override login state appears in machine status.
2. **Given** the feature is implemented, **When** an administrator reads the configuration documentation, **Then** they can understand: the new `oops_override_field` neongetter config option, how override authorization appears in users.json, and how to grant override authorization to static fob users.
3. **Given** the feature is implemented, **When** an administrator reads the Slack documentation, **Then** they can understand: that override logins generate control channel notifications but not oops channel notifications, and what the override notification messages look like.
4. **Given** the feature is implemented, **When** a developer reads the NeonOne integration documentation, **Then** they can understand: how the override field is pulled from Neon, the default field name, and how to configure a custom field name.

---

### Edge Cases

- What happens when an override user inserts their card on a machine that is both oopsed AND locked out? The override should activate the machine, and upon card removal, both oopsed and locked-out states should be restored.
- What happens when an override user inserts their card on a machine that is NOT oopsed or locked out? Normal login behavior should occur (the override capability is only meaningful when a machine is in oopsed or locked-out state).
- What happens if the server restarts while an override login is active? The persisted state should correctly restore the override login state, and upon the next card-remove update, the machine should return to its pre-override state.
- What happens if a machine reboots (uptime drops) during an override login? The machine should handle reboot detection the same as a normal login -- reset state appropriately, restoring the underlying oops/lockout state.
- What happens if an admin clears the oops or lockout via Slack or API while an override login is active? The override login should continue, but when the card is removed, the machine should return to normal state (since the underlying oops/lockout was cleared).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow designated users with oops override authorization to activate machines that are in oopsed or locked-out state without clearing those states.
- **FR-002**: System MUST display "OVERRIDE BY [preferred name]" on the LCD when an override login is active, instead of the normal "Welcome, [preferred name]" message.
- **FR-003**: System MUST restore the previous oopsed or locked-out state when the override user removes their RFID card.
- **FR-004**: System MUST post a notification to the Slack control channel when an override login occurs, identifying the machine and the user.
- **FR-005**: System MUST NOT post any notification to the Slack oops channel when an override login occurs or ends.
- **FR-006**: System MUST NOT send "un-oops" or "unlock" notifications when an override login is performed.
- **FR-007**: System MUST track the override login state in the machine state object, including persistence across server restarts.
- **FR-008**: System MUST expose the override login state as a Prometheus metric per machine.
- **FR-009**: The neongetter tool MUST support a configurable field name for the oops override authorization, defaulting to "OOPS_OVERRIDE".
- **FR-010**: System MUST include the oops override authorization in the user data schema (users.json).
- **FR-011**: When an override user inserts their card on a machine that is NOT oopsed or locked out, normal login behavior MUST occur.
- **FR-012**: System MUST correctly handle the case where a machine is both oopsed and locked out, restoring both states upon card removal.
- **FR-013**: Administrator documentation MUST be updated to describe the new Prometheus metric for override login state, the override login behavior in Slack notifications, and the new neongetter configuration option.
- **FR-014**: Configuration documentation MUST be updated to reflect any changes to users.json schema (override authorization field), neongetter config schema (oops_override_field), and static fob user configuration.
- **FR-015**: NeonOne integration documentation MUST be updated to describe the override authorization field, its default name, and how it is pulled from Neon accounts.

### Key Entities

- **Override Authorization**: A per-user flag indicating the user has permission to perform override logins. Sourced from NeonOne CRM via a configurable field.
- **Override Login State**: A per-machine state indicating that the machine is currently being operated under an override login, preserving the underlying oops/lockout state for restoration upon card removal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Override-authorized users can activate oopsed or locked-out machines within the normal RFID scan response time (under 2 seconds) without any additional steps.
- **SC-002**: 100% of override logins result in the machine returning to its previous oopsed/locked-out state upon card removal, with zero "cleared" notifications generated.
- **SC-003**: All override login events are logged in the Slack control channel with machine name and user identity.
- **SC-004**: Override login state is accurately reflected in Prometheus metrics within one scrape interval of the state change.
- **SC-005**: Comprehensive test coverage for all override login scenarios, including entry, exit, edge cases (both states, server restart, machine reboot), and Slack notification behavior.
- **SC-006**: All affected documentation pages (admin/monitoring, configuration, Slack integration, NeonOne integration) are updated and accurately describe the override login feature for their respective audiences.

## Assumptions

- The oops override field in NeonOne is a checkbox-style custom field, consistent with how other authorization fields are handled by neongetter.
- Override authorization applies to all machines -- it is not per-machine. Any user with the override authorization can override any machine's oops/lockout state.
- The override capability only activates when a machine is in oopsed or locked-out state. On a machine in normal state, override users behave identically to normal authorized users.
- The "OVERRIDE BY" LCD message follows the same two-line format as the existing "Welcome," message.
- Static fob users in the neongetter config can also be granted override authorization via their static configuration.
