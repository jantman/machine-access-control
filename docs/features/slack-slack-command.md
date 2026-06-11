# Slack Slash Command and Case-Insensitive Search

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We need to improve the user experience for clearing machines (oops or maintenance).

1. We should introduce a Slack slash command, `/oops-clear` for this. The slash command should only be usable from the configured control channel (`SLACK_CONTROL_CHANNEL_ID`). When used, it should optionally take the name of the machine to be cleared. If not provided, it should launch a Slack Block Kit Modal which has a single input, a dropdown listing all currently oopsed or locked out machines for the user to select from. There should be no default. Once the user selects the machine from the dropdown and submits the form, the machine should be cleared. Be sure to also include updates to the documentation for this new functionality and the installation process for it.
2. Both the new above slash command as well as the existing bot user mentions should be updated to use case-insensitive matching of machine names.

## Implementation Plan

### Overview

This feature adds a `/oops-clear` Slack slash command (in two forms: a direct
`/oops-clear <machine>` form and an interactive Block Kit modal form) and makes
all machine-name/alias lookups case-insensitive. The slash command is restricted
to the control channel (`SLACK_CONTROL_CHANNEL_ID`).

Both the slash command and existing `@mention` commands resolve machines through
`MachinesConfig.get_machine()`, so making that single method case-insensitive
satisfies requirement 2 for both code paths at once. Doing this first (Milestone
1) also lets later milestones rely on case-insensitive lookups.

The slash command and modal are handled in `slack_handler.py` using the existing
`slack-bolt` `AsyncApp` (already wired through Socket Mode in `__init__.py`), so
no new dependencies or server-startup changes are required. Slack delivers slash
commands and modal (view) submissions over the existing Socket Mode connection;
the only new Slack-app configuration the operator must do is to create the
`/oops-clear` slash command and enable Interactivity (documented in Milestone 4).

Key files to modify:

- `src/dm_mac/models/machine.py`: case-insensitive `get_machine()`.
- `src/dm_mac/slack_handler.py`: register and implement the slash command + modal
  view-submission handlers; refresh `HELP_RESPONSE`.
- `tests/test_slack_handler.py`: unit tests for new handlers and updated `test_init`.
- `tests/models/test_machine.py` (or existing machine-config test): tests for
  case-insensitive `get_machine()`.
- `docs/source/slack.rst`: setup (slash command + interactivity) and usage docs.
- `README.md` / `CLAUDE.md`: brief mentions where appropriate.

### Design Notes / Decisions

- **Channel gating:** Slash commands can be invoked from any channel the user can
  type in, so the handler must explicitly verify `body["channel_id"] ==
  self.control_channel_id`. If not, respond ephemerally (`await ack("...")`) that
  the command is only usable in the control channel and take no action.
- **Direct form (`/oops-clear <machine>`):** Resolve via `get_machine()`. Reuse
  the same clearing logic as the existing mention `clear` command (unoops and/or
  unlock if set). Respond ephemerally with the outcome (cleared / not
  oopsed-or-locked / invalid machine). Clearing itself already posts to the oops
  and control channels via `mach.unoops()` / `mach.unlock()`.
- **Modal form (`/oops-clear` with no argument):** Build the list of machines that
  are currently `is_oopsed` or `is_locked_out`. If none, respond ephemerally
  ("No machines are currently oopsed or locked out.") and do **not** open a modal
  (a `static_select` with zero options is invalid Block Kit). Otherwise open a
  modal via `client.views_open(trigger_id=..., view=...)` containing a single
  required `input` block with a `static_select` element (no `initial_option`, so
  no default). Each option uses the machine `display_name` for `text` and the
  canonical machine `name` for `value`. The view carries `callback_id =
  "oops_clear_modal"`.
- **Modal submission:** Registered via `self.app.view("oops_clear_modal")`. Extract
  the selected machine `name` from
  `body["view"]["state"]["values"][<block_id>][<action_id>]["selected_option"]["value"]`,
  resolve it, and clear it (unoops/unlock). `await ack()` to close the modal. The
  resulting Slack channel posts come from `mach.unoops()` / `mach.unlock()` as
  usual. Guard against the (rare) race where the machine was already cleared
  between modal open and submit.
