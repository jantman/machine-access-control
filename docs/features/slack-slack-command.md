# Slack Slash Command and Case-Insensitive Search

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We need to improve the user experience for clearing machines (oops or maintenance).

1. We should introduce a Slack slash command, `/oops-clear` for this. The slash command should only be usable from the configured control channel (`SLACK_CONTROL_CHANNEL_ID`). When used, it should optionally take the name of the machine to be cleared. If not provided, it should launch a Slack Block Kit Modal which has a single input, a dropdown listing all currently oopsed or locked out machines for the user to select from. There should be no default. Once the user selects the machine from the dropdown and submits the form, the machine should be cleared. Be sure to also include updates to the documentation for this new functionality and the installation process for it.
2. Both the new above slash command as well as the existing bot user mentions should be updated to use case-insensitive matching of machine names.
