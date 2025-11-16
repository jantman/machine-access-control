# Always-Enabled Machine

Right now, Machines can be configured to accept a list of authorizations and optionally set to `unauthorized_warn_only` mode. I would like to now add another `always_enabled` boolean to the Machine configuration which, if True, causes the machine to ALWAYS be authorized/enabled unless it is Oopsed. When in this state, the display of the machine should read "Always On". Please be sure to update the Machine CONFIG_SCHEMA, the Machine model itself, the MachineState model, all other relevant code, and all relevant documentation.

Please be sure to add unit tests for this new functionality for AT LEAST the following cases:

1. A machine with `always_enabled` True always has `Always On` on its display and always has its relay output turned on, unless Oopsed.
2. A machine with `always_enabled` True exhibits the same Oops behavior as existing tests.
3. A machine with `always_enabled` True does not change state when an RFID card is inserted or removed.
4. A machine with `always_enabled` True becomes enabled immediately when it contacts the server, unless Oopsed.