- **Refactor for reuse:** Extract the shared "clear this machine and report what
  happened" logic into a small helper (e.g. `_clear_machine(mach) -> str` returning
  a human-readable result string) used by the existing mention `clear`, the slash
  command direct form, and the modal submission, to avoid duplicating the
  oopsed/locked-out branching.
- **Registration:** In `SlackHandler.__init__`, after the existing
  `app.event("app_mention")` registration, add
  `self.app.command("/oops-clear")(self.oops_clear_command)` and
  `self.app.view("oops_clear_modal")(self.oops_clear_modal_submit)`. The existing
  `test_init` asserts exact `mock_calls`, so it must be updated to include these.
- **No server-startup changes:** Socket Mode already routes commands and view
  submissions; `__init__.py` needs no change.

### Milestone 1: Case-Insensitive Machine Matching

**Commit prefix:** `slack-slash-command - 1.1` through `slack-slash-command - 1.2`

#### Task 1.1: Make `MachinesConfig.get_machine()` case-insensitive
- In `src/dm_mac/models/machine.py`, build lowercase-keyed lookup dicts
  (`machines_by_name_lower`, `machines_by_alias_lower`) when machines are loaded,
  and update `get_machine()` to look up `name_or_alias.lower()` against them
  (name first, then alias), preserving current return semantics (`Optional[Machine]`).
- Keep the existing `machines_by_name` / `machines_by_alias` dicts intact (they are
  used elsewhere, e.g. status, tests) — only the lookup in `get_machine()` changes.

#### Task 1.2: Tests for case-insensitive lookup
- Add tests verifying `get_machine()` resolves names and aliases regardless of case
  (e.g. `METAL-MILL`, `metal-mill`, `Metal Mill`, `metal mill`) and still returns
  `None` for unknown values.
- This implicitly covers requirement 2 for the existing `@mention` commands, since
  they call `get_machine()`. Add an explicit `app_mention`/`handle_command` test
  using a mixed-case machine name to confirm end-to-end case-insensitivity for
  mentions.

**Milestone close-out:** update this document's progress section, run `nox -s tests`
(all passing), commit.

### Milestone 2: `/oops-clear` Slash Command (Direct Form)

**Commit prefix:** `slack-slash-command - 2.1` through `slack-slash-command - 2.3`

#### Task 2.1: Register the slash command and shared clear helper
- Register `self.app.command("/oops-clear")(self.oops_clear_command)` in
  `__init__`. Update `test_init` expectations accordingly.
- Add `_clear_machine(mach) -> str` helper encapsulating the unoops/unlock branching
  and result message; refactor the existing mention `clear()` to use it.

#### Task 2.2: Implement `oops_clear_command` (direct form + channel gating)
- Handler signature `async def oops_clear_command(self, ack, body, command)` (or
  using `respond`); `await ack(...)` promptly.
- Reject (ephemerally) when `body["channel_id"] != self.control_channel_id`.
- If `command["text"]` (trimmed) is non-empty, treat it as a machine name/alias,
  resolve via `get_machine()`, and clear it with `_clear_machine()`, responding
  ephemerally with the result (cleared / already clear / invalid machine).
- If `command["text"]` is empty, defer to the modal flow added in Milestone 3
  (in this milestone, a placeholder ephemeral response is acceptable, replaced in M3).

#### Task 2.3: Tests for the direct form
- Control channel + valid oopsed machine name → cleared (asserts unoops/unlock and
  ephemeral confirmation).
- Control channel + machine not oopsed/locked → appropriate ephemeral message.
- Control channel + invalid machine name → invalid-machine ephemeral message.
- Non-control channel → rejected ephemerally, no state change.
- Mixed-case machine name → resolves correctly (case-insensitivity through the
  command path).

**Milestone close-out:** update progress section, run `nox -s tests`, commit.

