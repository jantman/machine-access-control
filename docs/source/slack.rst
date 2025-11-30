.. _slack:

Slack Integration
=================

machine-access-control (MAC) offers a Slack integration for logging and control.

.. _slack.setup:

Setup
-----

To set up the Slack integration:

1. `Create a new Slack app <https://api.slack.com/apps?new_app=1&track=hello-world-bolt>`_

   1. Create your new app "from scratch".
   2. Set a meaningful name, such as ``machine-access-control`` and create the app in your Workspace.
   3. In the left menu, navigate to ``OAuth & Permissions``.
   4. In the "Scopes" pane, under "Bot Token Scopes", click "Add an OAuth Scope" and add scopes for ``app_mentions:read``, ``canvases:read``, ``canvases:write``, ``channels:read``, ``chat:write``, ``groups:read``, ``groups:write``, ``incoming-webhook``, ``users.profile:read``, and ``users:read``.

2. In your workspace, create a new private channel for admins to interact with MAC in, and MAC to post status updates to.
3. In the left menu, navigate to ``Install App``. Click on the button to install to your workspace. When prompted for a channel for the app to post in, select the private channel that you created in the previous step.
4. On the next screen, ``Installed App Settings``, copy the ``Bot User OAuth Token`` and set this as the ``SLACK_BOT_TOKEN`` environment variable for the MAC server.
5. Go back to the main settings for your app and navigate to ``Socket Mode`` under ``Settings`` on the left menu; toggle on ``Enable Socket Mode``. For ``Token Name``, enter ``socket-mode-token`` and click ``Generate``. Copy the generated token and set it as the ``SLACK_APP_TOKEN`` environment variable for the MAC server. If you need to retrieve this token later, it can be found in the ``App-Level Tokens`` pane of the ``Settings -> Basic Information`` page.
6. Go back to the main settings for your app and navigate to ``Basic Information`` under ``Settings`` on the left menu; in the ``App Credentials`` pane click ``Show`` in the ``Signing Secret`` box and then copy that value; set it as the ``SLACK_SIGNING_SECRET`` environment variable for the MAC server.
7. Go back to the main settings for your app and navigate to ``Event Subscriptions`` under ``Features`` on the left menu; click the toggle in the upper left of the panel to Enable Events; under ``Subscribe to bot events`` add a subscription for ``app_mention``.

.. _slack.configuration:

Configuration
-------------

1. Set :ref:`configuration.env-vars` as described in :ref:`slack.setup`, above.
2. If you don't already have one, create a private channel for the people who will be allowed to control MAC (i.e. clear Oopses and lock-out/unlock machines).
3. Invite your bot user to that channel by at-mentioning the bot username.
4. In that channel, click on the channel name to pull up the channel information tab, and copy the Channel ID (a string beginning with "C") from the bottom of that panel. Set this as the ``SLACK_CONTROL_CHANNEL_ID`` environment variable.
5. If you don't already have one, create a public channel for the bot to post Oops/maintenance notices in. Invite the bot to that channel via an at-mention. Get the Channel ID and set it as the ``SLACK_OOPS_CHANNEL_ID`` environment variable. Users in this channel will also be able to check machine status.


.. _slack.usage:

Usage
-----

The slack bot is controlled by mentioning its name (``@your-bot-name``) along with a command and optional arguments, in the ``SLACK_CONTROL_CHANNEL_ID`` channel (or, for the status command, any channel that the bot is in).

Using an example bot name of ``@machine-access-control``, the supported commands are:

* ``@machine-access-control status`` - List all machines and their current status. This command is the only one that is usable from channels other than the control channel.
* ``@machine-access-control oops <machine-name>`` - Set Oops'ed status on the machine with name ``machine-name``. This takes effect immediately, even if the machine is currently in use. You can use either the machine name or its alias (if configured).
* ``@machine-access-control lock <machine-name>`` - Set maintenance lock-out status on the machine with name ``machine-name``. This takes effect immediately, even if the machine is currently in use. You can use either the machine name or its alias (if configured).
* ``@machine-access-control clear <machine-name>`` - Clear all Oops and/or maintenance lock-out states on the machine with name ``machine-name``. You can use either the machine name or its alias (if configured).

**Note:** If a machine has an ``alias`` configured in ``machines.json``, the bot's responses will use the alias instead of the machine name for better readability.

In addition, changes to all machines' Oops and maintenance lock-out states will be posted as messages in the ``SLACK_OOPS_CHANNEL_ID`` channel.
