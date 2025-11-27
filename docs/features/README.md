# Features

This directory contains markdown files describing features that we want to implement for this project. Each feature initially just includes a human-generated explanation; for each feature you (Claude Code, the AI coding assistant) will update that document to include an implementation plan to resolve the feature and then await human approval before proceeding. You are encouraged to solicit human input/feedback during the planning phase for anything you have questions about or do not feel is clear. Once planning is complete, if you get confused or are unable to accomplish a feature without significant issues, please ask for human feedback. You MUST plan one feature at a time, in order, and then implement that feature. As earlier features may inform or change the implementation of later ones, we will work one feature at a time from planning through implementation, completion, and human validation, before moving on to the next.

The following guidelines MUST always be followed:

* Features that are non-trivial in size (i.e. more than a few simple changes) should be broken down into Milestones and Tasks. Those will be given a prefix to be used in commit messages, formatted as `{Feature Name} - {Milestone number}.{Task number}`. Human approval must always be obtained to move from one Milestone to the next.
* At the end of every Milestone and Feature you must (in order):
  1. Update the feature markdown document to indicate what progress has been made on the relevant Milestone or Feature.
  2. Run all `nox` tests and ensure that ALL tests are passing. You MAY NOT consider a Milestone complete until ALL tests that were passing at the beginning of the Milestone are still passing, unless given explicit human approval to defer testing until later.
  3. Commit that along with all changes to git, using a commit message beginning with the Milestone/Task prefix and a one-sentence concise summary of the changes followed by a detailed explanation of the changes.
* Every feature must end with an "Acceptance Criteria" Milestone. This Milestone must include tasks to:
  1. Ensure that all appropriate documentation (`README.md`, `docs/source/`, and `CLAUDE.md`) is updated as needed for the work done as part of the feature. Documentation should be easily readable, concise, and a match to the style, tone, and verbosity of the existing documentation.
  2. All code changes have appropriate unit test (`nox -s tests`) coverage.
  3. ALL nox sessions must be passing successfully.
  4. As the last step of every feature, move the feature markdown file from `docs/features/` to `docs/features/completed/`.
* If you become confused or unclear on how to proceed, have to make a significant decision not explicitly included in the implementation plan, or find yourself making changes and then undoing them without a clear and certain path forward, you must stop and ask for human guidance.
* From time to time we may identify a new, more pressing issue while implementing a feature; we refer to these as "side quests". When beginning a side quest you must update this document to include detailed information on exactly where we're departing from our feature implementation, such that we could use this document to resume from where we left off in a new session, and then commit that. When the side quest is complete, we will resume our feature work.