### Milestone 3: Block Kit Modal (Interactive Form)

**Commit prefix:** `slack-slash-command - 3.1` through `slack-slash-command - 3.3`

#### Task 3.1: Open the modal when no machine is given
- In `oops_clear_command`, when no text is supplied, gather machines with
  `state.is_oopsed or state.is_locked_out`.
- If empty → ephemeral "No machines are currently oopsed or locked out."
- Otherwise build the modal view (single required `input` block, `static_select`,
  no default, `callback_id="oops_clear_modal"`) and call
  `client.views_open(trigger_id=body["trigger_id"], view=view)` after `ack()`.
- Add a small builder method (e.g. `_build_clear_modal(machines) -> dict`) so the
  view structure is unit-testable in isolation.

#### Task 3.2: Handle modal submission
- Register `self.app.view("oops_clear_modal")(self.oops_clear_modal_submit)` in
  `__init__` (update `test_init`).
- Extract the selected machine `value`, resolve it, clear via `_clear_machine()`,
  and `await ack()`. Handle the already-cleared/missing-machine race gracefully.

#### Task 3.3: Tests for the modal flow
- No-argument command with one or more oopsed/locked machines → `views_open` called
  with a view whose options match exactly the oopsed/locked machines (text =
  display_name, value = name), no `initial_option`.
- No-argument command with nothing oopsed/locked → ephemeral message, `views_open`
  not called.
- Modal submission → selected machine cleared (unoops/unlock invoked), `ack` called.
- Modal submission for a machine already cleared → graceful handling, no error.

**Milestone close-out:** update progress section, run `nox -s tests`, commit.

### Milestone 4: Acceptance Criteria

**Commit prefix:** `slack-slash-command - 4.1` through `slack-slash-command - 4.4`

#### Task 4.1: Documentation
- `docs/source/slack.rst`:
  - **Setup:** add steps to create the `/oops-clear` slash command (Features →
    Slash Commands → Create New Command; command `/oops-clear`, a short
    description, and a usage hint such as `[machine name]`) and to enable
    Interactivity (Features → Interactivity & Shortcuts → toggle on) so modal
    submissions are delivered. Note that with Socket Mode no Request URL is needed.
    Reinstall the app if Slack prompts that new scopes/commands require it.
  - **Usage:** document `/oops-clear` (control-channel only), both the direct
    `/oops-clear <machine name>` form and the no-argument modal form, and that name
    matching is case-insensitive (for both slash command and mentions).
- Refresh `HELP_RESPONSE` and any README/CLAUDE.md references as needed, matching
  existing style/tone/verbosity.

#### Task 4.2: Test coverage
- Ensure all new code paths in `slack_handler.py` and `machine.py` have unit-test
  coverage (`nox -s tests`).

#### Task 4.3: All nox sessions pass
- Run and ensure passing: `nox -s tests`, `nox -s pre-commit`, `nox -s mypy`,
  `nox -s typeguard`, `nox -s docs` (and `safety` if part of the standard gate).
- Fix any lint/type/format issues introduced.

#### Task 4.4: Finalize
- Update this document marking the feature complete, then move it from
  `docs/features/slack-slack-command.md` to
  `docs/features/completed/slack-slack-command.md`. Commit.

## Decisions (confirmed)

- **No ephemeral success confirmation:** On a successful clear, the slash command
  silently `ack()`s (no extra reply), relying on the existing oops/control channel
  posts — matching the existing mention `clear` behavior. Ephemeral responses are
  still used for *error/edge* cases (wrong channel, invalid machine, machine not
  oopsed/locked, nothing to clear in the modal flow), since those produce no channel
  post otherwise. (Note: a slash command must still call `ack()` within 3 s to avoid
  Slack showing a failure; a silent `await ack()` satisfies this.)
- **Generic source label:** Channel messages keep the generic `"Slack"` source
  already hard-coded in the `Machine` model methods. No `Machine` model changes for
  source attribution.

## Progress

- Planning complete; awaiting human approval before implementation.
</content>
</invoke>
