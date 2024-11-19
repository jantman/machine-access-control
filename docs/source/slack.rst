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
5. Go back to the main settings for your app and navigate to ``Socket Mode`` under ``Settings`` on the left menu; toggle on ``Enable Socket Mode``. For ``Token Name``, enter ``socket-mode-token`` and click ``Generate``. Copy the generated token and set it as the ``SLACK_APP_TOKEN`` environment variable for the MAC server **TBD is this needed? document on config page.**
6. Go back to the main settings for your app and navigate to ``Basic Information`` under ``Settings`` on the left menu; in the ``App Credentials`` pane click ``Show`` in the ``Signing Secret`` box and then copy that value; set it as the ``SLACK_SIGNING_SECRET`` environment variable for the MAC server.

.. _slack.configuration:

Configuration
-------------

TBD.

.. _slack.usage:

Usage
-----

TBD.
